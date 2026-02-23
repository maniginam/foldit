"""ML-based garment classifier using MobileNetV2 + TFLite."""
import cv2
import numpy as np
from dataclasses import dataclass
from foldit.config import GarmentType


CLASS_LABELS = [
    GarmentType.SHIRT,
    GarmentType.PANTS,
    GarmentType.TOWEL,
    GarmentType.SMALL,
    GarmentType.UNKNOWN,
]


@dataclass
class ClassificationResult:
    garment_type: str
    confidence: float
    probabilities: dict


class MLClassifier:
    """Classifies garments using a TFLite MobileNetV2 model."""

    def __init__(self, interpreter, confidence_threshold=0.5):
        self._interpreter = interpreter
        self._interpreter.allocate_tensors()
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()
        self._confidence_threshold = confidence_threshold

    def classify_frame(self, frame):
        input_data = self._prepare_input(frame)
        self._interpreter.set_tensor(self._input_details[0]["index"], input_data)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_details[0]["index"])
        return self._interpret_output(output[0])

    def _prepare_input(self, frame):
        resized = cv2.resize(frame, (224, 224))
        normalized = resized.astype(np.float32) / 255.0
        return np.expand_dims(normalized, axis=0)

    def _interpret_output(self, probabilities):
        probs = {label: float(prob) for label, prob in zip(CLASS_LABELS, probabilities)}
        best_idx = int(np.argmax(probabilities))
        best_confidence = float(probabilities[best_idx])
        if best_confidence < self._confidence_threshold:
            return ClassificationResult(
                garment_type=GarmentType.UNKNOWN,
                confidence=best_confidence,
                probabilities=probs
            )
        return ClassificationResult(
            garment_type=CLASS_LABELS[best_idx],
            confidence=best_confidence,
            probabilities=probs
        )


class HybridClassifier:
    """Tries ML classification first, falls back to heuristic."""

    def __init__(self, ml_classifier, heuristic_classifier):
        self._ml = ml_classifier
        self._heuristic = heuristic_classifier

    def classify(self, contour, frame=None):
        if frame is not None:
            try:
                result = self._ml.classify_frame(frame)
                if result.garment_type != GarmentType.UNKNOWN:
                    return result.garment_type
            except Exception:
                pass
        return self._heuristic.classify(contour)
