from __future__ import annotations

import re

from sentient_cube.models import Intent, IntentType, Mode


def parse_intent(text: str) -> Intent:
    raw = (text or "").strip()
    if not raw:
        return Intent(intent_type=IntentType.CHAT, raw_text=raw)

    if "在哪" in raw or "哪里" in raw:
        item = (
            raw.replace("我的", "")
            .replace("在哪", "")
            .replace("哪里", "")
            .replace("？", "")
            .replace("?", "")
            .strip()
        )
        return Intent(intent_type=IntentType.FIND, item=item, raw_text=raw)

    if "提醒" in raw:
        parts = raw.split("提醒")
        time_text = (parts[0] or "").strip()
        content = "提醒".join(parts[1:]).strip() or "事项"
        return Intent(intent_type=IntentType.REMINDER, time_text=time_text, content=content, raw_text=raw)

    if "左脑" in raw:
        return Intent(intent_type=IntentType.MODE, mode=Mode.FOCUS, raw_text=raw)
    if "右脑" in raw or "ambient" in raw.lower():
        return Intent(intent_type=IntentType.MODE, mode=Mode.AMBIENT, raw_text=raw)

    return Intent(intent_type=IntentType.CHAT, content=raw, raw_text=raw)


def parse_reminder_time(time_text: str):
    from datetime import datetime, timedelta

    now = datetime.now()
    target = now
    text = (time_text or "").strip()

    if "后天" in text:
        target = target + timedelta(days=2)
    elif "明天" in text:
        target = target + timedelta(days=1)

    hour_match = re.search(r"(\d{1,2})\s*点", text)
    minute_match = re.search(r"(\d{1,2})\s*分", text)
    hour = int(hour_match.group(1)) if hour_match else 9
    minute = int(minute_match.group(1)) if minute_match else 0
    target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target <= now:
        target = target + timedelta(days=1)
    return target

