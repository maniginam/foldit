# FoldIt Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python-based clothes-folding robot algorithm with 3D-printable hardware files and a complete bill of materials.

**Architecture:** Modular Python package with separate concerns: camera capture, garment classification via OpenCV heuristics, fold sequence engine, and servo motor control via RPi GPIO. Hardware defined as OpenSCAD parametric models exportable to STL.

**Tech Stack:** Python 3.11+, OpenCV, RPi.GPIO, pytest, OpenSCAD (for 3D models)

---

### Task 1: Project Scaffolding

**Files:**
- Create: `foldit/foldit/__init__.py`
- Create: `foldit/foldit/config.py`
- Create: `foldit/tests/__init__.py`
- Create: `foldit/pyproject.toml`
- Create: `foldit/requirements.txt`

**Step 1: Create directory structure**

```bash
mkdir -p foldit/foldit foldit/tests
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "foldit"
version = "0.1.0"
description = "Clothes folding robot algorithm"
requires-python = ">=3.11"
dependencies = [
    "opencv-python>=4.8.0",
    "numpy>=1.24.0",
    "RPi.GPIO>=0.7.1",
    "picamera2>=0.3.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.11.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 3: Create requirements.txt**

```
opencv-python>=4.8.0
numpy>=1.24.0
RPi.GPIO>=0.7.1
picamera2>=0.3.12
pytest>=7.4.0
pytest-mock>=3.11.0
```

**Step 4: Create `foldit/__init__.py`**

```python
"""FoldIt - Clothes folding robot algorithm."""
__version__ = "0.1.0"
```

**Step 5: Create `tests/__init__.py`**

Empty file.

**Step 6: Create `foldit/config.py`**

```python
"""Hardware configuration for FoldIt robot."""


class PinConfig:
    """GPIO pin assignments for servo motors."""
    LEFT_PANEL_SERVO = 17
    RIGHT_PANEL_SERVO = 27
    BOTTOM_PANEL_SERVO = 22


class ServoConfig:
    """Servo motor calibration settings."""
    FOLD_ANGLE = 180
    HOME_ANGLE = 0
    STEP_DELAY_SEC = 0.02
    PWM_FREQUENCY_HZ = 50
    MIN_DUTY_CYCLE = 2.5
    MAX_DUTY_CYCLE = 12.5


class CameraConfig:
    """Camera capture settings."""
    RESOLUTION = (640, 480)
    FRAMERATE = 30


class PlatformConfig:
    """Physical platform dimensions in millimeters."""
    WIDTH_MM = 610   # ~24 inches
    LENGTH_MM = 762  # ~30 inches


class GarmentType:
    """Known garment classifications."""
    SHIRT = "shirt"
    PANTS = "pants"
    TOWEL = "towel"
    SMALL = "small"  # socks, underwear
    UNKNOWN = "unknown"
```

**Step 7: Commit**

```bash
git add foldit/ && git commit -m "feat: project scaffolding with config module"
```

---

### Task 2: Motor Controller Module (TDD)

**Files:**
- Create: `foldit/tests/test_motor_controller.py`
- Create: `foldit/foldit/motor_controller.py`

**Step 1: Write failing tests**

```python
"""Tests for motor controller module."""
import pytest


class FakeGPIO:
    """Test double for RPi.GPIO."""
    BCM = 11
    OUT = 0
    IN = 1

    def __init__(self):
        self.setup_calls = []
        self.cleanup_called = False
        self.setmode_called_with = None
        self.pwm_instances = {}

    def setmode(self, mode):
        self.setmode_called_with = mode

    def setup(self, pin, mode):
        self.setup_calls.append((pin, mode))

    def cleanup(self):
        self.cleanup_called = True

    def PWM(self, pin, frequency):
        pwm = FakePWM(pin, frequency)
        self.pwm_instances[pin] = pwm
        return pwm


