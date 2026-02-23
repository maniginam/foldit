# FoldIt v2 — Intelligent Separation & Classification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add conveyor-based garment separation, ML classification, adaptive thresholding, wrinkle handling, and multi-item detection to the FoldIt robot.

**Architecture:** Five independent modules that plug into the existing pipeline. Each new module follows the existing DIP pattern (abstractions first, then implementations). The main loop is updated to orchestrate the full flow: conveyor feeds garment → adaptive preprocessing detects it → multi-item check → flatness check → ML classification → fold.

**Tech Stack:** Python 3.11+, OpenCV, TensorFlow Lite (tflite-runtime), RPi.GPIO, existing foldit package

---

### Task 1: Adaptive Thresholding

**Files:**
- Modify: `foldit/foldit/camera.py`
- Modify: `foldit/tests/test_camera.py`

**Step 1: Write failing tests**

Add to `foldit/tests/test_camera.py`:

```python
class TestAdaptivePreprocessor:
    def test_capture_background_stores_frame(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 100, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        assert proc._background is not None
        assert proc._background.shape == (480, 640)

    def test_subtract_background_isolates_foreground(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 100, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        frame[200:300, 200:400] = 200  # garment region
        result = proc.subtract_background(frame)
        assert result[250, 300] > 0   # garment area is non-zero
        assert result[0, 0] == 0       # background area is zero

    def test_adaptive_threshold_returns_binary(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.zeros((480, 640, 3), dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        gray = np.full((480, 640), 128, dtype=np.uint8)
        binary = proc.adaptive_threshold(gray)
        unique = np.unique(binary)
        assert all(v in (0, 255) for v in unique)

    def test_preprocess_full_pipeline(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 50, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        frame = np.full((480, 640, 3), 50, dtype=np.uint8)
        frame[100:300, 100:400] = 200  # garment
        contour = proc.preprocess(frame)
        assert contour is not None

    def test_preprocess_no_garment_returns_none(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.full((480, 640, 3), 100, dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)  # same as bg
        contour = proc.preprocess(frame)
        assert contour is None

    def test_find_all_contours_returns_list(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.zeros((480, 640, 3), dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        binary = np.zeros((480, 640), dtype=np.uint8)
        binary[50:150, 50:150] = 255
        binary[300:400, 300:450] = 255
        contours = proc.find_all_contours(binary, min_area=1000)
        assert len(contours) == 2

    def test_find_all_contours_filters_small(self):
        from foldit.camera import AdaptivePreprocessor
        bg = np.zeros((480, 640, 3), dtype=np.uint8)
        proc = AdaptivePreprocessor(bg)
        binary = np.zeros((480, 640), dtype=np.uint8)
        binary[50:150, 50:150] = 255    # large: 10000 px
        binary[300:310, 300:310] = 255   # small: 100 px
        contours = proc.find_all_contours(binary, min_area=1000)
        assert len(contours) == 1
```

**Step 2: Run tests to verify failure**

Run: `cd /Users/maniginam/projects/foldit/foldit && source .venv/bin/activate && python -m pytest tests/test_camera.py::TestAdaptivePreprocessor -v`
Expected: FAIL — `cannot import name 'AdaptivePreprocessor'`

**Step 3: Write implementation**

Add to `foldit/foldit/camera.py`:

```python
class AdaptivePreprocessor:
    """Adaptive image preprocessing with background subtraction."""

    def __init__(self, background_frame):
        self._background = cv2.cvtColor(background_frame, cv2.COLOR_BGR2GRAY)

    def subtract_background(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray, self._background)
        _, mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        return mask

    def adaptive_threshold(self, gray_image):
        return cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

    def preprocess(self, frame):
        mask = self.subtract_background(frame)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)

    def find_all_contours(self, binary_image, min_area=5000):
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) >= min_area]
```

**Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_camera.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/camera.py foldit/tests/test_camera.py
git commit -m "feat: adaptive preprocessor with background subtraction"
```

---

### Task 2: Multi-Item Detection

**Files:**
- Create: `foldit/foldit/item_detector.py`
- Create: `foldit/tests/test_item_detector.py`

**Step 1: Write failing tests**

```python
"""Tests for multi-item detection."""
import numpy as np
import cv2


