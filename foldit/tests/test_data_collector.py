"""Tests for garment image data collection."""
import os
import tempfile
import numpy as np


class TestDataCollector:
    def test_save_frame_creates_file(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "shirt")
            assert os.path.exists(path)
            assert "shirt" in path

    def test_save_increments_counter(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path1 = collector.save(frame, "shirt")
            path2 = collector.save(frame, "shirt")
            assert path1 != path2

    def test_save_creates_date_subdirectory(self):
        from foldit.data_collector import DataCollector
        from datetime import date
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "pants")
            today = date.today().isoformat()
            assert today in path

    def test_disabled_collector_does_not_save(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir, enabled=False)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            path = collector.save(frame, "shirt")
            assert path is None
            assert len(os.listdir(tmpdir)) == 0

    def test_total_saved_count(self):
        from foldit.data_collector import DataCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
            collector.save(frame, "shirt")
            collector.save(frame, "pants")
            assert collector.total_saved == 2
