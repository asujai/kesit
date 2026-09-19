import os
from pexels_client import search_broll_video

queries = [
    "instagram phone",
    "facebook feed",
    "smartphone addiction dark",
    "slot machine casino"
]

for q in queries:
    res = search_broll_video(q, orientation="portrait", per_page=3)
    print(f"\n--- Query: {q} ---")
    for v in res:
        print(f"ID: {v['id']} | {v['width']}x{v['height']} | {v['duration']}s | Link: {v['download_url'][:80]}")
