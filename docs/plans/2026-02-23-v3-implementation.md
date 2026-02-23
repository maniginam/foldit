# FoldIt V3 Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 10 enhancements — YAML config, structured logging, orientation detection, size-aware folding, fold verification, error recovery, data collection, web dashboard, integration tests, and error recovery tests — bringing the test count from 118 to ~170+.

**Architecture:** New modules compose with existing V2 classes via dependency injection. YAML config overrides `config.py` defaults. Structured logging replaces silent exception handling. Flask dashboard reads from MetricsCollector. All new classes are tested in isolation before integration.

**Tech Stack:** Python 3.11+, OpenCV, NumPy, Flask, PyYAML, pytest

**Run all tests with:** `foldit/.venv/bin/python -m pytest foldit/tests/ -v`

**Project root:** `/Users/maniginam/projects/foldit`

---

## Task 1: Add flask and pyyaml dependencies

**Files:**
- Modify: `foldit/pyproject.toml`

**Step 1: Add dependencies to pyproject.toml**

Add `flask` and `pyyaml` to the `[project.dependencies]` list in `foldit/pyproject.toml`:

```toml
[project]
name = "foldit"
version = "0.2.0"
description = "Clothes folding robot algorithm"
requires-python = ">=3.11"
dependencies = [
    "opencv-python>=4.8.0",
    "numpy>=1.24.0",
    "RPi.GPIO>=0.7.1",
    "picamera2>=0.3.12",
    "flask>=3.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.11.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Install into venv**

Run: `foldit/.venv/bin/pip install flask pyyaml`

**Step 3: Verify imports work**

Run: `foldit/.venv/bin/python -c "import flask; import yaml; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add foldit/pyproject.toml
git commit -m "chore: add flask and pyyaml dependencies for V3"
```

---

## Task 2: YAML Config Loader

**Files:**
- Create: `foldit/tests/test_config_loader.py`
- Create: `foldit/foldit/config_loader.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_config_loader.py`:

```python
"""Tests for YAML config loader."""
import os
import tempfile
import yaml


class TestConfigLoader:
    def test_load_returns_defaults_when_no_file(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["conveyor"]["detection_distance_cm"] == 10.0
        assert config["conveyor"]["belt_speed_duty"] == 75

    def test_load_overrides_from_yaml(self):
        from foldit.config_loader import ConfigLoader
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"conveyor": {"detection_distance_cm": 15.0}}, f)
            f.flush()
            try:
                loader = ConfigLoader(path=f.name)
                config = loader.load()
                assert config["conveyor"]["detection_distance_cm"] == 15.0
                assert config["conveyor"]["belt_speed_duty"] == 75  # default preserved
            finally:
                os.unlink(f.name)

    def test_load_preserves_all_default_sections(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert "servo" in config
        assert "classifier" in config
        assert "camera" in config
        assert "logging" in config
        assert "dashboard" in config
        assert "data_collection" in config
        assert "fold_verify" in config

    def test_servo_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["servo"]["fold_angle"] == 180
        assert config["servo"]["home_angle"] == 0
        assert config["servo"]["step_delay_sec"] == 0.02

    def test_invalid_yaml_raises(self):
        from foldit.config_loader import ConfigLoader
        import pytest
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(": invalid: yaml: [[[")
            f.flush()
            try:
                loader = ConfigLoader(path=f.name)
                with pytest.raises(ValueError, match="Invalid YAML"):
                    loader.load()
            finally:
                os.unlink(f.name)

    def test_get_nested_value(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert loader.get("conveyor.detection_distance_cm") == 10.0
        assert loader.get("servo.fold_angle") == 180

    def test_get_missing_key_returns_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        loader.load()
        assert loader.get("nonexistent.key", default=42) == 42
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_config_loader.py -v`
Expected: FAIL (no module `foldit.config_loader`)

**Step 3: Write minimal implementation**

Create `foldit/foldit/config_loader.py`:

```python
"""YAML configuration loader with config.py defaults."""
import yaml
from foldit.config import (
    ServoConfig, CameraConfig, ConveyorConfig, GarmentType
)


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
    },
    "data_collection": {
        "enabled": False,
        "output_dir": "./data/captures",
    },
}


class ConfigLoader:
    """Loads YAML config with fallback to config.py defaults."""

    def __init__(self, path="./config.yaml"):
        self._path = path
        self._config = None

    def load(self):
        import copy
        self._config = copy.deepcopy(DEFAULTS)
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
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_config_loader.py -v`
Expected: All 7 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_config_loader.py foldit/foldit/config_loader.py
git commit -m "feat: YAML config loader with config.py fallback defaults"
```

