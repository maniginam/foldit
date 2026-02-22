"""Garment type classifier using shape heuristics."""
import cv2
from foldit.config import GarmentType


class GarmentClassifier:
    """Classifies garments by contour shape and size."""

    SMALL_AREA_THRESHOLD = 15000
    PANTS_RATIO_THRESHOLD = 0.6
    SHIRT_RATIO_THRESHOLD = 1.2

    @staticmethod
    def classify(contour):
        if contour is None:
            return GarmentType.UNKNOWN

        area = cv2.contourArea(contour)
        if area == 0:
            return GarmentType.UNKNOWN
        if area < GarmentClassifier.SMALL_AREA_THRESHOLD:
            return GarmentType.SMALL

        _, _, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0

        if aspect_ratio > GarmentClassifier.SHIRT_RATIO_THRESHOLD:
            return GarmentType.SHIRT
        elif aspect_ratio < GarmentClassifier.PANTS_RATIO_THRESHOLD:
            return GarmentType.PANTS
        else:
            return GarmentType.TOWEL
