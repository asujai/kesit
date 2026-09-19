import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from core.pexels_client import search_broll_video

queries = [
    'smartphone notification screen',
    'text message incoming phone',
    'friends smartphone cafe table',
    'restaurant phone social media friends',
    'person scrolling phone fast',
    'people walking phone crowd'
]

for q in queries:
    print(f"\n==========================================")
    print(f"QUERY: {q}")
    print(f"==========================================")
    try:
        p_res = search_broll_video(q, orientation='portrait', per_page=4)
        if not p_res:
            p_res = search_broll_video(q, per_page=4)
        print("Pexels results:")
        for i, r in enumerate(p_res):
            print(f"  [{i}] ID: {r['id']} | Dur: {r['duration']}s | Res: {r['width']}x{r['height']}")
            print(f"       DL: {r['download_url'][:90]}...")
    except Exception as e:
        print(f"  Pexels error: {e}")
