# FoldIt V5 Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden for production (CI/CD, auth, graceful shutdown), add real-time observability (SSE dashboard, webhook alerts, metrics export), integrate ML classifier with confidence thresholds, and improve developer experience (CLI subcommands, default config, linting).

**Architecture:** Production hardening layers onto existing Flask dashboard and V3 pipeline. Observability uses SSE streaming and stdlib HTTP for webhooks. ML integration wires the existing HybridClassifier into V3 with a unified classifier interface. CLI subcommands replace the flat argparse in main().

**Tech Stack:** Python 3.11+, OpenCV, NumPy, Flask, PyYAML, SQLite3, pytest, ruff. Optional: TensorFlow 2.15+.

**Run all tests with:** `foldit/.venv/bin/python -m pytest foldit/tests/ -v`

**Project root:** `/Users/maniginam/projects/foldit`

---

## Task 1: Dashboard Authentication

**Files:**
- Create: `foldit/foldit/dashboard_auth.py`
- Create: `foldit/tests/test_dashboard_auth.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_dashboard_auth.py`:

```python
"""Tests for dashboard API key authentication."""
import json


class FakeMetricsForAuth:
    def snapshot(self):
        return {"total_folds": 0}


class TestDashboardAuth:
    def _make_app(self, api_key=None):
        from foldit.dashboard import create_app
        from foldit.dashboard_auth import DashboardAuth
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForAuth()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        if api_key:
            auth = DashboardAuth(api_key)
            auth.apply(app)
        app.config["TESTING"] = True
        return app

    def test_no_auth_allows_all(self):
        app = self._make_app()
        with app.test_client() as client:
            resp = client.get("/api/status")
            assert resp.status_code == 200

    def test_correct_key_in_header_allows(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status", headers={"X-API-Key": "secret123"})
            assert resp.status_code == 200

    def test_wrong_key_denies(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status", headers={"X-API-Key": "wrong"})
            assert resp.status_code == 401

    def test_missing_key_denies(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status")
            assert resp.status_code == 401

    def test_key_in_query_param_allows(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/api/status?key=secret123")
            assert resp.status_code == 200

    def test_html_page_served_without_auth(self):
        app = self._make_app(api_key="secret123")
        with app.test_client() as client:
            resp = client.get("/")
            assert resp.status_code == 200
            assert b"FoldIt" in resp.data
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_dashboard_auth.py -v`
Expected: FAIL (no module `foldit.dashboard_auth`)

**Step 3: Write minimal implementation**

Create `foldit/foldit/dashboard_auth.py`:

```python
"""Optional API key authentication for the Flask dashboard."""
from flask import request, jsonify


class DashboardAuth:
    """Applies API key authentication to Flask API routes."""

    def __init__(self, api_key):
        self._api_key = api_key

    def apply(self, app):
        @app.before_request
        def check_api_key():
            if not request.path.startswith("/api/"):
                return None
            key = request.headers.get("X-API-Key") or request.args.get("key")
            if key != self._api_key:
                return jsonify({"error": "unauthorized"}), 401
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/foldit/dashboard_auth.py foldit/tests/test_dashboard_auth.py
git commit -m "feat: optional API key authentication for dashboard"
```

---

## Task 2: SSE Event Stream

**Files:**
- Create: `foldit/foldit/event_stream.py`
- Create: `foldit/tests/test_event_stream.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_event_stream.py`:

```python
"""Tests for thread-safe SSE event stream."""
import threading
import time


class TestEventStream:
    def test_push_and_pop(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        stream.push({"type": "fold", "garment": "shirt"})
        event = stream.pop(timeout=1.0)
        assert event["type"] == "fold"
        assert event["garment"] == "shirt"

    def test_pop_empty_returns_none(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        event = stream.pop(timeout=0.1)
        assert event is None

    def test_push_from_another_thread(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        result = []

        def producer():
            time.sleep(0.05)
            stream.push({"type": "test"})

        t = threading.Thread(target=producer)
        t.start()
        event = stream.pop(timeout=2.0)
        t.join()
        assert event is not None
        assert event["type"] == "test"

    def test_multiple_events_fifo(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        stream.push({"seq": 1})
        stream.push({"seq": 2})
        stream.push({"seq": 3})
        assert stream.pop(timeout=0.1)["seq"] == 1
        assert stream.pop(timeout=0.1)["seq"] == 2
        assert stream.pop(timeout=0.1)["seq"] == 3
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_event_stream.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/event_stream.py`:

