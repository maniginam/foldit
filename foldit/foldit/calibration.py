"""Calibration tooling for FoldIt robot servos and camera."""
import json
import time

import cv2

from foldit.camera import ImagePreprocessor
from foldit.classifier import GarmentClassifier
from foldit.config import ServoConfig


DEFAULT_CONFIG_PATH = "/opt/foldit/calibration.json"
SERVO_STEP_DELAY = 0.3
CAMERA_WARMUP_SEC = 2
CALIBRATION_IMAGE_PATH = "/tmp/calibration_frame.jpg"


class CalibrationStore:
    """Reads and writes calibration values to a JSON config file."""

    def __init__(self, path=DEFAULT_CONFIG_PATH):
        self._path = path

    def load(self):
        try:
            with open(self._path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self, data):
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)


class ServoCalibrator:
    """Interactive servo calibration to find min/max angles per channel."""

    def __init__(self, servo_driver, input_fn=None, print_fn=None):
        self._driver = servo_driver
        self._input = input_fn or input
        self._print = print_fn or print

    def calibrate_channel(self, channel):
        self._driver.attach(channel)
        self._print(f"\nCalibrating servo on channel {channel}")
        self._print("Enter angles to test (0-180), 'min' to set min, 'max' to set max, 'done' to finish.")

        min_angle = ServoConfig.HOME_ANGLE
        max_angle = ServoConfig.FOLD_ANGLE
        current = 90

        self._driver.move_to(channel, current)
        self._print(f"  Current position: {current}")

        while True:
            cmd = self._input("  > ").strip().lower()
            if cmd == "done":
                break
            elif cmd == "min":
                min_angle = current
                self._print(f"  Min angle set to {min_angle}")
            elif cmd == "max":
                max_angle = current
                self._print(f"  Max angle set to {max_angle}")
            else:
                try:
                    angle = int(cmd)
                    self._driver.move_to(channel, angle)
                    current = angle
                    self._print(f"  Moved to {angle}")
                    time.sleep(SERVO_STEP_DELAY)
                except ValueError:
                    self._print("  Enter a number (0-180), 'min', 'max', or 'done'")

        return {"channel": channel, "min_angle": min_angle, "max_angle": max_angle}

    def calibrate_all(self, channels):
        results = {}
        for channel in channels:
            cal = self.calibrate_channel(channel)
            results[str(channel)] = cal
        return results


class CameraCalibrator:
    """Camera calibration: capture frames, detect contours, classify."""

    def __init__(self, camera_capture, print_fn=None):
        self._camera = camera_capture
        self._print = print_fn or print

    def capture_and_analyze(self):
        self._print("\nStarting camera calibration...")
        self._camera.start()
        time.sleep(CAMERA_WARMUP_SEC)

        frame = self._camera.capture_frame()
        self._camera.stop()

        gray = ImagePreprocessor.to_grayscale(frame)
        binary = ImagePreprocessor.threshold(gray)
        contour = ImagePreprocessor.find_largest_contour(binary)

        result = {"contour_found": contour is not None}

        if contour is not None:
            garment_type = GarmentClassifier.classify(contour)
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            annotated = frame.copy()
            cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.imwrite(CALIBRATION_IMAGE_PATH, annotated)

            result["classification"] = garment_type
            result["area"] = area
            result["bounding_box"] = {"x": x, "y": y, "w": w, "h": h}
            result["image_path"] = CALIBRATION_IMAGE_PATH

            self._print(f"  Contour detected: area={area}, bbox=({x},{y},{w},{h})")
            self._print(f"  Classification: {garment_type}")
            self._print(f"  Annotated image saved to {CALIBRATION_IMAGE_PATH}")
        else:
            self._print("  No contour detected. Check lighting and garment placement.")

        return result


class CalibrationCLI:
    """CLI interface for calibration subcommands."""

    def __init__(self, servo_calibrator, camera_calibrator, store):
        self._servo_cal = servo_calibrator
        self._camera_cal = camera_calibrator
        self._store = store

    def run(self, args):
        if len(args) < 1:
            self._print_usage()
            return 1

        command = args[0]
        if command == "servos":
            return self._calibrate_servos(args[1:])
        elif command == "camera":
            return self._calibrate_camera()
        elif command == "test":
            return self._run_test()
        else:
            self._print_usage()
            return 1

    def _calibrate_servos(self, channel_args):
        if channel_args:
            channels = [int(c) for c in channel_args]
        else:
            channels = [0, 1, 2]

        results = self._servo_cal.calibrate_all(channels)

        config = self._store.load()
        config["servos"] = results
        self._store.save(config)
        print(f"Servo calibration saved to {self._store._path}")
        return 0

    def _calibrate_camera(self):
        result = self._camera_cal.capture_and_analyze()

        config = self._store.load()
        config["camera"] = result
        self._store.save(config)
        print(f"Camera calibration saved to {self._store._path}")
        return 0

    def _run_test(self):
        config = self._store.load()
        if not config:
            print("No calibration data found. Run 'calibrate servos' and 'calibrate camera' first.")
            return 1

        print("\nCalibration test results:")
        if "servos" in config:
            print("  Servos:")
            for ch, cal in config["servos"].items():
                print(f"    Channel {ch}: min={cal['min_angle']}, max={cal['max_angle']}")
        else:
            print("  Servos: not calibrated")

        if "camera" in config:
            print("  Camera:")
            cam = config["camera"]
            print(f"    Contour found: {cam.get('contour_found', False)}")
            if cam.get("classification"):
                print(f"    Classification: {cam['classification']}")
        else:
            print("  Camera: not calibrated")

        return 0

    def _print_usage(self):
        print("Usage: calibrate <command>")
        print("Commands:")
        print("  servos [channel...]  - Interactive servo calibration")
        print("  camera               - Camera calibration")
        print("  test                 - Show current calibration values")
