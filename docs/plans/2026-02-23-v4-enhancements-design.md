# FoldIt V4 Enhancements Design

**Goal:** Wire V3 modules into a real pipeline (FoldItRobotV3), add an ML training workflow, introduce vision quality checks with auto-calibration, and persist metrics with failure alerting.

**Architecture:** FoldItRobotV3 composes all V3 standalone modules into a single process_one() loop. Training pipeline runs offline on desktop. Frame quality and auto-calibration gate the pipeline input. SQLite stores durable metrics alongside the in-memory MetricsCollector.

---

## 1. Wire V3 Into Pipeline — FoldItRobotV3

### 1.1 Composed Pipeline

FoldItRobotV3 replaces FoldItRobotV2 as the primary robot class. Constructor takes all V2 + V3 dependencies via DI.

```
process_one():
  1. error_recovery.safe_advance(conveyor)
  2. error_recovery.safe_capture(camera)
  3. frame_quality.check(frame) → retry once if bad
  4. preprocess → detect → flatness check (same as V2)
  5. orientation = detector.detect(contour)
  6. size = estimator.estimate(contour)
  7. classify(contour)
  8. data_collector.save(frame, type) (if enabled)
  9. sequencer.fold(type, speed_factor=size.speed_factor)
  10. result = verifier.verify(type)
  11. if not result.success: refold once
  12. metrics.record_fold(type, success, elapsed)
  13. metrics_store.record(...)
  14. alerter.check(type, success)
  15. logger.log_event(...)
```

### 1.2 FoldSequencer Enhancement

`FoldSequencer.fold()` gets an optional `speed_factor` parameter that scales `step_delay_sec`. Default 1.0 (no change). Large garments get 1.5 (slower, more careful folds).

### 1.3 Dashboard Wiring

- `start_callback` in state_dict calls `robot.run()` on a background thread
- `stop_callback` sets a stop flag that `run()` checks each iteration
- Graceful shutdown via `signal.signal(SIGINT, ...)` sets the same stop flag

### 1.4 Tests (~12)

- Composed pipeline returns garment type
- Speed factor passed to sequencer
- Fold verification triggers refold on failure
- Error recovery used for capture and advance
- Metrics recorded after each fold
- Data collector called when enabled
- Orientation and size computed before classification
- Graceful shutdown stops the loop
- Dashboard start/stop wired correctly
- Frame quality retry on bad frame
- Logger called with fold event
- Full cycle timing recorded

---

## 2. ML Training Pipeline

### 2.1 Label Tool (`training/label_tool.py`)

CLI tool that reads unlabeled frames from `data/captures/`, displays each with OpenCV `imshow`, prompts for label (shirt/pants/towel/unknown/skip). Saves labels to `data/labels.csv` (path, label, timestamp). Tracks progress — resumes where left off.

### 2.2 Dataset Packaging (`training/dataset.py`)

- Reads `labels.csv`, splits train/val/test (70/15/15)
- Resizes frames to 224x224 (MobileNetV2 input)
- Augmentation: random rotation (±15°), horizontal flip, brightness jitter
- Outputs numpy arrays or TF dataset

### 2.3 Training (`training/train.py`)

- MobileNetV2 pre-trained (ImageNet), freeze base layers
- Classification head: GlobalAvgPool → Dense(128) → Dropout(0.3) → Dense(num_classes)
- Early stopping (patience=5), learning rate reduction
- Saves best `.h5`, exports TFLite (quantized int8 for Pi)
- Prints confusion matrix and per-class accuracy

### 2.4 Validation (`training/validate.py`)

- Loads TFLite model, runs against test split
- Reports accuracy, precision, recall per class
- Flags classes below 80% recall

### 2.5 Dependencies

`tensorflow>=2.15.0` as optional `[training]` dependency in pyproject.toml. Not required on Pi.

### 2.6 Tests (8)

- CSV label read/write round-trip
- Train/val/test split ratios correct
- Augmentation output shape matches input shape
- Dataset loader returns correct batch dimensions
- TFLite export produces valid file
- Validation report structure has required keys
- Label tool resumes from last position
- Empty labels.csv handled gracefully

---

## 3. Vision Quality & Auto-Calibration

### 3.1 Frame Quality Checker (`foldit/frame_quality.py`)

Three checks on each captured frame:

| Check | Method | Fail Threshold |
|-------|--------|----------------|
| Blur | Laplacian variance on grayscale | < 100 |
| Contrast | Std deviation of pixel intensities | < 30 |
| Brightness | Mean pixel intensity | < 40 or > 220 |

`FrameQualityChecker.check(frame)` → `QualityResult(acceptable, blur_score, contrast_score, brightness_score)`

If not acceptable, pipeline retries capture once via error recovery. If still bad, logs warning and proceeds — don't block the pipeline over marginal quality.

