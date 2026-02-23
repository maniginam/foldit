"""PCA-based garment orientation detection."""
import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class OrientationResult:
    angle_deg: float
    is_landscape: bool
    is_portrait: bool


class OrientationDetector:
    """Detects garment orientation using PCA on contour points."""

    def detect(self, contour):
        if contour is None:
            return OrientationResult(angle_deg=0.0, is_landscape=True, is_portrait=False)

        points = contour.reshape(-1, 2).astype(np.float64)
        mean, eigenvectors = cv2.PCACompute(points, mean=np.empty(0))
        angle = np.degrees(np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0]))

        x, y, w, h = cv2.boundingRect(contour)
        is_landscape = w >= h
        is_portrait = not is_landscape

        return OrientationResult(
            angle_deg=float(angle),
            is_landscape=is_landscape,
            is_portrait=is_portrait,
        )
