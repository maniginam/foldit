"""Tests for data augmentation in dataset splitter."""
import numpy as np


class TestAugmentation:
    def test_augment_preserves_shape(self):
        from training.dataset import augment_image
        img = np.full((224, 224, 3), 128, dtype=np.uint8)
        result = augment_image(img, seed=42)
        assert result.shape == (224, 224, 3)
        assert result.dtype == np.uint8

    def test_augment_changes_pixels(self):
        from training.dataset import augment_image
        img = np.full((224, 224, 3), 128, dtype=np.uint8)
        result = augment_image(img, seed=42)
        assert not np.array_equal(img, result)

    def test_load_images_with_augment(self):
        import os
        import tempfile
        import cv2
        from training.label_tool import LabelStore
        from training.dataset import DatasetSplitter
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            for i in range(5):
                path = os.path.join(tmpdir, f"frame_{i}.jpg")
                cv2.imwrite(path, np.full((100, 100, 3), 128, dtype=np.uint8))
                store.save_label(path, "shirt")
            splitter = DatasetSplitter(csv_path)
            rows = store.load_all()
            images, labels = splitter.load_images(rows, size=(224, 224), augment=True)
            assert images.shape[1:] == (224, 224, 3)
            assert len(labels) == 5
