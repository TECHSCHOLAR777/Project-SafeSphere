import whisper


class WhisperEngine:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio):
        result = self.model.transcribe(audio, language="en", fp16=False)
        return result["text"].lower()
