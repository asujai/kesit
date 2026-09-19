import speech_recognition as sr
import subprocess

r = sr.Recognizer()

for end in [64.5, 65.0, 65.5, 66.0, 66.5, 67.0]:
    wav_path = f"calisma/Gun_10/test_end_{end:.1f}.wav"
    cmd = [
        "ffmpeg", "-y", "-ss", "62.0", "-to", f"{end:.1f}",
        "-i", "calisma/Gun_10/base_source.mp4",
        "-ar", "16000", "-ac", "1",
        wav_path
    ]
    subprocess.run(cmd, capture_output=True)
    with sr.AudioFile(wav_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio)
        print(f"End {end:.1f}s -> '{text}'")
    except Exception as e:
        print(f"End {end:.1f}s -> error: {e}")
