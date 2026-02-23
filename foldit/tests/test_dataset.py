"""Tests for dataset packaging."""
import os
import tempfile
import numpy as np
import cv2


class TestDatasetSplitter:
    def _make_fake_data(self, tmpdir, count=20):
        from training.label_tool import LabelStore
        csv_path = os.path.join(tmpdir, "labels.csv")
        store = LabelStore(csv_path)
        for i in range(count):
            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.jpg")
            frame = np.full((100, 100, 3), i * 10, dtype=np.uint8)
            cv2.imwrite(frame_path, frame)
            label = "shirt" if i % 2 == 0 else "pants"
            store.save_label(frame_path, label)
        return csv_path

    def test_split_ratios(self):
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self._make_fake_data(tmpdir, count=20)
            splitter = DatasetSplitter(csv_path)
            train, val, test = splitter.split(train=0.7, val=0.15, test=0.15)
            assert len(train) == 14
            assert len(val) == 3
            assert len(test) == 3

    def test_load_images_returns_correct_shape(self):
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self._make_fake_data(tmpdir, count=10)
            splitter = DatasetSplitter(csv_path)
            train, _, _ = splitter.split()
            images, labels = splitter.load_images(train, size=(224, 224))
            assert images.shape == (7, 224, 224, 3)
            assert len(labels) == 7

    def test_empty_csv_returns_empty_splits(self):
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            with open(csv_path, "w"):
                pass
            splitter = DatasetSplitter(csv_path)
            train, val, test = splitter.split()
            assert len(train) == 0
