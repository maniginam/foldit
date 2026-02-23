"""Tests for SQLite metrics persistence."""
import os
import tempfile


class TestMetricsStore:
    def test_record_and_query_recent(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.85, 12.3)
            store.record("pants", False, 7.0, 0.40, -5.0)
            rows = store.query_recent(minutes=60)
            assert len(rows) == 2
            assert rows[0]["garment_type"] == "shirt"
            assert rows[1]["success"] is False

    def test_summary_matches_snapshot_shape(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.85, 0.0)
            store.record("shirt", True, 6.0, 0.90, 0.0)
            store.record("pants", False, 8.0, 0.30, 0.0)
            summary = store.summary(minutes=60)
            assert summary["total_folds"] == 3
            assert summary["success_count"] == 2
            assert abs(summary["success_rate"] - 2 / 3) < 0.01
            assert summary["counts_by_type"] == {"shirt": 2, "pants": 1}
            assert abs(summary["avg_cycle_sec"] - 19.0 / 3) < 0.1

    def test_db_file_created_on_first_record(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            assert not os.path.exists(db_path)
            store = MetricsStore(db_path)
            store.record("shirt", True, 5.0, 0.8, 0.0)
            assert os.path.exists(db_path)

    def test_query_empty_returns_empty_list(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            rows = store.query_recent(minutes=60)
            assert rows == []

    def test_summary_empty_returns_zeros(self):
        from foldit.metrics_store import MetricsStore
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "metrics.db")
            store = MetricsStore(db_path)
            summary = store.summary(minutes=60)
            assert summary["total_folds"] == 0
            assert summary["success_rate"] == 0.0
