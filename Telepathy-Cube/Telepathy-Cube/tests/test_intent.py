from sentient_cube.models import IntentType, Mode
from sentient_cube.voice.intent import parse_intent


def test_parse_find():
    intent = parse_intent("我的钥匙在哪？")
    assert intent.intent_type == IntentType.FIND
    assert intent.item == "钥匙"


def test_parse_reminder():
    intent = parse_intent("明天9点提醒带身份证")
    assert intent.intent_type == IntentType.REMINDER
    assert "明天9点" in intent.time_text


def test_parse_mode():
    intent = parse_intent("切换到左脑模式")
    assert intent.intent_type == IntentType.MODE
    assert intent.mode == Mode.FOCUS