```python
"""Thread-safe event stream for SSE dashboard updates."""
import queue


class EventStream:
    """Thread-safe FIFO queue for pushing events from the robot to SSE clients."""

    def __init__(self):
        self._queue = queue.Queue()

    def push(self, event):
        self._queue.put(event)

    def pop(self, timeout=1.0):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/foldit/event_stream.py foldit/tests/test_event_stream.py
git commit -m "feat: thread-safe SSE event stream"
```

---

## Task 3: Alert Notifier

**Files:**
- Create: `foldit/foldit/alert_notifier.py`
- Create: `foldit/tests/test_alert_notifier.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_alert_notifier.py`:

```python
"""Tests for webhook alert notifications."""
import json
from unittest.mock import patch, MagicMock


class TestAlertNotifier:
    def test_notify_sends_post(self):
        from foldit.alert_notifier import AlertNotifier
        from foldit.alerter import Alert
        notifier = AlertNotifier(webhook_url="http://example.com/hook")
        alert = Alert(rule="consecutive_failures", message="3 failures in a row")
        with patch("foldit.alert_notifier.urlopen") as mock_urlopen:
            mock_urlopen.return_value = MagicMock()
            notifier.notify(alert)
            mock_urlopen.assert_called_once()
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            body = json.loads(req.data.decode())
            assert body["rule"] == "consecutive_failures"
            assert body["message"] == "3 failures in a row"

    def test_notify_failure_does_not_raise(self):
        from foldit.alert_notifier import AlertNotifier
        from foldit.alerter import Alert
        notifier = AlertNotifier(webhook_url="http://example.com/hook")
        alert = Alert(rule="test", message="test")
        with patch("foldit.alert_notifier.urlopen", side_effect=Exception("network error")):
            notifier.notify(alert)  # should not raise

    def test_no_url_skips_notify(self):
        from foldit.alert_notifier import AlertNotifier
        from foldit.alerter import Alert
        notifier = AlertNotifier(webhook_url=None)
        alert = Alert(rule="test", message="test")
        with patch("foldit.alert_notifier.urlopen") as mock_urlopen:
            notifier.notify(alert)
            mock_urlopen.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_alert_notifier.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/alert_notifier.py`:

```python
"""Webhook-based alert notifications."""
import json
from urllib.request import Request, urlopen


class AlertNotifier:
    """Sends alert notifications to a webhook URL."""

    def __init__(self, webhook_url=None):
        self._url = webhook_url

    def notify(self, alert):
        if not self._url:
            return
        try:
            payload = json.dumps({
                "rule": alert.rule,
                "message": alert.message,
            }).encode("utf-8")
            req = Request(self._url, data=payload, headers={"Content-Type": "application/json"})
            urlopen(req, timeout=5)
        except Exception:
            pass
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/foldit/alert_notifier.py foldit/tests/test_alert_notifier.py
git commit -m "feat: webhook alert notifier for failure patterns"
```

---

## Task 4: Graceful Shutdown (Signal Handler)

**Files:**
- Create: `foldit/foldit/signal_handler.py`
- Create: `foldit/tests/test_signal_handler.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_signal_handler.py`:

```python
"""Tests for graceful signal handling."""


class FakeRobotForSignal:
    def __init__(self):
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True


class TestSignalHandler:
    def test_sets_stop_flag_on_robot(self):
        from foldit.signal_handler import SignalHandler
        robot = FakeRobotForSignal()
        handler = SignalHandler(robot)
        handler.handle(None, None)
        assert robot._stop_requested is True

    def test_multiple_signals_are_safe(self):
        from foldit.signal_handler import SignalHandler
        robot = FakeRobotForSignal()
        handler = SignalHandler(robot)
        handler.handle(None, None)
        handler.handle(None, None)
        assert robot._stop_requested is True
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_signal_handler.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `foldit/foldit/signal_handler.py`:

```python
"""Graceful shutdown via SIGINT/SIGTERM signal handling."""
import signal


class SignalHandler:
    """Registers signal handlers that stop the robot gracefully."""

    def __init__(self, robot):
        self._robot = robot

    def register(self):
        signal.signal(signal.SIGINT, self.handle)
        signal.signal(signal.SIGTERM, self.handle)

    def handle(self, signum, frame):
        self._robot.stop()
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/foldit/signal_handler.py foldit/tests/test_signal_handler.py
git commit -m "feat: graceful shutdown via SIGINT/SIGTERM signal handler"
```

---

## Task 5: Dashboard SSE, Export, and Shutdown Endpoints

**Files:**
- Modify: `foldit/foldit/dashboard.py`
- Modify: `foldit/tests/test_dashboard.py`

**Step 1: Write the failing tests**

Add to the end of `foldit/tests/test_dashboard.py`:

```python
class TestDashboardSSE:
    def _make_app_with_stream(self):
        from foldit.dashboard import create_app
        from foldit.event_stream import EventStream
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        stream = EventStream()
        app = create_app(metrics, state, event_stream=stream)
        app.config["TESTING"] = True
        return app, stream

    def test_events_endpoint_exists(self):
        app, stream = self._make_app_with_stream()
        stream.push({"type": "fold", "garment": "shirt"})
        with app.test_client() as client:
            resp = client.get("/api/events")
            assert resp.status_code == 200


