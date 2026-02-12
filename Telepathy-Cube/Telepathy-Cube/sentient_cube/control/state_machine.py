from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sentient_cube.models import Mode


@dataclass
class StateSnapshot:
    mode: Mode
    changed_at: datetime
    reason: str = ""


class DualBrainStateMachine:
    """State machine for AMBIENT/FOCUS transitions."""

    def __init__(self, idle_timeout_seconds: int = 30) -> None:
        self.mode = Mode.AMBIENT
        self.changed_at = datetime.now(timezone.utc)
        self.idle_timeout = timedelta(seconds=idle_timeout_seconds)

    def switch(self, mode: Mode, reason: str = "") -> StateSnapshot:
        self.mode = mode
        self.changed_at = datetime.now(timezone.utc)
        return StateSnapshot(mode=self.mode, changed_at=self.changed_at, reason=reason)

    def on_event(self, event: str) -> StateSnapshot:
        if self.mode == Mode.AMBIENT and event in {"wake_word", "find_request", "reminder_due"}:
            return self.switch(Mode.FOCUS, reason=event)
        if self.mode == Mode.FOCUS and event in {"task_completed", "idle_timeout", "switch_ambient"}:
            return self.switch(Mode.AMBIENT, reason=event)
        return StateSnapshot(mode=self.mode, changed_at=self.changed_at, reason="no_change")

    def check_idle_timeout(self) -> StateSnapshot:
        if self.mode == Mode.FOCUS and datetime.now(timezone.utc) - self.changed_at >= self.idle_timeout:
            return self.switch(Mode.AMBIENT, reason="idle_timeout")
        return StateSnapshot(mode=self.mode, changed_at=self.changed_at, reason="active")
