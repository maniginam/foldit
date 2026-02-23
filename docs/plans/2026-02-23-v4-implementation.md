# FoldIt V4 Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire all V3 standalone modules into a composed FoldItRobotV3 pipeline, add frame quality checks with auto-calibration, persist metrics to SQLite with failure alerting, and build an ML training workflow.

**Architecture:** FoldItRobotV3 composes V2's detection pipeline with V3's orientation, size estimation, fold verification, error recovery, metrics, logging, and data collection into a single process_one(). FoldSequencer gains a speed_factor parameter. New modules (frame_quality, auto_calibrator, metrics_store, alerter) slot into the pipeline via DI. Training pipeline runs offline.

**Tech Stack:** Python 3.11+, OpenCV, NumPy, Flask, PyYAML, SQLite3, pytest. Optional: TensorFlow 2.15+ for training.

**Run all tests with:** `foldit/.venv/bin/python -m pytest foldit/tests/ -v`

**Project root:** `/Users/maniginam/projects/foldit`

---

## Task 1: Add speed_factor to FoldSequencer

**Files:**
- Modify: `foldit/foldit/folder.py`
- Modify: `foldit/tests/test_folder.py`

**Step 1: Write the failing tests**

Add to the end of `foldit/tests/test_folder.py`:

```python
class FakeTimingPlatform:
    def __init__(self):
        self.actions = []
        self.delays = []

    def home(self):
        self.actions.append("home")

    def fold_left(self, delay_factor=1.0):
        self.actions.append("fold_left")
        self.delays.append(delay_factor)

    def fold_right(self, delay_factor=1.0):
        self.actions.append("fold_right")
        self.delays.append(delay_factor)

    def fold_bottom(self, delay_factor=1.0):
        self.actions.append("fold_bottom")
        self.delays.append(delay_factor)


class TestFoldSequencerSpeedFactor:
    def test_fold_with_speed_factor_passes_to_steps(self):
        from foldit.folder import FoldSequencer
        platform = FakeTimingPlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("shirt", speed_factor=1.5)
        assert all(d == 1.5 for d in platform.delays)

    def test_fold_default_speed_factor_is_one(self):
        from foldit.folder import FoldSequencer
        platform = FakeTimingPlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("pants", speed_factor=1.0)
        assert all(d == 1.0 for d in platform.delays)

    def test_fold_without_speed_factor_still_works(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        result = sequencer.fold("shirt")
        assert result == "shirt"
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_folder.py -v`
Expected: 2 new tests FAIL (FakeTimingPlatform fold methods have delay_factor but FoldSequencer doesn't pass it)

**Step 3: Write minimal implementation**

Replace the `fold` method in `foldit/foldit/folder.py`:

```python
class FoldSequencer:
    """Executes fold sequences on the platform for each garment type."""

    def __init__(self, platform):
        self._platform = platform

    def fold(self, garment_type, speed_factor=1.0):
        steps = FOLD_SEQUENCES.get(
            garment_type, FOLD_SEQUENCES[GarmentType.UNKNOWN]
        )
        self._platform.home()
        for step in steps:
            method = getattr(self._platform, step)
            try:
                method(delay_factor=speed_factor)
            except TypeError:
                method()
            self._platform.home()
        return garment_type
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_folder.py -v`
Expected: All 9 PASS (6 existing + 3 new)

**Step 5: Commit**

```bash
git add foldit/foldit/folder.py foldit/tests/test_folder.py
git commit -m "feat: add speed_factor parameter to FoldSequencer.fold()"
```

---

## Task 2: Frame Quality Checker

**Files:**
- Create: `foldit/tests/test_frame_quality.py`
- Create: `foldit/foldit/frame_quality.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_frame_quality.py`:

```python
"""Tests for pre-classification frame quality checks."""
import numpy as np


class TestFrameQualityChecker:
    def test_sharp_frame_passes(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:300] = 255
        result = checker.check(frame)
        assert result.acceptable is True

    def test_blurry_frame_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        import cv2
        checker = FrameQualityChecker(min_blur_score=100.0)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:300] = 255
        blurred = cv2.GaussianBlur(frame, (51, 51), 0)
        result = checker.check(blurred)
        assert result.acceptable is False
        assert result.blur_score < 100.0

    def test_low_contrast_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker(min_contrast=30.0)
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        result = checker.check(frame)
        assert result.acceptable is False
        assert result.contrast_score < 30.0

    def test_too_dark_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker(min_brightness=40.0)
        frame = np.full((480, 640, 3), 10, dtype=np.uint8)
        result = checker.check(frame)
        assert result.acceptable is False
        assert result.brightness_score < 40.0

    def test_too_bright_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker(max_brightness=220.0)
        frame = np.full((480, 640, 3), 250, dtype=np.uint8)
        result = checker.check(frame)
        assert result.acceptable is False
        assert result.brightness_score > 220.0

    def test_result_has_all_fields(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:300] = 255
        result = checker.check(frame)
        assert hasattr(result, "acceptable")
        assert hasattr(result, "blur_score")
        assert hasattr(result, "contrast_score")
        assert hasattr(result, "brightness_score")
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_frame_quality.py -v`
Expected: FAIL (no module `foldit.frame_quality`)

**Step 3: Write minimal implementation**

Create `foldit/foldit/frame_quality.py`:

```python
"""Pre-classification frame quality checks."""
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class QualityResult:
    acceptable: bool
    blur_score: float
    contrast_score: float
    brightness_score: float


class FrameQualityChecker:
    """Checks frame blur, contrast, and brightness before classification."""

    def __init__(self, min_blur_score=100.0, min_contrast=30.0,
                 min_brightness=40.0, max_brightness=220.0):
        self._min_blur = min_blur_score
        self._min_contrast = min_contrast
        self._min_brightness = min_brightness
        self._max_brightness = max_brightness

    def check(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast_score = float(np.std(gray))
        brightness_score = float(np.mean(gray))

        acceptable = (
            blur_score >= self._min_blur
            and contrast_score >= self._min_contrast
            and self._min_brightness <= brightness_score <= self._max_brightness
        )

        return QualityResult(
            acceptable=acceptable,
            blur_score=blur_score,
            contrast_score=contrast_score,
            brightness_score=brightness_score,
        )
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_frame_quality.py -v`
Expected: All 6 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_frame_quality.py foldit/foldit/frame_quality.py
git commit -m "feat: pre-classification frame quality checker"
```

---

## Task 3: Auto-Calibrator

**Files:**
- Create: `foldit/tests/test_auto_calibrator.py`
- Create: `foldit/foldit/auto_calibrator.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_auto_calibrator.py`:

```python
"""Tests for automatic pixels_per_mm calibration."""
import json
import os
import tempfile
import numpy as np


class TestAutoCalibrator:
    def _make_calibration_frame(self, rect_w_px=171, rect_h_px=108):
        """Create frame with white rectangle on black background.
        Default: credit card at ~2 px/mm (85.6mm * 2 = 171px, 53.98mm * 2 ≈ 108px)."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cx, cy = 320, 240
        x1, y1 = cx - rect_w_px // 2, cy - rect_h_px // 2
        x2, y2 = x1 + rect_w_px, y1 + rect_h_px
        frame[y1:y2, x1:x2] = 255
        return frame

    def test_calibrate_returns_pixels_per_mm(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator(reference_width_mm=85.6, reference_height_mm=53.98)
        frame = self._make_calibration_frame()
        result = cal.calibrate(frame)
        assert 1.5 < result.pixels_per_mm < 2.5

    def test_calibrate_no_rectangle_returns_none(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = cal.calibrate(frame)
        assert result is None

    def test_save_and_load_calibration(self):
        from foldit.auto_calibrator import AutoCalibrator
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "calibration.json")
            cal = AutoCalibrator()
            frame = self._make_calibration_frame()
            result = cal.calibrate(frame)
            cal.save(result, path)
            loaded = cal.load(path)
            assert abs(loaded.pixels_per_mm - result.pixels_per_mm) < 0.01

    def test_load_missing_file_returns_none(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        result = cal.load("/nonexistent/calibration.json")
        assert result is None

    def test_calibration_result_has_fields(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        frame = self._make_calibration_frame()
        result = cal.calibrate(frame)
        assert hasattr(result, "pixels_per_mm")
        assert hasattr(result, "reference_width_px")
        assert hasattr(result, "reference_height_px")
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_auto_calibrator.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/auto_calibrator.py`:

```python
"""Automatic camera calibration using a known-size reference object."""
import json
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class CalibrationResult:
    pixels_per_mm: float
    reference_width_px: float
    reference_height_px: float


class AutoCalibrator:
    """Calibrates pixels_per_mm using a known-size reference rectangle."""

    def __init__(self, reference_width_mm=85.6, reference_height_mm=53.98):
        self._ref_w = reference_width_mm
        self._ref_h = reference_height_mm

    def calibrate(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        if w < 20 or h < 20:
            return None

        ppm_w = w / self._ref_w
        ppm_h = h / self._ref_h
        pixels_per_mm = (ppm_w + ppm_h) / 2.0

        return CalibrationResult(
            pixels_per_mm=pixels_per_mm,
            reference_width_px=float(w),
            reference_height_px=float(h),
        )

    def save(self, result, path):
        with open(path, "w") as f:
            json.dump({
                "pixels_per_mm": result.pixels_per_mm,
                "reference_width_px": result.reference_width_px,
                "reference_height_px": result.reference_height_px,
            }, f)

    def load(self, path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return CalibrationResult(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_auto_calibrator.py -v`
Expected: All 5 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_auto_calibrator.py foldit/foldit/auto_calibrator.py
git commit -m "feat: automatic camera calibration using reference object"
```

---

## Task 4: Metrics Store (SQLite)

**Files:**
- Create: `foldit/tests/test_metrics_store.py`
- Create: `foldit/foldit/metrics_store.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_metrics_store.py`:

```python
"""Tests for SQLite metrics persistence."""
import os
import tempfile


class TestMetricsStore:
    def test_record_and_query_recent(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.85, 12.3)
            store.record("pants", False, 7.0, 0.40, -5.0)
            rows = store.query_recent(minutes=60)
            assert len(rows) == 2
            assert rows[0]["garment_type"] == "shirt"
            assert rows[1]["success"] is False

    def test_summary_matches_snapshot_shape(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.85, 0.0)
            store.record("shirt", True, 6.0, 0.90, 0.0)
            store.record("pants", False, 8.0, 0.30, 0.0)
            summary = store.summary(minutes=60)
            assert summary["total_folds"] == 3
            assert summary["success_count"] == 2
            assert abs(summary["success_rate"] - 2 / 3) < 0.01
            assert summary["counts_by_type"] == {"shirt": 2, "pants": 1}
            assert abs(summary["avg_cycle_sec"] - 19.0 / 3) < 0.1

    def test_db_file_created_on_first_record(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            assert not os.path.exists(db_path)
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.8, 0.0)
            assert os.path.exists(db_path)

    def test_query_empty_returns_empty_list(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            rows = store.query_recent(minutes=60)
            assert rows == []

    def test_summary_empty_returns_zeros(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            summary = store.summary(minutes=60)
            assert summary["total_folds"] == 0
            assert summary["success_rate"] == 0.0
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_metrics_store.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/metrics_store.py`:

```python
"""SQLite-based metrics persistence."""
import sqlite3
from datetime import datetime, timezone, timedelta


class MetricsStore:
    """Durable fold metrics stored in SQLite."""

    def __init__(self, db_path="data/metrics.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS folds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                garment_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                cycle_sec REAL NOT NULL,
                compactness REAL,
                orientation_angle REAL
            )
        """)
        self._conn.commit()

    def record(self, garment_type, success, cycle_sec, compactness=0.0, orientation_angle=0.0):
        ts = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO folds (timestamp, garment_type, success, cycle_sec, compactness, orientation_angle) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, garment_type, int(success), cycle_sec, compactness, orientation_angle),
        )
        self._conn.commit()

    def query_recent(self, minutes=60):
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        cursor = self._conn.execute(
            "SELECT * FROM folds WHERE timestamp >= ? ORDER BY timestamp",
            (cutoff,),
        )
        rows = cursor.fetchall()
        return [
            {
                "garment_type": r["garment_type"],
                "success": bool(r["success"]),
                "cycle_sec": r["cycle_sec"],
                "compactness": r["compactness"],
                "orientation_angle": r["orientation_angle"],
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]

    def summary(self, minutes=60):
        rows = self.query_recent(minutes=minutes)
        total = len(rows)
        if total == 0:
            return {
                "total_folds": 0,
                "success_count": 0,
                "success_rate": 0.0,
                "counts_by_type": {},
                "avg_cycle_sec": 0.0,
            }
        successes = sum(1 for r in rows if r["success"])
        by_type = {}
        for r in rows:
            by_type[r["garment_type"]] = by_type.get(r["garment_type"], 0) + 1
        avg_cycle = sum(r["cycle_sec"] for r in rows) / total
        return {
            "total_folds": total,
            "success_count": successes,
            "success_rate": successes / total,
            "counts_by_type": by_type,
            "avg_cycle_sec": avg_cycle,
        }

    def close(self):
        self._conn.close()
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_metrics_store.py -v`
Expected: All 5 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_metrics_store.py foldit/foldit/metrics_store.py
git commit -m "feat: SQLite metrics persistence with query and summary"
```

---

## Task 5: Failure Alerter

**Files:**
- Create: `foldit/tests/test_alerter.py`
- Create: `foldit/foldit/alerter.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_alerter.py`:

```python
"""Tests for failure pattern alerting."""


class TestAlerter:
    def test_no_alert_on_success(self):
        from foldit.alerter import Alerter
        alerter = Alerter()
        alert = alerter.check("shirt", success=True)
        assert alert is None

    def test_consecutive_failures_triggers_alert(self):
        from foldit.alerter import Alerter
        alerter = Alerter(consecutive_fail_threshold=3)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=False)
        alert = alerter.check("shirt", success=False)
        assert alert is not None
        assert alert.rule == "consecutive_failures"

    def test_consecutive_failures_resets_on_success(self):
        from foldit.alerter import Alerter
        alerter = Alerter(consecutive_fail_threshold=3)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=True)
        alert = alerter.check("shirt", success=False)
        assert alert is None

    def test_low_success_rate_triggers_alert(self):
        from foldit.alerter import Alerter
        alerter = Alerter(rate_window=4, min_success_rate=0.5)
        alerter.check("shirt", success=True)
        alerter.check("shirt", success=False)
        alerter.check("shirt", success=False)
        alert = alerter.check("shirt", success=False)
        assert alert is not None
        assert alert.rule == "low_success_rate"

    def test_no_rate_alert_when_above_threshold(self):
        from foldit.alerter import Alerter
        alerter = Alerter(rate_window=4, min_success_rate=0.5)
        alerter.check("shirt", success=True)
        alerter.check("shirt", success=True)
        alerter.check("shirt", success=True)
        alert = alerter.check("shirt", success=False)
        assert alert is None

    def test_alert_has_expected_fields(self):
        from foldit.alerter import Alerter
        alerter = Alerter(consecutive_fail_threshold=1)
        alert = alerter.check("shirt", success=False)
        assert hasattr(alert, "rule")
        assert hasattr(alert, "message")
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_alerter.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/alerter.py`:

```python
"""Failure pattern alerting for the robot pipeline."""
from collections import deque
from dataclasses import dataclass


@dataclass
class Alert:
    rule: str
    message: str


class Alerter:
    """Monitors fold outcomes and raises alerts on failure patterns."""

    def __init__(self, consecutive_fail_threshold=3, rate_window=20, min_success_rate=0.5):
        self._consec_threshold = consecutive_fail_threshold
        self._rate_window = rate_window
        self._min_rate = min_success_rate
        self._consecutive_failures = 0
        self._recent = deque(maxlen=rate_window)

    def check(self, garment_type, success):
        self._recent.append(success)

        if success:
            self._consecutive_failures = 0
            return None

        self._consecutive_failures += 1

        if self._consecutive_failures >= self._consec_threshold:
            return Alert(
                rule="consecutive_failures",
                message=f"{self._consecutive_failures} consecutive fold failures",
            )

        if len(self._recent) >= self._rate_window:
            rate = sum(self._recent) / len(self._recent)
            if rate < self._min_rate:
                return Alert(
                    rule="low_success_rate",
                    message=f"Success rate {rate:.0%} below {self._min_rate:.0%} threshold",
                )

        return None
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_alerter.py -v`
Expected: All 6 PASS

**Step 5: Commit**

```bash
git add foldit/tests/test_alerter.py foldit/foldit/alerter.py
git commit -m "feat: failure pattern alerter with consecutive and rate rules"
```

---

## Task 6: Add YAML config sections for new modules

**Files:**
- Modify: `foldit/foldit/config_loader.py`
- Modify: `foldit/tests/test_config_loader.py`

**Step 1: Write the failing test**

Add to the end of `foldit/tests/test_config_loader.py`:

```python
class TestConfigLoaderV4Sections:
    def test_frame_quality_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["frame_quality"]["min_blur_score"] == 100.0
        assert config["frame_quality"]["min_contrast"] == 30.0
        assert config["frame_quality"]["min_brightness"] == 40.0
        assert config["frame_quality"]["max_brightness"] == 220.0

    def test_alerting_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["alerting"]["consecutive_fail_threshold"] == 3
        assert config["alerting"]["rate_window"] == 20
        assert config["alerting"]["min_success_rate"] == 0.5

    def test_metrics_store_defaults(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["metrics_store"]["db_path"] == "data/metrics.db"
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_config_loader.py -v`
Expected: 3 new tests FAIL (KeyError on new sections)

**Step 3: Add new sections to DEFAULTS**

Add these sections to the `DEFAULTS` dict in `foldit/foldit/config_loader.py`, after the `"data_collection"` section:

```python
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
    },
    "metrics_store": {
        "db_path": "data/metrics.db",
    },
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_config_loader.py -v`
Expected: All 10 PASS (7 existing + 3 new)

**Step 5: Commit**

```bash
git add foldit/foldit/config_loader.py foldit/tests/test_config_loader.py
git commit -m "feat: add frame_quality, alerting, metrics_store config sections"
```

---

## Task 7: Dashboard history endpoint

**Files:**
- Modify: `foldit/foldit/dashboard.py`
- Modify: `foldit/tests/test_dashboard.py`

**Step 1: Write the failing tests**

Add to the end of `foldit/tests/test_dashboard.py`:

```python
class FakeMetricsStoreForDashboard:
    def query_recent(self, minutes=60):
        return [
            {"garment_type": "shirt", "success": True, "cycle_sec": 5.0,
             "compactness": 0.85, "orientation_angle": 0.0, "timestamp": "2026-02-23T10:00:00"},
            {"garment_type": "pants", "success": False, "cycle_sec": 7.0,
             "compactness": 0.30, "orientation_angle": 12.0, "timestamp": "2026-02-23T10:01:00"},
        ]


class TestDashboardHistory:
    def _make_app_with_store(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        store = FakeMetricsStoreForDashboard()
        state = {"state": RobotState.IDLE, "current_garment": None, "uptime_sec": 120}
        app = create_app(metrics, state, metrics_store=store)
        app.config["TESTING"] = True
        return app

    def test_history_returns_json_array(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            response = client.get("/api/metrics/history?minutes=60")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]["garment_type"] == "shirt"

    def test_history_default_minutes(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            response = client.get("/api/metrics/history")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_dashboard.py -v`
Expected: 2 new tests FAIL

**Step 3: Update create_app to accept metrics_store**

Replace the `create_app` function in `foldit/foldit/dashboard.py`:

```python
def create_app(metrics, state_dict, metrics_store=None):
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

    @app.route("/api/metrics/history")
    def metrics_history():
        from flask import request
        minutes = request.args.get("minutes", 60, type=int)
        if metrics_store:
            return jsonify(metrics_store.query_recent(minutes=minutes))
        return jsonify([])

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
Expected: All 7 PASS (5 existing + 2 new)

**Step 5: Commit**

```bash
git add foldit/foldit/dashboard.py foldit/tests/test_dashboard.py
git commit -m "feat: dashboard history endpoint with SQLite query"
```

---

## Task 8: FoldItRobotV3

**Files:**
- Create: `foldit/tests/test_v3_pipeline.py`
- Modify: `foldit/foldit/main.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_v3_pipeline.py`:

```python
"""Tests for FoldItRobotV3 composed pipeline."""
import time
import numpy as np


class FakeCameraV3:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def capture_frame(self):
        frame = np.full((480, 640, 3), 255, dtype=np.uint8)
        frame[140:340, 170:470] = [120, 80, 60]
        return frame


class FakePreprocessorV3:
    def to_grayscale(self, image):
        import cv2
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def threshold(self, gray):
        import cv2
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return binary

    def find_largest_contour(self, binary):
        import cv2
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)


