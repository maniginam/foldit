"""Failure pattern alerting for the robot pipeline."""
from collections import deque
from dataclasses import dataclass


@dataclass
class Alert:
    rule: str
    message: str


class Alerter:
    """Monitors fold outcomes and raises alerts on failure patterns."""

    def __init__(self, consecutive_fail_threshold=3, rate_window=20, min_success_rate=0.5):
        self._consec_threshold = consecutive_fail_threshold
        self._rate_window = rate_window
        self._min_rate = min_success_rate
        self._consecutive_failures = 0
        self._recent = deque(maxlen=rate_window)

    def check(self, garment_type, success):
        self._recent.append(success)

        if success:
            self._consecutive_failures = 0
            return None

        self._consecutive_failures += 1

        if len(self._recent) >= self._rate_window:
            rate = sum(self._recent) / len(self._recent)
            if rate < self._min_rate:
                return Alert(
                    rule="low_success_rate",
                    message=f"Success rate {rate:.0%} below {self._min_rate:.0%} threshold",
                )

        if self._consecutive_failures >= self._consec_threshold:
            return Alert(
                rule="consecutive_failures",
                message=f"{self._consecutive_failures} consecutive fold failures",
            )

        return None
