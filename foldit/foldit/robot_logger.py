"""Structured JSON logging and metrics collection for FoldIt robot."""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record):
        return record.getMessage()


class RobotLogger:
    """Structured event logger emitting JSON lines."""

    def __init__(self, name="foldit", handlers=None):
        self._name = name
        self._logger = logging.getLogger(f"foldit.{name}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False
        if handlers:
            for h in handlers:
                h.setFormatter(JsonFormatter())
                self._logger.addHandler(h)

    @property
    def name(self):
        return self._name

    def log_event(self, event, level="INFO", **kwargs):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
        }
        entry.update(kwargs)
        log_level = getattr(logging, level, logging.INFO)
        self._logger.log(log_level, json.dumps(entry))


class MetricsCollector:
    """Accumulates fold metrics for dashboard and logging."""

    def __init__(self):
        self._total = 0
        self._successes = 0
        self._by_type = {}
        self._cycle_times = []

    @property
    def total_folds(self):
        return self._total

    @property
    def success_count(self):
        return self._successes

    @property
    def counts_by_type(self):
        return dict(self._by_type)

    @property
    def success_rate(self):
        if self._total == 0:
            return 0.0
        return self._successes / self._total

    @property
    def avg_cycle_sec(self):
        if not self._cycle_times:
            return 0.0
        return sum(self._cycle_times) / len(self._cycle_times)

    def record_fold(self, garment_type, success, cycle_sec):
        self._total += 1
        if success:
            self._successes += 1
        self._by_type[garment_type] = self._by_type.get(garment_type, 0) + 1
        self._cycle_times.append(cycle_sec)

    def snapshot(self):
        return {
            "total_folds": self._total,
            "success_count": self._successes,
            "success_rate": self.success_rate,
            "counts_by_type": self.counts_by_type,
            "avg_cycle_sec": self.avg_cycle_sec,
        }
