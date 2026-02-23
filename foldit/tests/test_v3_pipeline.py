"""Tests for FoldItRobotV3 composed pipeline."""
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
    def classify(self, contour, frame=None):
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
