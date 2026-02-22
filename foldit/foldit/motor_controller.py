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
