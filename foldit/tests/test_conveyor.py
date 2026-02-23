"""Tests for conveyor controller."""


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
        sensor = UltrasonicSensor(measure_fn=lambda: 5.0)
        controller = ConveyorController(motor, sensor, detection_distance=10.0, speed=75)
        controller.advance_to_fold_zone(timeout_sec=1.0)
        assert gpio.pwm_instances[25].duty == 0

    def test_advance_timeout_stops_motor(self):
        from foldit.conveyor import ConveyorController, ConveyorMotor, UltrasonicSensor
        gpio = FakeGPIOForConveyor()
        motor = ConveyorMotor(gpio, pin_a=23, pin_b=24, enable_pin=25)
        sensor = UltrasonicSensor(measure_fn=lambda: 999.0)
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
