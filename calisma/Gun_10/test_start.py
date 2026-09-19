import subprocess

# Let's extract audio clips around 2.8s to 4.5s
cmd = [
    "ffmpeg", "-y", "-ss", "2.8", "-to", "7.0",
    "-i", "calisma/Gun_10/base_source.mp4",
    "-ar", "16000", "-ac", "1",
    "calisma/Gun_10/test_audio_start.wav"
]
subprocess.run(cmd, capture_output=True)
print("Extracted test_audio_start.wav")