---

## Task 3: Structured Logging and Metrics

**Files:**
- Create: `foldit/tests/test_robot_logger.py`
- Create: `foldit/foldit/robot_logger.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_robot_logger.py`:

```python
"""Tests for structured logging and metrics collection."""
import json
import logging


class TestRobotLogger:
    def test_creates_logger_with_name(self):
        from foldit.robot_logger import RobotLogger
        logger = RobotLogger(name="test")
        assert logger.name == "test"

    def test_log_event_writes_json(self):
        from foldit.robot_logger import RobotLogger
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = RobotLogger(name="test_json", handlers=[handler])
        logger.log_event("fold_complete", garment="shirt", cycle_sec=8.2)
        output = stream.getvalue()
        data = json.loads(output.strip())
        assert data["event"] == "fold_complete"
        assert data["garment"] == "shirt"
        assert data["cycle_sec"] == 8.2
        assert "ts" in data

    def test_log_event_includes_level(self):
        from foldit.robot_logger import RobotLogger
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = RobotLogger(name="test_level", handlers=[handler])
        logger.log_event("error", level="ERROR", message="camera failed")
        output = stream.getvalue()
        data = json.loads(output.strip())
        assert data["level"] == "ERROR"

    def test_default_level_is_info(self):
        from foldit.robot_logger import RobotLogger
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = RobotLogger(name="test_default_level", handlers=[handler])
        logger.log_event("test")
        data = json.loads(stream.getvalue().strip())
        assert data["level"] == "INFO"


class TestMetricsCollector:
    def test_initial_counts_are_zero(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        assert metrics.total_folds == 0
        assert metrics.success_count == 0

    def test_record_fold_increments_count(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        assert metrics.total_folds == 1
        assert metrics.success_count == 1

    def test_record_fold_tracks_by_type(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        metrics.record_fold("pants", success=True, cycle_sec=6.0)
        metrics.record_fold("shirt", success=True, cycle_sec=4.0)
        assert metrics.counts_by_type == {"shirt": 2, "pants": 1}

    def test_success_rate(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        metrics.record_fold("pants", success=False, cycle_sec=6.0)
        assert metrics.success_rate == 0.5

    def test_success_rate_zero_when_empty(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        assert metrics.success_rate == 0.0

    def test_average_cycle_time(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=4.0)
        metrics.record_fold("shirt", success=True, cycle_sec=6.0)
        assert metrics.avg_cycle_sec == 5.0

    def test_snapshot_returns_dict(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        snap = metrics.snapshot()
        assert snap["total_folds"] == 1
        assert snap["success_rate"] == 1.0
        assert snap["counts_by_type"] == {"shirt": 1}
        assert snap["avg_cycle_sec"] == 5.0
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_robot_logger.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/robot_logger.py`:

```python
"""Structured JSON logging and metrics collection for FoldIt robot."""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record):
        return record.getMessage()


class RobotLogger:
    """Structured event logger emitting JSON lines."""

    def __init__(self, name="foldit", handlers=None):
        self._name = name
        self._logger = logging.getLogger(f"foldit.{name}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False
        if handlers:
            for h in handlers:
                h.setFormatter(JsonFormatter())
                self._logger.addHandler(h)

    @property
    def name(self):
        return self._name

    def log_event(self, event, level="INFO", **kwargs):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
        }
        entry.update(kwargs)
        log_level = getattr(logging, level, logging.INFO)
        self._logger.log(log_level, json.dumps(entry))


class MetricsCollector:
    """Accumulates fold metrics for dashboard and logging."""

    def __init__(self):
        self._total = 0
        self._successes = 0
        self._by_type = {}
        self._cycle_times = []

    @property
    def total_folds(self):
        return self._total

    @property
    def success_count(self):
        return self._successes

    @property
    def counts_by_type(self):
        return dict(self._by_type)

    @property
    def success_rate(self):
        if self._total == 0:
            return 0.0
        return self._successes / self._total

    @property
    def avg_cycle_sec(self):
        if not self._cycle_times:
            return 0.0
        return sum(self._cycle_times) / len(self._cycle_times)

    def record_fold(self, garment_type, success, cycle_sec):
        self._total += 1
        if success:
            self._successes += 1
        self._by_type[garment_type] = self._by_type.get(garment_type, 0) + 1
        self._cycle_times.append(cycle_sec)

    def snapshot(self):
        return {
            "total_folds": self._total,
            "success_count": self._successes,
            "success_rate": self.success_rate,
            "counts_by_type": self.counts_by_type,
            "avg_cycle_sec": self.avg_cycle_sec,
        }
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_robot_logger.py -v`
Expected: All 11 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_robot_logger.py foldit/foldit/robot_logger.py
git commit -m "feat: structured JSON logging and MetricsCollector"
```

---

## Task 4: Orientation Detection

**Files:**
- Create: `foldit/tests/test_orientation.py`
- Create: `foldit/foldit/orientation.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_orientation.py`:

```python
"""Tests for PCA-based garment orientation detection."""
import numpy as np


