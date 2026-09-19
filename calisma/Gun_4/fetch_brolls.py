import os
import time
import urllib.request
from core.pexels_client import search_broll_video
from core.pixabay_client import search_pixabay_videos

broll_dir = 'calisma/Gun_4/dynamic_brolls'
os.makedirs(broll_dir, exist_ok=True)

queries = [
    ('c01_fast_scroll', 'scrolling phone portrait', 'pexels'),
    ('c02_notification_tap', 'smartphone touch screen', 'pexels'),
    ('c03_screen_excitement', 'young man mobile screen light night', 'pexels'),
    ('c04_burnout_crash', 'tired exhausted face dark', 'pexels'),
    ('c05_night_bed_phone', 'person in bed using smartphone night dark', 'pexels'),
    ('c06_clock_timelapse', 'clock timelapse', 'pexels')
]

downloaded = {}

def download_file(url, target_path):
    print("Downloading -> " + target_path)
    tmp_path = target_path + ".tmp"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, 'wb') as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 100000:
        if os.path.exists(target_path):
            os.remove(target_path)
        os.rename(tmp_path, target_path)
        print("Success! Size: " + str(os.path.getsize(target_path)))
        return True
    else:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        print("Download failed or file too small!")
        return False

for cid, q, pref in queries:
    target_path = os.path.join(broll_dir, cid + ".mp4")
    if os.path.exists(target_path) and os.path.getsize(target_path) > 200000:
        print("Already exists: " + target_path)
        continue
    
    print("\n=== Searching for " + cid + ": " + q + " ===")
    vids = search_broll_video(q, orientation='portrait', per_page=5)
    if not vids:
        vids = search_broll_video(q, orientation=None, per_page=5)
    
    chosen = None
    provider = 'pexels'
    if vids:
        chosen = vids[0]
        print("Found Pexels: ID=" + str(chosen['id']) + " " + str(chosen['width']) + "x" + str(chosen['height']))
    else:
        print("Searching Pixabay...")
        pb_vids = search_pixabay_videos(q, per_page=5)
        if pb_vids:
            chosen = pb_vids[0]
            provider = 'pixabay'
            print("Found Pixabay: ID=" + str(chosen['id']))
            
    if chosen and chosen.get('download_url'):
        ok = download_file(chosen['download_url'], target_path)
        if ok:
            downloaded[cid] = {
                'provider': provider,
                'id': str(chosen['id']),
                'path': target_path
            }
    time.sleep(1.0)

print("\nDone downloading B-rolls. Downloaded count: " + str(len(downloaded)))
