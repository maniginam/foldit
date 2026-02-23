"""Tests for the frame labeling tool."""
import os
import csv
import tempfile
import numpy as np
import cv2


class TestLabelTool:
    def test_save_label_writes_csv(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            store.save_label("/path/to/frame.jpg", "shirt")
            store.save_label("/path/to/frame2.jpg", "pants")
            labels = store.load_all()
            assert len(labels) == 2
            assert labels[0]["path"] == "/path/to/frame.jpg"
            assert labels[0]["label"] == "shirt"

    def test_load_empty_csv_returns_empty(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            labels = store.load_all()
            assert labels == []

    def test_resume_skips_labeled(self):
        from training.label_tool import LabelStore
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "labels.csv")
            store = LabelStore(csv_path)
            store.save_label("/a.jpg", "shirt")
            store.save_label("/b.jpg", "pants")
            labeled = store.labeled_paths()
            assert "/a.jpg" in labeled
            assert "/b.jpg" in labeled
