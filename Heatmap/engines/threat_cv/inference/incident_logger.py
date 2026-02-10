import cv2
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class IncidentRecord:
    """Record of a threat incident."""
    timestamp: str
    threat_level: str
    threat_score: float
    location: Optional[Dict] = None
    threat_reason: str = ""
    people_count: int = 0
    weapon_detected: bool = False
    weapon_types: List[str] = None
    behavior_summary: str = ""
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None


class IncidentLogger:
    """Logs and records threat incidents for evidence and analysis."""

    def __init__(self, log_dir: str = "safespherevenv/logs/incidents"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.incidents_file = self.log_dir / "incidents.jsonl"
        self.videos_dir = self.log_dir / "videos"
        self.screenshots_dir = self.log_dir / "screenshots"
        
        self.videos_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)

    def _get_timestamp_str(self) -> str:
        """Get formatted timestamp for filenames and logs."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    def log_incident(self, telemetry: Dict, is_critical: bool = False) -> str:
        """
        Log a threat incident.
        
        Args:
        - telemetry: Complete telemetry data from threat engine
        - is_critical: Whether this is a critical threat
        
        Returns:
        - incident_id: Unique identifier for this incident
        """
        timestamp_str = self._get_timestamp_str()
        incident_id = f"INC_{timestamp_str}"
        
        # Extract key information
        threat_level = telemetry.get("threat_assessment", {}).get("threat_level", "UNKNOWN")
        threat_score = telemetry.get("threat_assessment", {}).get("visual_threat_probability", 0.0)
        
        weapon_data = telemetry.get("weapon_detection", {})
        has_weapon = weapon_data.get("has_weapon", False)
        weapon_types = weapon_data.get("weapon_types", [])
        
        behavior = telemetry.get("behavior", {})
        overall_risk = behavior.get("overall_risk", "unknown")
        
        # Create incident record
        incident = IncidentRecord(
            timestamp=telemetry.get("timestamp", datetime.now().isoformat()),
            threat_level=threat_level,
            threat_score=float(threat_score),
            threat_reason=f"Risk: {overall_risk.upper()}, Score: {threat_score:.2f}",
            people_count=telemetry.get("tracking", {}).get("tracked_people", 0),
            weapon_detected=has_weapon,
            weapon_types=weapon_types,
            behavior_summary=f"Pairs: {len(behavior.get('pair_interactions', []))}, Risk: {overall_risk}",
        )
        
        # Log to JSON file
        self._write_incident_log(incident_id, incident, telemetry, is_critical)
        
        if is_critical:
            print(f"🚨 CRITICAL INCIDENT LOGGED: {incident_id}")
        else:
            print(f"⚠️ Incident logged: {incident_id}")
        
        return incident_id

    def _write_incident_log(self, incident_id: str, incident: IncidentRecord, 
                           telemetry: Dict, is_critical: bool):
        """Write incident to JSONL file."""
        log_entry = {
            "incident_id": incident_id,
            "is_critical": is_critical,
            "incident": asdict(incident),
            "full_telemetry": telemetry,
        }
        
        # Append to incidents file
        with open(self.incidents_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def save_screenshot(self, frame: cv2.Mat, incident_id: str, frame_offset: int = 0) -> str:
        """
        Save screenshot from frame.
        
        Args:
        - frame: Video frame to save
        - incident_id: Associated incident ID
        - frame_offset: Frame offset (before, during, after threat)
        
        Returns:
        - Path to saved screenshot
        """
        filename = f"{incident_id}_frame_{frame_offset:04d}.jpg"
        filepath = self.screenshots_dir / filename
        
        cv2.imwrite(str(filepath), frame)
        return str(filepath)

    def start_recording(self, incident_id: str, frame_shape: tuple, fps: float = 30.0) -> 'IncidentVideoRecorder':
        """
        Start recording video for an incident.
        
        Args:
        - incident_id: Incident identifier
        - frame_shape: Shape of video frames (H, W, C)
        - fps: Frames per second
        
        Returns:
        - IncidentVideoRecorder object for managing recording
        """
        return IncidentVideoRecorder(
            incident_id=incident_id,
            output_dir=self.videos_dir,
            frame_shape=frame_shape,
            fps=fps
        )

    def get_incident_report(self, incident_id: str) -> Optional[Dict]:
        """Retrieve a specific incident report."""
        with open(self.incidents_file, "r") as f:
            for line in f:
                entry = json.loads(line)
                if entry["incident_id"] == incident_id:
                    return entry
        return None

    def get_all_incidents(self, critical_only: bool = False, limit: int = 100) -> List[Dict]:
        """Get all incidents, optionally filtered."""
        incidents = []
        if not self.incidents_file.exists():
            return incidents
        
        with open(self.incidents_file, "r") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                entry = json.loads(line)
                if critical_only and not entry.get("is_critical"):
                    continue
                incidents.append(entry)
        
        # Return most recent first
        return incidents[::-1]


class IncidentVideoRecorder:
    """Records video for incidents."""

    def __init__(self, incident_id: str, output_dir: Path, frame_shape: tuple, fps: float = 30.0):
        self.incident_id = incident_id
        self.frame_shape = frame_shape
        self.fps = fps
        
        # Create video writer
        self.output_path = output_dir / f"{incident_id}.mp4"
        
        # Get video codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        h, w = frame_shape[:2]
        
        self.writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            fps,
            (w, h)
        )
        
        self.frame_count = 0
        print(f"📹 Recording started: {self.output_path}")

    def write_frame(self, frame: cv2.Mat):
        """Write frame to video."""
        if self.writer.isOpened():
            self.writer.write(frame)
            self.frame_count += 1

    def stop(self):
        """Stop recording and finalize video."""
        if self.writer.isOpened():
            self.writer.release()
            print(f"✅ Recording saved ({self.frame_count} frames): {self.output_path}")

    def __del__(self):
        """Ensure video is closed on object destruction."""
        self.stop()
