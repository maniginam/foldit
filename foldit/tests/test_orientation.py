"""Tests for PCA-based garment orientation detection."""
import numpy as np


class TestOrientationDetector:
    def test_landscape_rectangle_detected(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[50,100]],[[550,100]],[[550,300]],[[50,300]]], dtype=np.int32)
        result = detector.detect(contour)
        assert result.is_landscape is True
        assert result.is_portrait is False

    def test_portrait_rectangle_detected(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[200,50]],[[400,50]],[[400,450]],[[200,450]]], dtype=np.int32)
        result = detector.detect(contour)
        assert result.is_portrait is True
        assert result.is_landscape is False

    def test_angle_near_zero_for_horizontal(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[50,200]],[[550,200]],[[550,280]],[[50,280]]], dtype=np.int32)
        result = detector.detect(contour)
        assert abs(result.angle_deg) < 15

    def test_angle_near_90_for_vertical(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[280,50]],[[320,50]],[[320,430]],[[280,430]]], dtype=np.int32)
        result = detector.detect(contour)
        assert abs(abs(result.angle_deg) - 90) < 15

    def test_none_contour_returns_neutral(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        result = detector.detect(None)
        assert result.angle_deg == 0.0
        assert result.is_landscape is True

    def test_result_has_expected_fields(self):
        from foldit.orientation import OrientationDetector
        detector = OrientationDetector()
        contour = np.array([[[50,100]],[[550,100]],[[550,300]],[[50,300]]], dtype=np.int32)
        result = detector.detect(contour)
        assert hasattr(result, "angle_deg")
        assert hasattr(result, "is_landscape")
        assert hasattr(result, "is_portrait")
