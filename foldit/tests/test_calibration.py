"""Tests for calibration module."""
import json
import os
import tempfile

import numpy as np
import pytest


class FakeServoDriver:
    """Test double for servo driver."""

    def __init__(self):
        self.attached = set()
        self.positions = {}

    def attach(self, channel):
        self.attached.add(channel)

    def move_to(self, channel, angle):
        self.positions[channel] = angle

    def cleanup(self):
        pass


class FakeCameraCapture:
    """Test double for CameraCapture."""

    def __init__(self, frame=None):
        self._frame = frame if frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def capture_frame(self):
        return self._frame

    def stop(self):
        self.stopped = True


def make_input_sequence(commands):
    """Returns an input function that yields commands in order."""
    it = iter(commands)
    return lambda _: next(it)


class TestCalibrationStore:
    def test_load_returns_empty_dict_when_file_missing(self):
        from foldit.calibration import CalibrationStore
        store = CalibrationStore("/nonexistent/path.json")
        assert store.load() == {}

    def test_save_and_load_roundtrip(self):
        from foldit.calibration import CalibrationStore
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            store = CalibrationStore(path)
            data = {"servos": {"0": {"min_angle": 5, "max_angle": 170}}}
            store.save(data)
            loaded = store.load()
            assert loaded == data
        finally:
            os.unlink(path)

    def test_load_returns_empty_dict_for_invalid_json(self):
        from foldit.calibration import CalibrationStore
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{{{")
            path = f.name
        try:
            store = CalibrationStore(path)
            assert store.load() == {}
        finally:
            os.unlink(path)


class TestServoCalibrator:
    def test_calibrate_channel_with_min_max_done(self):
        from foldit.calibration import ServoCalibrator
        driver = FakeServoDriver()
        inputs = make_input_sequence(["45", "min", "135", "max", "done"])
        output = []
        cal = ServoCalibrator(driver, input_fn=inputs, print_fn=output.append)
        result = cal.calibrate_channel(0)
        assert result["channel"] == 0
        assert result["min_angle"] == 45
        assert result["max_angle"] == 135

    def test_calibrate_channel_attaches_servo(self):
        from foldit.calibration import ServoCalibrator
        driver = FakeServoDriver()
        inputs = make_input_sequence(["done"])
        cal = ServoCalibrator(driver, input_fn=inputs, print_fn=lambda _: None)
        cal.calibrate_channel(3)
        assert 3 in driver.attached

    def test_calibrate_channel_moves_to_entered_angle(self):
        from foldit.calibration import ServoCalibrator
        driver = FakeServoDriver()
        inputs = make_input_sequence(["60", "done"])
        cal = ServoCalibrator(driver, input_fn=inputs, print_fn=lambda _: None)
        cal.calibrate_channel(0)
        assert driver.positions[0] == 60

    def test_calibrate_channel_defaults_to_0_and_180(self):
        from foldit.calibration import ServoCalibrator
        driver = FakeServoDriver()
        inputs = make_input_sequence(["done"])
        cal = ServoCalibrator(driver, input_fn=inputs, print_fn=lambda _: None)
        result = cal.calibrate_channel(0)
        assert result["min_angle"] == 0
        assert result["max_angle"] == 180

    def test_calibrate_channel_handles_invalid_input(self):
        from foldit.calibration import ServoCalibrator
        driver = FakeServoDriver()
        inputs = make_input_sequence(["abc", "done"])
        output = []
        cal = ServoCalibrator(driver, input_fn=inputs, print_fn=output.append)
        result = cal.calibrate_channel(0)
        assert any("number" in str(msg) for msg in output)
        assert result["channel"] == 0

    def test_calibrate_all_returns_results_for_each_channel(self):
        from foldit.calibration import ServoCalibrator
        driver = FakeServoDriver()
        inputs = make_input_sequence(["done", "done", "done"])
        cal = ServoCalibrator(driver, input_fn=inputs, print_fn=lambda _: None)
        results = cal.calibrate_all([0, 1, 2])
        assert "0" in results
        assert "1" in results
        assert "2" in results


class TestCameraCalibrator:
    def test_capture_and_analyze_starts_and_stops_camera(self):
        from foldit.calibration import CameraCalibrator
        camera = FakeCameraCapture()
        cal = CameraCalibrator(camera, print_fn=lambda _: None)
        cal.capture_and_analyze()
        assert camera.started is True
        assert camera.stopped is True

    def test_capture_and_analyze_no_contour_on_blank_frame(self):
        from foldit.calibration import CameraCalibrator
        camera = FakeCameraCapture()
        cal = CameraCalibrator(camera, print_fn=lambda _: None)
        result = cal.capture_and_analyze()
        assert result["contour_found"] is False

    def test_capture_and_analyze_detects_contour(self):
        from foldit.calibration import CameraCalibrator
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:300, 100:400] = 255
        camera = FakeCameraCapture(frame)
        cal = CameraCalibrator(camera, print_fn=lambda _: None)
        result = cal.capture_and_analyze()
        assert result["contour_found"] is True
        assert "classification" in result
        assert "area" in result
        assert result["area"] > 0

    def test_capture_and_analyze_saves_annotated_image(self):
        from foldit.calibration import CameraCalibrator, CALIBRATION_IMAGE_PATH
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:300, 100:400] = 255
        camera = FakeCameraCapture(frame)
        cal = CameraCalibrator(camera, print_fn=lambda _: None)
        result = cal.capture_and_analyze()
        assert result["image_path"] == CALIBRATION_IMAGE_PATH

    def test_capture_and_analyze_includes_bounding_box(self):
        from foldit.calibration import CameraCalibrator
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:300, 200:500] = 255
        camera = FakeCameraCapture(frame)
        cal = CameraCalibrator(camera, print_fn=lambda _: None)
        result = cal.capture_and_analyze()
        bbox = result["bounding_box"]
        assert bbox["x"] == 200
        assert bbox["y"] == 100
        assert bbox["w"] == 300
        assert bbox["h"] == 200