class FakePWM:
    """Test double for GPIO.PWM."""
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.started = False
        self.stopped = False
        self.current_duty = 0

    def start(self, duty_cycle):
        self.started = True
        self.current_duty = duty_cycle

    def stop(self):
        self.stopped = True

    def ChangeDutyCycle(self, duty_cycle):
        self.current_duty = duty_cycle


class TestServoDriver:
    def test_init_sets_gpio_mode(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        ServoDriver(gpio)
        assert gpio.setmode_called_with == gpio.BCM

    def test_attach_configures_pin_as_output(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        driver.attach(17)
        assert (17, gpio.OUT) in gpio.setup_calls

    def test_attach_creates_pwm(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        driver.attach(17)
        assert 17 in gpio.pwm_instances
        assert gpio.pwm_instances[17].started is True

    def test_move_to_angle_zero(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        driver.attach(17)
        driver.move_to(17, 0)
        assert gpio.pwm_instances[17].current_duty == 2.5

    def test_move_to_angle_180(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        driver.attach(17)
        driver.move_to(17, 180)
        assert gpio.pwm_instances[17].current_duty == 12.5

    def test_move_to_angle_90(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        driver.attach(17)
        driver.move_to(17, 90)
        assert gpio.pwm_instances[17].current_duty == 7.5

    def test_cleanup_stops_all_pwms(self):
        from foldit.motor_controller import ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        driver.attach(17)
        driver.attach(27)
        driver.cleanup()
        assert gpio.pwm_instances[17].stopped is True
        assert gpio.pwm_instances[27].stopped is True
        assert gpio.cleanup_called is True


class TestFoldingPlatform:
    def test_init_attaches_three_servos(self):
        from foldit.motor_controller import FoldingPlatform, ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        FoldingPlatform(driver)
        assert 17 in gpio.pwm_instances
        assert 27 in gpio.pwm_instances
        assert 22 in gpio.pwm_instances

    def test_home_moves_all_to_zero(self):
        from foldit.motor_controller import FoldingPlatform, ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        platform = FoldingPlatform(driver)
        platform.home()
        assert gpio.pwm_instances[17].current_duty == 2.5
        assert gpio.pwm_instances[27].current_duty == 2.5
        assert gpio.pwm_instances[22].current_duty == 2.5

    def test_fold_left_moves_left_panel_to_180(self):
        from foldit.motor_controller import FoldingPlatform, ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        platform = FoldingPlatform(driver)
        platform.fold_left()
        assert gpio.pwm_instances[17].current_duty == 12.5

    def test_fold_right_moves_right_panel_to_180(self):
        from foldit.motor_controller import FoldingPlatform, ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        platform = FoldingPlatform(driver)
        platform.fold_right()
        assert gpio.pwm_instances[27].current_duty == 12.5

    def test_fold_bottom_moves_bottom_panel_to_180(self):
        from foldit.motor_controller import FoldingPlatform, ServoDriver
        gpio = FakeGPIO()
        driver = ServoDriver(gpio)
        platform = FoldingPlatform(driver)
        platform.fold_bottom()
        assert gpio.pwm_instances[22].current_duty == 12.5
```

**Step 2: Run tests to verify failure**

Run: `cd foldit && python -m pytest tests/test_motor_controller.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'foldit.motor_controller'`

**Step 3: Write minimal implementation**

```python
"""Servo motor control for folding platform."""
from foldit.config import PinConfig, ServoConfig


class ServoDriver:
    """Low-level servo motor driver using GPIO PWM."""

    def __init__(self, gpio_module):
        self._gpio = gpio_module
        self._gpio.setmode(self._gpio.BCM)
        self._pwm = {}

    def attach(self, pin):
        self._gpio.setup(pin, self._gpio.OUT)
        pwm = self._gpio.PWM(pin, ServoConfig.PWM_FREQUENCY_HZ)
        pwm.start(ServoConfig.MIN_DUTY_CYCLE)
        self._pwm[pin] = pwm

    def move_to(self, pin, angle):
        duty = ServoConfig.MIN_DUTY_CYCLE + (
            angle / 180.0
        ) * (ServoConfig.MAX_DUTY_CYCLE - ServoConfig.MIN_DUTY_CYCLE)
        self._pwm[pin].ChangeDutyCycle(duty)

    def cleanup(self):
        for pwm in self._pwm.values():
            pwm.stop()
        self._gpio.cleanup()


class FoldingPlatform:
    """High-level folding platform control."""

    def __init__(self, servo_driver):
        self._driver = servo_driver
        self._driver.attach(PinConfig.LEFT_PANEL_SERVO)
        self._driver.attach(PinConfig.RIGHT_PANEL_SERVO)
        self._driver.attach(PinConfig.BOTTOM_PANEL_SERVO)

    def home(self):
        self._driver.move_to(PinConfig.LEFT_PANEL_SERVO, ServoConfig.HOME_ANGLE)
        self._driver.move_to(PinConfig.RIGHT_PANEL_SERVO, ServoConfig.HOME_ANGLE)
        self._driver.move_to(PinConfig.BOTTOM_PANEL_SERVO, ServoConfig.HOME_ANGLE)

    def fold_left(self):
        self._driver.move_to(PinConfig.LEFT_PANEL_SERVO, ServoConfig.FOLD_ANGLE)

    def fold_right(self):
        self._driver.move_to(PinConfig.RIGHT_PANEL_SERVO, ServoConfig.FOLD_ANGLE)

    def fold_bottom(self):
        self._driver.move_to(PinConfig.BOTTOM_PANEL_SERVO, ServoConfig.FOLD_ANGLE)
```

**Step 4: Run tests to verify pass**

Run: `cd foldit && python -m pytest tests/test_motor_controller.py -v`
Expected: All 12 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/motor_controller.py foldit/tests/test_motor_controller.py
git commit -m "feat: motor controller with servo driver and folding platform"
```

---

### Task 3: Camera Module (TDD)

**Files:**
- Create: `foldit/tests/test_camera.py`
- Create: `foldit/foldit/camera.py`

**Step 1: Write failing tests**

```python
"""Tests for camera module."""
import numpy as np


class FakePicamera2:
    def __init__(self):
        self.configured = False
        self.started = False
        self.stopped = False
        self._frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def configure(self, config):
        self.configured = True
        self._config = config

    def create_still_configuration(self, main):
        return {"main": main}

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def capture_array(self):
        return self._frame


class TestCameraCapture:
    def test_start_configures_and_starts_camera(self):
        from foldit.camera import CameraCapture
        fake_cam = FakePicamera2()
        capture = CameraCapture(fake_cam)
        capture.start()
        assert fake_cam.configured is True
        assert fake_cam.started is True

    def test_capture_frame_returns_numpy_array(self):
        from foldit.camera import CameraCapture
        fake_cam = FakePicamera2()
        capture = CameraCapture(fake_cam)
        capture.start()
        frame = capture.capture_frame()
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

    def test_stop_stops_camera(self):
        from foldit.camera import CameraCapture
        fake_cam = FakePicamera2()
        capture = CameraCapture(fake_cam)
        capture.start()
        capture.stop()
        assert fake_cam.stopped is True


class TestImagePreprocessor:
    def test_to_grayscale_reduces_channels(self):
        from foldit.camera import ImagePreprocessor
        color_image = np.zeros((480, 640, 3), dtype=np.uint8)
        gray = ImagePreprocessor.to_grayscale(color_image)
        assert len(gray.shape) == 2

    def test_threshold_returns_binary_image(self):
        from foldit.camera import ImagePreprocessor
        gray = np.full((480, 640), 128, dtype=np.uint8)
        binary = ImagePreprocessor.threshold(gray)
        unique_values = np.unique(binary)
        assert all(v in (0, 255) for v in unique_values)

    def test_find_largest_contour_returns_contour_for_white_region(self):
        from foldit.camera import ImagePreprocessor
        binary = np.zeros((480, 640), dtype=np.uint8)
        binary[100:300, 100:400] = 255  # white rectangle
        contour = ImagePreprocessor.find_largest_contour(binary)
        assert contour is not None
        assert len(contour) > 0

    def test_find_largest_contour_returns_none_for_blank(self):
        from foldit.camera import ImagePreprocessor
        binary = np.zeros((480, 640), dtype=np.uint8)
        contour = ImagePreprocessor.find_largest_contour(binary)
        assert contour is None
```

**Step 2: Run tests to verify failure**

Run: `cd foldit && python -m pytest tests/test_camera.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""Camera capture and image preprocessing."""
import cv2
import numpy as np
from foldit.config import CameraConfig


class CameraCapture:
    """Captures frames from the Pi Camera."""

    def __init__(self, picamera):
        self._camera = picamera

    def start(self):
        config = self._camera.create_still_configuration(
            main={"size": CameraConfig.RESOLUTION}
        )
        self._camera.configure(config)
        self._camera.start()

    def capture_frame(self):
        return self._camera.capture_array()

    def stop(self):
        self._camera.stop()


class ImagePreprocessor:
    """Static methods for preprocessing captured images."""

    @staticmethod
    def to_grayscale(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def threshold(gray_image):
        _, binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        return binary

    @staticmethod
    def find_largest_contour(binary_image):
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)
```

**Step 4: Run tests to verify pass**

Run: `cd foldit && python -m pytest tests/test_camera.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/camera.py foldit/tests/test_camera.py
git commit -m "feat: camera capture and image preprocessing"
```

---

### Task 4: Classifier Module (TDD)

**Files:**
- Create: `foldit/tests/test_classifier.py`
- Create: `foldit/foldit/classifier.py`

**Step 1: Write failing tests**

```python
"""Tests for garment classifier."""
import numpy as np
import cv2


def _make_contour(width, height, x=100, y=100):
    """Create a rectangular contour with given dimensions."""
    points = np.array([
        [[x, y]],
        [[x + width, y]],
        [[x + width, y + height]],
        [[x, y + height]]
    ], dtype=np.int32)
    return points


class TestGarmentClassifier:
    def test_wide_short_shape_is_shirt(self):
        from foldit.classifier import GarmentClassifier
        # Shirt: wider than tall, aspect ratio > 1.2
        contour = _make_contour(400, 300)
        result = GarmentClassifier.classify(contour)
        assert result == "shirt"

    def test_tall_narrow_shape_is_pants(self):
        from foldit.classifier import GarmentClassifier
        # Pants: taller than wide, aspect ratio < 0.6
        contour = _make_contour(150, 400)
        result = GarmentClassifier.classify(contour)
        assert result == "pants"

    def test_roughly_square_large_is_towel(self):
        from foldit.classifier import GarmentClassifier
        # Towel: roughly square (0.6-1.2 ratio), large area
        contour = _make_contour(350, 350)
        result = GarmentClassifier.classify(contour)
        assert result == "towel"

    def test_small_area_is_small_item(self):
        from foldit.classifier import GarmentClassifier
        # Small items: area below threshold
        contour = _make_contour(80, 60)
        result = GarmentClassifier.classify(contour)
        assert result == "small"

    def test_none_contour_returns_unknown(self):
        from foldit.classifier import GarmentClassifier
        result = GarmentClassifier.classify(None)
        assert result == "unknown"
```

**Step 2: Run tests to verify failure**

Run: `cd foldit && python -m pytest tests/test_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""Garment type classifier using shape heuristics."""
import cv2
from foldit.config import GarmentType


class GarmentClassifier:
    """Classifies garments by contour shape and size."""

    SMALL_AREA_THRESHOLD = 15000
    PANTS_RATIO_THRESHOLD = 0.6
    SHIRT_RATIO_THRESHOLD = 1.2

    @staticmethod
    def classify(contour):
        if contour is None:
            return GarmentType.UNKNOWN

        area = cv2.contourArea(contour)
        if area < GarmentClassifier.SMALL_AREA_THRESHOLD:
            return GarmentType.SMALL

        _, _, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0

        if aspect_ratio > GarmentClassifier.SHIRT_RATIO_THRESHOLD:
            return GarmentType.SHIRT
        elif aspect_ratio < GarmentClassifier.PANTS_RATIO_THRESHOLD:
            return GarmentType.PANTS
        else:
            return GarmentType.TOWEL
```

**Step 4: Run tests to verify pass**

Run: `cd foldit && python -m pytest tests/test_classifier.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/classifier.py foldit/tests/test_classifier.py
git commit -m "feat: garment classifier with shape heuristics"
```

---

### Task 5: Folder Module — Fold Sequences (TDD)

**Files:**
- Create: `foldit/tests/test_folder.py`
- Create: `foldit/foldit/folder.py`

**Step 1: Write failing tests**

```python
"""Tests for fold sequence engine."""


class FakePlatform:
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


class TestFoldSequencer:
    def test_shirt_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("shirt")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_right", "home",
            "fold_bottom", "home"
        ]

    def test_pants_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("pants")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_bottom", "home"
        ]

    def test_towel_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("towel")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_bottom", "home"
        ]

    def test_small_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("small")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_bottom", "home"
        ]

    def test_unknown_fold_uses_basic_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("unknown")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_right", "home",
            "fold_bottom", "home"
        ]

    def test_fold_returns_garment_type(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        result = sequencer.fold("shirt")
        assert result == "shirt"
```

**Step 2: Run tests to verify failure**

Run: `cd foldit && python -m pytest tests/test_folder.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""Fold sequence engine for different garment types."""
from foldit.config import GarmentType


FOLD_SEQUENCES = {
    GarmentType.SHIRT: ["fold_left", "fold_right", "fold_bottom"],
    GarmentType.PANTS: ["fold_left", "fold_bottom"],
    GarmentType.TOWEL: ["fold_left", "fold_bottom"],
    GarmentType.SMALL: ["fold_left", "fold_bottom"],
    GarmentType.UNKNOWN: ["fold_left", "fold_right", "fold_bottom"],
}


class FoldSequencer:
    """Executes fold sequences on the platform for each garment type."""

    def __init__(self, platform):
        self._platform = platform

    def fold(self, garment_type):
        steps = FOLD_SEQUENCES.get(
            garment_type, FOLD_SEQUENCES[GarmentType.UNKNOWN]
        )
        self._platform.home()
        for step in steps:
            getattr(self._platform, step)()
            self._platform.home()
        return garment_type
```

**Step 4: Run tests to verify pass**

Run: `cd foldit && python -m pytest tests/test_folder.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/folder.py foldit/tests/test_folder.py
git commit -m "feat: fold sequence engine with per-garment patterns"
```

---

### Task 6: Main Loop

**Files:**
- Create: `foldit/tests/test_main.py`
- Create: `foldit/foldit/main.py`

**Step 1: Write failing tests**

```python
"""Tests for main robot loop."""
import numpy as np


class FakeCamera:
    def __init__(self, frames=None):
        self._frames = frames or []
        self._index = 0
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def capture_frame(self):
        if self._index < len(self._frames):
            frame = self._frames[self._index]
            self._index += 1
            return frame
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def stop(self):
        self.stopped = True


class FakeSequencer:
    def __init__(self):
        self.folded = []

    def fold(self, garment_type):
        self.folded.append(garment_type)
        return garment_type


class FakeClassifier:
    def __init__(self, results):
        self._results = results
        self._index = 0

    def classify(self, contour):
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            return result
        return "unknown"


class FakePreprocessor:
    def __init__(self, contour=None):
        self._contour = contour

    def to_grayscale(self, image):
        return image[:, :, 0] if len(image.shape) == 3 else image

    def threshold(self, gray):
        return gray

    def find_largest_contour(self, binary):
        return self._contour


class TestFoldItRobot:
    def test_process_single_garment(self):
        from foldit.main import FoldItRobot
        contour = np.array([[[100, 100]], [[500, 100]], [[500, 400]], [[100, 400]]], dtype=np.int32)
        frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        camera = FakeCamera(frames=[frame])
        preprocessor = FakePreprocessor(contour=contour)
        classifier = FakeClassifier(results=["shirt"])
        sequencer = FakeSequencer()

        robot = FoldItRobot(camera, preprocessor, classifier, sequencer)
        result = robot.process_one()
        assert result == "shirt"
        assert sequencer.folded == ["shirt"]

    def test_process_no_garment_detected(self):
        from foldit.main import FoldItRobot
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        camera = FakeCamera(frames=[frame])
        preprocessor = FakePreprocessor(contour=None)
        classifier = FakeClassifier(results=[])
        sequencer = FakeSequencer()

        robot = FoldItRobot(camera, preprocessor, classifier, sequencer)
        result = robot.process_one()
        assert result is None
        assert sequencer.folded == []
```

**Step 2: Run tests to verify failure**

Run: `cd foldit && python -m pytest tests/test_main.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
"""Main robot control loop."""


class FoldItRobot:
    """Orchestrates the garment detection and folding pipeline."""

    def __init__(self, camera, preprocessor, classifier, sequencer):
        self._camera = camera
        self._preprocessor = preprocessor
        self._classifier = classifier
        self._sequencer = sequencer

    def process_one(self):
        frame = self._camera.capture_frame()
        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)
        contour = self._preprocessor.find_largest_contour(binary)

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
        finally:
            self._camera.stop()
        return folded
```

**Step 4: Run tests to verify pass**

Run: `cd foldit && python -m pytest tests/test_main.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add foldit/foldit/main.py foldit/tests/test_main.py
git commit -m "feat: main robot loop orchestrating detect-classify-fold pipeline"
```

---

### Task 7: Hardware — OpenSCAD 3D Models

**Files:**
- Create: `hardware_files/base_plate.scad`
- Create: `hardware_files/left_panel.scad`
- Create: `hardware_files/right_panel.scad`
- Create: `hardware_files/bottom_panel.scad`
- Create: `hardware_files/hinge_bracket.scad`
- Create: `hardware_files/servo_mount.scad`
- Create: `hardware_files/camera_gantry.scad`
- Create: `hardware_files/assembly.scad`
- Create: `hardware_files/README.md`

No TDD for this task — these are 3D model files.

**Step 1: Create all OpenSCAD files**

See code in implementation. Each file is a parametric OpenSCAD model:

- **base_plate.scad** — Main platform (scaled down 1:4 for 3D printing)
- **left_panel.scad** — Left folding panel with hinge holes
- **right_panel.scad** — Right folding panel with hinge holes
- **bottom_panel.scad** — Bottom folding panel with hinge holes
- **hinge_bracket.scad** — L-bracket hinge that connects panels to base
- **servo_mount.scad** — Mount bracket for MG996R servos
- **camera_gantry.scad** — Overhead gantry to hold Pi Camera
- **assembly.scad** — Full assembly visualization (imports all parts)

**Step 2: Create README with print settings and assembly instructions**

**Step 3: Commit**

```bash
git add hardware_files/ && git commit -m "feat: OpenSCAD 3D models for folding robot prototype"
```

---

### Task 8: Bill of Materials

**Files:**
- Create: `hardware_files/BOM.md`

No TDD — documentation task.

**Step 1: Create comprehensive BOM**

Document all electrical components, hardware fasteners, and 3D-printed parts with quantities, estimated costs, and sourcing links.

**Step 2: Commit**

```bash
git add hardware_files/BOM.md && git commit -m "docs: bill of materials for robot prototype"
```

---

### Task Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | Project scaffolding + config | 0 (config only) |
| 2 | Motor controller | 12 |
| 3 | Camera module | 7 |
| 4 | Classifier | 5 |
| 5 | Fold sequences | 6 |
| 6 | Main loop | 2 |
| 7 | OpenSCAD 3D models | 0 (hardware) |
| 8 | Bill of materials | 0 (docs) |
| **Total** | | **32 tests** |
