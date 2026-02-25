from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from sentient_cube.models import Mode


@dataclass
class HardwareState:
    mode: Mode = Mode.AMBIENT
    laser_on: bool = False
    pan_angle: float = 0.0
    tilt_angle: float = 0.0
    breath_angle: float = 30.0


@dataclass
class HardwareConfig:
    backend: str = "mock"  # mock | serial | pca9685
    serial_port: str = "COM3"
    serial_baudrate: int = 115200
    serial_timeout: float = 0.1
    i2c_bus: int = 1
    pca9685_address: int = 0x40
    pca9685_frequency: int = 50
    pan_channel: int = 0
    tilt_channel: int = 1
    breath_channel: int = 2
    laser_channel: int = 3
    pan_min: float = -90.0
    pan_max: float = 90.0
    tilt_min: float = -45.0
    tilt_max: float = 45.0

    @classmethod
    def from_env(cls) -> "HardwareConfig":
        return cls(
            backend=os.getenv("CUBE_HARDWARE_BACKEND", "mock"),
            serial_port=os.getenv("CUBE_SERIAL_PORT", "COM3"),
            serial_baudrate=int(os.getenv("CUBE_SERIAL_BAUDRATE", "115200")),
            serial_timeout=float(os.getenv("CUBE_SERIAL_TIMEOUT", "0.1")),
            i2c_bus=int(os.getenv("CUBE_I2C_BUS", "1")),
            pca9685_address=int(os.getenv("CUBE_PCA9685_ADDRESS", "64")),
            pca9685_frequency=int(os.getenv("CUBE_PCA9685_FREQUENCY", "50")),
            pan_channel=int(os.getenv("CUBE_PAN_CHANNEL", "0")),
            tilt_channel=int(os.getenv("CUBE_TILT_CHANNEL", "1")),
            breath_channel=int(os.getenv("CUBE_BREATH_CHANNEL", "2")),
            laser_channel=int(os.getenv("CUBE_LASER_CHANNEL", "3")),
            pan_min=float(os.getenv("CUBE_PAN_MIN", "-90")),
            pan_max=float(os.getenv("CUBE_PAN_MAX", "90")),
            tilt_min=float(os.getenv("CUBE_TILT_MIN", "-45")),
            tilt_max=float(os.getenv("CUBE_TILT_MAX", "45")),
        )


class HardwareController:
    """Abstraction layer for Jetson/Arduino/PCA9685 control."""

    def set_mode(self, mode: Mode) -> None:
        raise NotImplementedError

    def set_breath(self, angle: float, speed: float) -> None:
        raise NotImplementedError

    def move_gimbal(self, pan: float, tilt: float) -> None:
        raise NotImplementedError

    def set_laser(self, enabled: bool) -> None:
        raise NotImplementedError

    def get_state(self) -> HardwareState:
        raise NotImplementedError

    def close(self) -> None:
        return None


class MockHardwareController(HardwareController):
    """Fallback controller for local development without hardware."""

    def __init__(self) -> None:
        self._state = HardwareState()

    def set_mode(self, mode: Mode) -> None:
        self._state.mode = mode
        if mode == Mode.AMBIENT:
            self._state.laser_on = False

    def set_breath(self, angle: float, speed: float) -> None:
        del speed
        self._state.breath_angle = max(0.0, min(180.0, angle))

    def move_gimbal(self, pan: float, tilt: float) -> None:
        self._state.pan_angle = max(-90.0, min(90.0, pan))
        self._state.tilt_angle = max(-45.0, min(45.0, tilt))

    def set_laser(self, enabled: bool) -> None:
        self._state.laser_on = enabled

    def get_state(self) -> HardwareState:
        return self._state


