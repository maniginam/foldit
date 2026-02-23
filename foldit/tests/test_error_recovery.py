"""Tests for error recovery handlers."""
import numpy as np


class FakeCameraRestarting:
    def __init__(self, fail_count=1):
        self._fail_count = fail_count
        self._calls = 0
        self.restarts = 0

    def start(self):
        self.restarts += 1

    def capture_frame(self):
        self._calls += 1
        if self._calls <= self._fail_count:
            raise RuntimeError("camera disconnected")
        return np.full((480, 640, 3), 200, dtype=np.uint8)

    def stop(self):
        pass


class FakeConveyorRetrying:
    def __init__(self, fail_count=1):
        self._fail_count = fail_count
        self._calls = 0

    def advance_to_fold_zone(self, timeout_sec=10.0):
        self._calls += 1
        return self._calls > self._fail_count


class TestErrorRecovery:
    def test_camera_restart_on_exception(self):
        from foldit.error_recovery import ErrorRecovery
        camera = FakeCameraRestarting(fail_count=1)
        recovery = ErrorRecovery()
        frame = recovery.safe_capture(camera)
        assert frame is not None
        assert camera.restarts >= 1

    def test_camera_gives_up_after_max_retries(self):
        from foldit.error_recovery import ErrorRecovery
        camera = FakeCameraRestarting(fail_count=10)
        recovery = ErrorRecovery(max_retries=1)
        frame = recovery.safe_capture(camera)
        assert frame is None

    def test_conveyor_retry_on_first_timeout(self):
        from foldit.error_recovery import ErrorRecovery
        conveyor = FakeConveyorRetrying(fail_count=1)
        recovery = ErrorRecovery()
        result = recovery.safe_advance(conveyor)
        assert result is True

    def test_conveyor_gives_up_after_max_retries(self):
        from foldit.error_recovery import ErrorRecovery
        conveyor = FakeConveyorRetrying(fail_count=10)
        recovery = ErrorRecovery(max_retries=1)
        result = recovery.safe_advance(conveyor)
        assert result is False

    def test_max_one_retry_default(self):
        from foldit.error_recovery import ErrorRecovery
        recovery = ErrorRecovery()
        assert recovery.max_retries == 1

    def test_records_errors(self):
        from foldit.error_recovery import ErrorRecovery
        camera = FakeCameraRestarting(fail_count=1)
        recovery = ErrorRecovery()
        recovery.safe_capture(camera)
        assert len(recovery.errors) >= 1
        assert "camera" in recovery.errors[0]["component"]

    def test_robot_state_transitions(self):
        from foldit.error_recovery import RobotState
        assert RobotState.IDLE != RobotState.ERROR
        assert RobotState.RECOVERING != RobotState.FOLDING
