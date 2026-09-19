import os
import sys
import urllib.request
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.pexels_client import search_broll_video as pexels_video, download_file
from core.pixabay_client import search_pixabay_videos as pixabay_video

def main():
    brolls = {
        'broll1_traffic': [
            'driver phone traffic',
            'driver using phone',
            'car phone steering'
        ],
        'broll2_cafe': [
            'friends cafe phone',
            'people phone dining',
            'friends talking phone'
        ],
        'broll3_night_bed': [
            'phone bed night dark',
            'woman phone bed',
            'person bed smartphone'
        ],
        'broll4_scrolling': [
            'scrolling phone close up',
            'phone screen scrolling',
            'smartphone tapping hand'
        ]
    }

    out_dir = os.path.join('calisma', 'Gun_2')
    os.makedirs(out_dir, exist_ok=True)

    print("--- PEXELS & PIXABAY B-ROLL DISCOVERY ---")
    for key, queries in brolls.items():
        print(f"\nSearching for {key}...")
        found = False
        for q in queries:
            try:
                results = pexels_video(q, orientation='portrait', per_page=4)
                if results:
                    best = results[0]
                    target_file = os.path.join(out_dir, f"{key}_{best['id']}.mp4")
                    print(f"  [Pexels] Found {q}: ID={best['id']}, res={best['width']}x{best['height']}, dur={best['duration']}s")
                    print(f"  Downloading to {target_file}...")
                    download_file(best['download_url'], target_file)
                    found = True
                    break
            except Exception as e:
                print(f"  Pexels query '{q}' error: {e}")

        if not found:
            # Fallback to Pixabay
            for q in queries:
                try:
                    res = pixabay_video(q, per_page=5)
                    if res:
                        best = res[0]
                        target_file = os.path.join(out_dir, f"{key}_{best['id']}.mp4")
                        print(f"  [Pixabay] Found {q}: ID={best['id']}, dur={best['duration']}s")
                        print(f"  Downloading to {target_file}...")
                        download_file(best['download_url'], target_file)
                        found = True
                        break
                except Exception as e:
                    print(f"  Pixabay query '{q}' error: {e}")

        if not found:
            print(f"  WARNING: No video found for {key}!")

if __name__ == '__main__':
    main()
