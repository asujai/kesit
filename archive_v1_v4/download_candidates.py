from pexels_client import download_video
import subprocess

candidates = [
    ('broll_dark_bed_7986737.mp4', 'https://videos.pexels.com/video-files/7986737/7986737-uhd_2160_3840_25fps.mp4'),
    ('broll_phone_app_4318554.mp4', 'https://videos.pexels.com/video-files/4318554/4318554-hd_1080_1920_30fps.mp4'),
    ('broll_casino_chips_7607102.mp4', 'https://videos.pexels.com/video-files/7607102/7607102-uhd_2160_3840_24fps.mp4'),
    ('broll_scrolling_37021581.mp4', 'https://videos.pexels.com/video-files/37021581/15685294_2160_3840_30fps.mp4')
]

for name, url in candidates:
    print(f"Downloading {name}...")
    try:
        download_video(url, name)
        print(f"Downloaded {name}")
        # Extract snapshot
        snap_name = name.replace('.mp4', '.jpg')
        cmd = ['ffmpeg', '-y', '-ss', '00:00:02', '-i', name, '-frames:v', '1', '-q:v', '2', snap_name]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Extracted snapshot {snap_name}")
    except Exception as e:
        print(f"Failed {name}: {e}")
