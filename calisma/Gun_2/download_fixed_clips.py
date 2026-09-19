import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from core.pexels_client import download_video

clips = {
    'notif_7822022': 'https://videos.pexels.com/video-files/7822022/7822022-hd_1080_1920_30fps.mp4',
    'cafe_7817089': 'https://videos.pexels.com/video-files/7817089/7817089-uhd_2160_3840_30fps.mp4',
    'scroll_10374885': 'https://videos.pexels.com/video-files/10374885/10374885-hd_1080_1920_24fps.mp4',
    'crowd_7823706': 'https://videos.pexels.com/video-files/7823706/7823706-uhd_2160_3840_30fps.mp4'
}

out_dir = os.path.join('calisma', 'Gun_2', 'dynamic_brolls')
os.makedirs(out_dir, exist_ok=True)

for name, url in clips.items():
    dest = os.path.join(out_dir, f"{name}.mp4")
    if not os.path.exists(dest) or os.path.getsize(dest) < 10000:
        print(f"Downloading {name}...")
        download_video(url, dest)
        print(f"Saved to {dest}, size={os.path.getsize(dest)} bytes")
    else:
        print(f"Already downloaded: {name}")
