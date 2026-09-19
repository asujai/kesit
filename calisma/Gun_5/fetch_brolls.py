import os
import json
from core.pexels_client import search_broll_video, download_file

work_dir = "calisma/Gun_5"
dynamic_broll_dir = os.path.join(work_dir, "dynamic_brolls")
os.makedirs(dynamic_broll_dir, exist_ok=True)

# Load existing registry to avoid repetition
registry_path = "assets/asset_registry.json"
used_ids = set()
if os.path.exists(registry_path):
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f).get("assets", {})
        used_ids = set(reg.keys())

print(f"Loaded {len(used_ids)} previously registered assets to avoid.")

queries = {
    "c01_texting_scrolling": "hands typing texting smartphone screen",
    "c02_selfie_social": "young woman taking selfie smartphone smiling outdoors",
    "c03_dinner_distraction": "people dining restaurant looking down smartphone",
    "c04_neural_dopamine": "digital brain glowing neural network technology",
    "c05_burnout_fatigue": "tired exhausted person resting head hands desk indoor"
}

results = {}

for cut_id, query in queries.items():
    print(f"\n--- Searching for {cut_id}: '{query}' ---")
    videos = search_broll_video(query, orientation='portrait', per_page=8)
    chosen = None
    for v in videos:
        key = f"pexels_{v['id']}"
        if key in used_ids:
            print(f"Skipping already used asset: {key}")
            continue
        # Check duration >= 3.5
        if v.get('duration', 0) >= 3.5:
            chosen = v
            break
    
    if not chosen and videos:
        chosen = videos[0]

    if chosen:
        print(f"Found candidate: Pexels ID {chosen['id']} ({chosen['duration']}s, {chosen['width']}x{chosen['height']})")
        out_file = os.path.join(dynamic_broll_dir, f"{cut_id}.mp4")
        if not os.path.exists(out_file) or os.path.getsize(out_file) < 10000:
            print(f"Downloading {chosen['download_url'][:60]}... -> {out_file}")
            download_file(chosen['download_url'], out_file)
            print(f"Downloaded {os.path.getsize(out_file)} bytes.")
        else:
            print(f"File already exists: {out_file} ({os.path.getsize(out_file)} bytes)")

        results[cut_id] = {
            "source_file": out_file.replace("\\", "/"),
            "provider": "pexels",
            "asset_id": str(chosen['id']),
            "duration": chosen['duration'],
            "width": chosen['width'],
            "height": chosen['height'],
            "description": query
        }
    else:
        print(f"No candidate found for {cut_id}!")

with open(os.path.join(work_dir, "broll_selection.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nAll B-rolls processed successfully.")