def _make_binary_with_items(item_rects):
    """Create a binary image with white rectangles at given positions."""
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
            (100, 100, 200, 150),  # 30000 px - above threshold
            (400, 400, 10, 10)     # 100 px - below threshold
        ])
        result = detector.detect(binary)
        assert result.count == 1

    def test_largest_is_biggest_contour(self):
        from foldit.item_detector import ItemDetector
        detector = ItemDetector(min_area=1000)
        binary = _make_binary_with_items([
            (50, 50, 100, 80),     # 8000 px
            (300, 200, 200, 150)   # 30000 px - largest
        ])
        result = detector.detect(binary)
        _, _, w, h = cv2.boundingRect(result.largest)
        assert w * h >= 20000  # the larger item
```

**Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_item_detector.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

```python
"""Multi-item detection for the folding platform."""
import cv2
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class DetectionResult:
    """Result of item detection on the platform."""
    count: int
    largest: Optional[np.ndarray]
    all_contours: list

    @property
    def is_single(self):
        return self.count == 1


class ItemDetector:
    """Detects and counts garments on the platform."""

    def __init__(self, min_area=5000):
        self._min_area = min_area

    def detect(self, binary_image):
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        valid = [c for c in contours if cv2.contourArea(c) >= self._min_area]
        largest = max(valid, key=cv2.contourArea) if valid else None
        return DetectionResult(
            count=len(valid),
            largest=largest,
            all_contours=valid
        )
```

**Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_item_detector.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/item_detector.py foldit/tests/test_item_detector.py
git commit -m "feat: multi-item detection with count and largest contour"
```

---

### Task 3: Wrinkle / Flatness Detection

**Files:**
- Create: `foldit/foldit/flatness.py`
- Create: `foldit/tests/test_flatness.py`

**Step 1: Write failing tests**

```python
"""Tests for wrinkle/flatness detection."""
import numpy as np
import cv2


class TestFlatnessChecker:
    def test_perfect_rectangle_is_flat(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        # Perfect rectangle has solidity ~1.0
        contour = np.array([
            [[100, 100]], [[400, 100]], [[400, 300]], [[100, 300]]
        ], dtype=np.int32)
        assert checker.is_flat(contour) is True

    def test_solidity_of_rectangle_near_one(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        contour = np.array([
            [[100, 100]], [[400, 100]], [[400, 300]], [[100, 300]]
        ], dtype=np.int32)
        solidity = checker.compute_solidity(contour)
        assert solidity > 0.95

    def test_irregular_shape_is_not_flat(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        # Star-like shape has low solidity
        contour = np.array([
            [[200, 50]], [[220, 150]], [[300, 150]],
            [[240, 210]], [[260, 300]], [[200, 240]],
            [[140, 300]], [[160, 210]], [[100, 150]],
            [[180, 150]]
        ], dtype=np.int32)
        assert checker.is_flat(contour) is False

    def test_none_contour_is_not_flat(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.75)
        assert checker.is_flat(None) is False

    def test_custom_threshold(self):
        from foldit.flatness import FlatnessChecker
        checker = FlatnessChecker(threshold=0.99)
        # Rectangle has solidity ~1.0 but not exactly 0.99+
        contour = np.array([
            [[100, 100]], [[400, 100]], [[400, 300]], [[100, 300]]
        ], dtype=np.int32)
        # With very high threshold, even a good rectangle might still pass
        solidity = checker.compute_solidity(contour)
        assert isinstance(solidity, float)
```

**Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_flatness.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

```python
"""Wrinkle/flatness detection for garments on the platform."""
import cv2


class FlatnessChecker:
    """Checks if a garment contour appears flat (well-spread) or bunched up."""

    def __init__(self, threshold=0.75):
        self._threshold = threshold

    def compute_solidity(self, contour):
        area = cv2.contourArea(contour)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            return 0.0
        return area / hull_area

    def is_flat(self, contour):
        if contour is None:
            return False
        solidity = self.compute_solidity(contour)
        return solidity >= self._threshold
```

**Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_flatness.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/flatness.py foldit/tests/test_flatness.py
git commit -m "feat: flatness checker using contour solidity"
```

---

### Task 4: ML Classification (MobileNetV2 + TFLite)

**Files:**
- Create: `foldit/foldit/ml_classifier.py`
- Create: `foldit/tests/test_ml_classifier.py`
- Create: `foldit/training/train_model.py`
- Create: `foldit/training/README.md`

**Step 1: Write failing tests**

```python
"""Tests for ML-based garment classifier."""
import numpy as np


class FakeTFLiteInterpreter:
    """Test double for tflite_runtime.interpreter.Interpreter."""

    def __init__(self, model_path):
        self.model_path = model_path
        self._input_details = [{"index": 0, "shape": [1, 224, 224, 3]}]
        self._output_details = [{"index": 1}]
        self._output_data = np.array([[0.1, 0.7, 0.05, 0.1, 0.05]])  # pants=0.7

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
        interp._output_data = np.array([[0.2, 0.2, 0.2, 0.2, 0.2]])  # all low
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
        result = hybrid.classify(frame, contour)
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
        # Wide contour -> heuristic says shirt
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        result = hybrid.classify(frame, contour)
        assert result == "shirt"

    def test_falls_back_when_ml_raises(self):
        from foldit.ml_classifier import MLClassifier, HybridClassifier
        from foldit.classifier import GarmentClassifier
        interp = FakeTFLiteInterpreter("model.tflite")
        ml = MLClassifier(interp)
        heuristic = GarmentClassifier()
        hybrid = HybridClassifier(ml, heuristic)
        # Cause ML to fail by corrupting interpreter
        interp.invoke = lambda: (_ for _ in ()).throw(RuntimeError("model error"))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        contour = np.array([[[100,100]],[[500,100]],[[500,300]],[[100,300]]], dtype=np.int32)
        result = hybrid.classify(frame, contour)
        assert result == "shirt"  # heuristic fallback
```

**Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_ml_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

```python
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

    def classify(self, frame, contour):
        try:
            result = self._ml.classify_frame(frame)
            if result.garment_type != GarmentType.UNKNOWN:
                return result.garment_type
        except Exception:
            pass
        return self._heuristic.classify(contour)
```

**Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_ml_classifier.py -v`
Expected: All 7 tests PASS

**Step 5: Create training script and README**

Create `foldit/training/train_model.py`:

```python
"""Training script for garment classification model.

Run on a desktop/laptop with TensorFlow installed (not on RPi).

Usage:
    python train_model.py --data_dir ./dataset --output model.tflite

Dataset structure:
    dataset/
        shirt/
            img001.jpg
            img002.jpg
        pants/
            img001.jpg
        towel/
            img001.jpg
        small/
            img001.jpg
        unknown/
            img001.jpg
"""
import argparse
import os


def create_parser():
    parser = argparse.ArgumentParser(description="Train garment classifier")
    parser.add_argument("--data_dir", required=True, help="Path to dataset directory")
    parser.add_argument("--output", default="model.tflite", help="Output .tflite file")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    return parser


def train(data_dir, output_path, epochs, batch_size):
    """Train MobileNetV2 with transfer learning and export to TFLite.

    Requires: pip install tensorflow

    Steps:
    1. Load MobileNetV2 pre-trained on ImageNet (exclude top layers)
    2. Add classification head: GlobalAveragePooling2D -> Dense(5, softmax)
    3. Freeze base model, train head for `epochs`
    4. Convert to TFLite and save
    """
    try:
        import tensorflow as tf
    except ImportError:
        print("ERROR: TensorFlow required. Install with: pip install tensorflow")
        print("This script runs on desktop/laptop, NOT on Raspberry Pi.")
        return

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(5, activation="softmax")
    ])

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
        horizontal_flip=True,
        rotation_range=15
    )

    train_gen = datagen.flow_from_directory(
        data_dir, target_size=(224, 224),
        batch_size=batch_size, class_mode="categorical", subset="training"
    )
    val_gen = datagen.flow_from_directory(
        data_dir, target_size=(224, 224),
        batch_size=batch_size, class_mode="categorical", subset="validation"
    )

    model.fit(train_gen, validation_data=val_gen, epochs=epochs)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(output_path, "wb") as f:
        f.write(tflite_model)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    train(args.data_dir, args.output, args.epochs, args.batch_size)
```

