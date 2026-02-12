from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from sentient_cube.control.hardware import MockHardwareController
from sentient_cube.control.state_machine import DualBrainStateMachine
from sentient_cube.memory.spatial_memory import SpatialMemoryDB
from sentient_cube.models import IntentType, Mode, ObjectMemory, Reminder
from sentient_cube.reminder.manager import ReminderManager
from sentient_cube.vision.detector import MockObjectDetector, ObjectDetector
from sentient_cube.voice.intent import parse_intent, parse_reminder_time


class SentientCubeCore:
    def __init__(self, db_path: str = "spatial_memory.db", detector: ObjectDetector | None = None) -> None:
        self.memory = SpatialMemoryDB(db_path=db_path)
        self.hardware = MockHardwareController()
        self.state_machine = DualBrainStateMachine()
        self.reminder_manager = ReminderManager()
        self.detector = detector or MockObjectDetector()
        self.emotion = "calm"
        self.last_message = "系统已启动"

    def set_mode(self, mode: Mode, reason: str = "manual") -> Dict[str, Any]:
        snapshot = self.state_machine.switch(mode, reason=reason)
        self.hardware.set_mode(mode)
        if mode == Mode.AMBIENT:
            self.hardware.set_laser(False)
        return {"mode": snapshot.mode.value, "reason": snapshot.reason}

    def set_emotion(self, emotion: str) -> Dict[str, Any]:
        self.emotion = emotion
        return {"emotion": self.emotion}

    def remember_object(self, name: str, location: str, confidence: float = 0.9) -> Dict[str, Any]:
        memory = ObjectMemory(name=name, location=location, confidence=confidence)
        self.memory.add_object(memory)
        return SpatialMemoryDB.as_dict(memory)

    def find_object(self, name: str) -> Dict[str, Any]:
        self.set_mode(Mode.FOCUS, reason="find_request")
        latest = self.memory.latest_object(name)
        if latest is None:
            self.last_message = f"没有找到{name}的位置信息。"
            return {"found": False, "message": self.last_message}

        self.hardware.move_gimbal(15.0, -5.0)
        self.hardware.set_laser(True)
        self.last_message = f"{name} 在 {latest.location}。"
        return {
            "found": True,
            "message": self.last_message,
            "memory": SpatialMemoryDB.as_dict(latest),
        }

    def detect_and_remember(self, image_path: str, location_hint: str = "桌面区域") -> Dict[str, Any]:
        detections = self.detector.detect(image_path)
        accepted = []
        for det in detections:
            if det.confidence < 0.35:
                continue
            memory = ObjectMemory(
                name=det.label,
                location=location_hint,
                confidence=det.confidence,
            )
            self.memory.add_object(memory)
            accepted.append(
                {
                    "label": det.label,
                    "confidence": det.confidence,
                    "bbox": det.bbox,
                }
            )
        self.last_message = f"识别完成，共记录 {len(accepted)} 个目标。"
        return {"detections": accepted, "count": len(accepted)}

    def add_reminder(self, time_text: str, content: str, location: str = "") -> Dict[str, Any]:
        reminder = Reminder(content=content, remind_at=parse_reminder_time(time_text), location=location)
        self.reminder_manager.add(reminder)
        self.last_message = f"已设置提醒：{time_text} 提醒 {content}"
        return {
            "content": reminder.content,
            "remind_at": reminder.remind_at.isoformat(),
            "location": reminder.location,
        }

    def process_text(self, text: str) -> Dict[str, Any]:
        intent = parse_intent(text)
        if intent.intent_type == IntentType.FIND:
            result = self.find_object(intent.item)
            return {"intent": intent.intent_type.value, "result": result}

        if intent.intent_type == IntentType.REMINDER:
            result = self.add_reminder(intent.time_text, intent.content)
            return {"intent": intent.intent_type.value, "result": result}

        if intent.intent_type == IntentType.MODE and intent.mode is not None:
            result = self.set_mode(intent.mode, reason="voice_command")
            self.last_message = f"已切换到{'左脑' if intent.mode == Mode.FOCUS else '右脑'}模式"
            return {"intent": intent.intent_type.value, "result": result}

        self.last_message = "我在，已收到你的指令。"
        return {"intent": IntentType.CHAT.value, "result": {"message": self.last_message}}

    def tick(self) -> Dict[str, Any]:
        due = self.reminder_manager.due_reminders()
        if due:
            self.set_mode(Mode.FOCUS, reason="reminder_due")
            self.last_message = "；".join([f"提醒：{item.content}" for item in due])
        timeout_snapshot = self.state_machine.check_idle_timeout()
        if timeout_snapshot.reason == "idle_timeout":
            self.hardware.set_mode(Mode.AMBIENT)
            self.hardware.set_laser(False)
        return self.status()

    def status(self) -> Dict[str, Any]:
        hardware_state = self.hardware.get_state()
        return {
            "mode": self.state_machine.mode.value,
            "emotion": self.emotion,
            "last_message": self.last_message,
            "hardware": asdict(hardware_state),
            "reminders": [
                {"content": r.content, "remind_at": r.remind_at.isoformat(), "triggered": r.triggered}
                for r in self.reminder_manager.list()
            ],
        }

    def close(self) -> None:
        self.memory.close()