class FakeClassifierV3:
    def classify(self, contour):
        return "shirt"


class FakeSequencerV3:
    def __init__(self):
        self.folded = []
        self.speed_factors = []

    def fold(self, garment_type, speed_factor=1.0):
        self.folded.append(garment_type)
        self.speed_factors.append(speed_factor)
        return garment_type


class FakeConveyorV3:
    def advance_to_fold_zone(self, timeout_sec=10.0):
        return True


class FakeDetectorV3:
    def detect(self, binary):
        from foldit.item_detector import DetectionResult
        contour = np.array([[[170,140]],[[470,140]],[[470,340]],[[170,340]]], dtype=np.int32)
        return DetectionResult(count=1, largest=contour, all_contours=[contour])


class FakeFlatnessV3:
    def is_flat(self, contour):
        return True


class TestFoldItRobotV3:
    def _make_robot(self, **overrides):
        from foldit.main import FoldItRobotV3
        from foldit.orientation import OrientationDetector
        from foldit.size_estimator import SizeEstimator
        from foldit.fold_verifier import FoldVerifier
        from foldit.error_recovery import ErrorRecovery
        from foldit.robot_logger import MetricsCollector, RobotLogger
        from foldit.data_collector import DataCollector
        from foldit.frame_quality import FrameQualityChecker
        from foldit.alerter import Alerter

        camera = overrides.get("camera", FakeCameraV3())
        preprocessor = overrides.get("preprocessor", FakePreprocessorV3())
        classifier = overrides.get("classifier", FakeClassifierV3())
        sequencer = overrides.get("sequencer", FakeSequencerV3())
        conveyor = overrides.get("conveyor", FakeConveyorV3())
        detector = overrides.get("detector", FakeDetectorV3())
        flatness = overrides.get("flatness", FakeFlatnessV3())

        robot = FoldItRobotV3(
            camera=camera,
            preprocessor=preprocessor,
            classifier=classifier,
            sequencer=sequencer,
            conveyor=conveyor,
            item_detector=detector,
            flatness_checker=flatness,
            orientation=OrientationDetector(),
            size_estimator=SizeEstimator(pixels_per_mm=1.0),
            fold_verifier=FoldVerifier(camera, preprocessor, min_compactness=0.3),
            error_recovery=ErrorRecovery(),
            metrics=MetricsCollector(),
            logger=RobotLogger(name="test"),
            data_collector=DataCollector(enabled=False),
            frame_quality=FrameQualityChecker(),
            alerter=Alerter(),
        )
        return robot, sequencer

    def test_process_one_returns_garment_type(self):
        robot, seq = self._make_robot()
        result = robot.process_one()
        assert result == "shirt"

    def test_process_one_records_metrics(self):
        robot, seq = self._make_robot()
        robot.process_one()
        assert robot._metrics.total_folds == 1

    def test_process_one_passes_speed_factor(self):
        robot, seq = self._make_robot()
        robot.process_one()
        assert len(seq.speed_factors) == 1
        assert seq.speed_factors[0] >= 1.0

    def test_process_one_runs_orientation(self):
        robot, seq = self._make_robot()
        robot.process_one()
        assert robot._last_orientation is not None

    def test_process_one_runs_size_estimation(self):
        robot, seq = self._make_robot()
        robot.process_one()
        assert robot._last_size is not None

    def test_run_processes_multiple_items(self):
        robot, seq = self._make_robot()
        folded = robot.run(max_items=3)
        assert len(folded) == 3
        assert robot._metrics.total_folds == 3

    def test_run_stops_camera_on_completion(self):
        camera = FakeCameraV3()
        robot, seq = self._make_robot(camera=camera)
        robot.run(max_items=1)
        assert camera.started is True
        assert camera.stopped is True

    def test_conveyor_failure_returns_none(self):
        class FailConveyor:
            def advance_to_fold_zone(self, timeout_sec=10.0):
                return False
        robot, seq = self._make_robot(conveyor=FailConveyor())
        result = robot.process_one()
        assert result is None

    def test_stop_flag_halts_run(self):
        robot, seq = self._make_robot()
        robot._stop_requested = True
        folded = robot.run(max_items=100)
        assert len(folded) == 0
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_v3_pipeline.py -v`
Expected: FAIL (no FoldItRobotV3)

**Step 3: Write FoldItRobotV3 implementation**

Add `FoldItRobotV3` class to `foldit/foldit/main.py` (after FoldItRobotV2, before main()):

```python
class FoldItRobotV3:
    """V3 pipeline: full V2 pipeline + orientation, size, verification, error recovery, metrics."""

    def __init__(self, camera, preprocessor, classifier, sequencer,
                 conveyor, item_detector, flatness_checker,
                 orientation, size_estimator, fold_verifier,
                 error_recovery, metrics, logger, data_collector,
                 frame_quality, alerter, platform=None):
        self._camera = camera
        self._preprocessor = preprocessor
        self._classifier = classifier
        self._sequencer = sequencer
        self._conveyor = conveyor
        self._detector = item_detector
        self._flatness = flatness_checker
        self._platform = platform
        self._orientation = orientation
        self._size_estimator = size_estimator
        self._verifier = fold_verifier
        self._recovery = error_recovery
        self._metrics = metrics
        self._logger = logger
        self._data_collector = data_collector
        self._frame_quality = frame_quality
        self._alerter = alerter
        self._stop_requested = False
        self._last_orientation = None
        self._last_size = None

    def process_one(self):
        import time
        start = time.monotonic()

        if not self._recovery.safe_advance(self._conveyor):
            return None

        frame = self._recovery.safe_capture(self._camera)
        if frame is None:
            return None

        quality = self._frame_quality.check(frame)
        if not quality.acceptable:
            frame = self._recovery.safe_capture(self._camera)
            if frame is None:
                return None

        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)

        detection = self._detector.detect(binary)
        if not detection.is_single:
            return None

        contour = detection.largest
        if not self._flatness.is_flat(contour) and self._platform:
            self._platform.fold_left()
            self._platform.home()
            self._platform.fold_right()
            self._platform.home()
            frame = self._recovery.safe_capture(self._camera)
            if frame is None:
                return None
            gray = self._preprocessor.to_grayscale(frame)
            binary = self._preprocessor.threshold(gray)
            detection = self._detector.detect(binary)
            contour = detection.largest

        if contour is None:
            return None

        self._last_orientation = self._orientation.detect(contour)
        self._last_size = self._size_estimator.estimate(contour)

        garment_type = self._classifier.classify(contour)
        self._data_collector.save(frame, garment_type)

        self._sequencer.fold(garment_type, speed_factor=self._last_size.speed_factor)

        verify_result = self._verifier.verify(garment_type)
        if not verify_result.success:
            self._sequencer.fold(garment_type, speed_factor=self._last_size.speed_factor)
            verify_result = self._verifier.verify(garment_type)

        elapsed = time.monotonic() - start
        self._metrics.record_fold(garment_type, success=verify_result.success, cycle_sec=elapsed)
        self._logger.log_event(
            "fold_complete", garment=garment_type,
            cycle_sec=round(elapsed, 2), verified=verify_result.success,
            compactness=round(verify_result.compactness, 3),
        )
        self._alerter.check(garment_type, success=verify_result.success)

        return garment_type

    def run(self, max_items=None):
        self._camera.start()
        folded = []
        try:
            count = 0
            while (max_items is None or count < max_items) and not self._stop_requested:
                result = self.process_one()
                if result is not None:
                    folded.append(result)
                    count += 1
        except Exception:
            pass
        finally:
            self._camera.stop()
        return folded

    def stop(self):
        self._stop_requested = True
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_v3_pipeline.py -v`
Expected: All 9 PASS

**Step 5: Run full suite**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add foldit/foldit/main.py foldit/tests/test_v3_pipeline.py
git commit -m "feat: FoldItRobotV3 composed pipeline with all V3 modules"
```

