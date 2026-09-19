import speech_recognition as sr
import subprocess

r = sr.Recognizer()

for start in [2.90, 2.95, 3.00, 3.05, 3.10, 3.15, 3.20]:
    wav_path = f"calisma/Gun_10/test_{start:.2f}.wav"
    cmd = [
        "ffmpeg", "-y", "-ss", f"{start:.2f}", "-t", "1.2",
        "-i", "calisma/Gun_10/base_source.mp4",
        "-ar", "16000", "-ac", "1",
        wav_path
    ]
    subprocess.run(cmd, capture_output=True)
    with sr.AudioFile(wav_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        print(f"Start {start:.2f}s -> '{text}'")
    except Exception as e:
        print(f"Start {start:.2f}s -> error: {e}")