Create `foldit/training/README.md`:

```markdown
# Training the Garment Classifier

## Prerequisites
- Desktop/laptop with TensorFlow 2.x installed (`pip install tensorflow`)
- A dataset of garment images organized by category

## Dataset Structure
```
dataset/
    shirt/      (100+ images)
    pants/      (100+ images)
    towel/      (100+ images)
    small/      (100+ images, socks/underwear)
    unknown/    (100+ images, misc items)
```

## Collecting Training Data
Use the calibration camera tool to capture images on the actual platform:
```bash
python -m foldit.calibration camera
```
Then manually sort images into category folders.

## Training
```bash
python train_model.py --data_dir ./dataset --output model.tflite --epochs 10
```

## Deploying to Raspberry Pi
Copy `model.tflite` to `/opt/foldit/model.tflite` on the Pi.
The robot loads it automatically if present, otherwise falls back to heuristic classification.
```

**Step 6: Commit**

```bash
git add foldit/foldit/ml_classifier.py foldit/tests/test_ml_classifier.py foldit/training/
git commit -m "feat: ML classifier with MobileNetV2 TFLite and hybrid fallback"
```

---

### Task 5: Conveyor Controller

**Files:**
- Create: `foldit/foldit/conveyor.py`
- Create: `foldit/tests/test_conveyor.py`
- Modify: `foldit/foldit/config.py`

**Step 1: Add conveyor config**

Add to `foldit/foldit/config.py`:

```python
class ConveyorConfig:
    """Conveyor belt motor and sensor settings."""
    MOTOR_PIN_A = 23       # L298N IN1
    MOTOR_PIN_B = 24       # L298N IN2
    MOTOR_ENABLE_PIN = 25  # L298N ENA (PWM speed)
    TRIGGER_PIN = 5        # HC-SR04 trigger
    ECHO_PIN = 6           # HC-SR04 echo
    DETECTION_DISTANCE_CM = 10.0  # garment detected if closer than this
    BELT_SPEED_DUTY = 75   # PWM duty cycle for belt motor (0-100)
    SETTLE_TIME_SEC = 0.5  # wait after stopping belt for garment to settle
```

**Step 2: Write failing tests**

