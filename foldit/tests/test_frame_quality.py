"""Tests for pre-classification frame quality checks."""
import numpy as np


class TestFrameQualityChecker:
    def test_sharp_frame_passes(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:300] = 255
        result = checker.check(frame)
        assert result.acceptable is True

    def test_blurry_frame_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        import cv2
        checker = FrameQualityChecker(min_blur_score=100.0)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:300] = 255
        blurred = cv2.GaussianBlur(frame, (51, 51), 0)
        result = checker.check(blurred)
        assert result.acceptable is False
        assert result.blur_score < 100.0

    def test_low_contrast_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker(min_contrast=30.0)
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        result = checker.check(frame)
        assert result.acceptable is False
        assert result.contrast_score < 30.0

    def test_too_dark_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker(min_brightness=40.0)
        frame = np.full((480, 640, 3), 10, dtype=np.uint8)
        result = checker.check(frame)
        assert result.acceptable is False
        assert result.brightness_score < 40.0

    def test_too_bright_fails(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker(max_brightness=220.0)
        frame = np.full((480, 640, 3), 250, dtype=np.uint8)
        result = checker.check(frame)
        assert result.acceptable is False
        assert result.brightness_score > 220.0

    def test_result_has_all_fields(self):
        from foldit.frame_quality import FrameQualityChecker
        checker = FrameQualityChecker()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:300] = 255
        result = checker.check(frame)
        assert hasattr(result, "acceptable")
        assert hasattr(result, "blur_score")
        assert hasattr(result, "contrast_score")
        assert hasattr(result, "brightness_score")
