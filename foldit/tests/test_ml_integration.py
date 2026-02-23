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
            def find_largest_contour(self, binary):
                import cv2
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    return None
                return max(contours, key=cv2.contourArea)

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