```python
"""Tests for conveyor controller."""
import time


class FakeGPIOForConveyor:
    BCM = 11
    OUT = 0
    IN = 1

    def __init__(self):
        self.setup_calls = []
        self.output_calls = []
        self.setmode_called = False
        self.pwm_instances = {}

    def setmode(self, mode):
        self.setmode_called = True

    def setup(self, pin, mode):
        self.setup_calls.append((pin, mode))

    def output(self, pin, value):
        self.output_calls.append((pin, value))

    def cleanup(self):
        pass

    def PWM(self, pin, freq):
        pwm = FakeConveyorPWM(pin, freq)
        self.pwm_instances[pin] = pwm
        return pwm


class FakeConveyorPWM:
    def __init__(self, pin, freq):
        self.pin = pin
        self.duty = 0
        self.started = False

    def start(self, duty):
        self.started = True
        self.duty = duty

    def ChangeDutyCycle(self, duty):
        self.duty = duty

    def stop(self):
        self.started = False


class FakeDistanceSensor:
    def __init__(self, distances):
        self._distances = distances
        self._index = 0

    def measure(self):
        if self._index < len(self._distances):
            d = self._distances[self._index]
            self._index += 1
            return d
        return 999.0


class TestConveyorMotor:
    def test_forward_sets_pins(self):
        from foldit.conveyor import ConveyorMotor
        gpio = FakeGPIOForConveyor()
        motor = ConveyorMotor(gpio, pin_a=23, pin_b=24, enable_pin=25)
        motor.forward(75)
        assert (23, 1) in gpio.output_calls
        assert (24, 0) in gpio.output_calls
        assert gpio.pwm_instances[25].duty == 75

    def test_stop_sets_pins_low(self):
        from foldit.conveyor import ConveyorMotor
        gpio = FakeGPIOForConveyor()
        motor = ConveyorMotor(gpio, pin_a=23, pin_b=24, enable_pin=25)
        motor.forward(75)
        motor.stop()
        # Last output calls should be stop (both low)
        assert (23, 0) in gpio.output_calls
        assert (24, 0) in gpio.output_calls
        assert gpio.pwm_instances[25].duty == 0


class TestUltrasonicSensor:
    def test_read_distance_returns_float(self):
        from foldit.conveyor import UltrasonicSensor
        sensor = UltrasonicSensor(measure_fn=lambda: 15.5)
        assert sensor.read_distance() == 15.5

    def test_object_detected_within_threshold(self):
        from foldit.conveyor import UltrasonicSensor
        sensor = UltrasonicSensor(measure_fn=lambda: 5.0)
        assert sensor.is_object_present(threshold_cm=10.0) is True

    def test_object_not_detected_beyond_threshold(self):
        from foldit.conveyor import UltrasonicSensor
        sensor = UltrasonicSensor(measure_fn=lambda: 25.0)
        assert sensor.is_object_present(threshold_cm=10.0) is False


class TestConveyorController:
    def test_advance_starts_motor(self):
        from foldit.conveyor import ConveyorController, ConveyorMotor, UltrasonicSensor
        gpio = FakeGPIOForConveyor()
        motor = ConveyorMotor(gpio, pin_a=23, pin_b=24, enable_pin=25)
        sensor = UltrasonicSensor(measure_fn=lambda: 5.0)  # immediately detected
        controller = ConveyorController(motor, sensor, detection_distance=10.0, speed=75)
        controller.advance_to_fold_zone(timeout_sec=1.0)
        assert gpio.pwm_instances[25].duty == 0  # motor stopped after detection

    def test_advance_timeout_stops_motor(self):
        from foldit.conveyor import ConveyorController, ConveyorMotor, UltrasonicSensor
        gpio = FakeGPIOForConveyor()
        motor = ConveyorMotor(gpio, pin_a=23, pin_b=24, enable_pin=25)
        sensor = UltrasonicSensor(measure_fn=lambda: 999.0)  # nothing detected
        controller = ConveyorController(motor, sensor, detection_distance=10.0, speed=75)
        result = controller.advance_to_fold_zone(timeout_sec=0.1)
        assert result is False
        assert gpio.pwm_instances[25].duty == 0

    def test_advance_returns_true_on_detection(self):
        from foldit.conveyor import ConveyorController, ConveyorMotor, UltrasonicSensor
        gpio = FakeGPIOForConveyor()
        motor = ConveyorMotor(gpio, pin_a=23, pin_b=24, enable_pin=25)
        sensor = UltrasonicSensor(measure_fn=lambda: 5.0)
        controller = ConveyorController(motor, sensor, detection_distance=10.0, speed=75)
        result = controller.advance_to_fold_zone(timeout_sec=1.0)
        assert result is True
```

**Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_conveyor.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

