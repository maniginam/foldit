"""Tests for main robot loop."""
import numpy as np


class FakeCamera:
    def __init__(self, frames=None):
        self._frames = frames or []
        self._index = 0
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def capture_frame(self):
        if self._index < len(self._frames):
            frame = self._frames[self._index]
            self._index += 1
            return frame
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def stop(self):
        self.stopped = True


class FakeSequencer:
    def __init__(self):
        self.folded = []

    def fold(self, garment_type):
        self.folded.append(garment_type)
        return garment_type


class FakeClassifier:
    def __init__(self, results):
        self._results = results
        self._index = 0

    def classify(self, contour):
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            return result
        return "unknown"


class FakePreprocessor:
    def __init__(self, contour=None):
        self._contour = contour

    def to_grayscale(self, image):
        return image[:, :, 0] if len(image.shape) == 3 else image

    def threshold(self, gray):
        return gray

    def find_largest_contour(self, binary):
        return self._contour


class TestFoldItRobot:
    def test_process_single_garment(self):
        from foldit.main import FoldItRobot
        contour = np.array([[[100, 100]], [[500, 100]], [[500, 400]], [[100, 400]]], dtype=np.int32)
        frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        camera = FakeCamera(frames=[frame])
        preprocessor = FakePreprocessor(contour=contour)
        classifier = FakeClassifier(results=["shirt"])
        sequencer = FakeSequencer()

        robot = FoldItRobot(camera, preprocessor, classifier, sequencer)
        result = robot.process_one()
        assert result == "shirt"
        assert sequencer.folded == ["shirt"]

    def test_process_no_garment_detected(self):
        from foldit.main import FoldItRobot
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        camera = FakeCamera(frames=[frame])
        preprocessor = FakePreprocessor(contour=None)
        classifier = FakeClassifier(results=[])
        sequencer = FakeSequencer()

        robot = FoldItRobot(camera, preprocessor, classifier, sequencer)
        result = robot.process_one()
        assert result is None
        assert sequencer.folded == []
