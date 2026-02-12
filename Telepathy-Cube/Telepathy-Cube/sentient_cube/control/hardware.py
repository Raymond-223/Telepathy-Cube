from __future__ import annotations

from dataclasses import dataclass

from sentient_cube.models import Mode


@dataclass
class HardwareState:
    mode: Mode = Mode.AMBIENT
    laser_on: bool = False
    pan_angle: float = 0.0
    tilt_angle: float = 0.0
    breath_angle: float = 30.0


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

