"""Post-fold quality verification via contour compactness."""
import cv2
from dataclasses import dataclass


@dataclass
class FoldResult:
    success: bool
    compactness: float


class FoldVerifier:
    """Verifies fold quality by checking post-fold contour compactness."""

    def __init__(self, camera, preprocessor, min_compactness=0.6):
        self._camera = camera
        self._preprocessor = preprocessor
        self._min_compactness = min_compactness

    def verify(self, garment_type):
        frame = self._camera.capture_frame()
        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)
        contour = self._preprocessor.find_largest_contour(binary)

        if contour is None:
            return FoldResult(success=False, compactness=0.0)

        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        rect_area = w * h
        compactness = area / rect_area if rect_area > 0 else 0.0

        return FoldResult(
            success=compactness >= self._min_compactness,
            compactness=compactness,
        )
