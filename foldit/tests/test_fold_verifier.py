"""Tests for post-fold quality verification."""
import numpy as np


class FakeCameraForVerifier:
    def __init__(self, frame):
        self._frame = frame

    def capture_frame(self):
        return self._frame


class TestFoldVerifier:
    def _make_compact_frame(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[150:330, 200:440] = [200, 200, 200]
        return frame

    def _make_messy_frame(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:400, 100:160] = [200, 200, 200]
        frame[340:400, 100:400] = [200, 200, 200]
        return frame

    def test_compact_fold_passes(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        camera = FakeCameraForVerifier(self._make_compact_frame())
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.5)
        result = verifier.verify("shirt")
        assert result.success is True

    def test_messy_fold_fails(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        camera = FakeCameraForVerifier(self._make_messy_frame())
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.95)
        result = verifier.verify("shirt")
        assert result.success is False

    def test_result_includes_compactness(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        camera = FakeCameraForVerifier(self._make_compact_frame())
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.5)
        result = verifier.verify("shirt")
        assert 0.0 <= result.compactness <= 1.0

    def test_no_contour_fails(self):
        from foldit.fold_verifier import FoldVerifier
        from foldit.camera import ImagePreprocessor
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        camera = FakeCameraForVerifier(blank)
        verifier = FoldVerifier(camera, ImagePreprocessor(), min_compactness=0.5)
        result = verifier.verify("shirt")
        assert result.success is False
        assert result.compactness == 0.0