---

## Task 9: Update simulator and main() for V3

**Files:**
- Modify: `foldit/foldit/simulator.py`
- Modify: `foldit/foldit/main.py`

**Step 1: Update create_simulated_robot_v3 to return FoldItRobotV3**

Replace the `create_simulated_robot_v3` function in `foldit/foldit/simulator.py`:

```python
def create_simulated_robot_v3(data_dir=None):
    """Factory that creates a FoldItRobotV3 with all modules wired."""
    from foldit.camera import ImagePreprocessor
    from foldit.classifier import GarmentClassifier
    from foldit.folder import FoldSequencer
    from foldit.item_detector import ItemDetector
    from foldit.flatness import FlatnessChecker
    from foldit.motor_controller import FoldingPlatform
    from foldit.main import FoldItRobotV3
    from foldit.orientation import OrientationDetector
    from foldit.size_estimator import SizeEstimator
    from foldit.fold_verifier import FoldVerifier
    from foldit.error_recovery import ErrorRecovery
    from foldit.robot_logger import MetricsCollector, RobotLogger
    from foldit.data_collector import DataCollector
    from foldit.frame_quality import FrameQualityChecker
    from foldit.alerter import Alerter

    camera = SimulatedCamera()
    servo = SimulatedServoDriver()
    platform = FoldingPlatform(servo)
    preprocessor = ImagePreprocessor()
    classifier = GarmentClassifier()
    sequencer = FoldSequencer(platform)
    conveyor = SimulatedConveyor()
    detector = ItemDetector()
    flatness = FlatnessChecker()

    robot = FoldItRobotV3(
        camera=camera,
        preprocessor=preprocessor,
        classifier=classifier,
        sequencer=sequencer,
        conveyor=conveyor,
        item_detector=detector,
        flatness_checker=flatness,
        platform=platform,
        orientation=OrientationDetector(),
        size_estimator=SizeEstimator(pixels_per_mm=1.0),
        fold_verifier=FoldVerifier(camera, preprocessor, min_compactness=0.3),
        error_recovery=ErrorRecovery(),
        metrics=MetricsCollector(),
        logger=RobotLogger(name="simulator"),
        data_collector=DataCollector(output_dir=data_dir or "./data/captures", enabled=data_dir is not None),
        frame_quality=FrameQualityChecker(),
        alerter=Alerter(),
    )

    return robot
```

