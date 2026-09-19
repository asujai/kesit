import os
import json
from core.pexels_client import get_pexels_api_key, _make_request, download_video

api_key = get_pexels_api_key()
headers = {'Authorization': api_key, 'User-Agent': 'Mozilla/5.0'}

targets = [
    {'id': '6327106', 'name': 'c01_talking_holding_phone.mp4', 'desc': 'Friends talking at table holding smartphone'},
    {'id': '6611951', 'name': 'c02_silent_phone_hand.mp4', 'desc': 'Person holding smartphone silent in hand'},
    {'id': '6953394', 'name': 'c03_dinner_table_phone.mp4', 'desc': 'Dinner table with friends using phone'},
    {'id': '6374206', 'name': 'c04_phone_on_table.mp4', 'desc': 'Smartphone lying on wooden table'}
]

out_dir = os.path.join('calisma', 'Gun_7', 'dynamic_brolls')
os.makedirs(out_dir, exist_ok=True)

for t in targets:
    out_path = os.path.join(out_dir, t['name'])
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
        print(f"Exists: {t['name']}")
        continue
    url = f"https://api.pexels.com/videos/videos/{t['id']}"
    data = _make_request(url, headers=headers)
    files = [f for f in data.get('video_files', []) if f.get('file_type') == 'video/mp4']
    files.sort(key=lambda x: (x.get('height', 0) * x.get('width', 0)), reverse=True)
    best = files[0]
    print(f"Downloading {t['name']} ({best.get('width')}x{best.get('height')})...")
    download_video(best['link'], out_path)
    print(f"Downloaded {t['name']}: {os.path.getsize(out_path)} bytes")

print("All candidates downloaded.")