class TestOrientationDetector:
    def test_landscape_rectangle_detected(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[50,100]],[[550,100]],[[550,300]],[[50,300]]], dtype=np.int32)
        result = detector.detect(contour)
        assert result.is_landscape is True
        assert result.is_portrait is False

    def test_portrait_rectangle_detected(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[200,50]],[[400,50]],[[400,450]],[[200,450]]], dtype=np.int32)
        result = detector.detect(contour)
        assert result.is_portrait is True
        assert result.is_landscape is False

    def test_angle_near_zero_for_horizontal(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[50,200]],[[550,200]],[[550,280]],[[50,280]]], dtype=np.int32)
        result = detector.detect(contour)
        assert abs(result.angle_deg) < 15

    def test_angle_near_90_for_vertical(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[280,50]],[[320,50]],[[320,430]],[[280,430]]], dtype=np.int32)
        result = detector.detect(contour)
        assert abs(abs(result.angle_deg) - 90) < 15

    def test_none_contour_returns_neutral(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        result = detector.detect(None)
        assert result.angle_deg == 0.0
        assert result.is_landscape is True

    def test_result_has_expected_fields(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[50,100]],[[550,100]],[[550,300]],[[50,300]]], dtype=np.int32)
        result = detector.detect(contour)
        assert hasattr(result, "angle_deg")
        assert hasattr(result, "is_landscape")
        assert hasattr(result, "is_portrait")
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_orientation.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/orientation.py`:

```python
"""PCA-based garment orientation detection."""
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class OrientationResult:
    angle_deg: float
    is_landscape: bool
    is_portrait: bool


class OrientationDetector:
    """Detects garment orientation using PCA on contour points."""

    def detect(self, contour):
        if contour is None:
            return OrientationResult(angle_deg=0.0, is_landscape=True, is_portrait=False)

        points = contour.reshape(-1, 2).astype(np.float64)
        mean, eigenvectors = cv2.PCACompute(points, mean=np.empty(0))
        angle = np.degrees(np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0]))

        x, y, w, h = cv2.boundingRect(contour)
        is_landscape = w >= h
        is_portrait = not is_landscape

        return OrientationResult(
            angle_deg=float(angle),
            is_landscape=is_landscape,
            is_portrait=is_portrait,
        )
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_orientation.py -v`
Expected: All 6 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_orientation.py foldit/foldit/orientation.py
git commit -m "feat: PCA-based garment orientation detection"
```

---

## Task 5: Size Estimator

**Files:**
- Create: `foldit/tests/test_size_estimator.py`
- Create: `foldit/foldit/size_estimator.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_size_estimator.py`:

```python
"""Tests for garment size estimation."""
import numpy as np


class TestSizeEstimator:
    def test_estimate_returns_dimensions(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[100,100]],[[400,100]],[[400,300]],[[100,300]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.width_mm == 300.0
        assert size.height_mm == 200.0

    def test_estimate_with_calibration_scaling(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=2.0)
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.width_mm == 200.0
        assert size.height_mm == 100.0

    def test_none_contour_returns_zero(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        size = estimator.estimate(None)
        assert size.width_mm == 0.0
        assert size.height_mm == 0.0

    def test_classify_size_large(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[0,0]],[[600,0]],[[600,400]],[[0,400]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "large"

    def test_classify_size_medium(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[100,100]],[[400,100]],[[400,300]],[[100,300]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "medium"

    def test_classify_size_small(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[200,200]],[[280,200]],[[280,260]],[[200,260]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "small"

    def test_speed_factor_large(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[0,0]],[[600,0]],[[600,400]],[[0,400]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.speed_factor > 1.0

    def test_speed_factor_small(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[200,200]],[[280,200]],[[280,260]],[[200,260]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.speed_factor == 1.0
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_size_estimator.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/size_estimator.py`:

