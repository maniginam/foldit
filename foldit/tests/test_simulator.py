"""Tests for simulator mode - hardware-free development."""
import pytest
import numpy as np


class TestSimulatedCamera:
    def test_capture_frame_returns_numpy_array(self):
        from foldit.simulator import SimulatedCamera
        camera = SimulatedCamera()
        frame = camera.capture_frame()
        assert isinstance(frame, np.ndarray)

    def test_capture_frame_shape_matches_resolution(self):
        from foldit.simulator import SimulatedCamera
        camera = SimulatedCamera(resolution=(640, 480))
        frame = camera.capture_frame()
        assert frame.shape == (480, 640, 3)

    def test_start_and_stop_do_not_raise(self):
        from foldit.simulator import SimulatedCamera
        camera = SimulatedCamera()
        camera.start()
        camera.stop()

    def test_frame_contains_garment_shape(self):
        from foldit.simulator import SimulatedCamera
        camera = SimulatedCamera()
        frame = camera.capture_frame()
        non_white = np.any(frame != 255, axis=2)
        assert np.any(non_white)


class TestSimulatedServoDriver:
    def test_extends_servo_driver_base(self):
        from foldit.simulator import SimulatedServoDriver
        from foldit.motor_controller import ServoDriverBase
        driver = SimulatedServoDriver()
        assert isinstance(driver, ServoDriverBase)

    def test_attach_and_move_records_log(self):
        from foldit.simulator import SimulatedServoDriver
        driver = SimulatedServoDriver()
        driver.attach(0)
        driver.move_to(0, 90)
        assert any("move" in entry.lower() for entry in driver.log)

    def test_move_validates_angle(self):
        from foldit.simulator import SimulatedServoDriver
        driver = SimulatedServoDriver()
        driver.attach(0)
        with pytest.raises(ValueError):
            driver.move_to(0, 200)
        with pytest.raises(ValueError):
            driver.move_to(0, -10)

    def test_cleanup_does_not_raise(self):
        from foldit.simulator import SimulatedServoDriver
        driver = SimulatedServoDriver()
        driver.cleanup()


class TestSimulatedConveyor:
    def test_advance_returns_true(self):
        from foldit.simulator import SimulatedConveyor
        conveyor = SimulatedConveyor()
        assert conveyor.advance_to_fold_zone() is True

    def test_advance_records_call(self):
        from foldit.simulator import SimulatedConveyor
        conveyor = SimulatedConveyor()
        conveyor.advance_to_fold_zone()
        assert len(conveyor.calls) == 1


class TestSimulatorFactory:
    def test_create_simulated_robot_returns_v2(self):
        from foldit.simulator import create_simulated_robot
        from foldit.main import FoldItRobotV2
        robot = create_simulated_robot()
        assert isinstance(robot, FoldItRobotV2)

    def test_simulated_robot_processes_one_item(self):
        from foldit.simulator import create_simulated_robot
        robot = create_simulated_robot()
        result = robot.process_one()
        assert isinstance(result, str)
