import time
import whisper
import sounddevice as sd
import numpy as np


class VoiceAIEngine:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name) 
        self.sample_rate = 16000
        self.duration = 5
        self.distress_keywords = ["help", "help me", "please help", "save me", "someone help", "stop", "leave me", "leave me alone", "go away", "don’t follow me", "stop following me", "i’m in danger", "i need help", "call police", "call the police", "police please", "emergency"]


    def record_audio(self):
        audio = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32"
        )
        sd.wait()
        return audio.flatten()

    def transcribe(self, audio):
        result = self.model.transcribe(audio, fp16=False)
        return result["text"].lower()

    def detect_emergency(self, text):
        detected = [k for k in self.distress_keywords if k in text]
        return detected, len(detected) > 0

    def run_once(self):
        start = time.time()

        audio = self.record_audio()
        text = self.transcribe(audio)

        detected, emergency = self.detect_emergency(text)

        latency = round(time.time() - start, 2)

        return {
            "transcription": text,
            "emergency": emergency,
            "keywords": detected,
            "latency_sec": latency
        }