```python
"""Garment size estimation from contour dimensions."""
import cv2
from dataclasses import dataclass


LARGE_AREA_THRESHOLD = 100000
SMALL_AREA_THRESHOLD = 20000


@dataclass
class SizeResult:
    width_mm: float
    height_mm: float
    area_mm2: float
    category: str
    speed_factor: float


class SizeEstimator:
    """Estimates physical garment size from contour and camera calibration."""

    def __init__(self, pixels_per_mm=1.0):
        self._ppm = pixels_per_mm

    def estimate(self, contour):
        if contour is None:
            return SizeResult(
                width_mm=0.0, height_mm=0.0, area_mm2=0.0,
                category="unknown", speed_factor=1.0,
            )

        x, y, w, h = cv2.boundingRect(contour)
        width_mm = w / self._ppm
        height_mm = h / self._ppm
        area_mm2 = width_mm * height_mm

        if area_mm2 >= LARGE_AREA_THRESHOLD:
            category = "large"
            speed_factor = 1.5
        elif area_mm2 >= SMALL_AREA_THRESHOLD:
            category = "medium"
            speed_factor = 1.0
        else:
            category = "small"
            speed_factor = 1.0

        return SizeResult(
            width_mm=width_mm,
            height_mm=height_mm,
            area_mm2=area_mm2,
            category=category,
            speed_factor=speed_factor,
        )
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_size_estimator.py -v`
Expected: All 8 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_size_estimator.py foldit/foldit/size_estimator.py
git commit -m "feat: garment size estimation with speed factor"
```

---

## Task 6: Fold Quality Verifier

**Files:**
- Create: `foldit/tests/test_fold_verifier.py`
- Create: `foldit/foldit/fold_verifier.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_fold_verifier.py`:

```python
"""Tests for post-fold quality verification."""
import numpy as np


class FakeCameraForVerifier:
    def __init__(self, frame):
        self._frame = frame

    def capture_frame(self):
        return self._frame


class TestFoldVerifier:
    def _make_compact_frame(self):
        frame = np.full((480, 640, 3), 255, dtype=np.uint8)
        frame[150:330, 200:440] = [60, 60, 60]
        return frame

    def _make_messy_frame(self):
        frame = np.full((480, 640, 3), 255, dtype=np.uint8)
        frame[100:200, 100:300] = [60, 60, 60]
        frame[300:400, 350:500] = [60, 60, 60]
        return frame

    def test_compact_fold_passes(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        camera = FakeCameraForVerifier(self._make_compact_frame())
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.5)
        result = verifier.verify("shirt")
        assert result.success is True

    def test_messy_fold_fails(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        camera = FakeCameraForVerifier(self._make_messy_frame())
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.95)
        result = verifier.verify("shirt")
        assert result.success is False

    def test_result_includes_compactness(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        camera = FakeCameraForVerifier(self._make_compact_frame())
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.5)
        result = verifier.verify("shirt")
        assert 0.0 <= result.compactness <= 1.0

    def test_no_contour_fails(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        blank = np.full((480, 640, 3), 255, dtype=np.uint8)
        camera = FakeCameraForVerifier(blank)
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.5)
        result = verifier.verify("shirt")
        assert result.success is False
        assert result.compactness == 0.0
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_fold_verifier.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/fold_verifier.py`:

```python
"""Post-fold quality verification via contour compactness."""
import cv2
from dataclasses import dataclass


@dataclass
class FoldResult:
    success: bool
    compactness: float


class FoldVerifier:
    """Verifies fold quality by checking post-fold contour compactness."""

    def __init__(self, camera, preprocessor, min_compactness=0.6):
        self._camera = camera
        self._preprocessor = preprocessor
        self._min_compactness = min_compactness

    def verify(self, garment_type):
        frame = self._camera.capture_frame()
        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)
        contour = self._preprocessor.find_largest_contour(binary)

        if contour is None:
            return FoldResult(success=False, compactness=0.0)

        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        rect_area = w * h
        compactness = area / rect_area if rect_area > 0 else 0.0

        return FoldResult(
            success=compactness >= self._min_compactness,
            compactness=compactness,
        )
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_fold_verifier.py -v`
Expected: All 4 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_fold_verifier.py foldit/foldit/fold_verifier.py
git commit -m "feat: post-fold quality verification via contour compactness"
```

---

## Task 7: Error Recovery

**Files:**
- Create: `foldit/tests/test_error_recovery.py`
- Create: `foldit/foldit/error_recovery.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_error_recovery.py`:

