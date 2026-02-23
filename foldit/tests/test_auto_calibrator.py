"""Tests for automatic pixels_per_mm calibration."""
import os
import tempfile
import numpy as np


class TestAutoCalibrator:
    def _make_calibration_frame(self, rect_w_px=171, rect_h_px=108):
        """Create frame with white rectangle on black background.
        Default: credit card at ~2 px/mm (85.6mm * 2 = 171px, 53.98mm * 2 ≈ 108px)."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cx, cy = 320, 240
        x1, y1 = cx - rect_w_px // 2, cy - rect_h_px // 2
        x2, y2 = x1 + rect_w_px, y1 + rect_h_px
        frame[y1:y2, x1:x2] = 255
        return frame

    def test_calibrate_returns_pixels_per_mm(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator(reference_width_mm=85.6, reference_height_mm=53.98)
        frame = self._make_calibration_frame()
        result = cal.calibrate(frame)
        assert 1.5 < result.pixels_per_mm < 2.5

    def test_calibrate_no_rectangle_returns_none(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = cal.calibrate(frame)
        assert result is None

    def test_save_and_load_calibration(self):
        from foldit.auto_calibrator import AutoCalibrator
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "calibration.json")
            cal = AutoCalibrator()
            frame = self._make_calibration_frame()
            result = cal.calibrate(frame)
            cal.save(result, path)
            loaded = cal.load(path)
            assert abs(loaded.pixels_per_mm - result.pixels_per_mm) < 0.01

    def test_load_missing_file_returns_none(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        result = cal.load("/nonexistent/calibration.json")
        assert result is None

    def test_calibration_result_has_fields(self):
        from foldit.auto_calibrator import AutoCalibrator
        cal = AutoCalibrator()
        frame = self._make_calibration_frame()
        result = cal.calibrate(frame)
        assert hasattr(result, "pixels_per_mm")
        assert hasattr(result, "reference_width_px")
        assert hasattr(result, "reference_height_px")
