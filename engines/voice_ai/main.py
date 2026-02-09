from __future__ import annotations

import argparse
import json
import logging
import queue
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import sounddevice as sd
import torch
import whisper


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


def build_structured_output(result: dict[str, Any], latency_ms: float) -> dict[str, Any]:
    return {
        "transcription": result.get("text", "").strip(),
        "confidence": compute_confidence(result),
        "latency_ms": float(latency_ms),
    }


def resolve_paths() -> EnginePaths:
    root_dir = Path(__file__).resolve().parent
    data_dir = root_dir / "data"
    models_dir = root_dir / "models"
    return EnginePaths(root_dir=root_dir, data_dir=data_dir, models_dir=models_dir)


def resolve_settings(args: argparse.Namespace) -> EngineSettings:
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    fp16 = args.fp16 and device == "cuda"
    return EngineSettings(
        model_name=args.model,
        language=args.language,
        task=args.task,
        device=device,
        fp16=fp16,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voice_ai", description="Local Whisper speech recognition")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    file_parser = subparsers.add_parser("file", help="Transcribe an audio file")
    file_parser.add_argument("--input", required=True, type=str, help="Path to audio file")

    mic_parser = subparsers.add_parser("mic", help="Record from microphone and transcribe")
    mic_parser.add_argument("--duration", type=float, default=5.0, help="Recording duration in seconds")
    mic_parser.add_argument("--sample-rate", type=int, default=16000, help="Microphone sample rate")

    for sub in (file_parser, mic_parser):
        sub.add_argument("--model", type=str, default="base", help="Whisper model size")
        sub.add_argument("--language", type=str, default=None, help="Spoken language code")
        sub.add_argument("--task", type=str, default="transcribe", choices=["transcribe", "translate"])
        sub.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
        sub.add_argument("--fp16", action="store_true", help="Enable fp16 when using CUDA")
        sub.add_argument("--json", action="store_true", help="Output JSON instead of plain text")

    return parser


def output_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("transcription", "").strip())


def run_file_mode(engine: WhisperEngine, args: argparse.Namespace) -> dict[str, Any]:
    audio_path = Path(args.input).expanduser().resolve()
    start = time.perf_counter()
    result = engine.transcribe_file(audio_path)
    latency_ms = (time.perf_counter() - start) * 1000.0
    return build_structured_output(result, latency_ms)


def run_mic_mode(engine: WhisperEngine, args: argparse.Namespace) -> dict[str, Any]:
    capture = RealTimeAudioCapture(sample_rate=args.sample_rate)
    try:
        capture.start()
        audio = capture.capture_utterance(max_seconds=max(3.0, args.duration))
    finally:
        capture.stop()
    if audio.size == 0:
        logging.warning("No speech detected")
        return {"transcription": "", "confidence": 0.0, "latency_ms": 0.0}
    start = time.perf_counter()
    result = engine.transcribe_audio(audio)
    latency_ms = (time.perf_counter() - start) * 1000.0
    return build_structured_output(result, latency_ms)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_arg_parser()
    args = parser.parse_args()

    paths = resolve_paths()
    settings = resolve_settings(args)
    engine = WhisperEngine(paths=paths, settings=settings)

    if args.mode == "file":
        try:
            result = run_file_mode(engine, args)
        except Exception as e:
            logging.exception(f"File mode error: {e}")
            result = {"transcription": "", "confidence": 0.0, "latency_ms": 0.0}
    else:
        try:
            result = run_mic_mode(engine, args)
        except Exception as e:
            logging.exception(f"Mic mode error: {e}")
            result = {"transcription": "", "confidence": 0.0, "latency_ms": 0.0}

    output_result(result, args.json)


if __name__ == "__main__":
    main()
