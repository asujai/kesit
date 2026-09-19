from pexels_client import search_broll_video
from pixabay_client import search_pixabay_videos, search_pixabay_images
import json

queries = [
    ('instagram feed', 'portrait'),
    ('social media smartphone', 'portrait'),
    ('phone bed dark', 'portrait'),
    ('phone addiction hypnotic', 'portrait'),
    ('scrolling screen', 'portrait'),
    ('casino chips', 'portrait'),
    ('roulette wheel', 'portrait')
]

for q, o in queries:
    print(f"=== Query: '{q}' ({o}) ===")
    vids = search_broll_video(q, orientation=o, per_page=4)
    for v in vids:
        print(f"ID: {v['id']} | Res: {v['width']}x{v['height']} | Dur: {v['duration']}s | URL: {v['download_url'][:70]}")
    print()
