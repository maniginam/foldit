"""Thread-safe event stream for SSE dashboard updates."""
import queue


class EventStream:
    """Thread-safe FIFO queue for pushing events from the robot to SSE clients."""

    def __init__(self):
        self._queue = queue.Queue()

    def push(self, event):
        self._queue.put(event)

    def pop(self, timeout=1.0):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
