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
