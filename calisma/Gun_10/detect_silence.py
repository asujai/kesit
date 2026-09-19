import subprocess, json

# Run silencedetect on base_source.mp4
cmd = [
    "ffmpeg", "-i", "calisma/Gun_10/base_source.mp4",
    "-af", "silencedetect=noise=-30dB:d=0.3",
    "-f", "null", "-"
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Silence detect lines:")
for line in res.stderr.split("\n"):
    if "silencedetect" in line:
        print(line)
