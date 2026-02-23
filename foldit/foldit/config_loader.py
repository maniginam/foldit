"""YAML configuration loader with config.py defaults."""
import copy

import yaml

from foldit.config import ServoConfig, CameraConfig, ConveyorConfig


DEFAULTS = {
    "conveyor": {
        "motor_pin_a": ConveyorConfig.MOTOR_PIN_A,
        "motor_pin_b": ConveyorConfig.MOTOR_PIN_B,
        "motor_enable_pin": ConveyorConfig.MOTOR_ENABLE_PIN,
        "trigger_pin": ConveyorConfig.TRIGGER_PIN,
        "echo_pin": ConveyorConfig.ECHO_PIN,
        "detection_distance_cm": ConveyorConfig.DETECTION_DISTANCE_CM,
        "belt_speed_duty": ConveyorConfig.BELT_SPEED_DUTY,
        "settle_time_sec": ConveyorConfig.SETTLE_TIME_SEC,
    },
    "servo": {
        "fold_angle": ServoConfig.FOLD_ANGLE,
        "home_angle": ServoConfig.HOME_ANGLE,
        "step_delay_sec": ServoConfig.STEP_DELAY_SEC,
        "pwm_frequency_hz": ServoConfig.PWM_FREQUENCY_HZ,
        "min_duty_cycle": ServoConfig.MIN_DUTY_CYCLE,
        "max_duty_cycle": ServoConfig.MAX_DUTY_CYCLE,
    },
    "camera": {
        "resolution": list(CameraConfig.RESOLUTION),
        "framerate": CameraConfig.FRAMERATE,
    },
    "classifier": {
        "confidence_threshold": 0.5,
        "small_area_threshold": 15000,
        "pants_ratio_threshold": 0.6,
        "shirt_ratio_threshold": 1.2,
        "model_path": None,
        "min_confidence": 0.7,
    },
    "fold_verify": {
        "enabled": True,
        "max_retries": 1,
    },
    "logging": {
        "level": "INFO",
        "file": None,
    },
    "dashboard": {
        "enabled": False,
        "port": 5000,
        "api_key": None,
    },
    "data_collection": {
        "enabled": False,
        "output_dir": "./data/captures",
    },
    "frame_quality": {
        "min_blur_score": 100.0,
        "min_contrast": 30.0,
        "min_brightness": 40.0,
        "max_brightness": 220.0,
    },
    "alerting": {
        "consecutive_fail_threshold": 3,
        "rate_window": 20,
        "min_success_rate": 0.5,
        "webhook_url": None,
    },
    "metrics_store": {
        "db_path": "data/metrics.db",
    },
}


class ConfigLoader:
    """Loads YAML config with fallback to config.py defaults."""

    def __init__(self, path="./config.yaml", default_path=None):
        self._path = path
        self._default_path = default_path
        self._config = None

    def load(self):
        self._config = copy.deepcopy(DEFAULTS)

        if self._default_path:
            try:
                with open(self._default_path, "r") as f:
                    defaults_yaml = yaml.safe_load(f)
                if defaults_yaml and isinstance(defaults_yaml, dict):
                    self._merge(self._config, defaults_yaml)
            except FileNotFoundError:
                pass

        try:
            with open(self._path, "r") as f:
                overrides = yaml.safe_load(f)
        except FileNotFoundError:
            return self._config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self._path}: {e}")

        if overrides and isinstance(overrides, dict):
            self._merge(self._config, overrides)
        return self._config

    def get(self, dotted_key, default=None):
        keys = dotted_key.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _merge(self, base, overrides):
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value
