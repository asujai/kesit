import sys, os
sys.path.insert(0, os.path.abspath('.'))
from core.pexels_client import search_broll_video, download_file

res = search_broll_video('driver looking smartphone car', orientation='portrait', per_page=5)
for v in res:
    if v['id'] == 7362635 or v['id'] == 6170792 or v['id'] == 36067578:
        print(f"Downloading ID={v['id']}...")
        download_file(v['download_url'], f"calisma/Gun_2/alt_car_{v['id']}.mp4")
        break
