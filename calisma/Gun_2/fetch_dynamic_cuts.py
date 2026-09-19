import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from core.pexels_client import search_broll_video, download_file as pexels_dl
from core.giphy_client import search_gifs, search_stickers, download_file as giphy_dl

out_dir = os.path.join('calisma', 'Gun_2', 'dynamic_brolls')
os.makedirs(out_dir, exist_ok=True)

# Define search targets for 1-2 second micro-cuts
targets = {
    # 1. Bus passenger looking at phone
    'cut_01_bus_phone': ('bus passenger smartphone', 'pexels'),
    # 2. Traffic red light / cars waiting
    'cut_02_red_light': ('traffic red light car', 'pexels'),
    # 3. Second cafe / friends ignoring
    'cut_03_cafe_second': ('two people smartphone cafe', 'pexels'),
    # 4. Message / Notification pop-up GIF
    'cut_04_notification_pop': ('phone notification', 'giphy'),
    # 5. Person walking dark bedroom / night
    'cut_05_night_bedroom_dark': ('person night bed room dark', 'pexels'),
    # 6. Face illuminated by blue light in dark
    'cut_06_blue_light_face': ('face blue light smartphone dark', 'pexels'),
    # 7. Pedestrians looking down at phones (phone zombies)
    'cut_07_walking_phone': ('people walking phone crowd', 'pexels'),
    # 8. Crazy fast scrolling / typing GIF
    'cut_08_fast_scroll_gif': ('scrolling phone fast', 'giphy'),
    # 9. Phone addiction metaphor / chain
    'cut_09_phone_chains': ('smartphone addiction', 'pexels')
}

print("--- FETCHING DYNAMIC MICRO-CUT ASSETS ---")

for key, (query, source) in targets.items():
    print(f"\nProcessing {key} (query: '{query}', source: {source})...")
    out_file = os.path.join(out_dir, f"{key}.mp4")
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        print(f"  Already exists: {out_file}")
        continue

    if source == 'pexels':
        try:
            res = search_broll_video(query, orientation='portrait', per_page=4)
            if not res:
                # try without portrait constraint
                res = search_broll_video(query, orientation='all', per_page=4)
            if res:
                best = res[0]
                print(f"  [Pexels] Found ID={best['id']}, dur={best['duration']}s, res={best['width']}x{best['height']}")
                pexels_dl(best['download_url'], out_file)
                print(f"  Downloaded to {out_file}")
            else:
                print(f"  No Pexels result for '{query}'")
        except Exception as e:
            print(f"  Pexels error for '{query}': {e}")

    elif source == 'giphy':
        try:
            res = search_gifs(query, limit=3)
            if res:
                # find first with mp4_url
                best = None
                for g in res:
                    if g.get('mp4_url'):
                        best = g
                        break
                if best:
                    print(f"  [GIPHY] Found title='{best['title']}' ID={best['id']}")
                    giphy_dl(best['mp4_url'], out_file)
                    print(f"  Downloaded to {out_file}")
                else:
                    print(f"  No mp4_url in GIPHY results for '{query}'")
            else:
                print(f"  No GIPHY results for '{query}'")
        except Exception as e:
            print(f"  GIPHY error for '{query}': {e}")
