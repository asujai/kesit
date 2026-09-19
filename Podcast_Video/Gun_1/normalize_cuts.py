import os
import json
import subprocess

with open("Podcast_Video/Gun_1/brolls_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

norm_dir = "Podcast_Video/Gun_1/norm_cuts"
os.makedirs(norm_dir, exist_ok=True)

# List scenes ordered by start time
scenes = sorted(manifest.values(), key=lambda x: x["start"])

print(f"Normalizing {len(scenes)} scenes to 1920x1080 @ 25fps...")

for idx, sc in enumerate(scenes):
    sc_id = sc["id"]
    in_path = sc["file_path"]
    duration = round(sc["end"] - sc["start"], 2)
    out_path = os.path.join(norm_dir, f"{sc_id}_norm.mp4")
    
    if os.path.exists(out_path) and os.path.getsize(out_path) > 20000:
        continue
        
    print(f"[{idx+1}/{len(scenes)}] Normalizing {sc_id} (duration={duration}s)...")
    
    # ffmpeg normalize filter: scale, crop to 1920x1080, set fps=25
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0.0",
        "-t", str(duration),
        "-i", in_path,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("All scenes normalized successfully!")
