"""Error recovery handlers for the robot pipeline."""
from enum import Enum


class RobotState(Enum):
    IDLE = "idle"
    ADVANCING = "advancing"
    DETECTING = "detecting"
    FOLDING = "folding"
    VERIFYING = "verifying"
    ERROR = "error"
    RECOVERING = "recovering"


class ErrorRecovery:
    """Provides retry logic for recoverable pipeline failures."""

    def __init__(self, max_retries=1):
        self._max_retries = max_retries
        self._errors = []

    @property
    def max_retries(self):
        return self._max_retries

    @property
    def errors(self):
        return list(self._errors)

    def safe_capture(self, camera):
        for attempt in range(self._max_retries + 1):
            try:
                return camera.capture_frame()
            except Exception as e:
                self._errors.append({
                    "component": "camera",
                    "error": str(e),
                    "attempt": attempt + 1,
                })
                if attempt < self._max_retries:
                    try:
                        camera.stop()
                        camera.start()
                    except Exception:
                        pass
        return None

    def safe_advance(self, conveyor, timeout_sec=10.0):
        for attempt in range(self._max_retries + 1):
            result = conveyor.advance_to_fold_zone(timeout_sec=timeout_sec)
            if result:
                return True
            self._errors.append({
                "component": "conveyor",
                "error": "timeout",
                "attempt": attempt + 1,
            })
        return False
