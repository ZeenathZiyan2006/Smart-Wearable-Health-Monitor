import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("pulseguardian.devices")


class BaseDeviceAdapter(ABC):
    """
    Extensible abstract adapter for wearable health monitoring hardware.
    """

    @abstractmethod
    def parse_telemetry(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and normalizes raw telemetry from device into standard schema."""
        pass

    @abstractmethod
    def validate_device_id(self, device_uuid: str) -> bool:
        """Verifies device hardware identifier format."""
        pass


class ESP32DeviceAdapter(BaseDeviceAdapter):
    """
    Adapter for ESP32 microcontrollers communicating over Wi-Fi/HTTP/MQTT.
    Interfacing with MAX30102 (HR/SpO2), MPU6050 (Accelerometer), and NEO-6M GPS.
    """

    def validate_device_id(self, device_uuid: str) -> bool:
        if not device_uuid or len(device_uuid.strip()) < 4:
            return False
        return True

    def parse_telemetry(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        # Extract and normalize
        hr = raw_payload.get("heart_rate")
        spo2 = raw_payload.get("spo2")
        temp = raw_payload.get("temperature")
        acc_x = raw_payload.get("accelerometer_x") or raw_payload.get("accel_x")
        acc_y = raw_payload.get("accelerometer_y") or raw_payload.get("accel_y")
        acc_z = raw_payload.get("accelerometer_z") or raw_payload.get("accel_z")
        fall = bool(raw_payload.get("fall_detected", False))

        return {
            "device_uuid": raw_payload.get("device_uuid"),
            "heart_rate": float(hr) if hr is not None else None,
            "spo2": float(spo2) if spo2 is not None else None,
            "temperature": float(temp) if temp is not None else None,
            "accelerometer_x": float(acc_x) if acc_x is not None else None,
            "accelerometer_y": float(acc_y) if acc_y is not None else None,
            "accelerometer_z": float(acc_z) if acc_z is not None else None,
            "fall_detected": fall,
            "battery_percentage": float(raw_payload.get("battery_percentage", 100.0)),
            "recorded_at": raw_payload.get("recorded_at") or datetime.now(timezone.utc),
            "is_simulated": False
        }


class MockWearableSimulatorAdapter(BaseDeviceAdapter):
    """
    Clearly identified development simulator adapter.
    Generates synthetic or simulated wearable telemetry without actual hardware.
    Never pretends simulated readings are real clinical measurements.
    """

    def validate_device_id(self, device_uuid: str) -> bool:
        return True

    def parse_telemetry(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        data = raw_payload.copy()
        data["is_simulated"] = True
        return data

    def generate_simulated_vitals(
        self,
        baseline_hr: float = 72.0,
        baseline_spo2: float = 98.0,
        baseline_temp: float = 36.6,
        simulate_fall: bool = False
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "heart_rate": baseline_hr,
            "spo2": baseline_spo2,
            "temperature": baseline_temp,
            "temperature_unit": "C",
            "step_count": 250,
            "activity_type": "resting",
            "fall_detected": simulate_fall,
            "accelerometer_x": 0.05 if not simulate_fall else 3.2,
            "accelerometer_y": 0.10 if not simulate_fall else 2.8,
            "accelerometer_z": 0.98 if not simulate_fall else 4.1,
            "battery_percentage": 92.0,
            "recorded_at": now,
            "is_simulated": True
        }


esp32_adapter = ESP32DeviceAdapter()
mock_simulator_adapter = MockWearableSimulatorAdapter()
