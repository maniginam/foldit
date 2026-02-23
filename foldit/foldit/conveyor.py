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
