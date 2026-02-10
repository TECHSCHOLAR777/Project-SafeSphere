from engines.threat_cv.inference.video_source import VideoSource
from engines.threat_cv.inference.motion_detector import MotionDetector
from engines.threat_cv.inference.person_detector import PersonDetector
from engines.threat_cv.inference.tracker import PersonTracker
from engines.threat_cv.inference.behavior_analyzer import BehaviorAnalyzer
from engines.threat_cv.inference.context_boost import ContextBooster
from engines.threat_cv.inference.threat_scorer import ThreatScorer


def main():
    video = VideoSource()
    motion = MotionDetector()
    detector = PersonDetector()
    tracker = PersonTracker()
    behavior = BehaviorAnalyzer()
    context = ContextBooster()
    scorer = ThreatScorer()

    print("\n📹 Threat CV Engine running...\n")

    for frame in video.frames():
        motion_level = motion.analyze(frame)
        people = detector.detect(frame)
        tracks = tracker.update(people)
        behavior_signals = behavior.analyze(tracks)
        boosted = context.apply(behavior_signals)
        threat_score = scorer.compute(motion_level, boosted)

        print(f"🔥 Threat Score: {round(threat_score, 2)}")


if __name__ == "__main__":
    main()