**Step 2: Update main() to use the new factory**

Replace the `main()` function in `foldit/foldit/main.py`:

```python
def main():
    import argparse
    parser = argparse.ArgumentParser(description="FoldIt Robot Controller")
    parser.add_argument("--simulate", action="store_true", help="Run in simulator mode without hardware")
    parser.add_argument("--items", type=int, default=1, help="Number of items to process in simulate mode")
    args = parser.parse_args()

    if args.simulate:
        from foldit.simulator import create_simulated_robot_v3
        robot = create_simulated_robot_v3()
        folded = robot.run(max_items=args.items)
        print(f"Folded {len(folded)} items: {folded}")
        print(f"Metrics: {robot._metrics.snapshot()}")


if __name__ == "__main__":
    main()
```

**Step 3: Run full test suite**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: ALL PASS

**Step 4: Verify simulate works**

Run: `foldit/.venv/bin/python -m foldit.main --simulate --items 3`
Expected: Prints folded items list and metrics snapshot

**Step 5: Commit**

```bash
git add foldit/foldit/simulator.py foldit/foldit/main.py
git commit -m "feat: V3 simulator factory returns FoldItRobotV3 directly"
```

---

## Task 10: ML Training — Label Tool and Dataset

**Files:**
- Create: `foldit/training/label_tool.py`
- Create: `foldit/training/dataset.py`
- Create: `foldit/tests/test_label_tool.py`
- Create: `foldit/tests/test_dataset.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_label_tool.py`:

