from dataclasses import dataclass
from typing import Dict
from enum import Enum


class ThreatLevel(str, Enum):
    """Threat level classification for universal safety (all people)."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ThreatClassifierConfig:
    # Score thresholds
    low_threshold: float = 0.3
    medium_threshold: float = 0.5
    high_threshold: float = 0.7
    critical_threshold: float = 0.85
    
    # Weapon escalation
    weapon_score_boost: float = 0.3  # Add 30% to score if weapon detected
    weapon_as_critical: bool = True  # Any weapon = at least HIGH threat


class ThreatClassifier:
    """Classifies threats into 4 levels with detailed reasoning."""

    def __init__(self, config: ThreatClassifierConfig = ThreatClassifierConfig()) -> None:
        self.cfg = config

    def classify(self, threat_score: float, has_weapon: bool, 
                 behavior_risk: str, context_boost: float,
                 people_count: int, is_night: bool) -> Dict:
        """
        Classify threat into LOW/MEDIUM/HIGH/CRITICAL with reasoning.
        
        Args:
        - threat_score: Base threat probability (0-1)
        - has_weapon: Whether weapon detected
        - behavior_risk: Overall behavior risk (low/medium/high)
        - context_boost: Context multiplier from boost engine
        - people_count: Number of people detected
        - is_night: Whether it's night time
        
        Returns:
        Dict with threat level, confidence, reason, and recommendations
        """
        
        # Adjust score based on weapon
        adjusted_score = float(threat_score)
        reasoning = []
        
        if has_weapon:
            adjusted_score = min(1.0, adjusted_score + self.cfg.weapon_score_boost)
            reasoning.append("🔴 WEAPON DETECTED - Critical escalation")
        
        # Behavior context
        if behavior_risk == "high":
            reasoning.append("🔴 High-risk behavior pattern detected")
        elif behavior_risk == "medium":
            reasoning.append("🟡 Suspicious behavior detected")
        
        # Context factors
        if is_night:
            reasoning.append("🌙 Night time - elevated threat environment")
        
        if people_count == 1:
            reasoning.append("👤 Isolated situation - limited help nearby")
        elif people_count == 0:
            reasoning.append("⚠️ No people around for assistance")
        
        # Determine threat level
        if has_weapon and self.cfg.weapon_as_critical:
            threat_level = ThreatLevel.CRITICAL
        elif adjusted_score >= self.cfg.critical_threshold:
            threat_level = ThreatLevel.CRITICAL
        elif adjusted_score >= self.cfg.high_threshold:
            threat_level = ThreatLevel.HIGH
        elif adjusted_score >= self.cfg.medium_threshold:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        # Recommendations based on threat level
        recommendations = self._get_recommendations(threat_level, has_weapon, people_count)
        
        return {
            "threat_level": threat_level.value,
            "threat_score": float(adjusted_score),
            "confidence": float(min(1.0, max(0.0, adjusted_score))),
            "is_critical": threat_level == ThreatLevel.CRITICAL,
            "requires_alert": threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL],
            "reasoning": reasoning,
            "recommendations": recommendations,
        }

    def _get_recommendations(self, threat_level: ThreatLevel, 
                            has_weapon: bool, people_count: int) -> Dict:
        """Get recommendations based on threat level."""
        
        recommendations = {
            ThreatLevel.LOW: {
                "action": "MONITOR",
                "description": "Normal activity - continue monitoring",
                "alert_police": False,
                "notify_contacts": False,
                "auto_recording": False,
            },
            ThreatLevel.MEDIUM: {
                "action": "ALERT_USER",
                "description": "Suspicious activity detected - be cautious",
                "alert_police": False,
                "notify_contacts": False,
                "auto_recording": True,  # Record for evidence
            },
            ThreatLevel.HIGH: {
                "action": "ALERT_POLICE",
                "description": "High threat imminent - alert security/police",
                "alert_police": True,
                "notify_contacts": True,  # Notify emergency contacts
                "auto_recording": True,
                "suggested_actions": [
                    "🆘 Activate SOS Button",
                    "📍 Share live location with trusted contacts",
                    "🚶 Move to populated/well-lit area",
                    "📞 Contact emergency services",
                ]
            },
            ThreatLevel.CRITICAL: {
                "action": "EMERGENCY_PROTOCOL",
                "description": "CRITICAL THREAT - Immediate action required",
                "alert_police": True,
                "notify_contacts": True,
                "auto_recording": True,
                "auto_alert": True,  # Auto-send alerts without waiting
                "suggested_actions": [
                    "🆘 ACTIVATE SOS - Emergency dispatched",
                    "📍 LOCATION SHARED with police + contacts",
                    "🎥 RECORDING + STREAMING in progress",
                    "🗣️ VOICE ALERT activated",
                    "🏃 SAFE ROUTE generated to nearest police station",
                    "💡 Lights ON + Device locked (anti-theft mode)",
                ]
            }
        }
        
        return recommendations[threat_level]
