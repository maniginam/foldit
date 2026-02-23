"""Camera capture and image preprocessing."""
import cv2
import numpy as np
from foldit.config import CameraConfig


class CameraCapture:
    """Captures frames from the Pi Camera."""

    def __init__(self, picamera):
        self._camera = picamera

    def start(self):
        config = self._camera.create_still_configuration(
            main={"size": CameraConfig.RESOLUTION}
        )
        self._camera.configure(config)
        self._camera.start()

    def capture_frame(self):
        return self._camera.capture_array()

    def stop(self):
        self._camera.stop()


class ImagePreprocessor:
    """Static methods for preprocessing captured images."""

    @staticmethod
    def to_grayscale(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def threshold(gray_image):
        _, binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        return binary

    @staticmethod
    def find_largest_contour(binary_image):
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)


class AdaptivePreprocessor:
    """Adaptive image preprocessing with background subtraction."""

    def __init__(self, background_frame):
        self._background = cv2.cvtColor(background_frame, cv2.COLOR_BGR2GRAY)

    def subtract_background(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray, self._background)
        _, mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        return mask

    def adaptive_threshold(self, gray_image):
        return cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

    def preprocess(self, frame):
        mask = self.subtract_background(frame)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)

    def find_all_contours(self, binary_image, min_area=5000):
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) >= min_area]
