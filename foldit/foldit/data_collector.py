"""Garment image data collection for ML training."""
import os
from datetime import date

import cv2


class DataCollector:
    """Saves classified garment frames for future ML training."""

    def __init__(self, output_dir="./data/captures", enabled=True):
        self._output_dir = output_dir
        self._enabled = enabled
        self._counter = 0

    @property
    def total_saved(self):
        return self._counter

    def save(self, frame, garment_type):
        if not self._enabled:
            return None

        today = date.today().isoformat()
        day_dir = os.path.join(self._output_dir, today)
        os.makedirs(day_dir, exist_ok=True)

        self._counter += 1
        filename = f"{garment_type}_{self._counter:04d}.jpg"
        path = os.path.join(day_dir, filename)
        cv2.imwrite(path, frame)
        return path
