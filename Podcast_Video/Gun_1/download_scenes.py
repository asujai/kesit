import os
import sys
import json
import time

sys.path.append("core")
from pexels_client import search_broll_video, download_video
from pixabay_client import search_pixabay_videos

# Define 41 scenes mapped to the narrative blocks
SCENE_PLAN = [
    # Act 1: Ancient Wiring & Scarcity (0s - 31s)
    {"id": "s01", "name": "ancient_fire", "query": "campfire in dark forest", "start": 0.0, "end": 4.36},
    {"id": "s02", "name": "hunter_nature", "query": "man walking in wild misty mountains", "start": 4.36, "end": 9.32},
    {"id": "s03", "name": "ancient_shelter", "query": "primitive wooden cabin fog", "start": 9.32, "end": 13.44},
    {"id": "s04", "name": "neural_brain", "query": "glowing brain neurons firing", "start": 13.44, "end": 20.28},
    {"id": "s05", "name": "dopamine_synapse", "query": "abstract neural network connection", "start": 20.28, "end": 25.64},
    {"id": "s06", "name": "synthetic_pills", "query": "laboratory pills chemical synthesis", "start": 25.64, "end": 31.44},
    
    # Act 2: The Modern Mismatch & Internet Addiction (31s - 65s)
    {"id": "s07", "name": "neon_internet", "query": "cyberpunk neon city data highway", "start": 31.44, "end": 36.28},
    {"id": "s08", "name": "phone_face", "query": "person face illuminated by phone screen dark", "start": 36.28, "end": 40.36},
    {"id": "s09", "name": "scrolling_zombie", "query": "fingers scrolling fast on smartphone", "start": 40.36, "end": 44.36},
    {"id": "s10", "name": "quote_screen", "query": "matrix code stream technology", "start": 44.36, "end": 50.48},
    {"id": "s11", "name": "digital_trap", "query": "man looking at glowing screen hypnotized", "start": 50.48, "end": 54.72},
    {"id": "s12", "name": "website_temptation", "query": "server room flashing lights internet", "start": 54.72, "end": 59.44},
    {"id": "s13", "name": "scarcity_desert", "query": "dry cracked earth desert wind", "start": 59.44, "end": 65.52},
    
    # Act 3: Overwhelming Overabundance & Hedonic Overload (65s - 105s)
    {"id": "s14", "name": "overabundance_mall", "query": "crowded shopping mall consumerism timelapse", "start": 65.52, "end": 69.92},
    {"id": "s15", "name": "endless_shelves", "query": "supermarket shelves colorful products", "start": 69.92, "end": 74.28},
    {"id": "s16", "name": "fast_food_junk", "query": "junk food burger fries feast dripping", "start": 74.28, "end": 80.2},
    {"id": "s17", "name": "casino_lights", "query": "casino roulette lights spinning excitement", "start": 80.2, "end": 84.72},
    {"id": "s18", "name": "sensory_overload", "query": "overwhelmed woman head in hands stress", "start": 84.72, "end": 89.28},
    {"id": "s19", "name": "digital_deluge", "query": "streams of digital particles flooding", "start": 89.28, "end": 95.2},
    {"id": "s20", "name": "endless_dopamine", "query": "times square neon billboards night chaos", "start": 95.2, "end": 100.28},
    {"id": "s21", "name": "scale_intro", "query": "vintage brass balance scale weight", "start": 100.28, "end": 105.16},
    
    # Act 4: The Pleasure-Pain Balance & Gremlins (105s - 156s)
    {"id": "s22", "name": "scale_tipping", "query": "pendulum swinging rhythmically dark", "start": 105.16, "end": 111.32},
    {"id": "s23", "name": "equilibrium_restored", "query": "smooth calm water drops ripples balance", "start": 111.32, "end": 117.04},
    {"id": "s24", "name": "seesaw_movement", "query": "empty playground seesaw moving alone", "start": 117.04, "end": 121.52},
    {"id": "s25", "name": "time_passing", "query": "hourglass sand running through glass", "start": 121.52, "end": 126.32},
    {"id": "s26", "name": "chain_smoke_addict", "query": "man smoking cigarette dark cinematic room", "start": 126.32, "end": 131.72},
    {"id": "s27", "name": "binge_screens", "query": "multiple screens glowing in dark room", "start": 131.72, "end": 137.64},
    {"id": "s28", "name": "heavy_weights", "query": "iron gears rusty machinery grinding", "start": 137.64, "end": 145.12},
    {"id": "s29", "name": "dark_camp", "query": "dark eerie smoke creeping ground", "start": 145.12, "end": 151.16},
    {"id": "s30", "name": "entrapped_mind", "query": "man trapped looking out barred window", "start": 151.16, "end": 156.72},
    
    # Act 5: Addicted Brain & Hedonic Setpoint Shift (156s - 191s)
    {"id": "s31", "name": "joy_setpoint_shift", "query": "desolate abandoned building corridor", "start": 156.72, "end": 160.88},
    {"id": "s32", "name": "seeking_more", "query": "restless man pacing in dark apartment", "start": 160.88, "end": 167.64},
    {"id": "s33", "name": "just_to_feel_normal", "query": "exhausted person washing face in bathroom mirror", "start": 167.64, "end": 175.04},
    {"id": "s34", "name": "empty_vessel", "query": "pouring water into overflowing glass", "start": 175.04, "end": 182.12},
    {"id": "s35", "name": "unquenchable_thirst", "query": "dry parched cracked mud close up", "start": 182.12, "end": 187.32},
    {"id": "s36", "name": "struggling_balance", "query": "tightrope walker balancing silhouette", "start": 187.32, "end": 191.8},
    
    # Act 6: Withdrawal Symptoms & Punchline Climax (191s - 218s)
    {"id": "s37", "name": "phone_put_down", "query": "putting smartphone face down on wooden table", "start": 191.8, "end": 196.08},
    {"id": "s38", "name": "subway_zombies", "query": "commuters on subway staring down at phones", "start": 196.08, "end": 202.16},
    {"id": "s39", "name": "anxiety_irritability", "query": "anxious person tapping fingers nervously", "start": 202.16, "end": 207.12},
    {"id": "s40", "name": "insomnia_tossing", "query": "person unable to sleep tossing in bed clock ticking", "start": 207.12, "end": 212.68},
    {"id": "s41", "name": "depression_craving_final", "query": "lone figure walking away in heavy rain storm night", "start": 212.68, "end": 218.10}
]

