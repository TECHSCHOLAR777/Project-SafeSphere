import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class PersonDetectorConfig:
    win_stride: Tuple[int, int] = (8, 8)
    padding: Tuple[int, int] = (8, 8)
    scale: float = 1.05
    hit_threshold: float = 0.0
    score_threshold: float = 0.3
    nms_threshold: float = 0.4
    max_width: Optional[int] = 720


class PersonDetector:
    def __init__(self, config: Optional[PersonDetectorConfig] = None) -> None:
        self.cfg = config or PersonDetectorConfig()
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def _maybe_resize(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        if self.cfg.max_width is None:
            return frame, 1.0
        h, w = frame.shape[:2]
        if w <= self.cfg.max_width:
            return frame, 1.0
        scale = self.cfg.max_width / float(w)
        resized = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
        return resized, scale

    def _scale_boxes(self, boxes: List[Tuple[int, int, int, int]], scale: float) -> List[Tuple[int, int, int, int]]:
        if scale == 1.0:
            return boxes
        inv = 1.0 / scale
        out: List[Tuple[int, int, int, int]] = []
        for (x, y, w, h) in boxes:
            out.append((int(x * inv), int(y * inv), int(w * inv), int(h * inv)))
        return out

    def process(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        img, scale = self._maybe_resize(frame)
        rects, weights = self.hog.detectMultiScale(
            img,
            hitThreshold=self.cfg.hit_threshold,
            winStride=self.cfg.win_stride,
            padding=self.cfg.padding,
            scale=self.cfg.scale,
        )
        boxes = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in rects]
        scores = [float(s) for s in (weights if weights is not None else [1.0] * len(boxes))]
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes,
            scores=scores,
            score_threshold=self.cfg.score_threshold,
            nms_threshold=self.cfg.nms_threshold,
        )
        if len(indices) == 0:
            return []
        keep = [boxes[int(i)] for i in np.array(indices).reshape(-1)]
        return self._scale_boxes(keep, scale)
