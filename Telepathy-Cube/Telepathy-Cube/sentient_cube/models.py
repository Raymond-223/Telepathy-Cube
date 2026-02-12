from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class Mode(str, Enum):
    AMBIENT = "ambient"
    FOCUS = "focus"


class IntentType(str, Enum):
    FIND = "find"
    REMINDER = "reminder"
    MODE = "mode"
    CHAT = "chat"


@dataclass(frozen=True)
class EmotionProfile:
    duration: float
    min_angle: int
    max_angle: int
    color: str


EMOTIONS: Dict[str, EmotionProfile] = {
    "calm": EmotionProfile(4.0, 30, 60, "#4ECDC4"),
    "anxious": EmotionProfile(2.0, 40, 80, "#FF6B6B"),
    "relaxed": EmotionProfile(6.0, 20, 50, "#96CEB4"),
    "excited": EmotionProfile(1.5, 50, 90, "#FFD166"),
    "deepSleep": EmotionProfile(8.0, 10, 40, "#7B68EE"),
    "meditative": EmotionProfile(10.0, 15, 45, "#9370DB"),
}


@dataclass
class Intent:
    intent_type: IntentType
    item: str = ""
    time_text: str = ""
    content: str = ""
    mode: Optional[Mode] = None
    raw_text: str = ""


@dataclass
class ObjectMemory:
    name: str
    location: str
    confidence: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Reminder:
    content: str
    remind_at: datetime
    location: str = ""
    repeat_daily: bool = False
    triggered: bool = False
