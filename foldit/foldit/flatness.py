"""Wrinkle/flatness detection for garments on the platform."""
import cv2


class FlatnessChecker:
    """Checks if a garment contour appears flat (well-spread) or bunched up."""

    def __init__(self, threshold=0.75):
        self._threshold = threshold

    def compute_solidity(self, contour):
        area = cv2.contourArea(contour)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            return 0.0
        return area / hull_area

    def is_flat(self, contour):
        if contour is None:
            return False
        solidity = self.compute_solidity(contour)
        return solidity >= self._threshold
