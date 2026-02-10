from dataclasses import dataclass
from typing import Dict


@dataclass
class ThreatScorerConfig:
    motion_low: float = 0.2
    motion_medium: float = 0.5
    motion_high: float = 0.8
    behavior_low: float = 0.2
    behavior_medium: float = 0.6
    behavior_high: float = 0.9
    w_motion: float = 0.4
    w_behavior: float = 0.6


class ThreatScorer:
    def __init__(self, config: ThreatScorerConfig = ThreatScorerConfig()) -> None:
        self.cfg = config

    def _motion_score(self, motion: Dict) -> float:
        lvl = str(motion.get("motion_level", "low")).lower()
        if lvl == "high":
            return self.cfg.motion_high
        if lvl == "medium":
            return self.cfg.motion_medium
        return self.cfg.motion_low

    def _behavior_score(self, behavior: Dict) -> float:
        risk = str(behavior.get("overall_risk", "low")).lower()
        if risk == "high":
            return self.cfg.behavior_high
        if risk == "medium":
            return self.cfg.behavior_medium
        return self.cfg.behavior_low

    def score(self, motion: Dict, behavior: Dict, context: Dict) -> Dict:
        m = float(self._motion_score(motion))
        b = float(self._behavior_score(behavior))
        base = float(self.cfg.w_motion * m + self.cfg.w_behavior * b)
        boost = float(context.get("boost", 0.0))
        p = base * (1.0 + boost)
        p = float(min(1.0, max(0.0, p)))
        return {"visual_threat_probability": p}
