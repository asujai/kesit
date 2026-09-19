import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from core.giphy_client import search_gifs, download_file

out_dir = os.path.join('calisma', 'Gun_2', 'dynamic_brolls')
os.makedirs(out_dir, exist_ok=True)

items = [
    ('cut_04_notification_pop', 'notification smartphone'),
    ('cut_08_fast_scroll_gif', 'scroll phone')
]

for key, q in items:
    print(f"Searching GIPHY for '{q}'...")
    res = search_gifs(q, limit=5)
    best = next((g for g in res if g.get('mp4_url')), None)
    if best:
        out_file = os.path.join(out_dir, f"{key}.mp4")
        print(f"  Found: {best['title']}, downloading MP4...")
        download_file(best['mp4_url'], out_file)
        print(f"  Saved to {out_file}")
    else:
        print(f"  No mp4 found for '{q}'")
