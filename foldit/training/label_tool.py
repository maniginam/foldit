"""CLI frame labeling tool for ML training data."""
import csv
import os
from datetime import datetime, timezone


class LabelStore:
    """Reads and writes frame labels to a CSV file."""

    def __init__(self, csv_path):
        self._csv_path = csv_path

    def save_label(self, frame_path, label):
        file_exists = os.path.exists(self._csv_path)
        with open(self._csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "label", "timestamp"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "path": frame_path,
                "label": label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    def load_all(self):
        if not os.path.exists(self._csv_path):
            return []
        with open(self._csv_path, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def labeled_paths(self):
        return {row["path"] for row in self.load_all()}