```python
"""Conveyor belt controller with ultrasonic garment detection."""
import time


class ConveyorMotor:
    """Controls the conveyor belt DC motor via L298N driver."""

    def __init__(self, gpio, pin_a, pin_b, enable_pin):
        self._gpio = gpio
        self._pin_a = pin_a
        self._pin_b = pin_b
        self._enable_pin = enable_pin
        self._gpio.setup(pin_a, self._gpio.OUT)
        self._gpio.setup(pin_b, self._gpio.OUT)
        self._gpio.setup(enable_pin, self._gpio.OUT)
        self._pwm = self._gpio.PWM(enable_pin, 1000)
        self._pwm.start(0)

    def forward(self, speed):
        self._gpio.output(self._pin_a, 1)
        self._gpio.output(self._pin_b, 0)
        self._pwm.ChangeDutyCycle(speed)

    def stop(self):
        self._gpio.output(self._pin_a, 0)
        self._gpio.output(self._pin_b, 0)
        self._pwm.ChangeDutyCycle(0)


class UltrasonicSensor:
    """Reads distance from an HC-SR04 ultrasonic sensor."""

    def __init__(self, measure_fn):
        self._measure = measure_fn

    def read_distance(self):
        return self._measure()

    def is_object_present(self, threshold_cm):
        return self.read_distance() < threshold_cm


class ConveyorController:
    """Orchestrates conveyor belt to feed garments to the fold zone."""

    def __init__(self, motor, sensor, detection_distance, speed):
        self._motor = motor
        self._sensor = sensor
        self._detection_distance = detection_distance
        self._speed = speed

    def advance_to_fold_zone(self, timeout_sec=10.0):
        self._motor.forward(self._speed)
        start = time.monotonic()
        try:
            while time.monotonic() - start < timeout_sec:
                if self._sensor.is_object_present(self._detection_distance):
                    self._motor.stop()
                    return True
                time.sleep(0.05)
        finally:
            self._motor.stop()
        return False
```

**Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_conveyor.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/conveyor.py foldit/tests/test_conveyor.py foldit/foldit/config.py
git commit -m "feat: conveyor controller with ultrasonic sensor and motor driver"
```

---

### Task 6: Updated Main Loop — Full v2 Pipeline

**Files:**
- Modify: `foldit/foldit/main.py`
- Modify: `foldit/tests/test_main.py`

**Step 1: Write failing tests**

Add to `foldit/tests/test_main.py`:

```python
class FakeFlatnessChecker:
    def __init__(self, flat=True):
        self._flat = flat

    def is_flat(self, contour):
        return self._flat


class FakeItemDetector:
    def __init__(self, count=1):
        self._count = count

    def detect(self, binary):
        from foldit.item_detector import DetectionResult
        if self._count == 0:
            return DetectionResult(count=0, largest=None, all_contours=[])
        contour = np.array([[[100,100]],[[500,100]],[[500,400]],[[100,400]]], dtype=np.int32)
        return DetectionResult(count=self._count, largest=contour, all_contours=[contour] * self._count)


class FakeConveyorController:
    def __init__(self, has_garment=True):
        self._has_garment = has_garment
        self.advance_called = False

    def advance_to_fold_zone(self, timeout_sec=10.0):
        self.advance_called = True
        return self._has_garment


class FakePlatformForFlatten:
    def __init__(self):
        self.actions = []

    def home(self):
        self.actions.append("home")

    def fold_left(self):
        self.actions.append("fold_left")

    def fold_right(self):
        self.actions.append("fold_right")

    def fold_bottom(self):
        self.actions.append("fold_bottom")