```python
"""Tests for the frame labeling tool."""
import os
import csv
import tempfile
import numpy as np
import cv2


class TestLabelTool:
    def test_save_label_writes_csv(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            store.save_label("/path/to/frame.jpg", "shirt")
            store.save_label("/path/to/frame2.jpg", "pants")
            labels = store.load_all()
            assert len(labels) == 2
            assert labels[0]["path"] == "/path/to/frame.jpg"
            assert labels[0]["label"] == "shirt"

    def test_load_empty_csv_returns_empty(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            labels = store.load_all()
            assert labels == []

    def test_resume_skips_labeled(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            store.save_label("/a.jpg", "shirt")
            store.save_label("/b.jpg", "pants")
            labeled = store.labeled_paths()
            assert "/a.jpg" in labeled
            assert "/b.jpg" in labeled
```

Create `foldit/tests/test_dataset.py`:

```python
"""Tests for dataset packaging."""
import os
import tempfile
import csv
import numpy as np
import cv2


class TestDatasetSplitter:
    def _make_fake_data(self, tmpdir, count=20):
        from training.label_tool import LabelStore
        csv_path = os.path.join(tmpdir, "labels.csv")
        store = LabelStore(csv_path)
        for i in range(count):
            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.jpg")
            frame = np.full((100, 100, 3), i * 10, dtype=np.uint8)
            cv2.imwrite(frame_path, frame)
            label = "shirt" if i % 2 == 0 else "pants"
            store.save_label(frame_path, label)
        return csv_path

    def test_split_ratios(self):
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self._make_fake_data(tmpdir, count=20)
            splitter = DatasetSplitter(csv_path)
            train, val, test = splitter.split(train=0.7, val=0.15, test=0.15)
            assert len(train) == 14
            assert len(val) == 3
            assert len(test) == 3

    def test_load_images_returns_correct_shape(self):
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self._make_fake_data(tmpdir, count=10)
            splitter = DatasetSplitter(csv_path)
            train, _, _ = splitter.split()
            images, labels = splitter.load_images(train, size=(224, 224))
            assert images.shape == (7, 224, 224, 3)
            assert len(labels) == 7

    def test_empty_csv_returns_empty_splits(self):
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            with open(csv_path, "w"):
                pass
            splitter = DatasetSplitter(csv_path)
            train, val, test = splitter.split()
            assert len(train) == 0
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_label_tool.py foldit/tests/test_dataset.py -v`
Expected: FAIL

