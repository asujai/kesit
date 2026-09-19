import os
import sys
sys.path.insert(0, '.')
from core.pexels_client import search_broll_video, download_video

broll_queries = [
    ("c01_procrastinating_desk_student", "procrastination student desk bored"),
    ("c02_putting_phone_away", "putting phone away desk table"),
    ("c03_staring_at_blank_wall", "bored person staring wall room"),
    ("c04_brain_dopamine_neurons", "brain neural network thoughts"),
    ("c05_deep_focus_work_flow", "focused study writing desk lamp")
]

out_dir = "calisma/Gun_11/dynamic_brolls"
os.makedirs(out_dir, exist_ok=True)

downloaded = []

for clip_id, query in broll_queries:
    print(f"\nSearching Pexels for: '{query}' ({clip_id})...")
    results = search_broll_video(query, orientation='portrait', per_page=6)
    if not results:
        print(f"  No portrait results, searching all orientations...")
        results = search_broll_video(query, orientation='all', per_page=6)
    
    if results:
        # Prefer HD/4K videos with duration >= 4s
        chosen = None
        for r in results:
            if r.get('duration', 0) >= 4:
                chosen = r
                break
        if not chosen:
            chosen = results[0]
            
        dest_path = os.path.join(out_dir, f"{clip_id}.mp4")
        print(f"  Selected: ID {chosen['id']} ({chosen['width']}x{chosen['height']}, {chosen['duration']}s)")
        download_video(chosen['download_url'], dest_path)
        downloaded.append({
            "id": clip_id,
            "source_file": dest_path.replace("\\", "/"),
            "provider": "pexels",
            "asset_id": str(chosen['id']),
            "duration": chosen['duration']
        })
    else:
        print(f"  ERROR: No video found for {query}")

print(f"\nSuccessfully downloaded {len(downloaded)}/5 B-rolls!")
