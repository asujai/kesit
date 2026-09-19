import speech_recognition as sr

r = sr.Recognizer()
# Let's inspect 1-second sliding slices to pinpoint exact word boundaries
for t in range(28, 44):
    with sr.AudioFile("calisma/Gun_5/audio_clip.wav") as src:
        aud_slice = r.record(src, offset=float(t), duration=2.0)
    try:
        txt = r.recognize_google(aud_slice)
        print(f"[{t}.0s - {t+2}.0s]: {txt}")
    except Exception:
        pass
