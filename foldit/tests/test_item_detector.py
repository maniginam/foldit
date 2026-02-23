"""Tests for multi-item detection."""
import numpy as np
import cv2


def _make_binary_with_items(item_rects):
    binary = np.zeros((480, 640), dtype=np.uint8)
    for (x, y, w, h) in item_rects:
        binary[y:y+h, x:x+w] = 255
    return binary


class TestItemDetector:
    def test_single_item_returns_one(self):
        from foldit.item_detector import ItemDetector
        detector = ItemDetector(min_area=1000)
        binary = _make_binary_with_items([(100, 100, 200, 150)])
        result = detector.detect(binary)
        assert result.count == 1
        assert result.is_single is True
        assert result.largest is not None

    def test_multiple_items_detected(self):
        from foldit.item_detector import ItemDetector
        detector = ItemDetector(min_area=1000)
        binary = _make_binary_with_items([
            (50, 50, 150, 100),
            (350, 300, 200, 120)
        ])
        result = detector.detect(binary)
        assert result.count == 2
        assert result.is_single is False

    def test_no_items_returns_zero(self):
        from foldit.item_detector import ItemDetector
        detector = ItemDetector(min_area=1000)
        binary = np.zeros((480, 640), dtype=np.uint8)
        result = detector.detect(binary)
        assert result.count == 0
        assert result.is_single is False
        assert result.largest is None

    def test_small_items_filtered_out(self):
        from foldit.item_detector import ItemDetector
        detector = ItemDetector(min_area=5000)
        binary = _make_binary_with_items([
            (100, 100, 200, 150),
            (400, 400, 10, 10)
        ])
        result = detector.detect(binary)
        assert result.count == 1

    def test_largest_is_biggest_contour(self):
        from foldit.item_detector import ItemDetector
        detector = ItemDetector(min_area=1000)
        binary = _make_binary_with_items([
            (50, 50, 100, 80),
            (300, 200, 200, 150)
        ])
        result = detector.detect(binary)
        _, _, w, h = cv2.boundingRect(result.largest)
        assert w * h >= 20000
