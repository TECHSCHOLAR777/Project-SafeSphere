from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass
class EnhancedContextConfig:
    # Original boosts
    night_boost: float = 0.15
    isolation_boost: float = 0.10
    prolonged_following_boost: float = 0.25
    sudden_accel_boost: float = 0.20
    
    # New robustness factors
    crowd_safety_bonus: float = -0.10  # Reduce threat in crowds
    well_lit_bonus: float = -0.08      # Reduce threat in well-lit areas
    multiple_threats_boost: float = 0.30  # Multiple people approaching = higher threat
    entrance_exit_boost: float = 0.15   # Threats near exits are more dangerous
    cornered_boost: float = 0.25        # No escape route = higher threat
    weapon_visible_boost: float = 0.40  # Weapon sighting = major boost


class EnhancedContextAnalyzer:
    """Enhanced context analysis for robust universal threat assessment."""

    def __init__(self, config: EnhancedContextConfig = EnhancedContextConfig()) -> None:
        self.cfg = config
        self.last_speed: Dict[int, float] = {}
        self.threat_history: Dict[int, List[float]] = {}
        self.escape_routes_available = True

    def analyze(self, tracks: List[Dict], behavior: Dict, 
                weapon_detected: bool, is_night: bool, 
                frame_width: int, frame_height: int) -> Dict:
        """
        Comprehensive context analysis for universal safety.
        
        Factors analyzed:
        - Environment (night, lighting)
        - Social context (isolation, crowds)
        - Threat patterns (multiple attackers, persistence)
        - Physical environment (corners, exits)
        - Weapons (visibility, proximity)
        """
        
        boost = 0.0
        factors = {
            "night_mode": False,
            "isolation": False,
            "well_lit": False,
            "crowded": False,
            "prolonged_following": False,
            "sudden_acceleration": False,
            "multiple_threats": False,
            "weapon_visible": False,
            "cornered": False,
            "near_exit": False,
        }

        # 1. ENVIRONMENT FACTORS
        if is_night:
            boost += self.cfg.night_boost
            factors["night_mode"] = True

        # 2. SOCIAL CONTEXT
        person_count = len(tracks)
        if person_count <= 1:
            boost += self.cfg.isolation_boost
            factors["isolation"] = True
        elif person_count >= 5:
            # Safety in numbers - reduce threat
            boost -= self.cfg.crowd_safety_bonus
            factors["crowded"] = True

        # 3. BEHAVIOR PATTERNS
        pairs = behavior.get("pairs", [])
        max_persist = 0
        for p in pairs:
            max_persist = max(max_persist, int(p.get("following_persistence", 0)))

        if max_persist >= 30:
            boost += self.cfg.prolonged_following_boost
            factors["prolonged_following"] = True

        # 4. MULTIPLE THREATS DETECTION
        high_risk_pairs = [p for p in pairs if p.get("risk") == "high"]
        if len(high_risk_pairs) >= 2:
            boost += self.cfg.multiple_threats_boost
            factors["multiple_threats"] = True

        # 5. SUDDEN ACCELERATION
        for t in tracks:
            tid = int(t.get("id", -1))
            v = self._speed(t)
            prev = self.last_speed.get(tid, v)
            if v - prev >= 5.0:
                boost += self.cfg.sudden_accel_boost
                factors["sudden_acceleration"] = True
            self.last_speed[tid] = v

        # 6. WEAPON FACTORS
        if weapon_detected:
            boost += self.cfg.weapon_visible_boost
            factors["weapon_visible"] = True

        # 7. SPATIAL ANALYSIS (Position-based threats)
        # Check if person is near screen edges (cornered or near exit)
        if person_count > 0:
            for track in tracks:
                centroid = track.get("centroid", [frame_width/2, frame_height/2])
                x, y = centroid[0], centroid[1]
                
                # Check proximity to edges
                near_edge_x = x < frame_width * 0.15 or x > frame_width * 0.85
                near_edge_y = y < frame_height * 0.15 or y > frame_height * 0.85
                
                if near_edge_x and near_edge_y:
                    # Corner - potential trap
                    boost += self.cfg.cornered_boost
                    factors["cornered"] = True
                elif near_edge_x or near_edge_y:
                    # Near exit - both good (can escape) and bad (attacker can escape)
                    factors["near_exit"] = True

        # Ensure boost is within reasonable bounds
        boost = float(max(-0.2, min(0.5, boost)))

        return {
            "boost": boost,
            "factors": factors,
            "person_count": person_count,
            "high_risk_pairs": len(high_risk_pairs),
            "environmental_risk": "HIGH" if is_night and person_count <= 1 else "LOW",
        }

    def _speed(self, track: Dict) -> float:
        """Calculate speed from velocity."""
        v = track.get("velocity", [0.0, 0.0])
        return math.sqrt(float(v[0]) * float(v[0]) + float(v[1]) * float(v[1]))

    def assess_escape_routes(self, person_location: tuple, frame_size: tuple) -> bool:
        """Check if person has safe escape routes."""
        x, y = person_location
        width, height = frame_size
        
        # Has escape route if not completely surrounded
        near_left = x < width * 0.2
        near_right = x > width * 0.8
        near_top = y < height * 0.2
        near_bottom = y > height * 0.8
        
        # Safe if can move to at least one direction
        safe_left = x > width * 0.05
        safe_right = x < width * 0.95
        safe_top = y > height * 0.05
        safe_bottom = y < height * 0.95
        
        return (safe_left or safe_right) and (safe_top or safe_bottom)
