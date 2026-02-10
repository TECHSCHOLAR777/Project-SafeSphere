import time
from .audio_io import AudioRecorder
from .whisper_engine import WhisperEngine
from .keyword_detector import KeywordDetector


class VoiceAIEngine:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.whisper_engine = WhisperEngine()
        self.detector = KeywordDetector()

    def run_once(self):
        start = time.time()

        audio = self.recorder.record()
        text = self.whisper_engine.transcribe(audio)

        detected, emergency = self.detector.detect(text)

        latency = round(time.time() - start, 2)

        return {
            "engine": "voice_ai",
            "transcription": text,
            "emergency": emergency,
            "keywords": detected,
            "latency_sec": latency
        }
