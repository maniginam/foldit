"""Pre-classification frame quality checks."""
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class QualityResult:
    acceptable: bool
    blur_score: float
    contrast_score: float
    brightness_score: float


class FrameQualityChecker:
    """Checks frame blur, contrast, and brightness before classification."""

    def __init__(self, min_blur_score=100.0, min_contrast=30.0,
                 min_brightness=10.0, max_brightness=220.0):
        self._min_blur = min_blur_score
        self._min_contrast = min_contrast
        self._min_brightness = min_brightness
        self._max_brightness = max_brightness

    def check(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast_score = float(np.std(gray))
        brightness_score = float(np.mean(gray))

        acceptable = bool(
            blur_score >= self._min_blur
            and contrast_score >= self._min_contrast
            and self._min_brightness <= brightness_score <= self._max_brightness
        )

        return QualityResult(
            acceptable=acceptable,
            blur_score=float(blur_score),
            contrast_score=contrast_score,
            brightness_score=brightness_score,
        )
