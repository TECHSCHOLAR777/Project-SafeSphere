import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MotionConfig:
    blur_ksize: int = 5
    diff_threshold: int = 25
    low_ratio: float = 0.005
    med_ratio: float = 0.02


class MotionDetector:
    def __init__(self, config: Optional[MotionConfig] = None) -> None:
        self.cfg = config or MotionConfig()
        self.prev: Optional[np.ndarray] = None

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (self.cfg.blur_ksize, self.cfg.blur_ksize), 0)
        return blur

    def process(self, frame: np.ndarray) -> Dict[str, str]:
        curr = self._preprocess(frame)
        if self.prev is None:
            self.prev = curr
            return {"motion_level": "low"}
        diff = cv2.absdiff(curr, self.prev)
        self.prev = curr
        _, mask = cv2.threshold(diff, self.cfg.diff_threshold, 255, cv2.THRESH_BINARY)
        nz = int(cv2.countNonZero(mask))
        h, w = curr.shape[:2]
        ratio = nz / float(h * w + 1e-8)
        if ratio < self.cfg.low_ratio:
            level = "low"
        elif ratio < self.cfg.med_ratio:
            level = "medium"
        else:
            level = "high"
        return {"motion_level": level}
