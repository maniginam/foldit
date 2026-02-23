# FoldIt V3 Enhancements Design

**Goal:** Add 10 enhancements across monitoring, pipeline intelligence, resilience, configuration, and testing to make the robot production-ready for development and eventual deployment.

**Architecture:** New behavior wraps or composes with existing V2 classes — no modifications to working code. YAML config overrides Python defaults. Structured logging replaces silent exception handling. Flask dashboard provides local network monitoring.

---

## 1. Architecture Overview

```
+---------------------------------------------------+
|           Web Dashboard (Flask)                    |  NEW
|  Camera feed, fold stats, start/stop controls      |
+---------------------------------------------------+
|           Logging & Metrics                        |  NEW
|  Structured logging, fold success rates, timing    |
+---------------------------------------------------+
|    FoldItRobotV3 (enhanced pipeline)               |  MODIFIED
|  Orientation -> Size-aware folds -> Fold verify    |
|  Error recovery -> YAML config -> Data collection  |
+---------------------------------------------------+
|   Existing V2 hardware layer (unchanged)           |  EXISTING
|   Conveyor, Camera, Servos, Sensors                |
+---------------------------------------------------+
```

---

## 2. Pipeline Enhancements

### 2.1 Orientation Detection (`orientation.py`)

- `OrientationDetector` uses PCA (principal component analysis) on contour points
- Returns `OrientationResult(angle_deg, is_landscape, is_portrait)`
- Pipeline uses angle to determine if fold sequence needs adjustment
- Pure geometry — no ML required

### 2.2 Size-Aware Folding (`size_estimator.py`)

- `SizeEstimator` takes contour + camera calibration (pixels-per-mm)
- Returns estimated garment dimensions in mm
- `FoldSequencer.fold_with_size(garment_type, size)` adjusts fold speed and step delay
- Falls back to current fixed sequences if no calibration data

### 2.3 Fold Quality Verification (`fold_verifier.py`)

- `FoldVerifier` captures post-fold frame
- Compares contour compactness (area / bounding_rect_area) to expected range per garment type
- Returns `FoldResult(success, compactness, expected_range)`
- Max 1 re-fold attempt on failure — no infinite loops

### 2.4 Updated V3 Pipeline

```
conveyor -> detect -> orientation -> flatness -> classify -> size estimate
    -> fold(type, size, orientation) -> verify -> (re-fold once if needed)
```

---

## 3. Error Recovery (`error_recovery.py`)

`ErrorRecovery` class with per-failure-type handlers:

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Conveyor timeout | advance returns False | Log, retry once, skip |
| Camera failure | capture raises exception | Log, restart camera, retry once |
| Motor stall | Fold step exceeds timeout (5s) | Stop servos, home, log, skip |
| Multi-item rejection | is_single is False | Run conveyor briefly, re-detect once |
| Classification failure | Both ML + heuristic return unknown | Log + save frame, fold as unknown |
| Fold verification fail | Bad compactness | Re-fold once, log and continue |

Design rules:
- Max 1 retry per failure per garment
- Every failure logged
- Camera frame saved on classification failure (doubles as training data)
- `RobotState` enum: IDLE, ADVANCING, DETECTING, FOLDING, ERROR, RECOVERING

---

## 4. YAML Config (`config_loader.py`)

`ConfigLoader` class:
- Loads from `/opt/foldit/config.yaml` (production) or `./config.yaml` (development)
- Every field in `config.py` overridable
- Missing keys fall back to `config.py` defaults
- Validated on load — invalid values raise at startup

```yaml
conveyor:
  detection_distance_cm: 12.0
  belt_speed_duty: 60
servo:
  fold_angle: 170
  step_delay_sec: 0.03
classifier:
  confidence_threshold: 0.6
  small_area_threshold: 18000
fold_verify:
  enabled: true
  max_retries: 1
logging:
  level: INFO
  file: /var/log/foldit/robot.log
dashboard:
  enabled: true
  port: 5000
data_collection:
  enabled: false
  output_dir: ./data/captures
```

---

## 5. Structured Logging (`robot_logger.py`)

