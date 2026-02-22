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
