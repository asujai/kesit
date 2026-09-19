import sys, os
sys.path.insert(0, os.path.abspath('.'))
from core.pexels_client import search_broll_video, download_file

queries = ['driver smartphone car', 'holding phone in car', 'person phone car red light', 'steering wheel smartphone']
for q in queries:
    print(f"Query: {q}")
    res = search_broll_video(q, orientation='portrait', per_page=4)
    for v in res:
        print(f"  ID={v['id']}, dur={v['duration']}, res={v['width']}x{v['height']}, url={v['download_url'][:60]}...")