`RobotLogger` wraps Python `logging` module:
- JSON-formatted entries: timestamp, level, event type, context data
- Console output for dev, file output for production (path from YAML)
- Key events: garment detected, classified, folded, error, recovery, cycle time

`MetricsCollector`:
- Accumulates fold counts by type, success rates, average cycle times
- Dashboard reads from MetricsCollector directly — no log parsing

Example: `{"ts": "2026-02-23T10:15:32", "event": "fold_complete", "garment": "shirt", "cycle_sec": 8.2, "verified": true}`

---

## 6. Data Collection (integrated into pipeline)

- On every classification, optionally save frame + contour + result
- Unknown classifications flagged for manual labeling
- Directory: `data/captures/YYYY-MM-DD/shirt_001.jpg`
- Controlled by `data_collection.enabled` in YAML — off by default

---

## 7. Web Dashboard (`dashboard.py`)

Flask app on background daemon thread, port 5000 (configurable):

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Dashboard HTML (single page, auto-refresh) |
| `/api/status` | GET | JSON: robot state, current garment, uptime |
| `/api/metrics` | GET | JSON: fold counts, success rate, avg cycle time |
| `/api/feed` | GET | MJPEG camera stream |
| `/api/control/start` | POST | Start processing loop |
| `/api/control/stop` | POST | Stop processing loop |

Design: MJPEG streaming (no WebSocket), static HTML with 5s polling, no JS framework, no auth.

---

## 8. Integration Tests (`test_integration.py`)

Full V3 pipeline tests using simulator:

| Test | Verifies |
|------|----------|
| test_full_cycle_detects_classifies_and_folds | Complete pipeline returns garment type |
| test_orientation_affects_fold_sequence | Rotated garment gets adjusted fold order |
| test_fold_verification_triggers_refold | Bad compactness -> retry -> succeeds |
| test_error_recovery_on_camera_failure | Camera exception -> restart -> retry |
| test_conveyor_timeout_skips_gracefully | Timeout -> logged -> continues |
| test_multi_item_rejection_and_retry | Multiple items -> shift -> re-detect |
| test_config_override_changes_behavior | YAML override affects classification |
| test_metrics_accumulate_across_cycles | 3 folds -> correct metric counts |
| test_data_collection_saves_frames | Frames saved to disk when enabled |
| test_dashboard_status_endpoint | Flask test client gets valid JSON |

---

## 9. Error Recovery Tests (`test_error_recovery.py`)

Failure injection via test doubles:

| Test | Scenario |
|------|----------|
| test_camera_restart_on_exception | Camera raises once, restart succeeds |
| test_motor_stall_timeout_homes_platform | Fold step exceeds timeout -> home + skip |
| test_conveyor_retry_on_first_timeout | First advance times out -> retry -> succeeds |
| test_max_one_retry_per_failure | No infinite retry loops |
| test_classification_failure_saves_frame | Unknown -> frame saved |
| test_fold_verify_fail_refolds_once | Bad compactness -> refold -> pass |
| test_fold_verify_fail_twice_moves_on | Bad twice -> log and continue |

---

## 10. New Files Summary

| File | Purpose |
|------|---------|
| `foldit/orientation.py` | PCA-based garment orientation |
| `foldit/size_estimator.py` | Contour-to-mm size estimation |
| `foldit/fold_verifier.py` | Post-fold compactness verification |
| `foldit/error_recovery.py` | Per-failure-type recovery handlers |
| `foldit/config_loader.py` | YAML config with fallbacks |
| `foldit/robot_logger.py` | Structured logging + MetricsCollector |
| `foldit/dashboard.py` | Flask web dashboard |
| `foldit/main.py` | Modified: FoldItRobotV3 pipeline |
| `tests/test_integration.py` | End-to-end pipeline tests |
| `tests/test_error_recovery.py` | Failure scenario tests |
| `tests/test_orientation.py` | Orientation detection tests |
| `tests/test_size_estimator.py` | Size estimation tests |
| `tests/test_fold_verifier.py` | Fold verification tests |
| `tests/test_config_loader.py` | YAML config tests |
| `tests/test_robot_logger.py` | Logging + metrics tests |
| `tests/test_dashboard.py` | Dashboard endpoint tests |

**Dependencies to add:** `flask`, `pyyaml`