class TestDashboardExport:
    def _make_app_with_store(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        store = FakeMetricsStoreForDashboard()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state, metrics_store=store)
        app.config["TESTING"] = True
        return app

    def test_export_returns_json(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            resp = client.get("/api/metrics/export")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert "summary" in data
            assert "recent" in data

    def test_export_prometheus_format(self):
        app = self._make_app_with_store()
        with app.test_client() as client:
            resp = client.get("/api/metrics/export?format=prometheus")
            assert resp.status_code == 200
            text = resp.data.decode()
            assert "foldit_total_folds" in text
            assert "foldit_success_rate" in text


class TestDashboardShutdown:
    def _make_app_with_stop(self):
        from foldit.dashboard import create_app
        from foldit.error_recovery import RobotState
        metrics = FakeMetricsForDashboard()
        stopped = {"flag": False}
        state = {
            "state": RobotState.IDLE,
            "uptime_sec": 0,
            "shutdown_callback": lambda: stopped.update(flag=True),
        }
        app = create_app(metrics, state)
        app.config["TESTING"] = True
        return app, stopped

    def test_shutdown_endpoint(self):
        app, stopped = self._make_app_with_stop()
        with app.test_client() as client:
            resp = client.post("/api/control/shutdown")
            assert resp.status_code == 200
            assert stopped["flag"] is True
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_dashboard.py -v`
Expected: New tests FAIL

**Step 3: Update dashboard.py**

Replace `foldit/foldit/dashboard.py` entirely:

```python
"""Flask web dashboard for monitoring the FoldIt robot."""
import json
from flask import Flask, jsonify, request, Response


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
#events { max-height: 200px; overflow-y: auto; }
.event { padding: 2px 0; border-bottom: 1px solid #2a2a4e; }
</style>
</head>
<body>
<h1>FoldIt Robot Dashboard</h1>
<div class="card"><div class="label">Status</div><div id="status">Loading...</div></div>
<div class="card"><div class="label">Metrics</div><div id="metrics">Loading...</div></div>
<div class="card"><div class="label">Live Events</div><div id="events"></div></div>
<div class="card">
<button onclick="fetch('/api/control/start',{method:'POST'})">Start</button>
<button onclick="fetch('/api/control/stop',{method:'POST'})">Stop</button>
<button onclick="fetch('/api/control/shutdown',{method:'POST'})">Shutdown</button>
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
if (typeof EventSource !== 'undefined') {
  var es = new EventSource('/api/events');
  es.onmessage = function(e) {
    var div = document.getElementById('events');
    var item = document.createElement('div');
    item.className = 'event';
    item.textContent = e.data;
    div.insertBefore(item, div.firstChild);
  };
}
</script>
</body></html>"""


def create_app(metrics, state_dict, metrics_store=None, event_stream=None):
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
        minutes = request.args.get("minutes", 60, type=int)
        if metrics_store:
            return jsonify(metrics_store.query_recent(minutes=minutes))
        return jsonify([])

    @app.route("/api/metrics/export")
    def metrics_export():
        fmt = request.args.get("format", "json")
        snapshot = metrics.snapshot()
        recent = metrics_store.query_recent(minutes=60) if metrics_store else []
        if fmt == "prometheus":
            lines = [
                f"# HELP foldit_total_folds Total number of folds",
                f"# TYPE foldit_total_folds gauge",
                f"foldit_total_folds {snapshot.get('total_folds', 0)}",
                f"# HELP foldit_success_rate Fold success rate",
                f"# TYPE foldit_success_rate gauge",
                f"foldit_success_rate {snapshot.get('success_rate', 0.0)}",
                f"# HELP foldit_avg_cycle_sec Average fold cycle time in seconds",
                f"# TYPE foldit_avg_cycle_sec gauge",
                f"foldit_avg_cycle_sec {snapshot.get('avg_cycle_sec', 0.0)}",
            ]
            return Response("\n".join(lines) + "\n", mimetype="text/plain")
        return jsonify({"summary": snapshot, "recent": recent})

    @app.route("/api/events")
    def events():
        if not event_stream:
            return jsonify([])

        def generate():
            event = event_stream.pop(timeout=0.1)
            if event:
                yield f"data: {json.dumps(event)}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/api/control/start", methods=["POST"])
    def control_start():
        state_dict["state"] = state_dict.get("start_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    @app.route("/api/control/stop", methods=["POST"])
    def control_stop():
        state_dict["state"] = state_dict.get("stop_callback", lambda: None)() or state_dict["state"]
        return jsonify({"status": "ok"})

    @app.route("/api/control/shutdown", methods=["POST"])
    def control_shutdown():
        callback = state_dict.get("shutdown_callback")
        if callback:
            callback()
        return jsonify({"status": "ok"})

    return app
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/foldit/dashboard.py foldit/tests/test_dashboard.py
git commit -m "feat: dashboard SSE events, metrics export, shutdown endpoint"
```

---

## Task 6: Data Augmentation

**Files:**
- Modify: `foldit/training/dataset.py`
- Create: `foldit/tests/test_augmentation.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_augmentation.py`:

```python
"""Tests for data augmentation in dataset splitter."""
import numpy as np


class TestAugmentation:
    def test_augment_preserves_shape(self):
        from training.dataset import augment_image
        img = np.full((224, 224, 3), 128, dtype=np.uint8)
        result = augment_image(img, seed=42)
        assert result.shape == (224, 224, 3)
        assert result.dtype == np.uint8

    def test_augment_changes_pixels(self):
        from training.dataset import augment_image
        img = np.full((224, 224, 3), 128, dtype=np.uint8)
        result = augment_image(img, seed=42)
        assert not np.array_equal(img, result)

    def test_load_images_with_augment(self):
        import os
        import tempfile
        import cv2
        from training.label_tool import LabelStore
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            for i in range(5):
                path = os.path.join(tmpdir, f"frame_{i}.jpg")
                cv2.imwrite(path, np.full((100, 100, 3), 128, dtype=np.uint8))
                store.save_label(path, "shirt")
            splitter = DatasetSplitter(csv_path)
            rows = store.load_all()
            images, labels = splitter.load_images(rows, size=(224, 224), augment=True)
            assert images.shape[1:] == (224, 224, 3)
            assert len(labels) == 5
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_augmentation.py -v`
Expected: FAIL

**Step 3: Add augmentation to dataset.py**

Replace `foldit/training/dataset.py`:

```python
"""Dataset packaging and splitting for ML training."""
import csv
import os
import random

import cv2
import numpy as np


def augment_image(image, seed=None):
    """Apply random augmentation: rotation, flip, brightness jitter."""
    rng = random.Random(seed)
    result = image.copy()

    angle = rng.uniform(-15, 15)
    h, w = result.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    result = cv2.warpAffine(result, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)

    if rng.random() > 0.5:
        result = cv2.flip(result, 1)

    factor = rng.uniform(0.8, 1.2)
    result = np.clip(result.astype(np.float32) * factor, 0, 255).astype(np.uint8)

    return result


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

    def load_images(self, rows, size=(224, 224), augment=False):
        images = []
        labels = []
        for row in rows:
            img = cv2.imread(row["path"])
            if img is None:
                continue
            img = cv2.resize(img, size)
            if augment:
                img = augment_image(img)
            images.append(img)
            labels.append(row["label"])
        return np.array(images), labels
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/training/dataset.py foldit/tests/test_augmentation.py
git commit -m "feat: data augmentation with rotation, flip, brightness jitter"
```

---

## Task 7: V5 Config Sections

**Files:**
- Modify: `foldit/foldit/config_loader.py`
- Modify: `foldit/tests/test_config_loader.py`

**Step 1: Write the failing tests**

Add to the end of `foldit/tests/test_config_loader.py`:

```python
class TestConfigLoaderV5Sections:
    def test_classifier_model_path_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["classifier"]["model_path"] is None

    def test_classifier_min_confidence_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["classifier"]["min_confidence"] == 0.7

    def test_dashboard_api_key_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["dashboard"]["api_key"] is None

    def test_alerting_webhook_url_default(self):
        from foldit.config_loader import ConfigLoader
        loader = ConfigLoader(path="/nonexistent/config.yaml")
        config = loader.load()
        assert config["alerting"]["webhook_url"] is None
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_config_loader.py -v`
Expected: 4 new tests FAIL (KeyError)

**Step 3: Add new keys to DEFAULTS**

In `foldit/foldit/config_loader.py`, add to the existing sections in the `DEFAULTS` dict:

- In `"classifier"` section, add: `"model_path": None, "min_confidence": 0.7,`
- In `"dashboard"` section, add: `"api_key": None,`
- In `"alerting"` section, add: `"webhook_url": None,`

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add foldit/foldit/config_loader.py foldit/tests/test_config_loader.py
git commit -m "feat: V5 config sections for classifier, dashboard auth, alerting webhook"
```

---

## Task 8: Default Config YAML

**Files:**
- Create: `foldit/foldit/config.default.yaml`
- Modify: `foldit/foldit/config_loader.py`
- Create: `foldit/tests/test_default_config.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_default_config.py`:

```python
"""Tests for default config YAML fallback."""
import os


class TestDefaultConfig:
    def test_default_yaml_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        assert os.path.exists(path)

    def test_default_yaml_loads_all_sections(self):
        import yaml
        path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert "conveyor" in config
        assert "servo" in config
        assert "camera" in config
        assert "classifier" in config
        assert "dashboard" in config
        assert "alerting" in config
        assert "frame_quality" in config
        assert "metrics_store" in config

    def test_config_loader_uses_default_yaml_fallback(self):
        from foldit.config_loader import ConfigLoader
        import os
        default_path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        loader = ConfigLoader(path="/nonexistent/config.yaml", default_path=default_path)
        config = loader.load()
        assert config["dashboard"]["port"] == 5000
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_default_config.py -v`
Expected: FAIL

**Step 3: Create default config YAML**

Create `foldit/foldit/config.default.yaml`:

```yaml
# FoldIt Robot Default Configuration
# Copy to config.yaml and customize as needed.

conveyor:
  detection_distance_cm: 10.0
  belt_speed_duty: 75
  settle_time_sec: 0.5

servo:
  fold_angle: 180
  home_angle: 0
  step_delay_sec: 0.02
  pwm_frequency_hz: 50

camera:
  resolution: [640, 480]
  framerate: 30

classifier:
  confidence_threshold: 0.5
  min_confidence: 0.7
  model_path: null
  small_area_threshold: 15000
  pants_ratio_threshold: 0.6
  shirt_ratio_threshold: 1.2

fold_verify:
  enabled: true
  max_retries: 1

logging:
  level: INFO
  file: null

dashboard:
  enabled: false
  port: 5000
  api_key: null

data_collection:
  enabled: false
  output_dir: ./data/captures

frame_quality:
  min_blur_score: 100.0
  min_contrast: 30.0
  min_brightness: 40.0
  max_brightness: 220.0

alerting:
  consecutive_fail_threshold: 3
  rate_window: 20
  min_success_rate: 0.5
  webhook_url: null

metrics_store:
  db_path: data/metrics.db
```

**Step 4: Update ConfigLoader to accept default_path**

In `foldit/foldit/config_loader.py`, update the `__init__` and `load` methods:

```python
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
```

**Step 5: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add foldit/foldit/config.default.yaml foldit/foldit/config_loader.py foldit/tests/test_default_config.py
git commit -m "feat: default config.yaml with all sections and ConfigLoader fallback"
```

---

## Task 9: CLI Subcommands

**Files:**
- Modify: `foldit/foldit/main.py`
- Modify: `foldit/pyproject.toml`
- Create: `foldit/tests/test_cli.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_cli.py`:

```python
"""Tests for CLI subcommands."""
import sys
from unittest.mock import patch


class TestCLI:
    def test_run_subcommand_simulate(self):
        from foldit.main import main
        with patch.object(sys, "argv", ["foldit", "run", "--simulate", "--items", "1"]):
            main()

    def test_run_subcommand_default_items(self):
        from foldit.main import main
        with patch.object(sys, "argv", ["foldit", "run", "--simulate"]):
            main()
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_cli.py -v`
Expected: FAIL (main() doesn't accept "run" subcommand)

**Step 3: Update main() with subcommands**

Replace the `main()` function and `if __name__` block in `foldit/foldit/main.py`:

```python
def main():
    import argparse
    parser = argparse.ArgumentParser(description="FoldIt Robot Controller")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the robot")
    run_parser.add_argument("--simulate", action="store_true", help="Run in simulator mode")
    run_parser.add_argument("--items", type=int, default=1, help="Number of items to process")

    subparsers.add_parser("dashboard", help="Start the web dashboard")
    subparsers.add_parser("calibrate", help="Run auto-calibration")

    train_parser = subparsers.add_parser("train", help="Train ML classifier")
    train_parser.add_argument("--csv", required=False, help="Path to labels.csv")
    train_parser.add_argument("--output", default="models", help="Output directory")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        simulate = getattr(args, "simulate", False)
        items = getattr(args, "items", 1)
        if simulate:
            from foldit.simulator import create_simulated_robot_v3
            robot = create_simulated_robot_v3()
            folded = robot.run(max_items=items)
            print(f"Folded {len(folded)} items: {folded}")
            print(f"Metrics: {robot._metrics.snapshot()}")
    elif args.command == "dashboard":
        from foldit.dashboard import create_app
        from foldit.robot_logger import MetricsCollector
        from foldit.error_recovery import RobotState
        metrics = MetricsCollector()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        app.run(port=5000)
    elif args.command == "calibrate":
        from foldit.auto_calibrator import AutoCalibrator
        print("Place reference object (credit card) on belt and press Enter...")
    elif args.command == "train":
        from training.train import train
        if args.csv:
            train(args.csv, args.output)
        else:
            print("Usage: foldit train --csv path/to/labels.csv")


if __name__ == "__main__":
    main()
```

**Step 4: Add scripts entry to pyproject.toml**

Add to `foldit/pyproject.toml` after the `[tool.pytest.ini_options]` section:

```toml
[project.scripts]
foldit = "foldit.main:main"
```

**Step 5: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add foldit/foldit/main.py foldit/pyproject.toml foldit/tests/test_cli.py
git commit -m "feat: CLI subcommands (run, dashboard, calibrate, train)"
```

---

## Task 10: Ruff Linting + CI

**Files:**
- Modify: `foldit/pyproject.toml`
- Create: `foldit/.github/workflows/ci.yml`

**Step 1: Add ruff to dev dependencies and configure**

In `foldit/pyproject.toml`, update the dev dependencies and add ruff config:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.11.0",
    "ruff>=0.4.0",
]
training = [
    "tensorflow>=2.15.0",
]
```

Add after existing sections:

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W"]
```

**Step 2: Install ruff and verify it passes**

Run: `foldit/.venv/bin/pip install ruff`
Run: `foldit/.venv/bin/ruff check foldit/ tests/ training/`
Fix any violations found.

**Step 3: Create CI workflow**

Create `foldit/.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install opencv-python-headless numpy flask pyyaml pytest pytest-mock ruff
          pip install --no-deps -e .
      - name: Lint
        run: ruff check foldit/ tests/ training/
      - name: Test
        run: pytest tests/ -v
```

**Step 4: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
mkdir -p foldit/.github/workflows
git add foldit/pyproject.toml foldit/.github/workflows/ci.yml
git commit -m "feat: ruff linting and GitHub Actions CI pipeline"
```

---

## Task 11: Wire HybridClassifier into V3 Pipeline

**Files:**
- Modify: `foldit/foldit/ml_classifier.py`
- Modify: `foldit/foldit/classifier.py`
- Modify: `foldit/foldit/main.py`
- Modify: `foldit/foldit/simulator.py`
- Create: `foldit/tests/test_ml_integration.py`

**Step 1: Write the failing tests**

Create `foldit/tests/test_ml_integration.py`:

```python
"""Tests for ML classifier integration with V3 pipeline."""
import numpy as np


class TestClassifierInterface:
    def test_heuristic_accepts_frame_kwarg(self):
        from foldit.classifier import GarmentClassifier
        classifier = GarmentClassifier()
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = classifier.classify(contour, frame=frame)
        assert isinstance(result, str)

    def test_hybrid_classify_with_frame_kwarg(self):
        from foldit.ml_classifier import HybridClassifier, MLClassifier
        from foldit.classifier import GarmentClassifier
        from tests.test_ml_classifier import FakeTFLiteInterpreter
        interp = FakeTFLiteInterpreter("model.tflite")
        interp._output_data = np.array([[0.05, 0.85, 0.03, 0.05, 0.02]])
        ml = MLClassifier(interp, confidence_threshold=0.5)
        heuristic = GarmentClassifier()
        hybrid = HybridClassifier(ml, heuristic)
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = hybrid.classify(contour, frame=frame)
        assert result == "pants"

    def test_hybrid_falls_back_without_frame(self):
        from foldit.ml_classifier import HybridClassifier, MLClassifier
        from foldit.classifier import GarmentClassifier
        from tests.test_ml_classifier import FakeTFLiteInterpreter
        interp = FakeTFLiteInterpreter("model.tflite")
        interp._output_data = np.array([[0.2, 0.2, 0.2, 0.2, 0.2]])
        ml = MLClassifier(interp, confidence_threshold=0.5)
        heuristic = GarmentClassifier()
        hybrid = HybridClassifier(ml, heuristic)
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        result = hybrid.classify(contour)
        assert result == "shirt"

    def test_v3_robot_passes_frame_to_classifier(self):
        """V3 pipeline should pass frame to classifier."""
        from foldit.main import FoldItRobotV3
        from foldit.orientation import OrientationDetector
        from foldit.size_estimator import SizeEstimator
        from foldit.fold_verifier import FoldVerifier
        from foldit.error_recovery import ErrorRecovery
        from foldit.robot_logger import MetricsCollector, RobotLogger
        from foldit.data_collector import DataCollector
        from foldit.frame_quality import FrameQualityChecker
        from foldit.alerter import Alerter
        from foldit.item_detector import DetectionResult

        frames_received = []

        class CapturingClassifier:
            def classify(self, contour, frame=None):
                frames_received.append(frame)
                return "shirt"

        class FakeCamera:
            def start(self): pass
            def stop(self): pass
            def capture_frame(self):
                f = np.full((480, 640, 3), 255, dtype=np.uint8)
                f[140:340, 170:470] = [120, 80, 60]
                return f

        class FakePreprocessor:
            def to_grayscale(self, img):
                import cv2
                return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            def threshold(self, gray):
                import cv2
                _, b = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                return b

        class FakeConveyor:
            def advance_to_fold_zone(self, timeout_sec=10.0): return True

        class FakeDetector:
            def detect(self, binary):
                c = np.array([[[170,140]],[[470,140]],[[470,340]],[[170,340]]], dtype=np.int32)
                return DetectionResult(count=1, largest=c, all_contours=[c])

        class FakeFlatness:
            def is_flat(self, contour): return True

        class FakeSequencer:
            def fold(self, t, speed_factor=1.0): return t

        camera = FakeCamera()
        preprocessor = FakePreprocessor()
        robot = FoldItRobotV3(
            camera=camera, preprocessor=preprocessor,
            classifier=CapturingClassifier(), sequencer=FakeSequencer(),
            conveyor=FakeConveyor(), item_detector=FakeDetector(),
            flatness_checker=FakeFlatness(),
            orientation=OrientationDetector(),
            size_estimator=SizeEstimator(pixels_per_mm=1.0),
            fold_verifier=FoldVerifier(camera, preprocessor, min_compactness=0.3),
            error_recovery=ErrorRecovery(), metrics=MetricsCollector(),
            logger=RobotLogger(name="test"), data_collector=DataCollector(enabled=False),
            frame_quality=FrameQualityChecker(), alerter=Alerter(),
        )
        robot.process_one()
        assert len(frames_received) == 1
        assert frames_received[0] is not None
```

**Step 2: Run tests to verify they fail**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/test_ml_integration.py -v`
Expected: FAIL

**Step 3: Update classifier interfaces**

Read `foldit/foldit/classifier.py` first, then update the `classify` method to accept an optional `frame` kwarg:

In `foldit/foldit/classifier.py`, change the classify method signature:
```python
def classify(self, contour, frame=None):
```
(The body stays the same — frame is ignored by heuristic classifier.)

In `foldit/foldit/ml_classifier.py`, update `HybridClassifier.classify`:
```python
def classify(self, contour, frame=None):
    if frame is not None:
        try:
            result = self._ml.classify_frame(frame)
            if result.garment_type != GarmentType.UNKNOWN:
                return result.garment_type
        except Exception:
            pass
    return self._heuristic.classify(contour)
```

In `foldit/foldit/main.py`, update the classify call in `FoldItRobotV3.process_one()` (line 178):
Change `garment_type = self._classifier.classify(contour)` to:
```python
garment_type = self._classifier.classify(contour, frame=frame)
```

**Step 4: Update existing HybridClassifier tests**

In `foldit/tests/test_ml_classifier.py`, update the three `TestHybridClassifier` test calls:
- Change `hybrid.classify(frame, contour)` to `hybrid.classify(contour, frame=frame)` in all three tests.

**Step 5: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add foldit/foldit/classifier.py foldit/foldit/ml_classifier.py foldit/foldit/main.py foldit/tests/test_ml_classifier.py foldit/tests/test_ml_integration.py
git commit -m "feat: wire HybridClassifier into V3 pipeline with unified interface"
```

---

## Task 12: V5 Integration Tests

**Files:**
- Create: `foldit/tests/test_v5_integration.py`

**Step 1: Write integration tests**

Create `foldit/tests/test_v5_integration.py`:

```python
"""V5 integration tests — production hardening, observability, ML integration."""
import json
import os
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock


class TestV5Integration:
    def test_dashboard_auth_with_export(self):
        from foldit.dashboard import create_app
        from foldit.dashboard_auth import DashboardAuth
        from foldit.robot_logger import MetricsCollector
        from foldit.error_recovery import RobotState
        metrics = MetricsCollector()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        auth = DashboardAuth("testkey")
        auth.apply(app)
        app.config["TESTING"] = True
        with app.test_client() as client:
            resp = client.get("/api/metrics/export")
            assert resp.status_code == 401
            resp = client.get("/api/metrics/export", headers={"X-API-Key": "testkey"})
            assert resp.status_code == 200

    def test_event_stream_with_dashboard(self):
        from foldit.dashboard import create_app
        from foldit.event_stream import EventStream
        from foldit.robot_logger import MetricsCollector
        from foldit.error_recovery import RobotState
        metrics = MetricsCollector()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        stream = EventStream()
        stream.push({"type": "fold", "garment": "shirt"})
        app = create_app(metrics, state, event_stream=stream)
        app.config["TESTING"] = True
        with app.test_client() as client:
            resp = client.get("/api/events")
            assert resp.status_code == 200

    def test_alert_notifier_integration(self):
        from foldit.alerter import Alerter
        from foldit.alert_notifier import AlertNotifier
        alerter = Alerter(consecutive_fail_threshold=2)
        notifier = AlertNotifier(webhook_url="http://example.com/hook")
        alerter.check("shirt", success=False)
        alert = alerter.check("shirt", success=False)
        assert alert is not None
        with patch("foldit.alert_notifier.urlopen") as mock:
            mock.return_value = MagicMock()
            notifier.notify(alert)
            mock.assert_called_once()

    def test_signal_handler_stops_robot(self):
        from foldit.simulator import create_simulated_robot_v3
        from foldit.signal_handler import SignalHandler
        robot = create_simulated_robot_v3()
        handler = SignalHandler(robot)
        handler.handle(None, None)
        assert robot._stop_requested is True

    def test_augmented_dataset_loads(self):
        import cv2
        from training.label_tool import LabelStore
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            for i in range(3):
                path = os.path.join(tmpdir, f"f_{i}.jpg")
                cv2.imwrite(path, np.full((100, 100, 3), 128, dtype=np.uint8))
                store.save_label(path, "shirt")
            splitter = DatasetSplitter(csv_path)
            images, labels = splitter.load_images(store.load_all(), augment=True)
            assert len(labels) == 3
            assert images.shape[1:] == (224, 224, 3)

    def test_v3_robot_with_frame_to_classifier(self):
        from foldit.simulator import create_simulated_robot_v3
        robot = create_simulated_robot_v3()
        result = robot.process_one()
        assert isinstance(result, str)

    def test_prometheus_export_format(self):
        from foldit.dashboard import create_app
        from foldit.robot_logger import MetricsCollector
        from foldit.error_recovery import RobotState
        metrics = MetricsCollector()
        metrics.record_fold("shirt", True, 5.0)
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        app.config["TESTING"] = True
        with app.test_client() as client:
            resp = client.get("/api/metrics/export?format=prometheus")
            text = resp.data.decode()
            assert "foldit_total_folds 1" in text

    def test_default_config_yaml_valid(self):
        import yaml
        path = os.path.join(os.path.dirname(__file__), "..", "foldit", "config.default.yaml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert config["dashboard"]["port"] == 5000
        assert config["alerting"]["consecutive_fail_threshold"] == 3
```

**Step 2: Run ALL tests to verify everything passes**

Run: `foldit/.venv/bin/python -m pytest foldit/tests/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add foldit/tests/test_v5_integration.py
git commit -m "test: V5 integration tests for auth, SSE, alerting, ML, augmentation"
```

---

## Summary

| Task | Component | New Tests | Files |
|------|-----------|-----------|-------|
| 1 | Dashboard Authentication | 6 | dashboard_auth.py, test_dashboard_auth.py |
| 2 | SSE Event Stream | 4 | event_stream.py, test_event_stream.py |
| 3 | Alert Notifier | 3 | alert_notifier.py, test_alert_notifier.py |
| 4 | Graceful Shutdown | 2 | signal_handler.py, test_signal_handler.py |
| 5 | Dashboard SSE + Export + Shutdown | 4 | dashboard.py, test_dashboard.py |
| 6 | Data Augmentation | 3 | dataset.py, test_augmentation.py |
| 7 | V5 Config Sections | 4 | config_loader.py, test_config_loader.py |
| 8 | Default Config YAML | 3 | config.default.yaml, config_loader.py, test_default_config.py |
| 9 | CLI Subcommands | 2 | main.py, pyproject.toml, test_cli.py |
| 10 | Ruff + CI | 0 | pyproject.toml, ci.yml |
| 11 | Wire HybridClassifier | 4 | classifier.py, ml_classifier.py, main.py, test_ml_integration.py |
| 12 | V5 Integration Tests | 8 | test_v5_integration.py |
| **Total** | | **43 new** | **~270+ total** |
