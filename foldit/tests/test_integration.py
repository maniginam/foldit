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