out_dir = "Podcast_Video/Gun_1/dynamic_brolls"
os.makedirs(out_dir, exist_ok=True)

manifest_file = "Podcast_Video/Gun_1/brolls_manifest.json"
manifest = {}
if os.path.exists(manifest_file):
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

print(f"Starting download plan for {len(SCENE_PLAN)} cinematic landscape scenes...")

for idx, sc in enumerate(SCENE_PLAN):
    sc_id = sc["id"]
    out_name = f"{sc_id}_{sc['name']}.mp4"
    out_path = os.path.join(out_dir, out_name)
    
    if sc_id in manifest and os.path.exists(manifest[sc_id].get("file_path", "")) and os.path.getsize(manifest[sc_id]["file_path"]) > 50000:
        print(f"[{idx+1}/{len(SCENE_PLAN)}] Already cached: {sc_id} -> {out_name}")
        continue
        
    print(f"\n[{idx+1}/{len(SCENE_PLAN)}] Searching Pexels for '{sc['query']}' (landscape)...")
    success = False
    
    # Try Pexels first
    try:
        results = search_broll_video(sc["query"], orientation="landscape", per_page=4)
        if results:
            best = results[0]
            print(f"  Found on Pexels ({best['width']}x{best['height']}, {best['duration']}s). Downloading...")
            download_video(best["download_url"], out_path)
            manifest[sc_id] = {
                "id": sc_id,
                "name": sc["name"],
                "query": sc["query"],
                "provider": "pexels",
                "width": best["width"],
                "height": best["height"],
                "file_path": out_path,
                "start": sc["start"],
                "end": sc["end"]
            }
            success = True
    except Exception as e:
        print(f"  Pexels error: {e}")
        
    # Fallback to Pixabay if Pexels fails
    if not success:
        print(f"  Trying Pixabay fallback for '{sc['query']}'...")
        try:
            pix_res = search_pixabay_videos(sc["query"], per_page=4)
            if pix_res:
                best_pix = pix_res[0]
                print(f"  Found on Pixabay ({best_pix['width']}x{best_pix['height']}, {best_pix['duration']}s). Downloading...")
                download_video(best_pix["download_url"], out_path)
                manifest[sc_id] = {
                    "id": sc_id,
                    "name": sc["name"],
                    "query": sc["query"],
                    "provider": "pixabay",
                    "width": best_pix["width"],
                    "height": best_pix["height"],
                    "file_path": out_path,
                    "start": sc["start"],
                    "end": sc["end"]
                }
                success = True
        except Exception as e2:
            print(f"  Pixabay error: {e2}")

    if not success:
        print(f"  WARNING: Could not download video for {sc_id} ({sc['query']})")

    # Save manifest progressively
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    time.sleep(0.5)

print(f"\nFinished scene download! Total downloaded: {len(manifest)}/{len(SCENE_PLAN)}")
