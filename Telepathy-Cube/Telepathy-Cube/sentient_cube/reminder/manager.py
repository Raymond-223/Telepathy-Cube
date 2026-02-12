from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sentient_cube.models import Reminder


class ReminderManager:
    def __init__(self) -> None:
        self.reminders: List[Reminder] = []

    def add(self, reminder: Reminder) -> None:
        self.reminders.append(reminder)
        self.reminders.sort(key=lambda item: item.remind_at)

    def due_reminders(self, now: datetime | None = None) -> List[Reminder]:
        current = now or datetime.now()
        due = [item for item in self.reminders if (not item.triggered and item.remind_at <= current)]
        for item in due:
            item.triggered = True
            if item.repeat_daily:
                item.remind_at = item.remind_at + timedelta(days=1)
                item.triggered = False
        return due

    def list(self) -> List[Reminder]:
        return list(self.reminders)

