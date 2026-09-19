import wave
import numpy as np

with wave.open('calisma/Gun_5/test_now.wav', 'rb') as w:
    sr = w.getframerate()
    frames = w.readframes(w.getnframes())
    samples = np.frombuffer(frames, dtype=np.int16)
    # Stereo -> take left channel
    samples = samples[::2]

win_size = int(sr * 0.05)
for i in range(0, min(len(samples), int(sr * 2.5)), win_size):
    t = i / sr
    rms = np.sqrt(np.mean(samples[i:i+win_size].astype(float)**2))
    print(f"offset={t:.2f}s (global={38.0+t:.2f}s): rms={rms:.0f}")
