"""Tests for camera module."""
import numpy as np


class FakePicamera2:
    def __init__(self):
        self.configured = False
        self.started = False
        self.stopped = False
        self._frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def configure(self, config):
        self.configured = True
        self._config = config

    def create_still_configuration(self, main):
        return {"main": main}

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def capture_array(self):
        return self._frame


class TestCameraCapture:
    def test_start_configures_and_starts_camera(self):
        from foldit.camera import CameraCapture
        fake_cam = FakePicamera2()
        capture = CameraCapture(fake_cam)
        capture.start()
        assert fake_cam.configured is True
        assert fake_cam.started is True

    def test_capture_frame_returns_numpy_array(self):
        from foldit.camera import CameraCapture
        fake_cam = FakePicamera2()
        capture = CameraCapture(fake_cam)
        capture.start()
        frame = capture.capture_frame()
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

    def test_stop_stops_camera(self):
        from foldit.camera import CameraCapture
        fake_cam = FakePicamera2()
        capture = CameraCapture(fake_cam)
        capture.start()
        capture.stop()
        assert fake_cam.stopped is True


class TestImagePreprocessor:
    def test_to_grayscale_reduces_channels(self):
        from foldit.camera import ImagePreprocessor
        color_image = np.zeros((480, 640, 3), dtype=np.uint8)
        gray = ImagePreprocessor.to_grayscale(color_image)
        assert len(gray.shape) == 2

    def test_threshold_returns_binary_image(self):
        from foldit.camera import ImagePreprocessor
        gray = np.full((480, 640), 128, dtype=np.uint8)
        binary = ImagePreprocessor.threshold(gray)
        unique_values = set(np.unique(binary))
        assert unique_values == {255}

    def test_find_largest_contour_returns_contour_for_white_region(self):
        from foldit.camera import ImagePreprocessor
        binary = np.zeros((480, 640), dtype=np.uint8)
        binary[100:300, 100:400] = 255
        contour = ImagePreprocessor.find_largest_contour(binary)
        assert contour is not None
        assert len(contour) > 0

    def test_find_largest_contour_returns_none_for_blank(self):
        from foldit.camera import ImagePreprocessor
        binary = np.zeros((480, 640), dtype=np.uint8)
        contour = ImagePreprocessor.find_largest_contour(binary)
        assert contour is None
