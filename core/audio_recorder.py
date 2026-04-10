import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import threading

class AudioRecorder:
    def __init__(self, filepath):
        self.filepath = filepath
        self.recording = False
        self.audio_chunks = []
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"[Audio] Status: {status}")
        self.audio_chunks.append(indata.copy())

    def start(self):
        self.recording = True
        self.audio_chunks = []
        self.stream = sd.InputStream(callback=self._callback, channels=1, samplerate=44100)
        self.stream.start()
        print("[Audio] Recording started...")

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        self.stream.stop()
        self.stream.close()

        audio = np.concatenate(self.audio_chunks, axis=0)
        wav.write(self.filepath, 44100, audio)
        print(f"[Audio] Saved to {self.filepath}")