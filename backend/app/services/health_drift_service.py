import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.digital_twin import DigitalTwinBaseline, HealthDriftRecord
from app.models.health import HealthTelemetry
from app.schemas.ai import MEDICAL_DISCLAIMER
from app.schemas.health_drift import (
    DriftDataPoint,
    HealthDriftTimelineItem,
    HealthDriftTimelineResponse,
    MetricDriftResult,
    OverallHealthDriftSummary,
)
from app.services.digital_twin_service import DigitalTwinService

logger = logging.getLogger("pulseguardian.health_drift")

# Baseline defaults for lifestyle metrics if not explicitly learned
DEFAULT_SLEEP_BASELINE_HOURS = 7.5
DEFAULT_STEPS_BASELINE = 5000.0


class HealthDriftService:
    """
    Health Drift Intelligence Service.
    Analyzes historical physiological and activity patterns across 3d, 7d, 30d (or custom) windows.
    Detects gradual upward and downward trajectory shifts using EWMA, moving averages, and linear trend slopes.
    Differentiates transient fluctuations from persistent health drift.
    """

    @staticmethod
    def analyze_drift(
        db: Session,
        patient_id: int,
        window_days: int = 7,
        metrics_to_analyze: Optional[List[str]] = None,
        persist: bool = True
    ) -> OverallHealthDriftSummary:
        """
        Analyzes multi-signal health drift across the configured evaluation window.
        """
        now = datetime.now(timezone.utc)
        period_end = now
        period_start = now - timedelta(days=window_days)

        # 1. Retrieve patient's digital twin baseline
        baseline, is_cold_start = DigitalTwinService.get_or_calculate_baseline(db, patient_id)

        # 2. Query historical telemetry within the requested window
        readings = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == patient_id,
            HealthTelemetry.recorded_at >= period_start,
            HealthTelemetry.recorded_at <= period_end
        ).order_by(HealthTelemetry.recorded_at.asc()).all()

        target_metrics = metrics_to_analyze or ["heart_rate", "spo2", "temperature", "sleep_duration", "daily_steps"]
        daily_df = HealthDriftService._build_daily_dataframe(readings)

        # 3. Analyze each metric
        metric_results: Dict[str, MetricDriftResult] = {}
        persisted_records: List[HealthDriftRecord] = []

        for metric in target_metrics:
            res = HealthDriftService._evaluate_metric_drift(
                daily_df=daily_df,
                metric_name=metric,
                baseline=baseline,
                window_days=window_days
            )
            metric_results[metric] = res

            # Persist significant or mild drift records if enabled
            if persist and res.significance not in ("stable", "insufficient_data"):
                drift_rec = HealthDriftRecord(
                    patient_id=patient_id,
                    period_start=period_start,
                    period_end=period_end,
                    drift_parameter=metric,
                    baseline_value=res.baseline_value,
                    current_period_value=res.current_value or res.baseline_value,
                    drift_delta=res.drift_delta or 0.0,
                    drift_percentage=res.drift_percentage or 0.0,
                    significance=res.significance,
                    ai_recommendation=res.explanation,
                    created_at=now
                )
                persisted_records.append(drift_rec)

        if persisted_records:
            db.add_all(persisted_records)
            db.commit()

        # 4. Multi-window trends (3d, 7d, 30d comparisons)
        multi_window = HealthDriftService._compute_multi_window_trends(db, patient_id, baseline, readings)

        # 5. Overall status and data completeness
        recorded_days = len(daily_df) if not daily_df.empty else 0
        completeness_pct = round(min((recorded_days / max(window_days, 1)) * 100.0, 100.0), 1)

        overall_status, overall_conf = HealthDriftService._determine_overall_drift(
            metric_results, recorded_days, window_days
        )

        key_findings = HealthDriftService._generate_key_findings(metric_results)
        recommendations = HealthDriftService._generate_guidance(metric_results, overall_status)

        return OverallHealthDriftSummary(
            patient_id=patient_id,
            analysis_timestamp=now,
            window_days=window_days,
            period_start=period_start,
            period_end=period_end,
            overall_drift_status=overall_status,
            overall_confidence=overall_conf,
            data_completeness_percentage=completeness_pct,
            metrics_summary=metric_results,
            multi_window_trends=multi_window,
            key_findings=key_findings,
            recommendations=recommendations,
            medical_disclaimer=MEDICAL_DISCLAIMER
        )

    @staticmethod
    def analyze_single_metric(
        db: Session,
        patient_id: int,
        metric_name: str,
        window_days: int = 7
    ) -> MetricDriftResult:
        """Evaluates health drift for one isolated metric."""
        valid_metrics = ["heart_rate", "spo2", "temperature", "sleep_duration", "daily_steps"]
        if metric_name not in valid_metrics:
            return MetricDriftResult(
                metric_name=metric_name,
                display_name=metric_name,
                unit="unknown",
                baseline_value=0.0,
                significance="insufficient_data",
                data_sufficiency="insufficient",
                recorded_days_count=0,
                total_window_days=window_days,
                explanation=f"Unsupported metric '{metric_name}'. Supported metrics: {', '.join(valid_metrics)}"
            )

        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=window_days)

        baseline, _ = DigitalTwinService.get_or_calculate_baseline(db, patient_id)

        readings = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == patient_id,
            HealthTelemetry.recorded_at >= period_start,
            HealthTelemetry.recorded_at <= now
        ).order_by(HealthTelemetry.recorded_at.asc()).all()

        daily_df = HealthDriftService._build_daily_dataframe(readings)

        return HealthDriftService._evaluate_metric_drift(
            daily_df=daily_df,
            metric_name=metric_name,
            baseline=baseline,
            window_days=window_days
        )

    @staticmethod
    def get_drift_timeline(
        db: Session,
        patient_id: int,
        metric_name: Optional[str] = None,
        limit: int = 50
    ) -> HealthDriftTimelineResponse:
        """Retrieves chronological health drift records for the patient."""
        query = db.query(HealthDriftRecord).filter(
            HealthDriftRecord.patient_id == patient_id
        )

        if metric_name:
            query = query.filter(HealthDriftRecord.drift_parameter == metric_name)

        records = query.order_by(HealthDriftRecord.created_at.desc()).limit(limit).all()

        timeline_items = [
            HealthDriftTimelineItem(
                id=r.id,
                patient_id=r.patient_id,
                period_start=r.period_start,
                period_end=r.period_end,
                drift_parameter=r.drift_parameter,
                baseline_value=r.baseline_value,
                current_period_value=r.current_period_value,
                drift_delta=r.drift_delta,
                drift_percentage=r.drift_percentage,
                significance=r.significance,
                ai_recommendation=r.ai_recommendation,
                created_at=r.created_at
            )
            for r in records
        ]

        return HealthDriftTimelineResponse(
            patient_id=patient_id,
            total_records=len(timeline_items),
            records=timeline_items
        )

    # -------------------------------------------------------------------------
    # Internal Statistical Processing
    # -------------------------------------------------------------------------
    @staticmethod
    def _build_daily_dataframe(readings: List[HealthTelemetry]) -> pd.DataFrame:
        """Aggregates telemetry records into daily summary points."""
        if not readings:
            return pd.DataFrame()

        records = []
        for r in readings:
            temp_c = r.temperature
            if temp_c is not None and r.temperature_unit.upper() == "F":
                temp_c = (temp_c - 32.0) * (5.0 / 9.0)

            records.append({
                "recorded_at": r.recorded_at,
                "date": r.recorded_at.strftime("%Y-%m-%d"),
                "heart_rate": r.heart_rate,
                "spo2": r.spo2,
                "temperature": temp_c,
                "step_count": r.step_count or 0,
                "sleep_duration_minutes": r.sleep_duration_minutes,
                "activity_type": r.activity_type or "resting",
            })

        df = pd.DataFrame(records)

        # Aggregate per date
        daily_rows = []
        for d, group in df.groupby("date"):
            # Resting HR preference
            resting_hr = group.loc[group["activity_type"] == "resting", "heart_rate"].dropna()
            hr_val = float(resting_hr.mean()) if not resting_hr.empty else float(group["heart_rate"].dropna().mean()) if not group["heart_rate"].dropna().empty else None

            # SpO2 median
            spo2_series = group["spo2"].dropna()
            spo2_val = float(spo2_series.median()) if not spo2_series.empty else None

            # Temperature mean
            temp_series = group["temperature"].dropna()
            temp_val = float(temp_series.mean()) if not temp_series.empty else None

            # Sleep: max tracked duration
            sleep_series = group["sleep_duration_minutes"].dropna()
            sleep_hours = (float(sleep_series.max()) / 60.0) if not sleep_series.empty else None

            # Steps: max or sum
            steps_val = float(group["step_count"].max()) if not group["step_count"].empty else 0.0

            daily_rows.append({
                "date": d,
                "heart_rate": round(hr_val, 1) if hr_val is not None else None,
                "spo2": round(spo2_val, 1) if spo2_val is not None else None,
                "temperature": round(temp_val, 2) if temp_val is not None else None,
                "sleep_duration": round(sleep_hours, 2) if sleep_hours is not None else None,
                "daily_steps": round(steps_val, 0)
            })

        daily_df = pd.DataFrame(daily_rows).sort_values("date").reset_index(drop=True)
        return daily_df

    @staticmethod
    def _evaluate_metric_drift(
        daily_df: pd.DataFrame,
        metric_name: str,
        baseline: DigitalTwinBaseline,
        window_days: int
    ) -> MetricDriftResult:
        """Computes statistical drift, EWMA, slope, persistence, and classification for a metric."""
        metric_meta = {
            "heart_rate": ("Resting Heart Rate", "BPM", baseline.baseline_resting_hr),
            "spo2": ("Blood Oxygen (SpO2)", "%", baseline.baseline_spo2),
            "temperature": ("Body Temperature", "°C", baseline.baseline_temperature),
            "sleep_duration": ("Sleep Duration", "hours", DEFAULT_SLEEP_BASELINE_HOURS),
            "daily_steps": ("Daily Step Count", "steps", DEFAULT_STEPS_BASELINE),
        }

        display_name, unit, baseline_val = metric_meta.get(
            metric_name, (metric_name, "", 0.0)
        )

        if daily_df.empty or metric_name not in daily_df.columns:
            return MetricDriftResult(
                metric_name=metric_name,
                display_name=display_name,
                unit=unit,
                baseline_value=baseline_val,
                significance="insufficient_data",
                data_sufficiency="insufficient",
                recorded_days_count=0,
                total_window_days=window_days,
                explanation=f"No readings recorded for {display_name} in the evaluation window."
            )

        series = daily_df[["date", metric_name]].dropna().reset_index(drop=True)
        recorded_days = len(series)

        if recorded_days < 3:
            return MetricDriftResult(
                metric_name=metric_name,
                display_name=display_name,
                unit=unit,
                baseline_value=baseline_val,
                significance="insufficient_data",
                data_sufficiency="insufficient",
                recorded_days_count=recorded_days,
                total_window_days=window_days,
                explanation=f"Insufficient historical data ({recorded_days}/{window_days} days recorded). Minimum 3 days required to establish trend."
            )

        y_vals = series[metric_name].values.astype(float)
        dates = series["date"].values

        # 1. EWMA smoothing
        ewma_vals = pd.Series(y_vals).ewm(span=min(3, recorded_days), adjust=False).mean().values
        current_val = round(float(ewma_vals[-1]), 2 if metric_name == "temperature" else 1)

        # 2. Linear Regression Slope (rate of change per day)
        x_vals = np.arange(recorded_days)
        if recorded_days > 1:
            x_mean = np.mean(x_vals)
            y_mean = np.mean(y_vals)
            denom = np.sum((x_vals - x_mean) ** 2)
            slope = float(np.sum((x_vals - x_mean) * (y_vals - y_mean)) / denom) if denom != 0 else 0.0
        else:
            slope = 0.0

        drift_delta = round(current_val - baseline_val, 2 if metric_name == "temperature" else 1)
        drift_pct = round((drift_delta / baseline_val) * 100.0, 1) if baseline_val != 0 else 0.0

        # 3. Trend Direction
        slope_threshold = 0.05 if metric_name != "temperature" else 0.02
        pct_threshold = 2.0 if metric_name != "temperature" else 0.5

        if slope > slope_threshold and drift_pct >= pct_threshold:
            trend_dir = "upward"
        elif slope < -slope_threshold and drift_pct <= -pct_threshold:
            trend_dir = "downward"
        else:
            trend_dir = "stable"

        # 4. Distinguish Persistence vs Temporary Fluctuation
        if drift_delta > 0:
            matching_days = np.sum(y_vals > baseline_val)
        elif drift_delta < 0:
            matching_days = np.sum(y_vals < baseline_val)
        else:
            matching_days = 0

        consistency_ratio = float(matching_days / recorded_days)
        persistence_score = round(min(max(consistency_ratio * 0.75 + (0.25 if trend_dir != "stable" else 0.0), 0.0), 1.0), 2)

        # Check for single-day spike vs sustained drift
        is_persistent = persistence_score >= 0.65 and abs(drift_pct) >= (2.0 if metric_name != "temperature" else 0.6)

        if is_persistent:
            classification = "persistent_drift"
        elif abs(drift_pct) >= 4.0 and persistence_score < 0.65:
            classification = "transient_fluctuation"
        else:
            classification = "stable"

        # 5. Determine Significance
        significance = HealthDriftService._calculate_significance(
            metric_name, drift_delta, drift_pct, is_persistent
        )

        # 6. Format Daily Data Points
        data_points = [
            DriftDataPoint(
                date=str(dates[i]),
                value=round(float(y_vals[i]), 2 if metric_name == "temperature" else 1),
                moving_avg=round(float(ewma_vals[i]), 2 if metric_name == "temperature" else 1),
                baseline=baseline_val
            )
            for i in range(recorded_days)
        ]

        # 7. Formulate Human-Understandable Explanation
        explanation = HealthDriftService._build_metric_explanation(
            display_name=display_name,
            unit=unit,
            current_val=current_val,
            baseline_val=baseline_val,
            drift_delta=drift_delta,
            drift_pct=drift_pct,
            trend_dir=trend_dir,
            slope=slope,
            is_persistent=is_persistent,
            classification=classification,
            matching_days=int(matching_days),
            recorded_days=recorded_days,
            significance=significance
        )

        data_suff = "sufficient" if recorded_days >= (window_days * 0.7) else "moderate"

        return MetricDriftResult(
            metric_name=metric_name,
            display_name=display_name,
            unit=unit,
            baseline_value=baseline_val,
            current_value=current_val,
            drift_delta=drift_delta,
            drift_percentage=drift_pct,
            trend_direction=trend_dir,
            slope_per_day=round(slope, 3),
            persistence_score=persistence_score,
            is_persistent=is_persistent,
            classification=classification,
            significance=significance,
            data_sufficiency=data_suff,
            recorded_days_count=recorded_days,
            total_window_days=window_days,
            explanation=explanation,
            data_points=data_points
        )

    @staticmethod
    def _calculate_significance(
        metric_name: str,
        delta: float,
        pct: float,
        is_persistent: bool
    ) -> str:
        """Determines clinical significance level based on metric domain rules."""
        if not is_persistent:
            return "stable"

        if metric_name == "heart_rate":
            if abs(pct) >= 20.0 or abs(delta) >= 15.0:
                return "significant_drift"
            elif abs(pct) >= 10.0 or abs(delta) >= 8.0:
                return "moderate_drift"
            elif abs(pct) >= 5.0 or abs(delta) >= 4.0:
                return "mild_drift"

        elif metric_name == "spo2":
            if delta <= -3.5:
                return "significant_drift"
            elif delta <= -2.0:
                return "moderate_drift"
            elif delta <= -1.0:
                return "mild_drift"

        elif metric_name == "temperature":
            if abs(delta) >= 0.8:
                return "significant_drift"
            elif abs(delta) >= 0.5:
                return "moderate_drift"
            elif abs(delta) >= 0.3:
                return "mild_drift"

        elif metric_name == "sleep_duration":
            if abs(pct) >= 30.0:
                return "significant_drift"
            elif abs(pct) >= 20.0:
                return "moderate_drift"
            elif abs(pct) >= 12.0:
                return "mild_drift"

        elif metric_name == "daily_steps":
            if pct <= -40.0:
                return "significant_drift"
            elif pct <= -25.0:
                return "moderate_drift"
            elif abs(pct) >= 15.0:
                return "mild_drift"

        return "stable"

    @staticmethod
    def _build_metric_explanation(
        display_name: str,
        unit: str,
        current_val: float,
        baseline_val: float,
        drift_delta: float,
        drift_pct: float,
        trend_dir: str,
        slope: float,
        is_persistent: bool,
        classification: str,
        matching_days: int,
        recorded_days: int,
        significance: str
    ) -> str:
        """Generates clear, natural language explanation without diagnostic claims."""
        sign = "+" if drift_delta > 0 else ""

        if classification == "stable":
            return (
                f"{display_name} is stable over the observed period (current {current_val} {unit} "
                f"vs baseline {baseline_val} {unit}, deviation {sign}{drift_pct}%)."
            )

        if classification == "transient_fluctuation":
            return (
                f"{display_name} showed temporary fluctuations (recent value {current_val} {unit}, {sign}{drift_pct}%), "
                f"but lack of multi-day consistency ({matching_days}/{recorded_days} days) indicates short-term variability rather than sustained health drift."
            )

        # Persistent drift explanation
        dir_text = "gradual upward" if trend_dir == "upward" else "gradual downward"
        slope_sign = "+" if slope > 0 else ""
        return (
            f"{display_name} exhibits a {dir_text} drift over the observed window: "
            f"current EWMA is {current_val} {unit} ({sign}{drift_pct}% from baseline {baseline_val} {unit}) "
            f"with a rate of {slope_sign}{slope:.2f} {unit}/day. "
            f"Consistency was maintained across {matching_days} of {recorded_days} days, indicating persistent {significance.replace('_', ' ')}."
        )

    @staticmethod
    def _compute_multi_window_trends(
        db: Session,
        patient_id: int,
        baseline: DigitalTwinBaseline,
        readings: List[HealthTelemetry]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculates multi-window comparative trends across 3d, 7d, and 30d."""
        windows = [3, 7, 30]
        results = {}
        now = datetime.now(timezone.utc)

        for w in windows:
            cutoff = now - timedelta(days=w)
            sub_readings = [r for r in readings if (r.recorded_at if r.recorded_at.tzinfo else r.recorded_at.replace(tzinfo=timezone.utc)) >= cutoff]
            sub_df = HealthDriftService._build_daily_dataframe(sub_readings)

            window_summary = {}
            for metric in ["heart_rate", "spo2", "temperature"]:
                if not sub_df.empty and metric in sub_df.columns and len(sub_df[metric].dropna()) >= 2:
                    vals = sub_df[metric].dropna().values
                    current_avg = float(np.mean(vals[-2:])) if len(vals) >= 2 else float(vals[0])
                    base_val = getattr(baseline, f"baseline_resting_hr" if metric == "heart_rate" else f"baseline_{metric}")
                    delta = round(current_avg - base_val, 2 if metric == "temperature" else 1)
                    pct = round((delta / base_val) * 100.0, 1) if base_val != 0 else 0.0
                    dir_str = "upward" if pct >= 2.0 else "downward" if pct <= -2.0 else "stable"

                    window_summary[metric] = {
                        "drift_delta": delta,
                        "drift_percentage": pct,
                        "trend_direction": dir_str
                    }
                else:
                    window_summary[metric] = {
                        "drift_delta": None,
                        "drift_percentage": None,
                        "trend_direction": "insufficient_data"
                    }

            results[f"{w}d"] = window_summary

        return results

    @staticmethod
    def _determine_overall_drift(
        metric_results: Dict[str, MetricDriftResult],
        recorded_days: int,
        window_days: int
    ) -> Tuple[str, str]:
        """Synthesizes overall drift status and confidence level."""
        if recorded_days < 3:
            return "insufficient_data", "low"

        significance_rank = {
            "significant_drift": 4,
            "moderate_drift": 3,
            "mild_drift": 2,
            "stable": 1,
            "insufficient_data": 0
        }

        max_rank = 1
        overall_status = "stable"

        for res in metric_results.values():
            rank = significance_rank.get(res.significance, 1)
            if rank > max_rank:
                max_rank = rank
                overall_status = res.significance

        if recorded_days >= (window_days * 0.75):
            confidence = "high"
        elif recorded_days >= 3:
            confidence = "medium"
        else:
            confidence = "low"

        return overall_status, confidence

    @staticmethod
    def _generate_key_findings(metric_results: Dict[str, MetricDriftResult]) -> List[str]:
        """Extracts primary highlights from analyzed metrics."""
        findings = []
        for m_key, res in metric_results.items():
            if res.significance in ("significant_drift", "moderate_drift", "mild_drift"):
                findings.append(f"{res.display_name}: Persistent {res.trend_direction} drift ({res.drift_percentage:+}% vs baseline).")
            elif res.classification == "transient_fluctuation":
                findings.append(f"{res.display_name}: Short-term fluctuation detected; baseline remains stable.")

        if not findings:
            findings.append("All analyzed physiological metrics remain stable and aligned with personal Digital Twin baseline.")

        return findings

    @staticmethod
    def _generate_guidance(metric_results: Dict[str, MetricDriftResult], overall_status: str) -> List[str]:
        """Provides non-diagnostic observational recommendations."""
        guidance = []

        if overall_status in ("significant_drift", "moderate_drift"):
            guidance.append("Consider sharing this trend summary with your assigned caregiver or healthcare provider during your next routine consultation.")

        hr_res = metric_results.get("heart_rate")
        if hr_res and hr_res.trend_direction == "upward" and hr_res.is_persistent:
            guidance.append("Resting heart rate has trended higher across multiple days. Ensure adequate hydration, rest, and minimize stimulants.")

        spo2_res = metric_results.get("spo2")
        if spo2_res and spo2_res.trend_direction == "downward" and spo2_res.is_persistent:
            guidance.append("Oxygen saturation levels have experienced a mild gradual decrease. Ensure good posture and monitor sensor placement.")

        sleep_res = metric_results.get("sleep_duration")
        if sleep_res and sleep_res.trend_direction == "downward" and sleep_res.is_persistent:
            guidance.append("Tracked sleep duration has declined over the observed window. Aim for regular sleep hygiene.")

        if not guidance:
            guidance.append("Continue routine daily wearable monitoring. Your physiological trends reflect steady baseline stability.")

        return guidance