**Step 3: Write implementations**

Create `foldit/training/__init__.py` (empty file).

Create `foldit/training/label_tool.py`:

```python
"""CLI frame labeling tool for ML training data."""
import csv
import os
from datetime import datetime, timezone


class LabelStore:
    """Reads and writes frame labels to a CSV file."""

    def __init__(self, csv_path):
        self._csv_path = csv_path

    def save_label(self, frame_path, label):
        file_exists = os.path.exists(self._csv_path)
        with open(self._csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "label", "timestamp"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "path": frame_path,
                "label": label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    def load_all(self):
        if not os.path.exists(self._csv_path):
            return []
        with open(self._csv_path, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def labeled_paths(self):
        return {row["path"] for row in self.load_all()}
```

Create `foldit/training/dataset.py`:

```python
"""Dataset packaging and splitting for ML training."""
import csv
import os
import random

import cv2
import numpy as np


class DatasetSplitter:
    """Splits labeled data into train/val/test sets and loads images."""

    def __init__(self, csv_path):
        self._csv_path = csv_path

    def _load_csv(self):
        if not os.path.exists(self._csv_path):
            return []
        with open(self._csv_path, "r") as f:
            reader = csv.DictReader(f)
            return [row for row in reader if row]

    def split(self, train=0.7, val=0.15, test=0.15):
        rows = self._load_csv()
        if not rows:
            return [], [], []
        random.seed(42)
        random.shuffle(rows)
        n = len(rows)
        train_end = int(n * train)
        val_end = train_end + int(n * val)
        return rows[:train_end], rows[train_end:val_end], rows[val_end:]

    def load_images(self, rows, size=(224, 224)):
        images = []
        labels = []
        for row in rows:
            img = cv2.imread(row["path"])
            if img is None:
                continue
            img = cv2.resize(img, size)
            images.append(img)
            labels.append(row["label"])
        return np.array(images), labels
```