```python
"""Tests for error recovery handlers."""
import numpy as np


class FakeCameraRestarting:
    def __init__(self, fail_count=1):
        self._fail_count = fail_count
        self._calls = 0
        self.restarts = 0

    def start(self):
        self.restarts += 1

    def capture_frame(self):
        self._calls += 1
        if self._calls <= self._fail_count:
            raise RuntimeError("camera disconnected")
        return np.full((480, 640, 3), 200, dtype=np.uint8)

    def stop(self):
        pass


class FakeConveyorRetrying:
    def __init__(self, fail_count=1):
        self._fail_count = fail_count
        self._calls = 0

    def advance_to_fold_zone(self, timeout_sec=10.0):
        self._calls += 1
        return self._calls > self._fail_count


class TestErrorRecovery:
    def test_camera_restart_on_exception(self):
        from foldit.error_recovery import ErrorRecovery
        camera = FakeCameraRestarting(fail_count=1)
        recovery = ErrorRecovery()
        frame = recovery.safe_capture(camera)
        assert frame is not None
        assert camera.restarts >= 1

    def test_camera_gives_up_after_max_retries(self):
        from foldit.error_recovery import ErrorRecovery
        camera = FakeCameraRestarting(fail_count=10)
        recovery = ErrorRecovery(max_retries=1)
        frame = recovery.safe_capture(camera)
        assert frame is None

    def test_conveyor_retry_on_first_timeout(self):
        from foldit.error_recovery import ErrorRecovery
        conveyor = FakeConveyorRetrying(fail_count=1)
        recovery = ErrorRecovery()
        result = recovery.safe_advance(conveyor)
        assert result is True

    def test_conveyor_gives_up_after_max_retries(self):
        from foldit.error_recovery import ErrorRecovery
        conveyor = FakeConveyorRetrying(fail_count=10)
        recovery = ErrorRecovery(max_retries=1)
        result = recovery.safe_advance(conveyor)
        assert result is False

    def test_max_one_retry_default(self):
        from foldit.error_recovery import ErrorRecovery
        recovery = ErrorRecovery()
        assert recovery.max_retries == 1

    def test_records_errors(self):
        from foldit.error_recovery import ErrorRecovery
        camera = FakeCameraRestarting(fail_count=1)
        recovery = ErrorRecovery()
        recovery.safe_capture(camera)
        assert len(recovery.errors) >= 1
        assert "camera" in recovery.errors[0]["component"]

    def test_robot_state_transitions(self):
        from foldit.error_recovery import RobotState
        assert RobotState.IDLE != RobotState.ERROR
        assert RobotState.RECOVERING != RobotState.FOLDING
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_error_recovery.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/error_recovery.py`:

```python
"""Error recovery handlers for the robot pipeline."""
from enum import Enum


class RobotState(Enum):
    IDLE = "idle"
    ADVANCING = "advancing"
    DETECTING = "detecting"
    FOLDING = "folding"
    VERIFYING = "verifying"
    ERROR = "error"
    RECOVERING = "recovering"


class ErrorRecovery:
    """Provides retry logic for recoverable pipeline failures."""

    def __init__(self, max_retries=1):
        self._max_retries = max_retries
        self._errors = []

    @property
    def max_retries(self):
        return self._max_retries

    @property
    def errors(self):
        return list(self._errors)

    def safe_capture(self, camera):
        for attempt in range(self._max_retries + 1):
            try:
                return camera.capture_frame()
            except Exception as e:
                self._errors.append({
                    "component": "camera",
                    "error": str(e),
                    "attempt": attempt + 1,
                })
                if attempt < self._max_retries:
                    try:
                        camera.stop()
                        camera.start()
                    except Exception:
                        pass
        return None

    def safe_advance(self, conveyor, timeout_sec=10.0):
        for attempt in range(self._max_retries + 1):
            result = conveyor.advance_to_fold_zone(timeout_sec=timeout_sec)
            if result:
                return True
            self._errors.append({
                "component": "conveyor",
                "error": "timeout",
                "attempt": attempt + 1,
            })
        return False
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_error_recovery.py -v`
Expected: All 7 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_error_recovery.py foldit/foldit/error_recovery.py
git commit -m "feat: error recovery with retry logic and state tracking"
```

---

## Task 8: Data Collection

**Files:**
- Create: `foldit/tests/test_data_collector.py`
- Create: `foldit/foldit/data_collector.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_data_collector.py`:

```python
"""Tests for garment image data collection."""
import os
import tempfile
import numpy as np


