from sentient_cube.vision.detector import Detection, MockObjectDetector


def test_mock_detector_returns_fixtures():
    detector = MockObjectDetector(
        fixtures=[
            Detection(label="钥匙", confidence=0.88, bbox=(10, 10, 100, 100)),
            Detection(label="手机", confidence=0.92, bbox=(120, 20, 240, 200)),
        ]
    )
    out = detector.detect("dummy.jpg")
    assert len(out) == 2
    assert out[0].label == "钥匙"

