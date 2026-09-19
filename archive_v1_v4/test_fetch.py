import json
from pexels_client import search_broll_video
from pixabay_client import search_pixabay_videos, search_pixabay_images

print("--- Pexels Social Media Videos ---")
p_vids = search_broll_video('social media phone', orientation='portrait', per_page=5)
for v in p_vids:
    print(f"Pexels ID: {v['id']}, Res: {v['width']}x{v['height']}, Dur: {v['duration']}s, URL: {v['download_url'][:50]}")

print("\n--- Pixabay Social Media Videos ---")
pb_vids = search_pixabay_videos('social media', per_page=5)
for v in pb_vids:
    print(f"Pixabay ID: {v['id']}, Res: {v['width']}x{v['height']}, Dur: {v['duration']}s, URL: {v['download_url'][:50]}")

print("\n--- Pixabay Vertical Images (Facebook / Instagram / Phone) ---")
pb_imgs = search_pixabay_images('smartphone screen', orientation='vertical', per_page=5)
for img in pb_imgs:
    print(f"Pixabay Img ID: {img['id']}, Res: {img['width']}x{img['height']}, URL: {img['download_url'][:50]}")
