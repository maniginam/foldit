"""Tests for ML-based garment classifier."""
import numpy as np


class FakeTFLiteInterpreter:
    def __init__(self, model_path):
        self.model_path = model_path
        self._input_details = [{"index": 0, "shape": [1, 224, 224, 3]}]
        self._output_details = [{"index": 1}]
        self._output_data = np.array([[0.1, 0.7, 0.05, 0.1, 0.05]])
        self._input_tensor = None

    def allocate_tensors(self):
        pass

    def get_input_details(self):
        return self._input_details

    def get_output_details(self):
        return self._output_details

    def set_tensor(self, index, data):
        self._input_tensor = data

    def invoke(self):
        pass

    def get_tensor(self, index):
        return self._output_data


class TestMLClassifier:
    def test_classify_returns_highest_confidence_class(self):
        from foldit.ml_classifier import MLClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        classifier = MLClassifier(interp)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = classifier.classify_frame(frame)
        assert result.garment_type == "pants"
        assert result.confidence > 0.5

    def test_classify_low_confidence_returns_unknown(self):
        from foldit.ml_classifier import MLClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        interp._output_data = np.array([[0.2, 0.2, 0.2, 0.2, 0.2]])
        classifier = MLClassifier(interp, confidence_threshold=0.5)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = classifier.classify_frame(frame)
        assert result.garment_type == "unknown"

    def test_classify_returns_all_probabilities(self):
        from foldit.ml_classifier import MLClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        classifier = MLClassifier(interp)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = classifier.classify_frame(frame)
        assert len(result.probabilities) == 5

    def test_input_resized_to_224x224(self):
        from foldit.ml_classifier import MLClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        classifier = MLClassifier(interp)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        classifier.classify_frame(frame)
        assert interp._input_tensor.shape == (1, 224, 224, 3)


class TestHybridClassifier:
    def test_uses_ml_when_confident(self):
        from foldit.ml_classifier import MLClassifier, HybridClassifier
        from foldit.classifier import GarmentClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        interp._output_data = np.array([[0.05, 0.85, 0.03, 0.05, 0.02]])
        ml = MLClassifier(interp, confidence_threshold=0.5)
        heuristic = GarmentClassifier()
        hybrid = HybridClassifier(ml, heuristic)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        contour = np.array([[[100,100]],[[500,100]],[[500,400]],[[100,400]]], dtype=np.int32)
        result = hybrid.classify(contour, frame=frame)
        assert result == "pants"

    def test_falls_back_to_heuristic_when_not_confident(self):
        from foldit.ml_classifier import MLClassifier, HybridClassifier
        from foldit.classifier import GarmentClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        interp._output_data = np.array([[0.2, 0.2, 0.2, 0.2, 0.2]])
        ml = MLClassifier(interp, confidence_threshold=0.5)
        heuristic = GarmentClassifier()
        hybrid = HybridClassifier(ml, heuristic)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        result = hybrid.classify(contour, frame=frame)
        assert result == "shirt"

    def test_falls_back_when_ml_raises(self):
        from foldit.ml_classifier import MLClassifier, HybridClassifier
        from foldit.classifier import GarmentClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        ml = MLClassifier(interp)
        heuristic = GarmentClassifier()
        hybrid = HybridClassifier(ml, heuristic)
        interp.invoke = lambda: (_ for _ in ()).throw(RuntimeError("model error"))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        result = hybrid.classify(contour, frame=frame)
        assert result == "shirt"
