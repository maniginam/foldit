"""Graceful shutdown via SIGINT/SIGTERM signal handling."""
import signal


class SignalHandler:
    """Registers signal handlers that stop the robot gracefully."""

    def __init__(self, robot):
        self._robot = robot

    def register(self):
        signal.signal(signal.SIGINT, self.handle)
        signal.signal(signal.SIGTERM, self.handle)

    def handle(self, signum, frame):
        self._robot.stop()
