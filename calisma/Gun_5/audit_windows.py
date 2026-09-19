import wave
import json
import speech_recognition as sr

r = sr.Recognizer()
with sr.AudioFile("calisma/Gun_5/audio_clip.wav") as source:
    audio = r.record(source)

# We can also transcribe in 2-second windows or use pocketsphinx / whisper if available
# Let's inspect small windows:
windows = [
    (0.0, 7.0),
    (6.0, 12.0),
    (11.0, 18.0),
    (17.0, 24.0),
    (23.0, 30.0),
    (29.0, 35.0),
    (34.0, 39.0),
    (38.0, 44.12)
]

for start, end in windows:
    with sr.AudioFile("calisma/Gun_5/audio_clip.wav") as src:
        # offset and duration
        aud_slice = r.record(src, offset=start, duration=(end - start))
    try:
        txt = r.recognize_google(aud_slice)
        print(f"[{start:4.1f}s - {end:4.1f}s]: {txt}")
    except Exception as e:
        print(f"[{start:4.1f}s - {end:4.1f}s]: <error: {e}>")
