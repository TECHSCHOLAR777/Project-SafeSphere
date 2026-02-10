import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class BehaviorConfig:
    proximity_threshold: float = 120.0
    approach_velocity_threshold: float = -4.0
    alignment_threshold: float = 0.7
    persistence_frames: int = 15
    history_len: int = 5


class BehaviorAnalyzer:
    def __init__(self, config: BehaviorConfig = BehaviorConfig()) -> None:
        self.cfg = config
        self.history: Dict[int, deque] = {}
        self.pair_last_distance: Dict[Tuple[int, int], float] = {}
        self.pair_counts: Dict[Tuple[int, int], int] = {}

    def _norm(self, v: Tuple[float, float]) -> float:
        return math.sqrt(v[0] * v[0] + v[1] * v[1])

    def _unit(self, v: Tuple[float, float]) -> Tuple[float, float]:
        n = self._norm(v)
        if n < 1e-6:
            return (0.0, 0.0)
        return (v[0] / n, v[1] / n)

    def _centroid(self, track: Dict) -> Tuple[float, float]:
        c = track["centroid"]
        return (float(c[0]), float(c[1]))

    def _velocity(self, track: Dict) -> Tuple[float, float]:
        v = track["velocity"]
        return (float(v[0]), float(v[1]))

    def _pair_key(self, a: int, b: int) -> Tuple[int, int]:
        return (a, b) if a < b else (b, a)

    def update(self, tracks: List[Dict]) -> Dict:
        for t in tracks:
            tid = int(t["id"])
            c = self._centroid(t)
            if tid not in self.history:
                self.history[tid] = deque(maxlen=self.cfg.history_len)
            self.history[tid].append(c)
        ids = [int(t["id"]) for t in tracks]
        centroids = {int(t["id"]): self._centroid(t) for t in tracks}
        velocities = {int(t["id"]): self._velocity(t) for t in tracks}
        pair_signals: List[Dict] = []
        max_risk = "low"
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a = ids[i]
                b = ids[j]
                ca = centroids[a]
                cb = centroids[b]
                va = velocities[a]
                vb = velocities[b]
                dx = ca[0] - cb[0]
                dy = ca[1] - cb[1]
                dist = math.sqrt(dx * dx + dy * dy)
                key = self._pair_key(a, b)
                prev_dist = self.pair_last_distance.get(key, dist)
                approach_vel = dist - prev_dist
                self.pair_last_distance[key] = dist
                ua = self._unit(va)
                ub = self._unit(vb)
                alignment = ua[0] * ub[0] + ua[1] * ub[1]
                close = dist <= self.cfg.proximity_threshold
                approaching = approach_vel <= self.cfg.approach_velocity_threshold
                aligned = alignment >= self.cfg.alignment_threshold
                follow_cond = close and aligned and (approaching or approach_vel <= 0.0)
                count = self.pair_counts.get(key, 0)
                if follow_cond:
                    count += 1
                else:
                    count = max(0, count - 1)
                self.pair_counts[key] = count
                if count >= self.cfg.persistence_frames:
                    risk = "high"
                elif count >= self.cfg.persistence_frames // 2:
                    risk = "medium"
                else:
                    risk = "low"
                if risk == "high":
                    max_risk = "high"
                elif risk == "medium" and max_risk != "high":
                    max_risk = "medium"
                pair_signals.append(
                    {
                        "ids": [a, b],
                        "proximity": float(dist),
                        "approach_velocity": float(approach_vel),
                        "alignment": float(alignment),
                        "following_persistence": int(count),
                        "risk": risk,
                    }
                )
        return {"pairs": pair_signals, "overall_risk": max_risk}
