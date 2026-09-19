import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from core.pexels_client import search_broll_photo, download_file
from core.pixabay_client import search_pixabay_images

print("--- SEARCHING REAL PHOTO FOR COVER ---")
queries = [
    'smartphone addiction dark',
    'alarm clock phone nightstand',
    'person checking smartphone bed night',
    'holding smartphone dark'
]

found = False
for q in queries:
    try:
        photos = search_broll_photo(q, orientation='portrait', per_page=5)
        if photos:
            print(f"Pexels results for '{q}':")
            for p in photos:
                print(f"  ID={p['id']}, res={p['width']}x{p['height']}")
            best = photos[0]
            out_file = os.path.join('calisma', 'Gun_2', f"cover_raw_{best['id']}.jpg")
            print(f"Downloading best photo to {out_file}...")
            download_file(best['download_url'], out_file)
            found = True
            break
    except Exception as e:
        print(f"Pexels error: {e}")

if not found:
    print("Trying Pixabay...")
    for q in queries:
        try:
            hits = search_pixabay_images(q, orientation='vertical', per_page=5)
            if hits:
                best = hits[0]
                out_file = os.path.join('calisma', 'Gun_2', f"cover_raw_{best['id']}.jpg")
                print(f"Pixabay found ID={best['id']}, downloading...")
                download_file(best['large_url'], out_file)
                found = True
                break
        except Exception as e:
            print(f"Pixabay error: {e}")
