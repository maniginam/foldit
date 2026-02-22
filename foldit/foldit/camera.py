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
