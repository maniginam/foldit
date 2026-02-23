# FoldIt V5 Improvements Design

**Goal:** Harden for production (CI/CD, auth, graceful shutdown), add real-time observability (SSE dashboard, webhook alerts, metrics export), integrate ML classifier with confidence thresholds, and improve developer experience (CLI subcommands, default config, linting).

**Architecture:** Production hardening layers onto existing Flask dashboard and V3 pipeline. Observability uses SSE streaming and stdlib HTTP for webhooks — no new dependencies. ML integration wires the existing HybridClassifier into V3 with confidence-based fallback. CLI subcommands replace the flat argparse in main().

---

## 1. Production Hardening

### 1.1 CI/CD Pipeline

`.github/workflows/ci.yml` runs on push/PR to main:
- Checkout, setup Python 3.11, install dev deps
- `pytest tests/ -v` — fail on any test failure
- `ruff check foldit/ tests/ training/` — fail on lint errors

### 1.2 Dashboard Authentication

`DashboardAuth` class — optional API key via `X-API-Key` header or `?key=` query param. Configured via YAML `dashboard.api_key` (default: None = no auth). Applied as Flask `before_request` hook — returns 401 for `/api/*` routes when key is set and request doesn't match. Static HTML served without auth.

### 1.3 Graceful Shutdown

`SignalHandler` registers SIGINT/SIGTERM handlers, sets `robot._stop_requested = True`. Robot finishes current fold cycle then exits. Dashboard gets `/api/control/shutdown` POST endpoint. Wired in `main()`.

### 1.4 Tests (~6)

- Auth allows request with correct key
- Auth denies request with wrong key
- Auth allows all when no key configured
- Signal handler sets stop flag
- Shutdown endpoint sets stop flag
- CI YAML is valid

---

## 2. Observability & Operations

### 2.1 Server-Sent Events Dashboard

Replace 5-second polling with SSE. New endpoint `GET /api/events` streams `text/event-stream`. Dashboard HTML uses `EventSource('/api/events')`. Thread-safe event queue — `process_one()` pushes events, SSE endpoint reads them.

### 2.2 Remote Alerting

`AlertNotifier` with `notify(alert)` method. Sends POST JSON to configurable webhook URL (works with Slack, Discord, any HTTP endpoint). Configured via YAML `alerting.webhook_url` (default: None = log only). Called from `Alerter.check()` — fire-and-forget, non-blocking. Uses `urllib.request` — no new dependencies.

### 2.3 Metrics Export

`GET /api/metrics/export` returns full JSON dump. Optional `format=prometheus` returns text format gauges (`foldit_total_folds`, `foldit_success_rate`, `foldit_avg_cycle_sec`). No Prometheus client library — just formatted text.

### 2.4 Tests (~8)

- SSE endpoint streams events
- Event queue push/pop works
- Webhook notifier sends POST
- Webhook failure doesn't crash
- Prometheus format output correct
- Export endpoint returns JSON
- No events returns empty stream
- Notifier skipped when no URL configured

---

## 3. ML & Vision

### 3.1 HybridClassifier Integration

Wire `HybridClassifier` into `FoldItRobotV3`. `create_simulated_robot_v3()` gets optional `model_path` — if TFLite model exists, use HybridClassifier; otherwise heuristic GarmentClassifier. Config: `classifier.model_path` in YAML (default: None).

### 3.2 Confidence Thresholds

`MLClassifier.classify()` returns `ClassificationResult(label, confidence)` instead of just the label. `HybridClassifier` checks confidence against threshold (default: 0.7) — falls back to heuristic if below. Config: `classifier.min_confidence` in YAML. V3 logs classification method and confidence per fold.

### 3.3 Data Augmentation

`augment_image(image)` in `DatasetSplitter` — random rotation (±15°), horizontal flip (50% chance), brightness jitter (±20%). `load_images()` gets `augment=False` flag — True for training, False for val/test. OpenCV only — no new dependencies.

### 3.4 Tests (~8)

- HybridClassifier wired in V3 when model exists
- Falls back to heuristic when no model
- Confidence below threshold triggers fallback
- ClassificationResult has label + confidence
- Augmented image same shape as input
- Augmentation changes pixel values
- No augmentation on val/test
- Config loads classifier section

---

## 4. Developer Experience

### 4.1 CLI Subcommands

Replace flat argparse with subcommands: `foldit run`, `foldit dashboard`, `foldit calibrate`, `foldit train`. Still uses argparse (subparsers). `pyproject.toml` gets `[project.scripts] foldit = "foldit.main:main"`.

### 4.2 Default Config

Ship `foldit/config.default.yaml` with all sections, commented. `ConfigLoader` checks `config.yaml` first, then `config.default.yaml`, then hardcoded DEFAULTS.

### 4.3 Linting

Add `ruff>=0.4.0` to dev deps. `pyproject.toml` gets `[tool.ruff]` section: line-length 120, select E/F/W. CI runs ruff check. One-time cleanup of existing violations.

### 4.4 Tests (~4)

- CLI run subcommand works
- CLI dashboard subcommand starts app
- config.default.yaml loads correctly
- config.yaml overrides defaults

---

## 5. New/Modified Files Summary

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI pipeline |
| `foldit/foldit/dashboard.py` | Modified: auth, SSE, shutdown, export endpoints |
| `foldit/foldit/dashboard_auth.py` | API key authentication |
| `foldit/foldit/signal_handler.py` | Graceful SIGINT/SIGTERM handling |
| `foldit/foldit/alert_notifier.py` | Webhook alert delivery |
| `foldit/foldit/event_stream.py` | Thread-safe SSE event queue |
| `foldit/foldit/ml_classifier.py` | Modified: ClassificationResult, confidence threshold |
| `foldit/foldit/main.py` | Modified: CLI subcommands, signal handler wiring |
| `foldit/foldit/simulator.py` | Modified: optional model_path for HybridClassifier |
| `foldit/foldit/config_loader.py` | Modified: new config sections, default.yaml fallback |
| `foldit/config.default.yaml` | Default configuration with comments |
| `foldit/training/dataset.py` | Modified: augment_image, augment flag |
| `foldit/pyproject.toml` | Modified: scripts entry, ruff config, ruff dep |
| `tests/test_dashboard_auth.py` | Auth tests |
| `tests/test_signal_handler.py` | Shutdown tests |
| `tests/test_event_stream.py` | SSE + event queue tests |
| `tests/test_alert_notifier.py` | Webhook tests |
| `tests/test_metrics_export.py` | Export + Prometheus tests |
| `tests/test_ml_integration.py` | HybridClassifier + confidence tests |
| `tests/test_augmentation.py` | Data augmentation tests |
| `tests/test_cli.py` | CLI subcommand tests |
| `tests/test_default_config.py` | Default config tests |

**Estimated new tests:** ~26
**Estimated total after V5:** ~260+
