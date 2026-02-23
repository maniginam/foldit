"""Tests for structured logging and metrics collection."""
import json
import logging


class TestRobotLogger:
    def test_creates_logger_with_name(self):
        from foldit.robot_logger import RobotLogger
        logger = RobotLogger(name="test")
        assert logger.name == "test"

    def test_log_event_writes_json(self):
        from foldit.robot_logger import RobotLogger
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = RobotLogger(name="test_json", handlers=[handler])
        logger.log_event("fold_complete", garment="shirt", cycle_sec=8.2)
        output = stream.getvalue()
        data = json.loads(output.strip())
        assert data["event"] == "fold_complete"
        assert data["garment"] == "shirt"
        assert data["cycle_sec"] == 8.2
        assert "ts" in data

    def test_log_event_includes_level(self):
        from foldit.robot_logger import RobotLogger
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = RobotLogger(name="test_level", handlers=[handler])
        logger.log_event("error", level="ERROR", message="camera failed")
        output = stream.getvalue()
        data = json.loads(output.strip())
        assert data["level"] == "ERROR"

    def test_default_level_is_info(self):
        from foldit.robot_logger import RobotLogger
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = RobotLogger(name="test_default_level", handlers=[handler])
        logger.log_event("test")
        data = json.loads(stream.getvalue().strip())
        assert data["level"] == "INFO"


class TestMetricsCollector:
    def test_initial_counts_are_zero(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        assert metrics.total_folds == 0
        assert metrics.success_count == 0

    def test_record_fold_increments_count(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        assert metrics.total_folds == 1
        assert metrics.success_count == 1

    def test_record_fold_tracks_by_type(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        metrics.record_fold("pants", success=True, cycle_sec=6.0)
        metrics.record_fold("shirt", success=True, cycle_sec=4.0)
        assert metrics.counts_by_type == {"shirt": 2, "pants": 1}

    def test_success_rate(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        metrics.record_fold("pants", success=False, cycle_sec=6.0)
        assert metrics.success_rate == 0.5

    def test_success_rate_zero_when_empty(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        assert metrics.success_rate == 0.0

    def test_average_cycle_time(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=4.0)
        metrics.record_fold("shirt", success=True, cycle_sec=6.0)
        assert metrics.avg_cycle_sec == 5.0

    def test_snapshot_returns_dict(self):
        from foldit.robot_logger import MetricsCollector
        metrics = MetricsCollector()
        metrics.record_fold("shirt", success=True, cycle_sec=5.0)
        snap = metrics.snapshot()
        assert snap["total_folds"] == 1
        assert snap["success_rate"] == 1.0
        assert snap["counts_by_type"] == {"shirt": 1}
        assert snap["avg_cycle_sec"] == 5.0
