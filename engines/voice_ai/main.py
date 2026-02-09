from __future__ import annotations

import json
import logging
import queue
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

import difflib
import re
from collections import deque
import numpy as np
import sounddevice as sd
import torch
import whisper
from scipy import signal


@dataclass(frozen=True)
class EnginePaths:
    root_dir: Path
    data_dir: Path
    models_dir: Path


@dataclass(frozen=True)
class EngineSettings:
    model_name: str
    language: Optional[str]
    task: str
    device: str
    fp16: bool


class AudioRecorder:
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate

    def record(self, duration_s: float) -> np.ndarray:
        frames = int(duration_s * self.sample_rate)
        recording = sd.rec(frames, samplerate=self.sample_rate, channels=1, dtype="float32")
        sd.wait()
        return np.squeeze(recording)


class RealTimeAudioCapture:
    def __init__(self, sample_rate: int, frame_ms: int = 30, energy_threshold: float = 0.01, silence_ms: int = 800) -> None:
        self.sample_rate = sample_rate
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        self.energy_threshold = energy_threshold
        self.required_silence_frames = max(1, int(silence_ms / frame_ms))
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: Optional[sd.InputStream] = None

    def _callback(self, indata: np.ndarray, frames: int, time_info: dict[str, Any], status: sd.CallbackFlags) -> None:
        if status:
            logging.warning(f"Audio status: {status}")
        self.q.put(indata.copy())

    def start(self) -> None:
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=self.frame_samples, callback=self._callback)
        self.stream.start()
        logging.info("Microphone stream started")

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logging.info("Microphone stream stopped")

    def capture_utterance(self, max_seconds: float = 15.0) -> np.ndarray:
        if self.stream is None:
            self.start()
        speech_started = False
        silence_count = 0
        frames_collected: list[np.ndarray] = []
        max_frames = int((max_seconds * 1000) / (self.frame_samples * 1000 / self.sample_rate))
        collected = 0
        while True:
            try:
                frame = self.q.get(timeout=1.0)
            except queue.Empty:
                continue
            energy = float(np.sqrt(np.mean(np.square(frame))))
            if energy >= self.energy_threshold:
                speech_started = True
                silence_count = 0
                frames_collected.append(frame)
            else:
                if speech_started:
                    silence_count += 1
                    if silence_count >= self.required_silence_frames:
                        break
            collected += 1
            if collected >= max_frames:
                break
        if not frames_collected:
            return np.array([], dtype=np.float32)
        audio = np.concatenate(frames_collected, axis=0)
        return np.squeeze(audio)


class NoiseFilter:
    def __init__(self, sample_rate: int, highpass_hz: int = 100, preemph: float = 0.97) -> None:
        self.sample_rate = sample_rate
        self.preemph = preemph
        wn = float(highpass_hz) / (sample_rate / 2.0)
        wn = min(max(wn, 1e-4), 0.99)
        self.b, self.a = signal.butter(2, wn, btype="highpass")
        self.zi = signal.lfilter_zi(self.b, self.a)

    def apply(self, x: np.ndarray) -> np.ndarray:
        if x.ndim > 1:
            x = np.squeeze(x)
        y, self.zi = signal.lfilter(self.b, self.a, x, zi=self.zi)
        z = np.empty_like(y)
        z[0] = y[0]
        z[1:] = y[1:] - self.preemph * y[:-1]
        return z


class ContinuousListener:
    def __init__(self, sample_rate: int, frame_ms: int, min_chunk_ms: int, silence_ms: int, energy_factor: float, idle_sleep_ms: int, noise_filter: NoiseFilter) -> None:
        self.sample_rate = sample_rate
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        self.required_silence_frames = max(1, int(silence_ms / frame_ms))
        self.min_chunk_frames = max(1, int(min_chunk_ms / frame_ms))
        self.energy_factor = energy_factor
        self.idle_sleep_ms = idle_sleep_ms
        self.filter = noise_filter
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: Optional[sd.InputStream] = None
        self.noise_floor = 1e-4
        self.alpha = 0.995
        self.buffer: deque[np.ndarray] = deque()
        self.voiced = False
        self.silence_count = 0
        self.last_processed_len = 0
        self.processed_interim = False

    def _callback(self, indata: np.ndarray, frames: int, time_info: dict[str, Any], status: sd.CallbackFlags) -> None:
        if status:
            logging.warning(f"Audio status: {status}")
        x = self.filter.apply(indata.copy())
        self.q.put(x)

    def start(self) -> None:
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=self.frame_samples, callback=self._callback)
        self.stream.start()
        logging.info("Continuous listening started")

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logging.info("Continuous listening stopped")

    def _rms(self, x: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(x))))

    def _update_noise(self, e: float) -> None:
        self.noise_floor = self.alpha * self.noise_floor + (1.0 - self.alpha) * e

    def _energy_threshold(self) -> float:
        return max(1e-5, self.energy_factor * self.noise_floor)

    def next_chunk(self) -> Optional[np.ndarray]:
        try:
            frame = self.q.get(timeout=self.idle_sleep_ms / 1000.0)
        except queue.Empty:
            return None
        e = self._rms(frame)
        thr = self._energy_threshold()
        if e < thr:
            self._update_noise(e)
        if e >= thr:
            self.voiced = True
            self.silence_count = 0
            self.buffer.append(frame)
            if len(self.buffer) >= self.min_chunk_frames and not self.processed_interim:
                self.processed_interim = True
                self.last_processed_len = len(self.buffer)
                return np.squeeze(np.concatenate(list(self.buffer), axis=0))
        else:
            if self.voiced:
                self.silence_count += 1
                if self.silence_count >= self.required_silence_frames:
                    if self.buffer:
                        chunk = np.squeeze(np.concatenate(list(self.buffer), axis=0))
                        self.buffer.clear()
                        self.voiced = False
                        self.silence_count = 0
                        self.processed_interim = False
                        self.last_processed_len = 0
                        return chunk
        return None


