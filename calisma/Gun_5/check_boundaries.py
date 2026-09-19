import subprocess

def test_slice(start, dur, name):
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-t", str(dur),
        "-i", "calisma/Gun_5/huberman_full.mp4",
        "-c:a", "pcm_s16le", f"calisma/Gun_5/test_{name}.wav"
    ]
    subprocess.run(cmd, capture_output=True)

test_slice(37.5, 5.0, "hook_38")
test_slice(72.0, 6.0, "hook_72")
test_slice(81.0, 5.0, "end_82")
test_slice(106.0, 5.0, "end_107")
test_slice(201.0, 6.0, "hook_201")
test_slice(261.0, 6.0, "end_263")
print("Slices extracted successfully.")