class SerialArduinoHardwareController(MockHardwareController):
    """Send hardware commands to Arduino over serial."""

    def __init__(self, config: HardwareConfig) -> None:
        super().__init__()
        self.config = config
        try:
            import serial  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("pyserial not installed. Please `pip install pyserial`.") from exc
        self._serial = serial.Serial(
            port=config.serial_port,
            baudrate=config.serial_baudrate,
            timeout=config.serial_timeout,
        )

    def _send(self, cmd: str) -> None:
        self._serial.write((cmd + "\n").encode("utf-8"))
        self._serial.flush()

    def set_mode(self, mode: Mode) -> None:
        super().set_mode(mode)
        self._send(f"MODE,{mode.value}")

    def set_breath(self, angle: float, speed: float) -> None:
        super().set_breath(angle, speed)
        self._send(f"BREATH,{self._state.breath_angle:.1f},{max(0.1, speed):.2f}")

    def move_gimbal(self, pan: float, tilt: float) -> None:
        super().move_gimbal(pan, tilt)
        self._send(f"GIMBAL,{self._state.pan_angle:.1f},{self._state.tilt_angle:.1f}")

    def set_laser(self, enabled: bool) -> None:
        super().set_laser(enabled)
        self._send(f"LASER,{1 if enabled else 0}")

    def close(self) -> None:
        if getattr(self, "_serial", None) and self._serial.is_open:
            self._serial.close()


class PCA9685HardwareController(MockHardwareController):
    """Directly drive servos from Jetson/Raspberry Pi over I2C."""

    def __init__(self, config: HardwareConfig) -> None:
        super().__init__()
        self.config = config
        try:
            import board  # type: ignore
            import busio  # type: ignore
            from adafruit_motor import servo  # type: ignore
            from adafruit_pca9685 import PCA9685  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "PCA9685 dependencies missing. Install `adafruit-circuitpython-pca9685 adafruit-circuitpython-motor adafruit-blinka`."
            ) from exc

        # Most Jetson setups expose board.SCL/SDA; if custom bus is needed, adapt here.
        i2c = busio.I2C(board.SCL, board.SDA)
        self._pca = PCA9685(i2c, address=config.pca9685_address)
        self._pca.frequency = config.pca9685_frequency
        self._pan_servo = servo.Servo(self._pca.channels[config.pan_channel])
        self._tilt_servo = servo.Servo(self._pca.channels[config.tilt_channel])
        self._breath_servo = servo.Servo(self._pca.channels[config.breath_channel])

    @staticmethod
    def _to_servo_angle(value: float, min_value: float, max_value: float) -> float:
        ratio = (value - min_value) / max(1e-6, (max_value - min_value))
        return max(0.0, min(180.0, ratio * 180.0))

    def set_breath(self, angle: float, speed: float) -> None:
        super().set_breath(angle, speed)
        self._breath_servo.angle = self._state.breath_angle

    def move_gimbal(self, pan: float, tilt: float) -> None:
        super().move_gimbal(pan, tilt)
        self._pan_servo.angle = self._to_servo_angle(self._state.pan_angle, self.config.pan_min, self.config.pan_max)
        self._tilt_servo.angle = self._to_servo_angle(
            self._state.tilt_angle, self.config.tilt_min, self.config.tilt_max
        )

    def set_laser(self, enabled: bool) -> None:
        super().set_laser(enabled)
        # Laser GPIO can be wired to Jetson/MCU GPIO depending on your board.
        # Keep state here; actual GPIO write is expected in board-specific extension.

    def close(self) -> None:
        if getattr(self, "_pca", None):
            self._pca.deinit()


def build_hardware_controller(config: Optional[HardwareConfig] = None) -> HardwareController:
    cfg = config or HardwareConfig.from_env()
    backend = cfg.backend.lower().strip()

    if backend == "mock":
        return MockHardwareController()
    if backend == "serial":
        return SerialArduinoHardwareController(cfg)
    if backend == "pca9685":
        return PCA9685HardwareController(cfg)
    raise ValueError(f"Unsupported backend: {cfg.backend}")