class TestFoldItRobotV2:
    def test_process_with_conveyor_advances_belt(self):
        from foldit.main import FoldItRobotV2
        frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        camera = FakeCamera(frames=[frame])
        contour = np.array([[[100,100]],[[500,100]],[[500,400]],[[100,400]]], dtype=np.int32)
        preprocessor = FakePreprocessor(contour=contour)
        classifier = FakeClassifier(results=["shirt"])
        sequencer = FakeSequencer()
        conveyor = FakeConveyorController(has_garment=True)
        detector = FakeItemDetector(count=1)
        flatness = FakeFlatnessChecker(flat=True)

        robot = FoldItRobotV2(
            camera=camera, preprocessor=preprocessor, classifier=classifier,
            sequencer=sequencer, conveyor=conveyor, item_detector=detector,
            flatness_checker=flatness
        )
        result = robot.process_one()
        assert conveyor.advance_called is True
        assert result == "shirt"

    def test_skips_when_multiple_items(self):
        from foldit.main import FoldItRobotV2
        frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        camera = FakeCamera(frames=[frame])
        contour = np.array([[[100,100]],[[500,100]],[[500,400]],[[100,400]]], dtype=np.int32)
        preprocessor = FakePreprocessor(contour=contour)
        classifier = FakeClassifier(results=["shirt"])
        sequencer = FakeSequencer()
        conveyor = FakeConveyorController(has_garment=True)
        detector = FakeItemDetector(count=3)  # multiple items!
        flatness = FakeFlatnessChecker(flat=True)

        robot = FoldItRobotV2(
            camera=camera, preprocessor=preprocessor, classifier=classifier,
            sequencer=sequencer, conveyor=conveyor, item_detector=detector,
            flatness_checker=flatness
        )
        result = robot.process_one()
        assert result is None  # rejected: multiple items
        assert sequencer.folded == []

    def test_conveyor_no_garment_returns_none(self):
        from foldit.main import FoldItRobotV2
        camera = FakeCamera(frames=[])
        preprocessor = FakePreprocessor(contour=None)
        classifier = FakeClassifier(results=[])
        sequencer = FakeSequencer()
        conveyor = FakeConveyorController(has_garment=False)
        detector = FakeItemDetector(count=0)
        flatness = FakeFlatnessChecker(flat=True)

        robot = FoldItRobotV2(
            camera=camera, preprocessor=preprocessor, classifier=classifier,
            sequencer=sequencer, conveyor=conveyor, item_detector=detector,
            flatness_checker=flatness
        )
        result = robot.process_one()
        assert result is None
```

**Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_main.py::TestFoldItRobotV2 -v`
Expected: FAIL — `cannot import name 'FoldItRobotV2'`

**Step 3: Write implementation**

Add to `foldit/foldit/main.py`:

```python
class FoldItRobotV2:
    """V2 pipeline: conveyor → detect → multi-check → flatten → classify → fold."""

    def __init__(self, camera, preprocessor, classifier, sequencer,
                 conveyor, item_detector, flatness_checker, platform=None):
        self._camera = camera
        self._preprocessor = preprocessor
        self._classifier = classifier
        self._sequencer = sequencer
        self._conveyor = conveyor
        self._detector = item_detector
        self._flatness = flatness_checker
        self._platform = platform

    def process_one(self):
        if not self._conveyor.advance_to_fold_zone():
            return None

        frame = self._camera.capture_frame()
        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)

        detection = self._detector.detect(binary)
        if not detection.is_single:
            return None

        contour = detection.largest
        if not self._flatness.is_flat(contour) and self._platform:
            self._platform.fold_left()
            self._platform.home()
            self._platform.fold_right()
            self._platform.home()
            frame = self._camera.capture_frame()
            gray = self._preprocessor.to_grayscale(frame)
            binary = self._preprocessor.threshold(gray)
            detection = self._detector.detect(binary)
            contour = detection.largest

        if contour is None:
            return None

        garment_type = self._classifier.classify(contour)
        self._sequencer.fold(garment_type)
        return garment_type

    def run(self, max_items=None):
        self._camera.start()
        folded = []
        try:
            count = 0
            while max_items is None or count < max_items:
                result = self.process_one()
                if result is not None:
                    folded.append(result)
                    count += 1
        except Exception:
            pass
        finally:
            self._camera.stop()
        return folded
```

**Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_main.py -v`
Expected: All tests PASS (original + v2 tests)

**Step 5: Commit**

```bash
git add foldit/foldit/main.py foldit/tests/test_main.py
git commit -m "feat: FoldItRobotV2 with conveyor, multi-item, and flatness pipeline"
```

---

### Task Summary

| Task | Description | New Tests |
|------|-------------|-----------|
| 1 | Adaptive thresholding | 7 |
| 2 | Multi-item detection | 5 |
| 3 | Flatness checker | 5 |
| 4 | ML classifier + hybrid + training | 7 |
| 5 | Conveyor controller | 8 |
| 6 | V2 main loop | 3 |
| **Total** | | **35 new tests** |
