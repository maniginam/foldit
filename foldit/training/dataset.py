"""Dataset packaging and splitting for ML training."""
import csv
import os
import random

import cv2
import numpy as np


def augment_image(image, seed=None):
    """Apply random augmentation: rotation, flip, brightness jitter."""
    rng = random.Random(seed)
    result = image.copy()

    angle = rng.uniform(-15, 15)
    h, w = result.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    result = cv2.warpAffine(result, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)

    if rng.random() > 0.5:
        result = cv2.flip(result, 1)

    factor = rng.uniform(0.8, 1.2)
    result = np.clip(result.astype(np.float32) * factor, 0, 255).astype(np.uint8)

    return result


class DatasetSplitter:
    """Splits labeled data into train/val/test sets and loads images."""

    def __init__(self, csv_path):
        self._csv_path = csv_path

    def _load_csv(self):
        if not os.path.exists(self._csv_path):
            return []
        with open(self._csv_path, "r") as f:
            reader = csv.DictReader(f)
            return [row for row in reader if row]

    def split(self, train=0.7, val=0.15, test=0.15):
        rows = self._load_csv()
        if not rows:
            return [], [], []
        random.seed(42)
        random.shuffle(rows)
        n = len(rows)
        train_end = int(n * train)
        val_end = train_end + int(n * val)
        return rows[:train_end], rows[train_end:val_end], rows[val_end:]

    def load_images(self, rows, size=(224, 224), augment=False):
        images = []
        labels = []
        for row in rows:
            img = cv2.imread(row["path"])
            if img is None:
                continue
            img = cv2.resize(img, size)
            if augment:
                img = augment_image(img)
            images.append(img)
            labels.append(row["label"])
        return np.array(images), labels
