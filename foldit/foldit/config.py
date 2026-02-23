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


class ConveyorConfig:
    """Conveyor belt motor and sensor settings."""
    MOTOR_PIN_A = 23
    MOTOR_PIN_B = 24
    MOTOR_ENABLE_PIN = 25
    TRIGGER_PIN = 5
    ECHO_PIN = 6
    DETECTION_DISTANCE_CM = 10.0
    BELT_SPEED_DUTY = 75
    SETTLE_TIME_SEC = 0.5
