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


class TestAdaptivePreprocessor:
    def test_capture_background_stores_frame(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 100, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        assert proc._background is not None
        assert proc._background.shape == (480, 640)

    def test_subtract_background_isolates_foreground(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 100, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        frame[200:300, 200:400] = 200
        result = proc.subtract_background(frame)
        assert result[250, 300] > 0
        assert result[0, 0] == 0

    def test_adaptive_threshold_returns_binary(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.zeros((480, 640, 3), dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        gray = np.full((480, 640), 128, dtype=np.uint8)
        binary = proc.adaptive_threshold(gray)
        unique = np.unique(binary)
        assert all(v in (0, 255) for v in unique)

    def test_preprocess_full_pipeline(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 50, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        frame = np.full((480, 640, 3), 50, dtype=np.uint8)
        frame[100:300, 100:400] = 200
        contour = proc.preprocess(frame)
        assert contour is not None

    def test_preprocess_no_garment_returns_none(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 100, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        contour = proc.preprocess(frame)
        assert contour is None

    def test_find_all_contours_returns_list(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.zeros((480, 640, 3), dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        binary = np.zeros((480, 640), dtype=np.uint8)
        binary[50:150, 50:150] = 255
        binary[300:400, 300:450] = 255
        contours = proc.find_all_contours(binary, min_area=1000)
        assert len(contours) == 2

    def test_find_all_contours_filters_small(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.zeros((480, 640, 3), dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        binary = np.zeros((480, 640), dtype=np.uint8)
        binary[50:150, 50:150] = 255
        binary[300:310, 300:310] = 255
        contours = proc.find_all_contours(binary, min_area=1000)
        assert len(contours) == 1
