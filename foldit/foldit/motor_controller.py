"""Servo motor control for folding platform."""
from abc import ABC, abstractmethod
from foldit.config import PinConfig, ServoConfig


class ServoDriverBase(ABC):
    """Abstract interface for servo motor drivers."""

    @abstractmethod
    def attach(self, channel):
        pass

    @abstractmethod
    def move_to(self, channel, angle):
        pass

    @abstractmethod
    def cleanup(self):
        pass

    def _validate_angle(self, angle):
        if not 0 <= angle <= 180:
            raise ValueError(f"Angle must be between 0 and 180, got {angle}")

    def _validate_attached(self, channel, attached):
        if channel not in attached:
            raise ValueError(f"Channel {channel} not attached")


class ServoDriver(ServoDriverBase):
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
        self._validate_angle(angle)
        self._validate_attached(pin, self._pwm)
        duty = ServoConfig.MIN_DUTY_CYCLE + (
            angle / 180.0
        ) * (ServoConfig.MAX_DUTY_CYCLE - ServoConfig.MIN_DUTY_CYCLE)
        self._pwm[pin].ChangeDutyCycle(duty)

    def cleanup(self):
        for pwm in self._pwm.values():
            pwm.stop()
        self._gpio.cleanup()


class PCA9685ServoDriver(ServoDriverBase):
    """Servo motor driver using PCA9685 I2C servo board."""

    MIN_PULSE_US = 500
    MAX_PULSE_US = 2500
    PERIOD_US = 20000

    def __init__(self, pca_board):
        self._pca = pca_board
        self._channels = set()

    def attach(self, channel):
        self._channels.add(channel)

    def move_to(self, channel, angle):
        self._validate_angle(angle)
        self._validate_attached(channel, self._channels)
        pulse_us = self.MIN_PULSE_US + (angle / 180.0) * (self.MAX_PULSE_US - self.MIN_PULSE_US)
        duty_cycle = int(pulse_us / self.PERIOD_US * 0xFFFF)
        self._pca.channels[channel].duty_cycle = duty_cycle

    def cleanup(self):
        self._pca.deinit()


class FoldingPlatform:
    """High-level folding platform control."""

    def __init__(self, servo_driver, left_channel=PinConfig.LEFT_PANEL_SERVO,
                 right_channel=PinConfig.RIGHT_PANEL_SERVO,
                 bottom_channel=PinConfig.BOTTOM_PANEL_SERVO):
        self._driver = servo_driver
        self._left = left_channel
        self._right = right_channel
        self._bottom = bottom_channel
        self._driver.attach(self._left)
        self._driver.attach(self._right)
        self._driver.attach(self._bottom)

    def home(self):
        self._driver.move_to(self._left, ServoConfig.HOME_ANGLE)
        self._driver.move_to(self._right, ServoConfig.HOME_ANGLE)
        self._driver.move_to(self._bottom, ServoConfig.HOME_ANGLE)

    def fold_left(self):
        self._driver.move_to(self._left, ServoConfig.FOLD_ANGLE)

    def fold_right(self):
        self._driver.move_to(self._right, ServoConfig.FOLD_ANGLE)

    def fold_bottom(self):
        self._driver.move_to(self._bottom, ServoConfig.FOLD_ANGLE)
