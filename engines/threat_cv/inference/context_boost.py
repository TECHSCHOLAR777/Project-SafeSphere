from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass
class ContextBoostConfig:
    night_boost: float = 0.15
    isolation_boost: float = 0.10
    prolonged_following_boost: float = 0.25
    sudden_accel_boost: float = 0.20
    isolation_min_people: int = 1
    prolonged_persistence_threshold: int = 30
    accel_increase_threshold: float = 5.0


class ContextBooster:
    def __init__(self, config: ContextBoostConfig = ContextBoostConfig()) -> None:
        self.cfg = config
        self.last_speed: Dict[int, float] = {}

    def _speed(self, track: Dict) -> float:
        v = track.get("velocity", [0.0, 0.0])
        return math.sqrt(float(v[0]) * float(v[0]) + float(v[1]) * float(v[1]))

    def compute(self, tracks: List[Dict], behavior: Dict, is_night: bool) -> Dict:
        boost = 0.0
        night_flag = bool(is_night)
        isolation_flag = False
        prolonged_flag = False
        sudden_accel_flag = False
        count = len(tracks)
        if night_flag:
            boost += self.cfg.night_boost
        if count <= self.cfg.isolation_min_people and count > 0:
            isolation_flag = True
            boost += self.cfg.isolation_boost
        pairs = behavior.get("pairs", [])
        max_persist = 0
        for p in pairs:
            max_persist = max(max_persist, int(p.get("following_persistence", 0)))
        if max_persist >= self.cfg.prolonged_persistence_threshold:
            prolonged_flag = True
            boost += self.cfg.prolonged_following_boost
        for t in tracks:
            tid = int(t.get("id", -1))
            s = self._speed(t)
            prev = self.last_speed.get(tid, s)
            if s - prev >= self.cfg.accel_increase_threshold:
                sudden_accel_flag = True
            self.last_speed[tid] = s
        if sudden_accel_flag:
            boost += self.cfg.sudden_accel_boost
        boost = float(max(0.0, boost))
        return {
            "boost": boost,
            "night": night_flag,
            "isolation": isolation_flag,
            "prolonged_following": prolonged_flag,
            "sudden_acceleration": sudden_accel_flag,
        }
