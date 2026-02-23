"""Tests for thread-safe SSE event stream."""
import threading
import time


class TestEventStream:
    def test_push_and_pop(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        stream.push({"type": "fold", "garment": "shirt"})
        event = stream.pop(timeout=1.0)
        assert event["type"] == "fold"
        assert event["garment"] == "shirt"

    def test_pop_empty_returns_none(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        event = stream.pop(timeout=0.1)
        assert event is None

    def test_push_from_another_thread(self):
        from foldit.event_stream import EventStream
        stream = EventStream()

        def producer():
            time.sleep(0.05)
            stream.push({"type": "test"})

        t = threading.Thread(target=producer)
        t.start()
        event = stream.pop(timeout=2.0)
        t.join()
        assert event is not None
        assert event["type"] == "test"

    def test_multiple_events_fifo(self):
        from foldit.event_stream import EventStream
        stream = EventStream()
        stream.push({"seq": 1})
        stream.push({"seq": 2})
        stream.push({"seq": 3})
        assert stream.pop(timeout=0.1)["seq"] == 1
        assert stream.pop(timeout=0.1)["seq"] == 2
        assert stream.pop(timeout=0.1)["seq"] == 3