Thresholds configurable via YAML under `frame_quality:` section.

### 3.2 Auto-Calibrator (`foldit/auto_calibrator.py`)

- User places known-size reference (credit card 85.6mm × 53.98mm or printed marker) on belt
- `AutoCalibrator.calibrate(frame)` detects rectangular reference via contour detection, measures pixel dimensions, computes `pixels_per_mm`
- Saves to `calibration.json`, loaded on startup by SizeEstimator
- CLI: `python -m foldit.auto_calibrator --capture`
- Falls back to manual `pixels_per_mm` from YAML if no calibration file

### 3.3 Pipeline Integration

- FrameQualityChecker runs between capture and preprocessing in FoldItRobotV3
- AutoCalibrator runs once at startup or on-demand via dashboard
- SizeEstimator reads pixels_per_mm from calibration file or config

### 3.4 Tests (8)

- Blur detection: sharp frame passes, blurred frame fails
- Contrast check: high-contrast passes, flat gray fails
- Brightness check: normal passes, too dark and too bright fail
- Calibration from known rectangle returns correct pixels_per_mm
- Calibration file save and load round-trip
- Fallback to config default when no calibration file
- QualityResult has all expected fields
- YAML threshold override changes behavior

---

## 4. Metrics Persistence & Alerting

### 4.1 SQLite Metrics Store (`foldit/metrics_store.py`)

- Single file DB, path from YAML (default: `data/metrics.db`)
- Table: `folds(id INTEGER PRIMARY KEY, timestamp TEXT, garment_type TEXT, success INTEGER, cycle_sec REAL, compactness REAL, orientation_angle REAL)`
- `MetricsStore.record(garment_type, success, cycle_sec, compactness, orientation_angle)`
- `MetricsStore.query_recent(minutes=60)` → list of fold dicts
- `MetricsStore.summary(minutes=60)` → same shape as MetricsCollector.snapshot()
- MetricsCollector stays for dashboard fast reads; MetricsStore is the durable layer

### 4.2 Dashboard History Endpoint

- `GET /api/metrics/history?minutes=60` returns time-series from SQLite
- Dashboard HTML gets inline SVG line chart (fold count over time) — no JS charting library, server-side computed `<polyline>` points

### 4.3 Alerter (`foldit/alerter.py`)

Two rules:

| Rule | Trigger | Action |
|------|---------|--------|
| Consecutive failures | 3+ failed folds in a row | Log ERROR, set RobotState.ERROR |
| Low success rate | < 50% over last 20 folds | Log WARNING |

- Called from FoldItRobotV3.process_one() after each fold
- No external notifications — structured log events only
- Dashboard displays alerts from the log
- Thresholds configurable via YAML under `alerting:` section

### 4.4 Tests (8)

- SQLite insert and query_recent returns correct records
- summary() matches MetricsCollector.snapshot() shape
- History endpoint returns JSON array
- Consecutive failure alert triggers at threshold
- Consecutive failure alert resets after success
- Low success rate alert triggers correctly
- Alert thresholds overridden from YAML config
- DB file created on first record

---

## 5. New Files Summary

| File | Purpose |
|------|---------|
| `foldit/foldit/main.py` | Modified: FoldItRobotV3 class + updated main() |
| `foldit/foldit/folder.py` | Modified: speed_factor param in fold() |
| `foldit/foldit/frame_quality.py` | Pre-classification frame quality gate |
| `foldit/foldit/auto_calibrator.py` | Automatic pixels_per_mm calibration |
| `foldit/foldit/metrics_store.py` | SQLite metrics persistence |
| `foldit/foldit/alerter.py` | Failure pattern alerting |
| `foldit/foldit/dashboard.py` | Modified: history endpoint + SVG chart |
| `foldit/foldit/config_loader.py` | Modified: new YAML sections |
| `training/label_tool.py` | CLI frame labeler |
| `training/dataset.py` | Dataset packaging + augmentation |
| `training/train.py` | MobileNetV2 fine-tuning + TFLite export |
| `training/validate.py` | Model validation + per-class metrics |
| `tests/test_v3_pipeline.py` | FoldItRobotV3 composed pipeline tests |
| `tests/test_frame_quality.py` | Frame quality checker tests |
| `tests/test_auto_calibrator.py` | Auto-calibration tests |
| `tests/test_metrics_store.py` | SQLite persistence tests |
| `tests/test_alerter.py` | Alerter rule tests |
| `tests/test_label_tool.py` | Label tool tests |
| `tests/test_dataset.py` | Dataset packaging tests |
| `tests/test_training.py` | Training + export tests |

**Dependencies to add:** `tensorflow>=2.15.0` as optional `[training]`

**Estimated new tests:** ~36
**Estimated total after V4:** ~217+
