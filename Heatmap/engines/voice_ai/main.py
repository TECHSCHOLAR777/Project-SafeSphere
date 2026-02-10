from engines.voice_ai.inference.speech_recognizer import VoiceAIEngine


def main():
    engine = VoiceAIEngine()

    print("\n🎙 Speak now...\n")
    result = engine.run_once()

    print("\n--- OUTPUT ---")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
