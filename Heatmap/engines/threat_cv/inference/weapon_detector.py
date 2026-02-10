import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


@dataclass
class WeaponDetectorConfig:
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    weapon_threat_multiplier: float = 2.5
    weapon_classes: List[str] = None

    def __post_init__(self):
        if self.weapon_classes is None:
            self.weapon_classes = [
                "gun", "knife", "gun_loaded", "gun_aiming", "firearm",
                "blade", "sword", "axe", "hammer", "crowbar",
                "bat", "stick", "club", "explosive", "bomb"
            ]


class WeaponDetector:
    """Detects weapons and dangerous objects in video frames."""

    def __init__(self, config: Optional[WeaponDetectorConfig] = None) -> None:
        self.cfg = config or WeaponDetectorConfig()
        # Placeholder for YOLO model - will be loaded on demand
        self.model = None
        self._init_attempt = False

    def _load_model(self) -> bool:
        """Load YOLO model for weapon detection."""
        try:
            # Try to import ultralytics YOLO
            from ultralytics import YOLO
            # Use a pre-trained model that detects weapons
            # In production, use: YOLO('weights/best.pt') for custom weapon detection
            self.model = YOLO('yolov8n.pt')  # nano model for speed
            return True
        except Exception as e:
            print(f"⚠️ Weapon detection unavailable: {e}")
            print("💡 To enable: pip install ultralytics")
            return False

    def detect(self, frame: np.ndarray) -> Dict:
        """
        Detect weapons in frame.
        
        Returns dict with:
        - weapons_detected: List of weapon objects
        - has_weapon: True if weapon found
        - threat_multiplier: Score multiplier (>1 if weapon)
        - confidence: Confidence of detection
        """
        result = {
            "weapons_detected": [],
            "has_weapon": False,
            "threat_multiplier": 1.0,
            "confidence": 0.0,
            "weapon_types": [],
        }

        # If model not loaded, try once
        if not self._init_attempt:
            self._init_attempt = True
            if not self._load_model():
                return result

        # If model still not available, return default
        if self.model is None:
            return result

        try:
            # Run detection
            detections = self.model(frame, verbose=False)

            if len(detections) > 0:
                boxes = detections[0].boxes

                for box in boxes:
                    conf = float(box.conf[0])
                    if conf >= self.cfg.confidence_threshold:
                        cls_id = int(box.cls[0])
                        class_name = detections[0].names.get(cls_id, f"unknown_{cls_id}")

                        # Check if it's a weapon-like class
                        is_weapon = any(w.lower() in class_name.lower() for w in self.cfg.weapon_classes)

                        if is_weapon:
                            x1, y1, x2, y2 = [int(x) for x in box.xyxy[0]]
                            result["weapons_detected"].append({
                                "class": class_name,
                                "confidence": float(conf),
                                "bbox": [x1, y1, x2 - x1, y2 - y1],
                                "center": [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                            })
                            result["weapon_types"].append(class_name)

                if result["weapons_detected"]:
                    result["has_weapon"] = True
                    result["confidence"] = max(w["confidence"] for w in result["weapons_detected"])
                    result["threat_multiplier"] = self.cfg.weapon_threat_multiplier

        except Exception as e:
            print(f"⚠️ Weapon detection error: {e}")

        return result

    def process(self, frame: np.ndarray) -> Dict:
        """Alias for detect() for API consistency."""
        return self.detect(frame)
