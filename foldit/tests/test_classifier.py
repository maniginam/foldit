"""Tests for garment classifier."""
import numpy as np


def _make_contour(width, height, x=100, y=100):
    """Create a rectangular contour with given dimensions."""
    points = np.array([
        [[x, y]],
        [[x + width, y]],
        [[x + width, y + height]],
        [[x, y + height]]
    ], dtype=np.int32)
    return points


class TestGarmentClassifier:
    def test_wide_short_shape_is_shirt(self):
        from foldit.classifier import GarmentClassifier
        contour = _make_contour(400, 300)
        result = GarmentClassifier.classify(contour)
        assert result == "shirt"

    def test_tall_narrow_shape_is_pants(self):
        from foldit.classifier import GarmentClassifier
        contour = _make_contour(150, 400)
        result = GarmentClassifier.classify(contour)
        assert result == "pants"

    def test_roughly_square_large_is_towel(self):
        from foldit.classifier import GarmentClassifier
        contour = _make_contour(350, 350)
        result = GarmentClassifier.classify(contour)
        assert result == "towel"

    def test_small_area_is_small_item(self):
        from foldit.classifier import GarmentClassifier
        contour = _make_contour(80, 60)
        result = GarmentClassifier.classify(contour)
        assert result == "small"

    def test_none_contour_returns_unknown(self):
        from foldit.classifier import GarmentClassifier
        result = GarmentClassifier.classify(None)
        assert result == "unknown"

    def test_zero_area_contour_returns_unknown(self):
        from foldit.classifier import GarmentClassifier
        degenerate = np.array([[[0, 0]], [[0, 0]]], dtype=np.int32)
        result = GarmentClassifier.classify(degenerate)
        assert result == "unknown"
