"""Multi-item detection for the folding platform."""
import cv2
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class DetectionResult:
    """Result of item detection on the platform."""
    count: int
    largest: Optional[np.ndarray]
    all_contours: list

    @property
    def is_single(self):
        return self.count == 1


class ItemDetector:
    """Detects and counts garments on the platform."""

    def __init__(self, min_area=5000):
        self._min_area = min_area

    def detect(self, binary_image):
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        valid = [c for c in contours if cv2.contourArea(c) >= self._min_area]
        largest = max(valid, key=cv2.contourArea) if valid else None
        return DetectionResult(
            count=len(valid),
            largest=largest,
            all_contours=valid
        )
