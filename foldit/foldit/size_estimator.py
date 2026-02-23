"""Garment size estimation from contour dimensions."""
import cv2
from dataclasses import dataclass


LARGE_AREA_THRESHOLD = 100000
SMALL_AREA_THRESHOLD = 20000


@dataclass
class SizeResult:
    width_mm: float
    height_mm: float
    area_mm2: float
    category: str
    speed_factor: float


class SizeEstimator:
    """Estimates physical garment size from contour and camera calibration."""

    def __init__(self, pixels_per_mm=1.0):
        self._ppm = pixels_per_mm

    def estimate(self, contour):
        if contour is None:
            return SizeResult(
                width_mm=0.0, height_mm=0.0, area_mm2=0.0,
                category="unknown", speed_factor=1.0,
            )

        x, y, w, h = cv2.boundingRect(contour)
        width_mm = w / self._ppm
        height_mm = h / self._ppm
        area_mm2 = width_mm * height_mm

        if area_mm2 >= LARGE_AREA_THRESHOLD:
            category = "large"
            speed_factor = 1.5
        elif area_mm2 >= SMALL_AREA_THRESHOLD:
            category = "medium"
            speed_factor = 1.0
        else:
            category = "small"
            speed_factor = 1.0

        return SizeResult(
            width_mm=width_mm,
            height_mm=height_mm,
            area_mm2=area_mm2,
            category=category,
            speed_factor=speed_factor,
        )
