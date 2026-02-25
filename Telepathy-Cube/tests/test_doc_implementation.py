from sentient_cube.doc_implementation import (
    GestureDetector,
    MultiModalWakeDetector,
    SemanticBacktracking,
    SmartTimeManager,
    TextToSpeech,
    VisionScanner,
    WakeWordDetector,
)


def test_multimodal_wake_detector():
    detector = MultiModalWakeDetector(WakeWordDetector(["小灵犀"]), gesture=GestureDetector(True))
    assert detector.on_voice_wake("小灵犀，帮我找钥匙")


def test_vision_scanner_memory_roundtrip():
    scanner = VisionScanner()
    scanner.push_memory("钥匙", "桌面左侧", 0.91)
    latest = scanner.query_visual_memory("钥匙")
    assert latest is not None
    assert scanner.verify_location("钥匙", "桌面左侧")


def test_semantic_backtracking():
    backtracking = SemanticBacktracking()
    backtracking.push("昨晚把钥匙放在玄关抽屉")
    assert backtracking.semantic_backtrack("钥匙") is not None


def test_tts_and_time_manager():
    tts = TextToSpeech()
    payload = tts.speak("测试")
    assert "测试" in payload

    manager = SmartTimeManager()
    target = manager.suggest_reminder_time(9)
    assert target is not None
