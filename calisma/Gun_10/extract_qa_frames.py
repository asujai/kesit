import subprocess, os

video_path = "turkce/youtube/Gun_10/Gun_10_Shorts.mp4"
qa_frames_dir = "calisma/Gun_10/qa_verification_frames"
os.makedirs(qa_frames_dir, exist_ok=True)

timestamps = [2.0, 6.0, 10.0, 16.0, 25.0, 30.0, 43.0, 50.0, 54.0, 60.0]

for t in timestamps:
    out_f = os.path.join(qa_frames_dir, f"qa_frame_{int(t):02d}s.jpg")
    cmd = [
        "ffmpeg", "-y", "-ss", str(t),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        out_f
    ]
    subprocess.run(cmd, capture_output=True)
    print(f"Extracted frame at {t}s -> {out_f}")