class WhisperEngine:
    def __init__(self, paths: EnginePaths, settings: EngineSettings) -> None:
        self.paths = paths
        self.settings = settings
        self.model = self._load_model()

    def _load_model(self) -> Any:
        if not self.paths.models_dir.exists():
            raise FileNotFoundError(
                f"Models directory not found at {self.paths.models_dir}. Create it first."
            )
        return whisper.load_model(
            self.settings.model_name,
            device=self.settings.device,
            download_root=str(self.paths.models_dir),
        )

    def transcribe_audio(self, audio: np.ndarray) -> dict[str, Any]:
        return self.model.transcribe(
            audio,
            language=self.settings.language,
            task=self.settings.task,
            fp16=self.settings.fp16,
        )

    def transcribe_file(self, audio_path: Path) -> dict[str, Any]:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found at {audio_path}")
        return self.model.transcribe(
            str(audio_path),
            language=self.settings.language,
            task=self.settings.task,
            fp16=self.settings.fp16,
        )


def compute_confidence(result: dict[str, Any]) -> float:
    segments = result.get("segments") or []
    if not segments:
        prob = 1.0 - float(result.get("no_speech_prob", 0.0)) if "no_speech_prob" in result else 0.0
        return float(np.clip(prob, 0.0, 1.0))
    scores: list[float] = []
    for seg in segments:
        avg_logprob = seg.get("avg_logprob")
        no_speech_prob = float(seg.get("no_speech_prob", 0.0))
        if avg_logprob is None:
            continue
        prob = float(np.exp(float(avg_logprob)))
        score = 0.7 * prob + 0.3 * (1.0 - no_speech_prob)
        scores.append(score)
    if not scores:
        return 0.0
    return float(np.clip(float(np.mean(scores)), 0.0, 1.0))


@dataclass(frozen=True)
class DistressConfig:
    keywords: list[str]
    phrases: list[str]
    min_similarity: float


