import speech_recognition as sr
import subprocess

r = sr.Recognizer()

for start in [2.5, 2.8, 3.0, 3.2, 3.4]:
    wav_path = f"calisma/Gun_10/test_{start}.wav"
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-t", "3.0",
        "-i", "calisma/Gun_10/base_source.mp4",
        "-ar", "16000", "-ac", "1",
        wav_path
    ]
    subprocess.run(cmd, capture_output=True)
    with sr.AudioFile(wav_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        print(f"Start {start}s -> '{text}'")
    except Exception as e:
        print(f"Start {start}s -> error: {e}")
