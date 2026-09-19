import urllib.request
import urllib.parse
import json
import os
from pexels_client import get_pexels_api_key

api_key = get_pexels_api_key()
queries = [
    "instagram reels",
    "social media addiction",
    "scrolling feeds mobile",
    "facebook scrolling"
]

for q in queries:
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&orientation=portrait&per_page=4"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(f"\n=== {q} ===")
    for v in data.get("videos", []):
        v_files = v.get("video_files", [])
        best = [f for f in v_files if f.get("width") and f["width"] >= 1080 and f.get("height", 0) > f.get("width", 0)]
        link = best[0]["link"] if best else (v_files[0]["link"] if v_files else "")
        print(f"ID: {v['id']} | {v['width']}x{v['height']} | {v['duration']}s | thumb: {v.get('image')} | link: {link[:70]}...")
