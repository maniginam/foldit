"""Tests for graceful signal handling."""


class FakeRobotForSignal:
    def __init__(self):
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True


class TestSignalHandler:
    def test_sets_stop_flag_on_robot(self):
        from foldit.signal_handler import SignalHandler
        robot = FakeRobotForSignal()
        handler = SignalHandler(robot)
        handler.handle(None, None)
        assert robot._stop_requested is True

    def test_multiple_signals_are_safe(self):
        from foldit.signal_handler import SignalHandler
        robot = FakeRobotForSignal()
        handler = SignalHandler(robot)
        handler.handle(None, None)
        handler.handle(None, None)
        assert robot._stop_requested is True