class TestCalibrationCLI:
    def _make_cli(self, driver=None, camera=None, store_path=None):
        from foldit.calibration import (
            CalibrationCLI, CalibrationStore,
            CameraCalibrator, ServoCalibrator,
        )
        driver = driver or FakeServoDriver()
        camera = camera or FakeCameraCapture()
        if store_path is None:
            f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            store_path = f.name
            f.close()
        store = CalibrationStore(store_path)
        servo_cal = ServoCalibrator(driver, input_fn=make_input_sequence(["done"] * 10), print_fn=lambda _: None)
        camera_cal = CameraCalibrator(camera, print_fn=lambda _: None)
        cli = CalibrationCLI(servo_cal, camera_cal, store)
        return cli, store_path

    def test_run_no_args_returns_1(self):
        cli, path = self._make_cli()
        try:
            assert cli.run([]) == 1
        finally:
            os.unlink(path)

    def test_run_unknown_command_returns_1(self):
        cli, path = self._make_cli()
        try:
            assert cli.run(["unknown"]) == 1
        finally:
            os.unlink(path)

    def test_run_servos_saves_calibration(self):
        from foldit.calibration import CalibrationStore
        cli, path = self._make_cli()
        try:
            result = cli.run(["servos", "0", "1"])
            assert result == 0
            data = CalibrationStore(path).load()
            assert "servos" in data
            assert "0" in data["servos"]
            assert "1" in data["servos"]
        finally:
            os.unlink(path)

    def test_run_camera_saves_calibration(self):
        from foldit.calibration import CalibrationStore
        cli, path = self._make_cli()
        try:
            result = cli.run(["camera"])
            assert result == 0
            data = CalibrationStore(path).load()
            assert "camera" in data
        finally:
            os.unlink(path)

    def test_run_test_with_no_data_returns_1(self):
        cli, path = self._make_cli()
        try:
            assert cli.run(["test"]) == 1
        finally:
            os.unlink(path)

    def test_run_test_with_data_returns_0(self):
        from foldit.calibration import CalibrationStore
        cli, path = self._make_cli()
        try:
            store = CalibrationStore(path)
            store.save({"servos": {"0": {"min_angle": 0, "max_angle": 180}}, "camera": {"contour_found": True}})
            assert cli.run(["test"]) == 0
        finally:
            os.unlink(path)

    def test_servos_default_channels_0_1_2(self):
        from foldit.calibration import CalibrationStore
        cli, path = self._make_cli()
        try:
            cli.run(["servos"])
            data = CalibrationStore(path).load()
            assert "0" in data["servos"]
            assert "1" in data["servos"]
            assert "2" in data["servos"]
        finally:
            os.unlink(path)
