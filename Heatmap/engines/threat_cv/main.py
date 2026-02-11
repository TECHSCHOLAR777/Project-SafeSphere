from engines.threat_cv.inference.video_source import VideoSource
from engines.threat_cv.inference.motion_detector import MotionDetector
from engines.threat_cv.inference.person_detector import PersonDetector
from engines.threat_cv.inference.tracker import SimpleTracker
from engines.threat_cv.inference.behavior_analyzer import BehaviorAnalyzer
from engines.threat_cv.inference.context_boost import ContextBooster
from engines.threat_cv.inference.threat_scorer import ThreatScorer
from engines.threat_cv.inference.weapon_detector import WeaponDetector
from engines.threat_cv.inference.threat_classifier import ThreatClassifier, ThreatLevel
from engines.threat_cv.inference.enhanced_context import EnhancedContextAnalyzer
from engines.threat_cv.inference.incident_logger import IncidentLogger

import json
import requests
from datetime import datetime
from collections import deque


class SafeSphereThreatsCV:
    """
    SafeSphere Threat Detection Engine
    
    Comprehensive computer vision system for real-time threat detection
    designed for universal safety - protecting everyone from harm.
    
    Features:
    - Real-time threat detection
    - Weapon recognition
    - Behavior pattern analysis
    - Advanced context awareness
    - Incident logging and recording
    - Emergency alert generation
    """

    def __init__(self, enable_recording: bool = True, backend_url: str = "http://localhost:8000"):
        """Initialize threat detection engine."""
        print("\n" + "="*80)
        print("🛡️  SAFESPHERE THREAT DETECTION ENGINE v1.0")
        print("="*80)
        print("🌍 Universal Safety Platform - Protecting Everyone")
        print("="*80 + "\n")
        
        # Backend configuration
        self.backend_url = backend_url
        self.backend_available = False
        self._check_backend()
        
        # Initialize all detectors and analyzers
        self.video = VideoSource()
        self.motion = MotionDetector()
        self.detector = PersonDetector()
        self.tracker = SimpleTracker()
        self.behavior = BehaviorAnalyzer()
        self.context = ContextBooster()
        self.enhanced_context = EnhancedContextAnalyzer()
        self.threat_scorer = ThreatScorer()
        self.weapon = WeaponDetector()
        self.classifier = ThreatClassifier()
        self.logger = IncidentLogger()
        
        self.enable_recording = enable_recording
        self.active_recorders = {}  # incident_id -> recorder
        self.frame_buffer = deque(maxlen=30)  # Keep last 30 frames for context
        self.high_threat_threshold = 0.6
        self.alert_history = {}  # Track alerted incidents to avoid spam

    def _check_backend(self):
        """Check if backend API is available."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=2)
            if response.status_code == 200:
                self.backend_available = True
                print(f"✅ Backend API connected: {self.backend_url}")
            else:
                print(f"⚠️ Backend API not responding: {self.backend_url}")
        except Exception as e:
            print(f"⚠️ Backend API unavailable: {self.backend_url}")
            print(f"   Incidents will be logged locally only")

    def _send_to_backend(self, incident_data: dict) -> bool:
        """Send threat incident to backend for processing."""
        if not self.backend_available:
            return False
        
        try:
            response = requests.post(
                f"{self.backend_url}/threats/report",
                json=incident_data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Backend processed: {result.get('message')}")
                return True
            else:
                print(f"⚠️ Backend error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Failed to send to backend: {e}")
            return False

    def _build_telemetry(self, frame_num: int, motion_result: dict, people: list, 
                        tracks: list, behavior_signals: dict, context_result: dict,
                        weapon_result: dict, threat_result: dict) -> dict:
        """Build comprehensive telemetry data."""
        threat_score = threat_result.get("visual_threat_probability", 0.0)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "frame_number": frame_num,
            "motion": {
                "level": motion_result.get("motion_level", "unknown"),
            },
            "detection": {
                "people_count": len(people),
                "bounding_boxes": [{"x": b[0], "y": b[1], "width": b[2], "height": b[3]} for b in people],
            },
            "tracking": {
                "tracked_people": len(tracks),
                "individuals": [
                    {
                        "id": int(t.get("id")),
                        "centroid": t.get("centroid"),
                        "velocity": t.get("velocity"),
                        "missing_frames": t.get("missing", 0),
                    }
                    for t in tracks
                ],
            },
            "behavior": {
                "overall_risk": behavior_signals.get("overall_risk", "unknown"),
                "pair_interactions": behavior_signals.get("pairs", []),
            },
            "context_factors": {
                "boost_applied": float(context_result.get("boost", 0.0)),
                "night_mode": context_result.get("night", False),
                "isolation": context_result.get("isolation", False),
                "prolonged_following": context_result.get("prolonged_following", False),
                "sudden_acceleration": context_result.get("sudden_acceleration", False),
            },
            "weapon_detection": {
                "has_weapon": weapon_result.get("has_weapon", False),
                "weapons_detected": weapon_result.get("weapons_detected", []),
                "weapon_types": weapon_result.get("weapon_types", []),
                "confidence": weapon_result.get("confidence", 0.0),
            },
            "threat_assessment": {
                "visual_threat_probability": float(threat_score),
                "threat_level": "HIGH" if threat_score >= 0.7 else "MEDIUM" if threat_score >= 0.4 else "LOW",
            },
        }

    def _process_frame(self, frame, frame_num: int) -> dict:
        """Process single frame through entire pipeline."""
        
        motion_result = self.motion.process(frame)
        people = self.detector.process(frame)
        tracks = self.tracker.update(people)
        behavior_signals = self.behavior.update(tracks)
        context_result = self.context.compute(tracks, behavior_signals, is_night=False)
        weapon_result = self.weapon.detect(frame)
        threat_result = self.threat_scorer.score(motion_result, behavior_signals, context_result)
        
        # Get base threat score
        threat_score = threat_result.get("visual_threat_probability", 0.0)
        
        # Adjust for weapons
        if weapon_result.get("has_weapon"):
            threat_score = min(1.0, threat_score + weapon_result.get("threat_multiplier", 2.5) * 0.1)
        
        # Build telemetry
        telemetry = self._build_telemetry(
            frame_num, motion_result, people, tracks, behavior_signals,
            context_result, weapon_result, threat_result
        )
        
        # Enhanced context analysis
        enhanced = self.enhanced_context.analyze(
            tracks, behavior_signals, weapon_result.get("has_weapon", False),
            is_night=False, frame_width=frame.shape[1], frame_height=frame.shape[0]
        )
        
        # Classify threat level
        classification = self.classifier.classify(
            threat_score=threat_score,
            has_weapon=weapon_result.get("has_weapon", False),
            behavior_risk=behavior_signals.get("overall_risk", "low"),
            context_boost=enhanced.get("boost", 0.0),
            people_count=len(tracks),
            is_night=False
        )
        
        return {
            "telemetry": telemetry,
            "threat_score": threat_score,
            "classification": classification,
            "weapon_result": weapon_result,
            "motion_level": motion_result.get("motion_level"),
            "tracks": tracks,
            "frame": frame,
        }

    def _handle_threat_alert(self, result: dict, frame_num: int):
        """Handle high threat detection."""
        classification = result["classification"]
        is_critical = classification.get("is_critical", False)
        threat_level = classification.get("threat_level", "UNKNOWN")
        
        # Avoid spam - don't alert too frequently for same threat
        threat_key = f"{threat_level}_{frame_num // 10}"
        if threat_key in self.alert_history and self.alert_history[threat_key] > frame_num - 5:
            return
        
        self.alert_history[threat_key] = frame_num
        
        # Log incident locally
        incident_id = self.logger.log_incident(result["telemetry"], is_critical=is_critical)
        
        # Save screenshot
        screenshot_path = self.logger.save_screenshot(result["frame"], incident_id)
        
        # Start recording if high threat
        if is_critical and self.enable_recording:
            recorder = self.logger.start_recording(
                incident_id,
                result["frame"].shape,
                fps=30.0
            )
            self.active_recorders[incident_id] = recorder
        
        # Send to backend for instant action
        incident_data = {
            "incident_id": incident_id,
            "timestamp": datetime.now().isoformat(),
            "threat_level": threat_level,
            "threat_score": float(result["threat_score"]),
            "people_count": len(result.get("tracks", [])),
            "weapon_detected": result["weapon_result"].get("has_weapon", False),
            "weapon_types": result["weapon_result"].get("weapon_types", []),
            "behavior_summary": f"Risk: {result['classification'].get('reasoning', ['Unknown'])[0]}",
            "is_critical": is_critical,
            "full_telemetry": result["telemetry"]
        }
        
        if self.backend_available:
            self._send_to_backend(incident_data)
        
        # Display alert
        self._display_alert(classification, result["weapon_result"])

    def _display_alert(self, classification: dict, weapon_result: dict):
        """Display threat alert."""
        threat_level = classification.get("threat_level", "UNKNOWN")
        recommendations = classification.get("recommendations", {})
        
        print("\n" + "🚨" * 40)
        print(f"THREAT ALERT: {threat_level}")
        print("🚨" * 40)
        print(f"Action Required: {recommendations.get('action')}")
        print(f"Description: {recommendations.get('description')}")
        
        if weapon_result.get("has_weapon"):
            print(f"\n⚠️  WEAPON DETECTED: {', '.join(weapon_result.get('weapon_types', []))}")
        
        for reason in classification.get("reasoning", []):
            print(f"  {reason}")
        
        if "suggested_actions" in recommendations:
            print("\n📋 Suggested Actions:")
            for action in recommendations["suggested_actions"]:
                print(f"  {action}")
        
        print("🚨" * 40 + "\n")

    def run(self):
        """Main execution loop."""
        frame_num = 0
        
        try:
            for frame in self.video.frames():
                frame_num += 1
                self.frame_buffer.append(frame)
                
                # Process frame through entire pipeline
                result = self._process_frame(frame, frame_num)
                
                # Get classification
                classification = result["classification"]
                threat_level = classification.get("threat_level", "LOW")
                threat_score = result["threat_score"]
                
                # Print frame info
                motion = result.get("motion_level", "unknown")
                people = len(result.get("tracks", []))
                weapon = "🔴 WEAPON" if result["weapon_result"].get("has_weapon") else "✓"
                
                print(f"Frame {frame_num:04d} | Motion: {motion:7s} | People: {people} | "
                      f"Risk: {classification.get('reasoning', [''])[0][:20]:20s} | "
                      f"Score: {threat_score:.2f} | Level: {threat_level:8s} | {weapon}")
                
                # Handle alerts
                if classification.get("requires_alert"):
                    self._handle_threat_alert(result, frame_num)
                
                # Write to active recorders
                for incident_id, recorder in list(self.active_recorders.items()):
                    recorder.write_frame(frame)
                    # Stop recording after 60 frames (~2 seconds at 30fps)
                    if frame_num % 60 == 0:
                        recorder.stop()
                        del self.active_recorders[incident_id]
                
        except KeyboardInterrupt:
            print("\n\n✋ Stopping threat detection...")
        except Exception as e:
            print(f"\n❌ Error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            for incident_id, recorder in self.active_recorders.items():
                recorder.stop()
            self.video.close()
            print("\n✅ Threat detection engine shut down safely")
            print(f"📊 Total frames processed: {frame_num}")
            print(f"📁 Logs saved to: {self.logger.log_dir}")


def main():
    """Entry point."""
    engine = SafeSphereThreatsCV(enable_recording=True)
    engine.run()


if __name__ == "__main__":
    main()

