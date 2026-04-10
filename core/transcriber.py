import whisper
import os

class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None

    def load_model(self):
        if self.model is None:
            print(f"[Transcriber] Loading Whisper model ({self.model_size})...")
            self.model = whisper.load_model(self.model_size)
            print("[Transcriber] Model loaded.")

    def transcribe(self, audio_path):
        self.load_model()
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"[Transcriber] Transcribing {audio_path}...")
        result = self.model.transcribe(audio_path, fp16=False) # fp16=False for cross-platform stability
        return result["text"]