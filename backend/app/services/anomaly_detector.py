import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app.models.digital_twin import DigitalTwinBaseline
from app.models.health import HealthTelemetry
from app.schemas.ai import (
    AIAnalysisResult,
    AnomalyDetail,
    MEDICAL_DISCLAIMER,
    VitalReadingsInput,
)
from app.services.digital_twin_service import DigitalTwinService, MIN_BASELINE_SAMPLES

logger = logging.getLogger("pulseguardian.anomaly_detector")

MIN_ISOLATION_FOREST_SAMPLES = 30
STALE_THRESHOLD_MINUTES = 15


class AnomalyDetectorService:
    """
    AI Anomaly Detection Engine.
    Combines:
    1. Patient-specific Digital Twin baseline deviations (Z-score & personalized bounds)
    2. Circadian time-of-day contextual analysis
    3. Multi-signal physiological correlation (e.g. resting HR vs step exertion, cardiorespiratory stress)
    4. Scikit-learn multivariate Isolation Forest (when sufficient data exists)
    5. Acute physiological redlines & fall impact detection
    """

    @staticmethod
    def analyze_vitals(
        db: Session,
        patient_id: int,
        vitals_input: Optional[VitalReadingsInput] = None,
        telemetry_id: Optional[int] = None
    ) -> AIAnalysisResult:
        """
        Analyzes vitals for a given patient.
        If vitals_input is not provided, extracts the latest telemetry record from the database.
        """
        # 1. Fetch or resolve vitals to evaluate
        telemetry_record = None
        if vitals_input is None:
            telemetry_record = db.query(HealthTelemetry).filter(
                HealthTelemetry.patient_id == patient_id
            ).order_by(HealthTelemetry.recorded_at.desc()).first()

            if not telemetry_record:
                # No data recorded at all
                baseline, cold_start = DigitalTwinService.get_or_calculate_baseline(db, patient_id)
                now = datetime.now(timezone.utc)
                return AIAnalysisResult(
                    patient_id=patient_id,
                    analysis_timestamp=now,
                    overall_status="normal",
                    severity="normal",
                    confidence_score=0.9,
                    data_quality_status="incomplete",
                    personal_baseline={
                        "resting_hr": baseline.baseline_resting_hr,
                        "spo2": baseline.baseline_spo2,
                        "temperature": baseline.baseline_temperature,
                        "cold_start": cold_start,
                        "samples_count": baseline.samples_count,
                    },
                    current_readings={},
                    detected_anomalies=[],
                    isolation_forest_triggered=False,
                    explanation="No health telemetry records found for this patient. Awaiting wearable data.",
                    recommendations=["Connect the wearable device to start tracking personal health telemetry."],
                    medical_disclaimer=MEDICAL_DISCLAIMER,
                )

            current_hr = telemetry_record.heart_rate
            current_spo2 = telemetry_record.spo2
            current_temp = telemetry_record.temperature
            temp_unit = telemetry_record.temperature_unit
            step_count = telemetry_record.step_count or 0
            activity_type = telemetry_record.activity_type or "resting"
            fall_detected = telemetry_record.fall_detected or False
            recorded_at = telemetry_record.recorded_at
            battery_pct = telemetry_record.battery_percentage
            target_telemetry_id = telemetry_record.id
        else:
            current_hr = vitals_input.heart_rate
            current_spo2 = vitals_input.spo2
            current_temp = vitals_input.temperature
            temp_unit = vitals_input.temperature_unit
            step_count = vitals_input.step_count or 0
            activity_type = vitals_input.activity_type or "resting"
            fall_detected = vitals_input.fall_detected or False
            recorded_at = vitals_input.recorded_at or datetime.now(timezone.utc)
            battery_pct = vitals_input.battery_percentage
            target_telemetry_id = telemetry_id

        # Normalize temperature to Celsius
        if current_temp is not None and temp_unit.upper() == "F":
            current_temp_c = round((current_temp - 32.0) * (5.0 / 9.0), 2)
        else:
            current_temp_c = current_temp

        # 2. Get personal Digital Twin baseline
        baseline, is_cold_start = DigitalTwinService.get_or_calculate_baseline(db, patient_id)

        # 3. Assess Data Quality
        data_quality = AnomalyDetectorService._evaluate_data_quality(
            current_hr, current_spo2, current_temp_c, recorded_at
        )

        # 4. Detect Anomalies across all tiers
        detected_anomalies: List[AnomalyDetail] = []
        scores: List[float] = []
        explanations: List[str] = []

        # A. Fall Detection (Acute)
        if fall_detected:
            detected_anomalies.append(AnomalyDetail(
                parameter="fall_impact",
                current_value=1.0,
                baseline_value=0.0,
                deviation=1.0,
                unit="status",
                severity="critical",
                explanation="High-impact fall pattern detected by wearable accelerometer."
            ))
            scores.append(0.95)
            explanations.append("Fall impact detected by wearable accelerometer.")

        # B. Heart Rate Evaluation (Baseline + Circadian + Acute)
        if current_hr is not None:
            # Acute Redlines
            if current_hr < 45.0:
                detected_anomalies.append(AnomalyDetail(
                    parameter="heart_rate",
                    current_value=current_hr,
                    baseline_value=baseline.baseline_resting_hr,
                    deviation=round(current_hr - baseline.baseline_resting_hr, 1),
                    unit="BPM",
                    severity="high",
                    explanation=f"Severe bradycardia: Heart rate is critically low at {current_hr:.1f} BPM."
                ))
                scores.append(0.85)
                explanations.append(f"Bradycardia alert: Low heart rate ({current_hr:.1f} BPM).")
            elif current_hr > 130.0 and (activity_type == "resting" or step_count < 15):
                detected_anomalies.append(AnomalyDetail(
                    parameter="heart_rate",
                    current_value=current_hr,
                    baseline_value=baseline.baseline_resting_hr,
                    deviation=round(current_hr - baseline.baseline_resting_hr, 1),
                    unit="BPM",
                    severity="high",
                    explanation=f"Acute resting tachycardia: Heart rate {current_hr:.1f} BPM is elevated without physical exertion."
                ))
                scores.append(0.80)
                explanations.append(f"Resting tachycardia alert: Elevated heart rate ({current_hr:.1f} BPM at rest).")
            else:
                # Personal Baseline Statistical Comparison (Z-score)
                std_dev = max(baseline.hr_std_dev, 3.0)
                z_score = (current_hr - baseline.baseline_resting_hr) / std_dev

                if activity_type == "resting":
                    if z_score >= 3.0 or current_hr > baseline.hr_max_normal:
                        severity = "high" if z_score >= 3.5 else "moderate"
                        score = min(0.65 + 0.05 * (z_score - 3.0), 0.85)
                        detected_anomalies.append(AnomalyDetail(
                            parameter="heart_rate",
                            current_value=current_hr,
                            baseline_value=baseline.baseline_resting_hr,
                            deviation=round(z_score, 2),
                            unit="Z-score (BPM)",
                            severity=severity,
                            explanation=(
                                f"Heart rate {current_hr:.1f} BPM is +{z_score:.1f} standard deviations "
                                f"above personal resting baseline ({baseline.baseline_resting_hr:.1f} ± {std_dev:.1f} BPM)."
                            )
                        ))
                        scores.append(score)
                        explanations.append(f"Resting heart rate (+{z_score:.1f}σ) exceeds personal baseline.")
                    elif z_score <= -3.0 or current_hr < baseline.hr_min_normal:
                        detected_anomalies.append(AnomalyDetail(
                            parameter="heart_rate",
                            current_value=current_hr,
                            baseline_value=baseline.baseline_resting_hr,
                            deviation=round(z_score, 2),
                            unit="Z-score (BPM)",
                            severity="moderate",
                            explanation=(
                                f"Heart rate {current_hr:.1f} BPM is {z_score:.1f} standard deviations "
                                f"below personal resting baseline ({baseline.baseline_resting_hr:.1f} ± {std_dev:.1f} BPM)."
                            )
                        ))
                        scores.append(0.60)
                        explanations.append(f"Resting heart rate ({z_score:.1f}σ) below personal baseline.")

                # Circadian nocturnal check (between 23:00 and 06:00 UTC)
                hour = recorded_at.hour
                if (hour >= 23 or hour <= 6) and current_hr > (baseline.baseline_resting_hr + 15.0) and activity_type == "resting":
                    explanations.append("Nocturnal elevated heart rate noted during typical sleep window.")

        # C. SpO2 Blood Oxygen Evaluation
        if current_spo2 is not None:
            if current_spo2 < 90.0:
                severity = "critical" if current_spo2 < 88.0 else "high"
                score = 0.90 if severity == "critical" else 0.80
                detected_anomalies.append(AnomalyDetail(
                    parameter="spo2",
                    current_value=current_spo2,
                    baseline_value=baseline.baseline_spo2,
                    deviation=round(current_spo2 - baseline.baseline_spo2, 1),
                    unit="%",
                    severity=severity,
                    explanation=f"Severe hypoxemia: Blood oxygen saturation ({current_spo2:.1f}%) is critically low."
                ))
                scores.append(score)
                explanations.append(f"Hypoxemia alert: SpO2 {current_spo2:.1f}% is critically low.")
            elif current_spo2 < baseline.spo2_min_normal:
                drop = round(baseline.baseline_spo2 - current_spo2, 1)
                detected_anomalies.append(AnomalyDetail(
                    parameter="spo2",
                    current_value=current_spo2,
                    baseline_value=baseline.baseline_spo2,
                    deviation=drop,
                    unit="%",
                    severity="moderate",
                    explanation=f"Blood oxygen {current_spo2:.1f}% dropped below personal normal threshold ({baseline.spo2_min_normal:.1f}%)."
                ))
                scores.append(0.55 + 0.05 * (baseline.spo2_min_normal - current_spo2))
                explanations.append(f"SpO2 {current_spo2:.1f}% dropped below personal baseline threshold.")

        # D. Body Temperature Evaluation
        if current_temp_c is not None:
            if current_temp_c > 39.0:
                detected_anomalies.append(AnomalyDetail(
                    parameter="temperature",
                    current_value=current_temp_c,
                    baseline_value=baseline.baseline_temperature,
                    deviation=round(current_temp_c - baseline.baseline_temperature, 2),
                    unit="°C",
                    severity="high",
                    explanation=f"High fever: Body temperature is {current_temp_c:.1f}°C."
                ))
                scores.append(0.75)
                explanations.append(f"Fever alert: Body temperature {current_temp_c:.1f}°C.")
            elif current_temp_c < 35.0:
                detected_anomalies.append(AnomalyDetail(
                    parameter="temperature",
                    current_value=current_temp_c,
                    baseline_value=baseline.baseline_temperature,
                    deviation=round(current_temp_c - baseline.baseline_temperature, 2),
                    unit="°C",
                    severity="high",
                    explanation=f"Hypothermia: Body temperature is {current_temp_c:.1f}°C."
                ))
                scores.append(0.75)
                explanations.append(f"Hypothermia alert: Body temperature {current_temp_c:.1f}°C.")
            elif current_temp_c > baseline.temp_max_normal:
                detected_anomalies.append(AnomalyDetail(
                    parameter="temperature",
                    current_value=current_temp_c,
                    baseline_value=baseline.baseline_temperature,
                    deviation=round(current_temp_c - baseline.baseline_temperature, 2),
                    unit="°C",
                    severity="moderate",
                    explanation=f"Mild hyperthermia: Temperature {current_temp_c:.1f}°C exceeds personal normal envelope ({baseline.temp_max_normal:.1f}°C)."
                ))
                scores.append(0.50)
                explanations.append(f"Temperature deviation: {current_temp_c:.1f}°C is elevated.")
            elif current_temp_c < baseline.temp_min_normal:
                detected_anomalies.append(AnomalyDetail(
                    parameter="temperature",
                    current_value=current_temp_c,
                    baseline_value=baseline.baseline_temperature,
                    deviation=round(current_temp_c - baseline.baseline_temperature, 2),
                    unit="°C",
                    severity="moderate",
                    explanation=f"Subnormal body temperature: {current_temp_c:.1f}°C is below personal normal baseline envelope."
                ))
                scores.append(0.50)
                explanations.append(f"Temperature deviation: {current_temp_c:.1f}°C is below baseline envelope.")

        # E. Multi-Signal Pattern Correlations
        if current_hr is not None and current_spo2 is not None:
            if current_hr > 100.0 and current_spo2 < 93.0 and activity_type == "resting":
                detected_anomalies.append(AnomalyDetail(
                    parameter="multi_signal",
                    current_value=current_hr,
                    baseline_value=baseline.baseline_resting_hr,
                    deviation=None,
                    unit="HR+SpO2",
                    severity="high",
                    explanation="Cardiorespiratory stress pattern: Concurrent low oxygen saturation and compensatory resting tachycardia."
                ))
                scores.append(0.85)
                explanations.append("Multi-signal cardiorespiratory stress pattern detected.")

        if current_temp_c is not None and current_hr is not None:
            if current_temp_c > 37.8 and current_hr > 100.0 and activity_type == "resting":
                detected_anomalies.append(AnomalyDetail(
                    parameter="multi_signal",
                    current_value=current_temp_c,
                    baseline_value=baseline.baseline_temperature,
                    deviation=None,
                    unit="Temp+HR",
                    severity="moderate",
                    explanation="Febrile stress pattern: Concurrent elevated body temperature and elevated resting heart rate."
                ))
                scores.append(0.65)
                explanations.append("Multi-signal febrile response pattern detected.")

        # F. Scikit-learn Isolation Forest Multivariate Outlier Detection
        if_triggered, if_score, if_explanation = AnomalyDetectorService._run_isolation_forest(
            db, patient_id, current_hr, current_spo2, current_temp_c, step_count, baseline
        )
        if if_triggered:
            detected_anomalies.append(AnomalyDetail(
                parameter="multi_signal",
                current_value=round(if_score, 3) if if_score else None,
                baseline_value=0.0,
                deviation=round(if_score, 3) if if_score else None,
                unit="Outlier Score",
                severity="moderate",
                explanation=if_explanation
            ))
            scores.append(min(max((if_score or 0.5) * 1.5, 0.55), 0.85))
            explanations.append(if_explanation)

        # 5. Composite Severity, Confidence, and Overall Status
        if not detected_anomalies:
            overall_status = "normal"
            severity = "normal"
            confidence_score = 0.95
            composite_explanation = "All monitored vital signs are within normal personal baseline and expected physiological limits."
        else:
            max_score = max(scores) if scores else 0.5
            has_critical = any(a.severity == "critical" for a in detected_anomalies)
            has_high = any(a.severity == "high" for a in detected_anomalies)

            if has_critical:
                severity = "critical"
                overall_status = "anomalous"
            elif has_high or max_score >= 0.70:
                severity = "high"
                overall_status = "anomalous"
            elif max_score >= 0.45:
                severity = "moderate"
                overall_status = "cautionary"
            else:
                severity = "low"
                overall_status = "cautionary"

            # Confidence score based on sample richness & data quality
            if is_cold_start:
                confidence_score = round(min(0.75 + (baseline.samples_count / MIN_BASELINE_SAMPLES) * 0.15, 0.90), 2)
            else:
                confidence_score = 0.94 if data_quality == "good" else 0.82

            composite_explanation = " | ".join(dict.fromkeys(explanations))

        # 6. Actionable Non-Diagnostic Recommendations
        recommendations = AnomalyDetectorService._generate_recommendations(
            severity, detected_anomalies, current_hr, current_spo2, current_temp_c, fall_detected
        )

        # 7. Update Telemetry Record in DB if linked
        if target_telemetry_id:
            record_to_update = db.query(HealthTelemetry).filter(
                HealthTelemetry.id == target_telemetry_id
            ).first()
            if record_to_update:
                record_to_update.is_anomalous = len(detected_anomalies) > 0
                record_to_update.anomaly_score = max(scores) if scores else 0.0
                record_to_update.anomaly_reason = composite_explanation if detected_anomalies else None
                db.commit()

        # 8. Build structured output
        now = datetime.now(timezone.utc)
        return AIAnalysisResult(
            patient_id=patient_id,
            analysis_timestamp=now,
            overall_status=overall_status,
            severity=severity,
            confidence_score=confidence_score,
            data_quality_status=data_quality,
            personal_baseline={
                "resting_hr": baseline.baseline_resting_hr,
                "hr_min_normal": baseline.hr_min_normal,
                "hr_max_normal": baseline.hr_max_normal,
                "spo2": baseline.baseline_spo2,
                "spo2_min_normal": baseline.spo2_min_normal,
                "temperature": baseline.baseline_temperature,
                "cold_start": is_cold_start,
                "samples_count": baseline.samples_count,
            },
            current_readings={
                "heart_rate": current_hr,
                "spo2": current_spo2,
                "temperature": current_temp_c,
                "temperature_unit": "C",
                "step_count": step_count,
                "activity_type": activity_type,
                "fall_detected": fall_detected,
                "battery_percentage": battery_pct,
                "recorded_at": recorded_at,
            },
            detected_anomalies=detected_anomalies,
            isolation_forest_triggered=if_triggered,
            isolation_forest_score=if_score,
            explanation=composite_explanation,
            recommendations=recommendations,
            medical_disclaimer=MEDICAL_DISCLAIMER,
        )

    @staticmethod
    def _evaluate_data_quality(
        hr: Optional[float],
        spo2: Optional[float],
        temp: Optional[float],
        recorded_at: datetime
    ) -> str:
        """Determines data quality status ('good', 'fair', 'stale', 'incomplete', 'sensor_noise')."""
        if hr is None and spo2 is None and temp is None:
            return "incomplete"

        # Check extreme physical implausibility
        if (hr is not None and (hr < 25.0 or hr > 260.0)) or \
           (spo2 is not None and (spo2 < 40.0 or spo2 > 100.0)) or \
           (temp is not None and (temp < 25.0 or temp > 46.0)):
            return "sensor_noise"

        # Check staleness
        now = datetime.now(timezone.utc)
        rec_time = recorded_at if recorded_at.tzinfo else recorded_at.replace(tzinfo=timezone.utc)
        if (now - rec_time).total_seconds() > (STALE_THRESHOLD_MINUTES * 60):
            return "stale"

        # If partial readings missing
        if hr is None or spo2 is None or temp is None:
            return "fair"

        return "good"

    @staticmethod
    def _run_isolation_forest(
        db: Session,
        patient_id: int,
        hr: Optional[float],
        spo2: Optional[float],
        temp: Optional[float],
        step_count: int,
        baseline: DigitalTwinBaseline
    ) -> Tuple[bool, Optional[float], str]:
        """
        Executes Scikit-learn Isolation Forest on multi-signal feature vector
        if sufficient historical readings exist for the patient.
        """
        readings = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == patient_id
        ).order_by(HealthTelemetry.recorded_at.desc()).limit(300).all()

        if len(readings) < MIN_ISOLATION_FOREST_SAMPLES:
            return False, None, "Insufficient sample size for multivariate Isolation Forest modeling."

        # Prepare feature matrix: [heart_rate, spo2, temperature, step_count]
        records = []
        for r in readings:
            t = r.temperature
            if t is not None and r.temperature_unit == "F":
                t = (t - 32.0) * (5.0 / 9.0)

            # Impute missing values with personal baseline defaults
            records.append([
                r.heart_rate if r.heart_rate is not None else baseline.baseline_resting_hr,
                r.spo2 if r.spo2 is not None else baseline.baseline_spo2,
                t if t is not None else baseline.baseline_temperature,
                float(r.step_count or 0),
            ])

        if len(records) < MIN_ISOLATION_FOREST_SAMPLES:
            return False, None, "Insufficient data matrix for Isolation Forest."

        try:
            X = np.array(records)
            clf = IsolationForest(
                n_estimators=50,
                contamination=0.05,
                random_state=42
            )
            clf.fit(X)

            # Prepare current sample vector
            current_vector = np.array([[
                hr if hr is not None else baseline.baseline_resting_hr,
                spo2 if spo2 is not None else baseline.baseline_spo2,
                temp if temp is not None else baseline.baseline_temperature,
                float(step_count or 0),
            ]])

            pred = clf.predict(current_vector)[0]
            score = -clf.decision_function(current_vector)[0]

            if pred == -1:
                return True, round(float(score), 3), (
                    f"Multivariate Isolation Forest identified an outlier physiological cluster "
                    f"(anomaly score: {score:.3f})."
                )
            return False, round(float(score), 3), "Isolation Forest evaluated reading within historical cluster."
        except Exception as e:
            logger.warning(f"Isolation Forest execution error: {e}")
            return False, None, "Isolation Forest execution bypassed."

    @staticmethod
    def _generate_recommendations(
        severity: str,
        detected_anomalies: List[AnomalyDetail],
        hr: Optional[float],
        spo2: Optional[float],
        temp: Optional[float],
        fall_detected: bool
    ) -> List[str]:
        """Provides actionable, non-diagnostic guidance according to detected status."""
        recs = []

        if fall_detected:
            recs.append("Ensure immediate patient safety. Use SOS emergency button if physical assistance is required.")

        if any(a.parameter == "heart_rate" for a in detected_anomalies):
            if hr and hr > 110.0:
                recs.append("Sit down in a comfortable position and rest for 5 minutes. Re-check heart rate once relaxed.")
            elif hr and hr < 50.0:
                recs.append("Low heart rate detected. If feeling lightheaded or weak, sit or lie down and alert your caregiver.")

        if any(a.parameter == "spo2" for a in detected_anomalies):
            recs.append("Verify the pulse oximeter sensor has snug contact with your skin. Take deep, slow breaths.")

        if any(a.parameter == "temperature" for a in detected_anomalies):
            if temp and temp > 37.8:
                recs.append("Stay hydrated and rest in a well-ventilated room. Re-measure temperature periodically.")

        if severity in ("critical", "high"):
            recs.append("Alert your primary caregiver or healthcare provider if acute symptoms persist or worsen.")
        elif severity == "normal":
            recs.append("Your physiological metrics are consistent with your personal baseline. Keep up your healthy routine.")

        return recs
