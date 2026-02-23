#!/usr/bin/env python3
"""FoldIt Robot - Hardware Verification Script

Tests I2C bus, servo motors, camera, ultrasonic sensor, and conveyor motor
to verify hardware connections. Run after setup_pi.sh to confirm everything
is wired correctly.
"""

import sys
import time

SERVO_CHANNELS = list(range(6))
SWEEP_ANGLES = [0, 90, 180, 0]
SWEEP_DELAY = 0.5
TEST_IMAGE_PATH = "/tmp/test_frame.jpg"
PCA9685_ADDRESS = 0x40
TRIGGER_PIN = 5
ECHO_PIN = 6
MOTOR_PIN_A = 23
MOTOR_PIN_B = 24
MOTOR_ENABLE_PIN = 25


def test_i2c():
    """Test I2C bus for PCA9685 servo driver."""
    print("\n[TEST] I2C Bus - PCA9685 Detection")
    print("-" * 40)
    try:
        from board import SCL, SDA
        import busio
        i2c = busio.I2C(SCL, SDA)

        while not i2c.try_lock():
            pass

        devices = i2c.scan()
        i2c.unlock()

        if PCA9685_ADDRESS in devices:
            print(f"  PCA9685 found at 0x{PCA9685_ADDRESS:02x}")
            print("  [PASS] I2C")
            return True

        print(f"  PCA9685 not found at 0x{PCA9685_ADDRESS:02x}")
        print(f"  Detected devices: {['0x{:02x}'.format(d) for d in devices]}")
        print("  [FAIL] I2C")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        print("  [FAIL] I2C")
        return False


def test_servos():
    """Test each servo by sweeping through angles."""
    print("\n[TEST] Servo Motors")
    print("-" * 40)
    try:
        from board import SCL, SDA
        import busio
        from adafruit_pca9685 import PCA9685
        from adafruit_motor import servo

        i2c = busio.I2C(SCL, SDA)
        pca = PCA9685(i2c)
        pca.frequency = 50

        all_passed = True
        for channel in SERVO_CHANNELS:
            try:
                s = servo.Servo(pca.channels[channel])
                print(f"  Servo {channel}: sweeping ", end="", flush=True)
                for angle in SWEEP_ANGLES:
                    s.angle = angle
                    print(f"{angle}", end=" ", flush=True)
                    time.sleep(SWEEP_DELAY)
                print(" [PASS]")
            except Exception as e:
                print(f" [FAIL] {e}")
                all_passed = False

        pca.deinit()

        if all_passed:
            print("  [PASS] Servos")
        else:
            print("  [FAIL] Servos - some channels failed")
        return all_passed
    except Exception as e:
        print(f"  Error: {e}")
        print("  [FAIL] Servos")
        return False


def test_camera():
    """Test camera by capturing a frame."""
    print("\n[TEST] Camera")
    print("-" * 40)
    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration()
        camera.configure(config)
        camera.start()
        time.sleep(2)

        camera.capture_file(TEST_IMAGE_PATH)
        camera.stop()
        camera.close()

        import os
        if os.path.exists(TEST_IMAGE_PATH) and os.path.getsize(TEST_IMAGE_PATH) > 0:
            size = os.path.getsize(TEST_IMAGE_PATH)
            print(f"  Frame captured: {TEST_IMAGE_PATH} ({size} bytes)")
            print("  [PASS] Camera")
            return True

        print("  Capture file is empty or missing")
        print("  [FAIL] Camera")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        print("  [FAIL] Camera")
        return False


def test_ultrasonic():
    """Test HC-SR04 ultrasonic distance sensor on GPIO pins 5 (trigger) and 6 (echo)."""
    print("\n[TEST] Ultrasonic Sensor (HC-SR04)")
    print("-" * 40)
    try:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIGGER_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)

        GPIO.output(TRIGGER_PIN, False)
        time.sleep(0.1)

        GPIO.output(TRIGGER_PIN, True)
        time.sleep(0.00001)
        GPIO.output(TRIGGER_PIN, False)

        timeout = time.monotonic() + 0.1
        pulse_start = time.monotonic()
        while GPIO.input(ECHO_PIN) == 0:
            pulse_start = time.monotonic()
            if pulse_start > timeout:
                GPIO.cleanup([TRIGGER_PIN, ECHO_PIN])
                print("  No echo response (timeout waiting for pulse start)")
                print("  [FAIL] Ultrasonic")
                return False

        timeout = time.monotonic() + 0.1
        pulse_end = time.monotonic()
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end = time.monotonic()
            if pulse_end > timeout:
                GPIO.cleanup([TRIGGER_PIN, ECHO_PIN])
                print("  Echo stuck high (timeout waiting for pulse end)")
                print("  [FAIL] Ultrasonic")
                return False

        distance = (pulse_end - pulse_start) * 17150
        GPIO.cleanup([TRIGGER_PIN, ECHO_PIN])

        if 2 <= distance <= 400:
            print(f"  Distance reading: {distance:.1f} cm")
            print("  [PASS] Ultrasonic")
            return True

        print(f"  Distance out of range: {distance:.1f} cm (expected 2-400)")
        print("  [FAIL] Ultrasonic")
        return False
    except Exception as e:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup([TRIGGER_PIN, ECHO_PIN])
        except Exception:
            pass
        print(f"  Error: {e}")
        print("  [FAIL] Ultrasonic")
        return False


def test_conveyor_motor():
    """Test L298N motor driver with DC conveyor motor on GPIO pins 23, 24, 25."""
    print("\n[TEST] Conveyor Motor (L298N)")
    print("-" * 40)
    try:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOTOR_PIN_A, GPIO.OUT)
        GPIO.setup(MOTOR_PIN_B, GPIO.OUT)
        GPIO.setup(MOTOR_ENABLE_PIN, GPIO.OUT)

        pwm = GPIO.PWM(MOTOR_ENABLE_PIN, 1000)
        pwm.start(0)

        print("  Running motor forward at 50% for 1 second...", flush=True)
        GPIO.output(MOTOR_PIN_A, GPIO.HIGH)
        GPIO.output(MOTOR_PIN_B, GPIO.LOW)
        pwm.ChangeDutyCycle(50)
        time.sleep(1)

        pwm.ChangeDutyCycle(0)
        GPIO.output(MOTOR_PIN_A, GPIO.LOW)
        GPIO.output(MOTOR_PIN_B, GPIO.LOW)
        pwm.stop()

        GPIO.cleanup([MOTOR_PIN_A, MOTOR_PIN_B, MOTOR_ENABLE_PIN])
        print("  Motor ran and stopped successfully")
        print("  [PASS] Conveyor Motor")
        return True
    except Exception as e:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup([MOTOR_PIN_A, MOTOR_PIN_B, MOTOR_ENABLE_PIN])
        except Exception:
            pass
        print(f"  Error: {e}")
        print("  [FAIL] Conveyor Motor")
        return False


def main():
    print("=" * 40)
    print(" FoldIt Hardware Verification")
    print("=" * 40)

    results = {
        "I2C / PCA9685": test_i2c(),
        "Servo Motors": test_servos(),
        "Camera": test_camera(),
        "Ultrasonic Sensor": test_ultrasonic(),
        "Conveyor Motor": test_conveyor_motor(),
    }

    print("\n" + "=" * 40)
    print(" Summary")
    print("=" * 40)

    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: [{status}]")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All hardware tests PASSED.")
    else:
        print("Some hardware tests FAILED. Check connections and try again.")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