**Step 4: Run tests to verify they pass**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_label_tool.py foldit/tests/test_dataset.py -v`
Expected: All 6 PASS

**Step 5: Commit**

```bash
git add foldit/training/__init__.py foldit/training/label_tool.py foldit/training/dataset.py foldit/tests/test_label_tool.py foldit/tests/test_dataset.py
git commit -m "feat: label tool and dataset splitter for ML training pipeline"
```

---

## Task 11: ML Training — Train and Validate Scripts

**Files:**
- Create: `foldit/training/train.py`
- Create: `foldit/training/validate.py`
- Modify: `foldit/pyproject.toml`

**Step 1: Add tensorflow as optional dependency**

Add to `foldit/pyproject.toml` under `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.11.0",
]
training = [
    "tensorflow>=2.15.0",
]
```

**Step 2: Create training script**

Create `foldit/training/train.py`:

```python
"""MobileNetV2 fine-tuning for garment classification."""
import os
import sys


def train(csv_path, output_dir="models", epochs=20, batch_size=16):
    """Fine-tune MobileNetV2 on labeled garment data."""
    try:
        import tensorflow as tf
    except ImportError:
        print("TensorFlow not installed. Install with: pip install tensorflow>=2.15.0")
        sys.exit(1)

    from training.dataset import DatasetSplitter

    splitter = DatasetSplitter(csv_path)
    train_rows, val_rows, _ = splitter.split()

    if not train_rows:
        print("No training data found.")
        return None

    train_images, train_labels = splitter.load_images(train_rows, size=(224, 224))
    val_images, val_labels = splitter.load_images(val_rows, size=(224, 224))

    label_set = sorted(set(train_labels))
    label_to_idx = {l: i for i, l in enumerate(label_set)}
    train_y = tf.keras.utils.to_categorical([label_to_idx[l] for l in train_labels], len(label_set))
    val_y = tf.keras.utils.to_categorical([label_to_idx[l] for l in val_labels], len(label_set))

    train_x = tf.keras.applications.mobilenet_v2.preprocess_input(train_images.astype("float32"))
    val_x = tf.keras.applications.mobilenet_v2.preprocess_input(val_images.astype("float32"))

    base = tf.keras.applications.MobileNetV2(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
    base.trainable = False

    model = tf.keras.Sequential([
        base,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(len(label_set), activation="softmax"),
    ])

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(patience=3, factor=0.5),
    ]

    model.fit(train_x, train_y, validation_data=(val_x, val_y),
              epochs=epochs, batch_size=batch_size, callbacks=callbacks)

    os.makedirs(output_dir, exist_ok=True)
    h5_path = os.path.join(output_dir, "garment_classifier.h5")
    model.save(h5_path)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    tflite_path = os.path.join(output_dir, "garment_classifier.tflite")
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)

    label_path = os.path.join(output_dir, "labels.txt")
    with open(label_path, "w") as f:
        for label in label_set:
            f.write(label + "\n")

    print(f"Model saved to {h5_path}")
    print(f"TFLite model saved to {tflite_path}")
    print(f"Labels saved to {label_path}")
    return tflite_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train garment classifier")
    parser.add_argument("--csv", required=True, help="Path to labels.csv")
    parser.add_argument("--output", default="models", help="Output directory")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    train(args.csv, args.output, args.epochs)
```

Create `foldit/training/validate.py`:

```python
"""Validate a TFLite garment classifier model."""
import os
import sys


