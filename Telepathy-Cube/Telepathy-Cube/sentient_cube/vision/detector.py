from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]


class ObjectDetector:
    """Base detector interface."""

    def detect(self, image_path: str | Path) -> List[Detection]:
        raise NotImplementedError


class YoloObjectDetector(ObjectDetector):
    """YOLOv8 detector.

    Requires:
    - pip install ultralytics
    - model file, e.g. yolo11n.pt or fine-tuned weights
    """

    def __init__(self, model_path: str = "yolo11n.pt") -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "ultralytics not installed. Install with `pip install ultralytics`."
            ) from exc
        self.model = YOLO(model_path)

    def detect(self, image_path: str | Path) -> List[Detection]:
        results = self.model.predict(str(image_path), verbose=False)
        detections: List[Detection] = []

        for result in results:
            names = result.names
            for box in result.boxes:
                cls_idx = int(box.cls.item())
                conf = float(box.conf.item())
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                label = str(names.get(cls_idx, cls_idx))
                detections.append(
                    Detection(label=label, confidence=conf, bbox=(x1, y1, x2, y2))
                )
        return detections


class MockObjectDetector(ObjectDetector):
    """Deterministic detector for local development and tests."""

    def __init__(self, fixtures: Sequence[Detection] | None = None) -> None:
        self.fixtures = list(fixtures or [])

    def detect(self, image_path: str | Path) -> List[Detection]:
        del image_path
        return list(self.fixtures)

