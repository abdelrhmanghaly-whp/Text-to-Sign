import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np


def record_wav(filename, duration, fs=44100):
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs,
                   channels=1, dtype='int16')
    sd.wait()
    write(filename, fs, audio)
    print(f"Saved recording to {filename}")


if __name__ == "__main__":
    duration = float(input("Enter duration in seconds: "))
    filename = input("Enter output filename (e.g., test.wav): ")
    record_wav(filename, duration)