def validate(tflite_path, csv_path, labels_path):
    """Run validation on test split and report per-class metrics."""
    try:
        import numpy as np
    except ImportError:
        print("NumPy not installed.")
        sys.exit(1)

    from training.dataset import DatasetSplitter

    splitter = DatasetSplitter(csv_path)
    _, _, test_rows = splitter.split()

    if not test_rows:
        print("No test data found.")
        return None

    test_images, test_labels = splitter.load_images(test_rows, size=(224, 224))

    with open(labels_path, "r") as f:
        label_set = [line.strip() for line in f if line.strip()]

    try:
        import tflite_runtime.interpreter as tflite
        interpreter = tflite.Interpreter(model_path=tflite_path)
    except ImportError:
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=tflite_path)

    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    predictions = []
    for img in test_images:
        input_data = np.expand_dims(img.astype(np.float32), axis=0)
        interpreter.set_tensor(input_details[0]["index"], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])
        predictions.append(label_set[np.argmax(output[0])])

    report = {}
    for label in label_set:
        tp = sum(1 for p, t in zip(predictions, test_labels) if p == label and t == label)
        fp = sum(1 for p, t in zip(predictions, test_labels) if p == label and t != label)
        fn = sum(1 for p, t in zip(predictions, test_labels) if p != label and t == label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        report[label] = {"precision": precision, "recall": recall, "tp": tp, "fp": fp, "fn": fn}

    accuracy = sum(1 for p, t in zip(predictions, test_labels) if p == t) / len(test_labels)
    return {"accuracy": accuracy, "per_class": report}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate garment classifier")
    parser.add_argument("--model", required=True, help="Path to .tflite model")
    parser.add_argument("--csv", required=True, help="Path to labels.csv")
    parser.add_argument("--labels", required=True, help="Path to labels.txt")
    args = parser.parse_args()
    result = validate(args.model, args.csv, args.labels)
    if result:
        print(f"Accuracy: {result['accuracy']:.1%}")
        for cls, metrics in result["per_class"].items():
            flag = " ⚠️" if metrics["recall"] < 0.8 else ""
            print(f"  {cls}: precision={metrics['precision']:.1%} recall={metrics['recall']:.1%}{flag}")
```

**Step 3: Commit**

```bash
git add foldit/training/train.py foldit/training/validate.py foldit/pyproject.toml
git commit -m "feat: ML training and validation scripts for garment classifier"
```

---

## Task 12: V4 Integration Tests

**Files:**
- Create: `foldit/tests/test_v4_integration.py`

**Step 1: Write integration tests**

Create `foldit/tests/test_v4_integration.py`:

```python
"""V4 integration tests — full composed pipeline."""
import os
import tempfile
import numpy as np


class TestV4Integration:
    def test_v3_robot_full_cycle(self):
        from foldit.simulator import create_simulated_robot_v3
        robot = create_simulated_robot_v3()
        result = robot.process_one()
        assert isinstance(result, str)
        assert robot._metrics.total_folds == 1

    def test_v3_robot_multiple_items(self):
        from foldit.simulator import create_simulated_robot_v3
        robot = create_simulated_robot_v3()
        folded = robot.run(max_items=3)
        assert len(folded) == 3
        assert robot._metrics.total_folds == 3

    def test_frame_quality_on_simulated_camera(self):
        from foldit.simulator import SimulatedCamera
        from foldit.frame_quality import FrameQualityChecker
        camera = SimulatedCamera()
        checker = FrameQualityChecker()
        frame = camera.capture_frame()
        result = checker.check(frame)
        assert result.blur_score > 0
        assert result.brightness_score > 0

    def test_metrics_store_round_trip(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.85, 10.0)
            rows = store.query_recent(minutes=60)
            assert len(rows) == 1
            summary = store.summary(minutes=60)
            assert summary["total_folds"] == 1
            store.close()

    def test_alerter_no_false_positives(self):
        from foldit.alerter import Alerter
        alerter = Alerter()
        for _ in range(10):
            alert = alerter.check("shirt", success=True)
            assert alert is None

    def test_auto_calibrator_with_reference(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[190:298, 235:406] = 255
        result = cal.calibrate(frame)
        assert result is not None
        assert result.pixels_per_mm > 0

    def test_label_store_round_trip(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            store.save_label("/test.jpg", "shirt")
            labels = store.load_all()
            assert len(labels) == 1

    def test_dashboard_history_with_store(self):
        from foldit.dashboard import create_app
        from foldit.robot_logger import MetricsCollector
        from foldit.metrics_store import MetricsStore
        from foldit.error_recovery import RobotState
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.85, 0.0)
            metrics = MetricsCollector()
            state = {"state": RobotState.IDLE, "uptime_sec": 0}
            app = create_app(metrics, state, metrics_store=store)
            app.config["TESTING"] = True
            with app.test_client() as client:
                resp = client.get("/api/metrics/history?minutes=60")
                data = json.loads(resp.data)
                assert len(data) == 1
            store.close()
```

**Step 2: Run integration tests**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_v4_integration.py -v`
Expected: All 8 PASS

**Step 3: Run full suite**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add foldit/tests/test_v4_integration.py
git commit -m "test: V4 integration tests for composed pipeline and new modules"
```

---

## Summary

| Task | Component | New Tests | Files |
|------|-----------|-----------|-------|
| 1 | Speed factor in FoldSequencer | 3 | folder.py, test_folder.py |
| 2 | Frame Quality Checker | 6 | frame_quality.py, test_frame_quality.py |
| 3 | Auto-Calibrator | 5 | auto_calibrator.py, test_auto_calibrator.py |
| 4 | Metrics Store (SQLite) | 5 | metrics_store.py, test_metrics_store.py |
| 5 | Failure Alerter | 6 | alerter.py, test_alerter.py |
| 6 | Config sections for V4 | 3 | config_loader.py, test_config_loader.py |
| 7 | Dashboard history endpoint | 2 | dashboard.py, test_dashboard.py |
| 8 | FoldItRobotV3 | 9 | main.py, test_v3_pipeline.py |
| 9 | Simulator + main() update | 0 | simulator.py, main.py |
| 10 | Label tool + Dataset | 6 | label_tool.py, dataset.py, tests |
| 11 | Train + Validate scripts | 0 | train.py, validate.py, pyproject.toml |
| 12 | V4 Integration Tests | 8 | test_v4_integration.py |
| **Total** | | **53 new** | **~230+ total** |
