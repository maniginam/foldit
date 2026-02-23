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