class DistressDetector:
    def __init__(self, config: DistressConfig) -> None:
        self.config = config

    def _normalize(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _ratio(self, a: str, b: str) -> float:
        return float(difflib.SequenceMatcher(None, a, b).ratio())

    def _best_window_ratio(self, text_tokens: list[str], candidate_norm: str) -> float:
        cand_tokens = candidate_norm.split()
        n = len(cand_tokens)
        if n == 0:
            return 0.0
        best = 0.0
        for i in range(0, max(1, len(text_tokens) - n + 1)):
            window = " ".join(text_tokens[i : i + n])
            r = self._ratio(window, candidate_norm)
            if r > best:
                best = r
        return best

    def detect(self, text: str) -> tuple[bool, str]:
        norm = self._normalize(text)
        tokens = norm.split()
        best_score = 0.0
        best_reason = ""
        for cand in self.config.phrases:
            c = self._normalize(cand)
            score = self._best_window_ratio(tokens, c)
            if score > best_score:
                best_score = score
                best_reason = f"phrase:{cand}"
        for cand in self.config.keywords:
            c = self._normalize(cand)
            score = self._best_window_ratio(tokens, c)
            if score > best_score:
                best_score = score
                best_reason = f"keyword:{cand}"
        flag = best_score >= self.config.min_similarity
        reason = best_reason + f" score={best_score:.2f}" if flag else ""
        return flag, reason


def build_structured_output(result: dict[str, Any], latency_ms: float, detector: Optional[DistressDetector] = None) -> dict[str, Any]:
    text = result.get("text", "").strip()
    emergency_flag = False
    trigger_reason = ""
    if detector is not None and text:
        try:
            emergency_flag, trigger_reason = detector.detect(text)
        except Exception as e:
            logging.exception(f"Detection error: {e}")
    return {
        "transcription": text,
        "confidence": compute_confidence(result),
        "latency_ms": float(latency_ms),
        "emergency_flag": bool(emergency_flag),
        "trigger_reason": trigger_reason,
    }


def resolve_paths() -> EnginePaths:
    root_dir = Path(__file__).resolve().parent
    data_dir = root_dir / "data"
    models_dir = root_dir / "models"
    return EnginePaths(root_dir=root_dir, data_dir=data_dir, models_dir=models_dir)


@dataclass
class EngineConfig:
    model_name: str = "base"
    language: Optional[str] = None
    task: str = "transcribe"
    device: str = "auto"
    fp16: bool = False
    sample_rate: int = 16000
    frame_ms: int = 30
    min_chunk_ms: int = 1200
    silence_ms: int = 600
    energy_factor: float = 3.0
    idle_sleep_ms: int = 20
    highpass_hz: int = 100
    preemph: float = 0.97
    emergency_keywords: list[str] = field(default_factory=list)
    emergency_phrases: list[str] = field(default_factory=list)
    emergency_threshold: float = 0.82
    models_dir: Optional[Path] = None


def resolve_settings_from_config(cfg: EngineConfig) -> EngineSettings:
    device = cfg.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    fp16 = cfg.fp16 and device == "cuda"
    return EngineSettings(
        model_name=cfg.model_name,
        language=cfg.language,
        task=cfg.task,
        device=device,
        fp16=fp16,
    )


def build_distress_detector_from_config(cfg: EngineConfig) -> DistressDetector:
    default_keywords = [
        "help",
        "emergency",
        "danger",
        "police",
        "911",
        "stop",
        "no",
        "don't",
        "please help",
        "assault",
        "harassment",
    ]
    default_phrases = [
        "i need help",
        "please help me",
        "call the police",
        "call 911",
        "i'm in danger",
        "leave me alone",
        "stop it",
        "don't touch me",
    ]
    merged_keywords = default_keywords + (cfg.emergency_keywords or [])
    merged_phrases = default_phrases + (cfg.emergency_phrases or [])
    cfg_d = DistressConfig(keywords=merged_keywords, phrases=merged_phrases, min_similarity=float(cfg.emergency_threshold))
    return DistressDetector(cfg_d)


class VoiceAIEngine:
    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        self.cfg = config or EngineConfig()
        paths = resolve_paths()
        models_dir = self.cfg.models_dir or paths.models_dir
        self.paths = EnginePaths(root_dir=paths.root_dir, data_dir=paths.data_dir, models_dir=models_dir)
        self.settings = resolve_settings_from_config(self.cfg)
        self.engine = WhisperEngine(paths=self.paths, settings=self.settings)
        self.detector = build_distress_detector_from_config(self.cfg)
        self.noise_filter = NoiseFilter(sample_rate=self.cfg.sample_rate, highpass_hz=self.cfg.highpass_hz, preemph=self.cfg.preemph)
        self.listener = ContinuousListener(
            sample_rate=self.cfg.sample_rate,
            frame_ms=self.cfg.frame_ms,
            min_chunk_ms=self.cfg.min_chunk_ms,
            silence_ms=self.cfg.silence_ms,
            energy_factor=self.cfg.energy_factor,
            idle_sleep_ms=self.cfg.idle_sleep_ms,
            noise_filter=self.noise_filter,
        )

    def transcribe_file(self, audio_path: str | Path) -> dict[str, Any]:
        p = Path(audio_path).expanduser().resolve()
        start = time.perf_counter()
        result = self.engine.transcribe_file(p)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return build_structured_output(result, latency_ms, self.detector)

    def transcribe_array(self, audio: np.ndarray) -> dict[str, Any]:
        if audio.size == 0:
            return {"transcription": "", "confidence": 0.0, "latency_ms": 0.0, "emergency_flag": False, "trigger_reason": ""}
        start = time.perf_counter()
        result = self.engine.transcribe_audio(audio)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return build_structured_output(result, latency_ms, self.detector)

    def record_and_transcribe(self, duration_s: float) -> dict[str, Any]:
        recorder = AudioRecorder(sample_rate=self.cfg.sample_rate)
        audio = recorder.record(duration_s)
        return self.transcribe_array(audio)

    def listen(self) -> Iterator[dict[str, Any]]:
        self.listener.start()
        try:
            while True:
                chunk = self.listener.next_chunk()
                if chunk is None:
                    continue
                start = time.perf_counter()
                result = self.engine.transcribe_audio(chunk)
                latency_ms = (time.perf_counter() - start) * 1000.0
                yield build_structured_output(result, latency_ms, self.detector)
        finally:
            self.listener.stop()


def run_file_mode(engine: WhisperEngine, args: argparse.Namespace) -> dict[str, Any]:
    raise RuntimeError("CLI has been removed; use VoiceAIEngine")


def run_listen_mode(engine: WhisperEngine, args: argparse.Namespace) -> None:
    raise RuntimeError("CLI has been removed; use VoiceAIEngine.listen()")

def run_mic_mode(engine: WhisperEngine, args: argparse.Namespace) -> dict[str, Any]:
    raise RuntimeError("CLI has been removed; use VoiceAIEngine.record_and_transcribe()")


def build_distress_detector(args: argparse.Namespace) -> DistressDetector:
    raise RuntimeError("CLI has been removed; use build_distress_detector_from_config()")


from engines.voice_ai.inference.speech_recognizer import VoiceAIEngine
def main():
    engine = VoiceAIEngine()
    print("\n🎙 Speak now...\n")
    result = engine.run_once()

    for k, v in result.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
