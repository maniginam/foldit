"""Simulator mode for development without hardware."""
import numpy as np
from foldit.motor_controller import ServoDriverBase


class SimulatedCamera:

    def __init__(self, resolution=(640, 480)):
        self._width, self._height = resolution

    def start(self):
        pass

    def stop(self):
        pass

    def capture_frame(self):
        frame = np.full((self._height, self._width, 3), 255, dtype=np.uint8)
        cx, cy = self._width // 2, self._height // 2
        half_w, half_h = self._width // 4, self._height // 4
        frame[cy - half_h:cy + half_h, cx - half_w:cx + half_w] = [120, 80, 60]
        return frame


class SimulatedServoDriver(ServoDriverBase):

    def __init__(self):
        self._log = []
        self._attached = set()

    def attach(self, channel):
        self._attached.add(channel)
        self._log.append(f"attach channel {channel}")

    def move_to(self, channel, angle):
        self._validate_angle(angle)
        self._validate_attached(channel, self._attached)
        self._log.append(f"move channel {channel} to {angle}")

    def cleanup(self):
        self._log.append("cleanup")

    @property
    def log(self):
        return list(self._log)


class SimulatedConveyor:

    def __init__(self):
        self._calls = []

    def advance_to_fold_zone(self, timeout_sec=10.0):
        self._calls.append(f"advance_to_fold_zone(timeout={timeout_sec})")
        return True

    @property
    def calls(self):
        return list(self._calls)


def create_simulated_robot():
    from foldit.camera import ImagePreprocessor
    from foldit.classifier import GarmentClassifier
    from foldit.folder import FoldSequencer
    from foldit.item_detector import ItemDetector
    from foldit.flatness import FlatnessChecker
    from foldit.motor_controller import FoldingPlatform
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

    return FoldItRobotV2(
        camera=camera,
        preprocessor=preprocessor,
        classifier=classifier,
        sequencer=sequencer,
        conveyor=conveyor,
        item_detector=detector,
        flatness_checker=flatness,
        platform=platform,
    )


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