class TestDataCollector:
    def test_save_frame_creates_file(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "shirt")
            assert os.path.exists(path)
            assert "shirt" in path

    def test_save_increments_counter(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path1 = collector.save(frame, "shirt")
            path2 = collector.save(frame, "shirt")
            assert path1 != path2

    def test_save_creates_date_subdirectory(self):
        from foldit.data_collector import DataCollector
        from datetime import date
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "pants")
            today = date.today().isoformat()
            assert today in path

    def test_disabled_collector_does_not_save(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir, enabled=False)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "shirt")
            assert path is None
            assert len(os.listdir(tmpdir)) == 0

    def test_total_saved_count(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            collector.save(frame, "shirt")
            collector.save(frame, "pants")
            assert collector.total_saved == 2
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_data_collector.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/data_collector.py`:

```python
"""Garment image data collection for ML training."""
import os
from datetime import date

import cv2


class DataCollector:
    """Saves classified garment frames for future ML training."""

    def __init__(self, output_dir="./data/captures", enabled=True):
        self._output_dir = output_dir
        self._enabled = enabled
        self._counter = 0

    @property
    def total_saved(self):
        return self._counter

    def save(self, frame, garment_type):
        if not self._enabled:
            return None

        today = date.today().isoformat()
        day_dir = os.path.join(self._output_dir, today)
        os.makedirs(day_dir, exist_ok=True)

        self._counter += 1
        filename = f"{garment_type}_{self._counter:04d}.jpg"
        path = os.path.join(day_dir, filename)
        cv2.imwrite(path, frame)
        return path
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_data_collector.py -v`
Expected: All 5 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_data_collector.py foldit/foldit/data_collector.py
git commit -m "feat: garment image data collection for ML training"
```

---

## Task 9: Web Dashboard

**Files:**
- Create: `foldit/tests/test_dashboard.py`
- Create: `foldit/foldit/dashboard.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_dashboard.py`:

```python
"""Tests for Flask web dashboard."""
import json


class FakeMetricsForDashboard:
    def snapshot(self):
        return {
            "total_folds": 5,
            "success_count": 4,
            "success_rate": 0.8,
            "counts_by_type": {"shirt": 3, "pants": 2},
            "avg_cycle_sec": 7.5,
        }


class TestDashboard:
    def _make_app(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        state = {"state": RobotState.IDLE, "current_garment": None, "uptime_sec": 120}
        app = create_app(metrics, state)
        app.config["TESTING"] = True
        return app

    def test_index_returns_html(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200
            assert b"FoldIt" in response.data

    def test_status_returns_json(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.get("/api/status")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["state"] == "idle"
            assert "uptime_sec" in data

    def test_metrics_returns_json(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.get("/api/metrics")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["total_folds"] == 5
            assert data["success_rate"] == 0.8

    def test_control_start_returns_ok(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.post("/api/control/start")
            assert response.status_code == 200

    def test_control_stop_returns_ok(self):
        app = self._make_app()
        with app.test_client() as client:
            response = client.post("/api/control/stop")
            assert response.status_code == 200
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_dashboard.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/dashboard.py`:

```python
"""Flask web dashboard for monitoring the FoldIt robot."""
from flask import Flask, jsonify


DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head><title>FoldIt Dashboard</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
h1 { color: #00d4ff; }
.card { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
.stat { font-size: 24px; color: #00d4ff; }
.label { color: #a0a0a0; font-size: 14px; }
#status, #metrics { white-space: pre; }
</style>
</head>
<body>
<h1>FoldIt Robot Dashboard</h1>
<div class="card"><div class="label">Status</div><div id="status">Loading...</div></div>
<div class="card"><div class="label">Metrics</div><div id="metrics">Loading...</div></div>
<div class="card">
<button onclick="fetch('/api/control/start',{method:'POST'})">Start</button>
<button onclick="fetch('/api/control/stop',{method:'POST'})">Stop</button>
</div>
<script>
function update() {
  fetch('/api/status').then(r=>r.json()).then(d=>{
    document.getElementById('status').textContent=JSON.stringify(d,null,2);
  });
  fetch('/api/metrics').then(r=>r.json()).then(d=>{
    document.getElementById('metrics').textContent=JSON.stringify(d,null,2);
  });
}
update(); setInterval(update, 5000);
</script>
</body></html>"""


def create_app(metrics, state_dict):
    """Create Flask app with metrics and state references."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        return DASHBOARD_HTML

    @app.route("/api/status")
    def status():
        return jsonify({
            "state": state_dict["state"].value,
            "current_garment": state_dict.get("current_garment"),
            "uptime_sec": state_dict.get("uptime_sec", 0),
        })

    @app.route("/api/metrics")
    def metrics_endpoint():
        return jsonify(metrics.snapshot())

    @app.route("/api/control/start", methods=["POST"])
    def control_start():
        state_dict["state"] = state_dict.get("start_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    @app.route("/api/control/stop", methods=["POST"])
    def control_stop():
        state_dict["state"] = state_dict.get("stop_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    return app
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_dashboard.py -v`
Expected: All 5 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_dashboard.py foldit/foldit/dashboard.py
git commit -m "feat: Flask web dashboard with status, metrics, and controls"
```

---

## Task 10: Integration Tests

**Files:**
- Create: `foldit/tests/test_integration.py`

This task uses the existing `SimulatedCamera`, `SimulatedServoDriver`, `SimulatedConveyor`, and all new V3 modules to test the full pipeline end-to-end.

**Step 1: Write the integration tests**

Create `foldit/tests/test_integration.py`:

```python
"""End-to-end integration tests using simulator."""
import numpy as np
import os
import tempfile


class TestV3Integration:
    def _create_v3_robot(self):
        from foldit.simulator import SimulatedCamera, SimulatedServoDriver, SimulatedConveyor
        from foldit.camera import ImagePreprocessor
        from foldit.classifier import GarmentClassifier
        from foldit.folder import FoldSequencer
        from foldit.item_detector import ItemDetector
        from foldit.flatness import FlatnessChecker
        from foldit.motor_controller import FoldingPlatform
        from foldit.orientation import OrientationDetector
        from foldit.size_estimator import SizeEstimator
        from foldit.fold_verifier import FoldVerifier
        from foldit.error_recovery import ErrorRecovery
        from foldit.robot_logger import MetricsCollector
        from foldit.main import FoldItRobotV2

        camera = SimulatedCamera()
        servo = SimulatedServoDriver()
        platform = FoldingPlatform(servo)
        preprocessor = ImagePreprocessor()
        classifier = GarmentClassifier()
        sequencer = FoldSequencer(platform)
        conveyor = SimulatedConveyor()
        detector = ItemDetector()
        flatness = FlatnessChecker()

        robot = FoldItRobotV2(
            camera=camera, preprocessor=preprocessor, classifier=classifier,
            sequencer=sequencer, conveyor=conveyor, item_detector=detector,
            flatness_checker=flatness, platform=platform,
        )
        return robot, camera, servo, conveyor

    def test_full_cycle_detects_classifies_and_folds(self):
        robot, camera, servo, conveyor = self._create_v3_robot()
        result = robot.process_one()
        assert isinstance(result, str)
        assert result in ["shirt", "pants", "towel", "small", "unknown"]

    def test_conveyor_is_called(self):
        robot, camera, servo, conveyor = self._create_v3_robot()
        robot.process_one()
        assert len(conveyor.calls) == 1

    def test_servos_receive_moves(self):
        robot, camera, servo, conveyor = self._create_v3_robot()
        robot.process_one()
        move_entries = [e for e in servo.log if "move" in e]
        assert len(move_entries) > 0

    def test_orientation_detector_standalone(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        wide = np.array([[[50,100]],[[550,100]],[[550,300]],[[50,300]]], dtype=np.int32)
        result = detector.detect(wide)
        assert result.is_landscape is True

    def test_size_estimator_standalone(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[0,0]],[[600,0]],[[600,400]],[[0,400]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "large"
        assert size.speed_factor > 1.0

    def test_fold_verifier_with_simulated_camera(self):
        from foldit.simulator import SimulatedCamera
        from foldit.camera import ImagePreprocessor
        from foldit.fold_verifier import FoldVerifier
        camera = SimulatedCamera()
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.3)
        result = verifier.verify("shirt")
        assert result.compactness > 0.0

    def test_metrics_accumulate_across_cycles(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        metrics.record_fold("pants", success=True, cycle_sec=6.0)
        metrics.record_fold("shirt", success=False, cycle_sec=8.0)
        snap = metrics.snapshot()
        assert snap["total_folds"] == 3
        assert snap["success_count"] == 2
        assert snap["counts_by_type"]["shirt"] == 2

    def test_config_loader_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent.yaml")
        config = loader.load()
        assert config["conveyor"]["belt_speed_duty"] == 75

    def test_data_collection_saves_frames(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "shirt")
            assert os.path.exists(path)

    def test_dashboard_status_endpoint(self):
        from foldit.dashboard import create_app
        from foldit.robot_logger import MetricsCollector
        from foldit.error_recovery import RobotState
        import json
        metrics = MetricsCollector()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        app.config["TESTING"] = True
        with app.test_client() as client:
            resp = client.get("/api/status")
            data = json.loads(resp.data)
            assert data["state"] == "idle"
```

**Step 2: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_integration.py -v`
Expected: All 10 PASS (these use already-implemented modules)

**Step 3: Run full test suite**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All tests PASS (~170+ total)

**Step 4: Commit**

```bash
git add foldit/tests/test_integration.py
git commit -m "test: end-to-end integration tests for V3 pipeline"
```

---

## Task 11: Update main.py with V3 --simulate enhancements

**Files:**
- Modify: `foldit/foldit/main.py`
- Modify: `foldit/foldit/simulator.py`

**Step 1: Update simulator to include V3 components**

Add to `foldit/foldit/simulator.py` — a `create_simulated_robot_v3()` factory that includes orientation, size estimation, fold verification, error recovery, metrics, and data collection:

```python
def create_simulated_robot_v3(data_dir=None):
    """Factory that creates a V2 robot with all V3 support objects."""
    from foldit.camera import ImagePreprocessor
    from foldit.classifier import GarmentClassifier
    from foldit.folder import FoldSequencer
    from foldit.item_detector import ItemDetector
    from foldit.flatness import FlatnessChecker
    from foldit.motor_controller import FoldingPlatform
    from foldit.main import FoldItRobotV2
    from foldit.orientation import OrientationDetector
    from foldit.size_estimator import SizeEstimator
    from foldit.fold_verifier import FoldVerifier
    from foldit.error_recovery import ErrorRecovery
    from foldit.robot_logger import MetricsCollector, RobotLogger
    from foldit.data_collector import DataCollector

    camera = SimulatedCamera()
    servo = SimulatedServoDriver()
    platform = FoldingPlatform(servo)
    preprocessor = ImagePreprocessor()
    classifier = GarmentClassifier()
    sequencer = FoldSequencer(platform)
    conveyor = SimulatedConveyor()
    detector = ItemDetector()
    flatness = FlatnessChecker()

    robot = FoldItRobotV2(
        camera=camera, preprocessor=preprocessor, classifier=classifier,
        sequencer=sequencer, conveyor=conveyor, item_detector=detector,
        flatness_checker=flatness, platform=platform,
    )

    v3_context = {
        "orientation": OrientationDetector(),
        "size_estimator": SizeEstimator(pixels_per_mm=1.0),
        "fold_verifier": FoldVerifier(camera, preprocessor, min_compactness=0.3),
        "error_recovery": ErrorRecovery(),
        "metrics": MetricsCollector(),
        "logger": RobotLogger(name="simulator"),
        "data_collector": DataCollector(output_dir=data_dir or "./data/captures", enabled=data_dir is not None),
    }

    return robot, v3_context
```

**Step 2: Update main.py --simulate to show V3 info**

Update the `main()` function in `foldit/foldit/main.py` to use the V3 factory and print metrics after processing:

```python
def main():
    import argparse
    parser = argparse.ArgumentParser(description="FoldIt Robot Controller")
    parser.add_argument("--simulate", action="store_true", help="Run in simulator mode without hardware")
    parser.add_argument("--items", type=int, default=1, help="Number of items to process in simulate mode")
    args = parser.parse_args()

    if args.simulate:
        from foldit.simulator import create_simulated_robot_v3
        import time
        robot, ctx = create_simulated_robot_v3()
        for i in range(args.items):
            start = time.monotonic()
            result = robot.process_one()
            elapsed = time.monotonic() - start
            if result:
                ctx["metrics"].record_fold(result, success=True, cycle_sec=elapsed)
                ctx["logger"].log_event("fold_complete", garment=result, cycle_sec=round(elapsed, 2))
        print(ctx["metrics"].snapshot())


if __name__ == "__main__":
    main()
```

**Step 3: Run all tests**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: ALL PASS

**Step 4: Verify simulate mode works**

Run: `foldit/.venv/bin/python -m foldit.main --simulate --items 3`
Expected: Prints metrics snapshot dict with 3 folds

**Step 5: Commit**

```bash
git add foldit/foldit/simulator.py foldit/foldit/main.py
git commit -m "feat: V3 simulator factory and --items CLI flag"
```

---

## Summary

| Task | Component | New Tests | Files |
|------|-----------|-----------|-------|
| 1 | Dependencies | 0 | pyproject.toml |
| 2 | YAML Config | 7 | config_loader.py, test_config_loader.py |
| 3 | Logging + Metrics | 11 | robot_logger.py, test_robot_logger.py |
| 4 | Orientation | 6 | orientation.py, test_orientation.py |
| 5 | Size Estimator | 8 | size_estimator.py, test_size_estimator.py |
| 6 | Fold Verifier | 4 | fold_verifier.py, test_fold_verifier.py |
| 7 | Error Recovery | 7 | error_recovery.py, test_error_recovery.py |
| 8 | Data Collection | 5 | data_collector.py, test_data_collector.py |
| 9 | Web Dashboard | 5 | dashboard.py, test_dashboard.py |
| 10 | Integration Tests | 10 | test_integration.py |
| 11 | V3 Simulator | 0 | simulator.py, main.py (modified) |
| **Total** | | **63 new** | **~170+ total** |
