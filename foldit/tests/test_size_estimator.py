"""Tests for garment size estimation."""
import numpy as np


class TestSizeEstimator:
    def test_estimate_returns_dimensions(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[100,100]],[[399,100]],[[399,299]],[[100,299]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.width_mm == 300.0
        assert size.height_mm == 200.0

    def test_estimate_with_calibration_scaling(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=2.0)
        contour = np.array([[[100,100]],[[499,100]],[[499,299]],[[100,299]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.width_mm == 200.0
        assert size.height_mm == 100.0

    def test_none_contour_returns_zero(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        size = estimator.estimate(None)
        assert size.width_mm == 0.0
        assert size.height_mm == 0.0

    def test_classify_size_large(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[0,0]],[[600,0]],[[600,400]],[[0,400]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "large"

    def test_classify_size_medium(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[100,100]],[[400,100]],[[400,300]],[[100,300]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "medium"

    def test_classify_size_small(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[200,200]],[[280,200]],[[280,260]],[[200,260]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.category == "small"

    def test_speed_factor_large(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[0,0]],[[600,0]],[[600,400]],[[0,400]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.speed_factor > 1.0

    def test_speed_factor_small(self):
        from foldit.size_estimator import SizeEstimator
        estimator = SizeEstimator(pixels_per_mm=1.0)
        contour = np.array([[[200,200]],[[280,200]],[[280,260]],[[200,260]]], dtype=np.int32)
        size = estimator.estimate(contour)
        assert size.speed_factor == 1.0
