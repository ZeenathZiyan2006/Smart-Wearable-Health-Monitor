import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.digital_twin import DigitalTwinBaseline, HealthDriftRecord
from app.models.health import HealthTelemetry

logger = logging.getLogger("pulseguardian.digital_twin")

MIN_BASELINE_SAMPLES = 20

# Clinical population reference standards (used during cold start)
COLD_START_DEFAULTS = {
    "baseline_resting_hr": 72.0,
    "hr_min_normal": 55.0,
    "hr_max_normal": 100.0,
    "hr_std_dev": 8.0,
    "baseline_spo2": 98.0,
    "spo2_min_normal": 95.0,
    "baseline_temperature": 36.8,
    "temp_min_normal": 36.1,
    "temp_max_normal": 37.2,
}


class DigitalTwinService:
    """
    Personal Health Digital Twin Service.
    Learns and maintains an adaptive physiological baseline model for each patient
    from historical wearable readings.
    """

    @staticmethod
    def get_or_calculate_baseline(
        db: Session,
        patient_id: int,
        force_recalculate: bool = False
    ) -> Tuple[DigitalTwinBaseline, bool]:
        """
        Retrieves the patient's digital twin baseline.
        If missing or force_recalculate is True, re-learns the baseline from telemetry.
        Returns (DigitalTwinBaseline, is_cold_start).
        """
        existing = db.query(DigitalTwinBaseline).filter(
            DigitalTwinBaseline.patient_id == patient_id
        ).first()

        # If existing baseline exists and no recalculate requested, return it
        if existing and not force_recalculate:
            is_cold_start = existing.samples_count < MIN_BASELINE_SAMPLES
            return existing, is_cold_start

        # Calculate / update from historical readings
        return DigitalTwinService.recalculate_baseline(db, patient_id)

    @staticmethod
    def recalculate_baseline(
        db: Session,
        patient_id: int
    ) -> Tuple[DigitalTwinBaseline, bool]:
        """
        Learns personal physiological baseline from patient's historical wearable telemetry.
        Persists baseline parameters and circadian profiles.
        """
        # Fetch historical telemetry for this patient (most recent 2,000 readings)
        readings = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == patient_id
        ).order_by(HealthTelemetry.recorded_at.desc()).limit(2000).all()

        existing = db.query(DigitalTwinBaseline).filter(
            DigitalTwinBaseline.patient_id == patient_id
        ).first()

        if not existing:
            existing = DigitalTwinBaseline(
                patient_id=patient_id,
                baseline_resting_hr=COLD_START_DEFAULTS["baseline_resting_hr"],
                hr_min_normal=COLD_START_DEFAULTS["hr_min_normal"],
                hr_max_normal=COLD_START_DEFAULTS["hr_max_normal"],
                hr_std_dev=COLD_START_DEFAULTS["hr_std_dev"],
                baseline_spo2=COLD_START_DEFAULTS["baseline_spo2"],
                spo2_min_normal=COLD_START_DEFAULTS["spo2_min_normal"],
                baseline_temperature=COLD_START_DEFAULTS["baseline_temperature"],
                temp_min_normal=COLD_START_DEFAULTS["temp_min_normal"],
                temp_max_normal=COLD_START_DEFAULTS["temp_max_normal"],
                samples_count=0,
                last_calculated_at=datetime.now(timezone.utc),
            )
            db.add(existing)

        # Convert readings to structured format
        records = []
        for r in readings:
            temp_c = r.temperature
            if temp_c is not None and r.temperature_unit == "F":
                temp_c = (temp_c - 32.0) * (5.0 / 9.0)

            records.append({
                "recorded_at": r.recorded_at,
                "heart_rate": r.heart_rate,
                "spo2": r.spo2,
                "temperature": temp_c,
                "step_count": r.step_count or 0,
                "activity_type": r.activity_type or "resting",
                "fall_detected": r.fall_detected,
            })

        if not records:
            existing.samples_count = 0
            existing.circadian_profile_json = json.dumps({"status": "cold_start", "samples": 0})
            existing.last_calculated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing, True

        df = pd.DataFrame(records)

        # Clean physiological sensor artifacts
        valid_mask = (
            (df["heart_rate"].isna() | ((df["heart_rate"] >= 30.0) & (df["heart_rate"] <= 240.0))) &
            (df["spo2"].isna() | ((df["spo2"] >= 50.0) & (df["spo2"] <= 100.0))) &
            (df["temperature"].isna() | ((df["temperature"] >= 30.0) & (df["temperature"] <= 45.0)))
        )
        clean_df = df[valid_mask].copy()
        clean_samples_count = len(clean_df)

        # Check Cold-Start threshold
        if clean_samples_count < MIN_BASELINE_SAMPLES:
            existing.samples_count = clean_samples_count
            existing.circadian_profile_json = json.dumps({
                "status": "cold_start",
                "samples_count": clean_samples_count,
                "min_required": MIN_BASELINE_SAMPLES,
                "message": f"Digital Twin is in cold start mode. Collected {clean_samples_count}/{MIN_BASELINE_SAMPLES} readings."
            })
            existing.last_calculated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing, True

        # -------------------------------------------------------------
        # 1. Heart Rate Baseline & Bounds
        # -------------------------------------------------------------
        # Filter for resting heart rate where available
        resting_mask = (clean_df["activity_type"] == "resting") & clean_df["heart_rate"].notna()
        if resting_mask.sum() >= 10:
            hr_series = clean_df.loc[resting_mask, "heart_rate"]
        else:
            hr_series = clean_df["heart_rate"].dropna()

        if len(hr_series) >= 5:
            baseline_hr = float(hr_series.mean())
            std_hr = float(hr_series.std())
            std_hr = max(std_hr, 3.0)  # Lower bound guard for std dev
            existing.baseline_resting_hr = round(baseline_hr, 1)
            existing.hr_std_dev = round(std_hr, 1)
            existing.hr_min_normal = round(max(45.0, baseline_hr - 2.5 * std_hr), 1)
            existing.hr_max_normal = round(min(130.0, baseline_hr + 2.5 * std_hr), 1)

        # -------------------------------------------------------------
        # 2. SpO2 Baseline & Bounds
        # -------------------------------------------------------------
        spo2_series = clean_df["spo2"].dropna()
        if len(spo2_series) >= 5:
            baseline_spo2 = float(spo2_series.median())
            p5_spo2 = float(spo2_series.quantile(0.05))
            existing.baseline_spo2 = round(baseline_spo2, 1)
            existing.spo2_min_normal = round(max(92.0, min(95.0, p5_spo2)), 1)

        # -------------------------------------------------------------
        # 3. Body Temperature Baseline & Bounds
        # -------------------------------------------------------------
        temp_series = clean_df["temperature"].dropna()
        if len(temp_series) >= 5:
            baseline_temp = float(temp_series.mean())
            std_temp = float(temp_series.std())
            std_temp = max(std_temp, 0.2)
            existing.baseline_temperature = round(baseline_temp, 2)
            existing.temp_min_normal = round(max(35.5, baseline_temp - 2.5 * std_temp), 2)
            existing.temp_max_normal = round(min(38.0, baseline_temp + 2.5 * std_temp), 2)

        # -------------------------------------------------------------
        # 4. Circadian Profiles (Hourly & Day/Night Patterns)
        # -------------------------------------------------------------
        clean_df["recorded_at"] = pd.to_datetime(clean_df["recorded_at"])
        clean_df["hour"] = clean_df["recorded_at"].dt.hour

        # Hourly heart rate means
        hourly_hr = clean_df.groupby("hour")["heart_rate"].mean().dropna().round(1).to_dict()

        # Day (07:00 - 22:00) vs Night (23:00 - 06:00)
        day_mask = clean_df["hour"].between(7, 22)
        day_hr = clean_df.loc[day_mask, "heart_rate"].mean()
        night_hr = clean_df.loc[~day_mask, "heart_rate"].mean()

        # Resting vs Active Heart Rate
        resting_hr = clean_df.loc[clean_df["activity_type"] == "resting", "heart_rate"].mean()
        active_hr = clean_df.loc[clean_df["activity_type"] != "resting", "heart_rate"].mean()

        circadian_profile = {
            "status": "active",
            "samples_analyzed": clean_samples_count,
            "day_hr_average": round(float(day_hr), 1) if pd.notna(day_hr) else existing.baseline_resting_hr,
            "night_hr_average": round(float(night_hr), 1) if pd.notna(night_hr) else existing.baseline_resting_hr,
            "resting_hr_average": round(float(resting_hr), 1) if pd.notna(resting_hr) else existing.baseline_resting_hr,
            "active_hr_average": round(float(active_hr), 1) if pd.notna(active_hr) else None,
            "hourly_hr_profile": {int(k): v for k, v in hourly_hr.items()}
        }

        existing.circadian_profile_json = json.dumps(circadian_profile)
        existing.samples_count = clean_samples_count
        existing.last_calculated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(existing)

        return existing, False

    @staticmethod
    def get_circadian_profile(baseline: DigitalTwinBaseline) -> Optional[Dict[str, Any]]:
        """Parses the JSON circadian profile if present."""
        if not baseline.circadian_profile_json:
            return None
        try:
            return json.loads(baseline.circadian_profile_json)
        except Exception:
            return None
