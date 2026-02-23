"""Automatic camera calibration using a known-size reference object."""
import json
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class CalibrationResult:
    pixels_per_mm: float
    reference_width_px: float
    reference_height_px: float


class AutoCalibrator:
    """Calibrates pixels_per_mm using a known-size reference rectangle."""

    def __init__(self, reference_width_mm=85.6, reference_height_mm=53.98):
        self._ref_w = reference_width_mm
        self._ref_h = reference_height_mm

    def calibrate(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        if w < 20 or h < 20:
            return None

        ppm_w = w / self._ref_w
        ppm_h = h / self._ref_h
        pixels_per_mm = (ppm_w + ppm_h) / 2.0

        return CalibrationResult(
            pixels_per_mm=pixels_per_mm,
            reference_width_px=float(w),
            reference_height_px=float(h),
        )

    def save(self, result, path):
        with open(path, "w") as f:
            json.dump({
                "pixels_per_mm": result.pixels_per_mm,
                "reference_width_px": result.reference_width_px,
                "reference_height_px": result.reference_height_px,
            }, f)

    def load(self, path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return CalibrationResult(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
