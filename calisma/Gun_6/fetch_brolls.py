import os
import sys
import json
from core.pexels_client import get_pexels_api_key, _make_request, download_video

work_dir = os.path.dirname(os.path.abspath(__file__))
brolls_dir = os.path.join(work_dir, "dynamic_brolls")
os.makedirs(brolls_dir, exist_ok=True)

targets = [
    {
        "id": "36067574",
        "name": "c01_hazardous_driving.mp4",
        "description": "Driver looking down and texting on smartphone while driving"
    },
    {
        "id": "7279738",
        "name": "c02_social_isolation.mp4",
        "description": "Person alone in dark moody room absorbed in smartphone"
    },
    {
        "id": "4318554",
        "name": "c03_screentime_tolerance.mp4",
        "description": "Vertical smartphone screen rapid feed scrolling"
    },
    {
        "id": "6598883",
        "name": "c04_doomscroll_night.mp4",
        "description": "Night bedroom insomnia doomscrolling in dark"
    },
    {
        "id": "6672202",
        "name": "c05_abandoned_hobbies.mp4",
        "description": "Acoustic guitar sitting untouched in atmospheric room"
    }
]

api_key = get_pexels_api_key()
headers = {
    "Authorization": api_key,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

for t in targets:
    out_path = os.path.join(brolls_dir, t["name"])
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
        print(f"Already exists: {t['name']}")
        continue
    
    url = f"https://api.pexels.com/videos/videos/{t['id']}"
    print(f"Fetching metadata for {t['name']} (ID: {t['id']})...")
    data = _make_request(url, headers=headers)
    
    files = [f for f in data.get("video_files", []) if f.get("file_type") == "video/mp4"]
    files.sort(key=lambda x: (x.get("height", 0) * x.get("width", 0)), reverse=True)
    best_file = files[0]
    dl_url = best_file["link"]
    print(f"Downloading {t['name']} ({best_file.get('width')}x{best_file.get('height')})...")
    download_video(dl_url, out_path)
    print(f"Saved: {out_path} ({os.path.getsize(out_path)} bytes)")

print("All B-rolls successfully downloaded.")
