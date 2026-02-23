"""Tests for wrinkle/flatness detection."""
import numpy as np
import cv2


class TestFlatnessChecker:
    def test_perfect_rectangle_is_flat(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        contour = np.array([
            [[100, 100]], [[400, 100]], [[400, 300]], [[100, 300]]
        ], dtype=np.int32)
        assert checker.is_flat(contour) is True

    def test_solidity_of_rectangle_near_one(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        contour = np.array([
            [[100, 100]], [[400, 100]], [[400, 300]], [[100, 300]]
        ], dtype=np.int32)
        solidity = checker.compute_solidity(contour)
        assert solidity > 0.95

    def test_irregular_shape_is_not_flat(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        contour = np.array([
            [[200, 50]], [[220, 150]], [[300, 150]],
            [[240, 210]], [[260, 300]], [[200, 240]],
            [[140, 300]], [[160, 210]], [[100, 150]],
            [[180, 150]]
        ], dtype=np.int32)
        assert checker.is_flat(contour) is False

    def test_none_contour_is_not_flat(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        assert checker.is_flat(None) is False

    def test_custom_threshold(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.99)
        contour = np.array([
            [[100, 100]], [[400, 100]], [[400, 300]], [[100, 300]]
        ], dtype=np.int32)
        solidity = checker.compute_solidity(contour)
        assert isinstance(solidity, float)
