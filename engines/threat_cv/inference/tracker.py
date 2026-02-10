import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class TrackerConfig:
    max_distance: float = 80.0
    max_missing: int = 10


@dataclass
class Track:
    id: int
    bbox: Tuple[int, int, int, int]
    centroid: np.ndarray
    velocity: np.ndarray
    missing: int = 0


class SimpleTracker:
    def __init__(self, config: TrackerConfig = TrackerConfig()) -> None:
        self.cfg = config
        self.tracks: Dict[int, Track] = {}
        self.next_id = 1

    def _centroid(self, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = bbox
        return np.array([x + w * 0.5, y + h * 0.5], dtype=np.float32)

    def _distance(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.linalg.norm(a - b))

    def update(self, detections: List[Tuple[int, int, int, int]]) -> List[Dict]:
        det_centroids = [self._centroid(b) for b in detections]
        unmatched_dets = set(range(len(detections)))
        unmatched_tracks = set(self.tracks.keys())
        matches: List[Tuple[int, int]] = []
        if self.tracks and detections:
            dist_matrix = np.zeros((len(self.tracks), len(detections)), dtype=np.float32)
            track_ids = list(self.tracks.keys())
            for ti, tid in enumerate(track_ids):
                tc = self.tracks[tid].centroid
                for di, dc in enumerate(det_centroids):
                    dist_matrix[ti, di] = self._distance(tc, dc)
            while True:
                ti, di = np.unravel_index(np.argmin(dist_matrix), dist_matrix.shape)
                best = float(dist_matrix[ti, di])
                if best > self.cfg.max_distance:
                    break
                tid = track_ids[ti]
                if tid in unmatched_tracks and di in unmatched_dets:
                    matches.append((tid, di))
                    unmatched_tracks.remove(tid)
                    unmatched_dets.remove(di)
                    dist_matrix[ti, :] = np.inf
                    dist_matrix[:, di] = np.inf
                else:
                    dist_matrix[ti, di] = np.inf
                if not np.isfinite(dist_matrix).any():
                    break
        for tid, di in matches:
            old = self.tracks[tid]
            new_bbox = detections[di]
            new_centroid = det_centroids[di]
            velocity = new_centroid - old.centroid
            self.tracks[tid] = Track(id=tid, bbox=new_bbox, centroid=new_centroid, velocity=velocity, missing=0)
        for di in unmatched_dets:
            bbox = detections[di]
            c = det_centroids[di]
            v = np.zeros(2, dtype=np.float32)
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = Track(id=tid, bbox=bbox, centroid=c, velocity=v, missing=0)
        to_remove: List[int] = []
        for tid in unmatched_tracks:
            tr = self.tracks[tid]
            tr.missing += 1
            if tr.missing > self.cfg.max_missing:
                to_remove.append(tid)
        for tid in to_remove:
            self.tracks.pop(tid, None)
        outputs: List[Dict] = []
        for tid, tr in self.tracks.items():
            outputs.append(
                {
                    "id": tid,
                    "bbox": tr.bbox,
                    "centroid": [float(tr.centroid[0]), float(tr.centroid[1])],
                    "velocity": [float(tr.velocity[0]), float(tr.velocity[1])],
                    "missing": tr.missing,
                }
            )
        return outputs
