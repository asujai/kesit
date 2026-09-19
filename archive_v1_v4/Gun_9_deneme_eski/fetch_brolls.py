import os
import sys
import json
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.pexels_client import search_broll_video, download_video
from core.asset_registry import registry

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
BROLL_DIR = os.path.join(WORK_DIR, "dynamic_brolls")
os.makedirs(BROLL_DIR, exist_ok=True)

CUT_DEFINITIONS = [
    {
        "id": "c01_instagram_scroll",
        "start_t": 0.0,
        "end_t": 3.8,
        "query": "phone scrolling dark hands screen",
        "alt_queries": ["social media phone vertical scroll", "smart phone in dark room"],
        "in_point": 1.0
    },
    {
        "id": "c02_library_research",
        "start_t": 3.8,
        "end_t": 7.0,
        "query": "library books bookshelf cinematic study",
        "alt_queries": ["studying books research library", "books shelves vertical"],
        "in_point": 1.5
    },
    {
        "id": "c03_city_neon_digital",
        "start_t": 7.0,
        "end_t": 10.5,
        "query": "cyberpunk city night neon billboards",
        "alt_queries": ["night city lights skyscrapers vertical", "tokyo night neon digital"],
        "in_point": 1.0
    },
    {
        "id": "c04_stress_mental_health",
        "start_t": 10.5,
        "end_t": 14.0,
        "query": "depressed stressed person head in hands screen",
        "alt_queries": ["exhausted tired person dark room", "anxiety headache stress dark"],
        "in_point": 1.0
    },
    {
        "id": "c05_eye_screen_reflection",
        "start_t": 14.0,
        "end_t": 18.0,
        "query": "close up eye pupil looking screen light",
        "alt_queries": ["macro human eye blinking reflection", "eye looking at light dark"],
        "in_point": 1.0
    },
    {
        "id": "c06_hourglass_passing_time",
        "start_t": 18.0,
        "end_t": 22.0,
        "query": "hourglass sand falling time",
        "alt_queries": ["clock ticking antique time passing", "macro hourglass sand"],
        "in_point": 1.5
    },
    {
        "id": "c07_office_distracted_worker",
        "start_t": 22.0,
        "end_t": 25.5,
        "query": "office worker overwhelmed computer typing",
        "alt_queries": ["frustrated worker office desk", "man working late office computer"],
        "in_point": 1.0
    },
    {
        "id": "c08_couple_couch_phones",
        "start_t": 25.5,
        "end_t": 29.0,
        "query": "couple on couch looking at smartphones",
        "alt_queries": ["two people looking at phones together", "couple ignoring each other phone"],
        "in_point": 1.0
    },
    {
        "id": "c09_solitary_unsuccessful_walk",
        "start_t": 29.0,
        "end_t": 33.5,
        "query": "lonely man walking rain night city street",
        "alt_queries": ["solitary person walking dark city", "sad person walking street back view"],
        "in_point": 1.0
    },
    {
        "id": "c10_neural_brain_cognition",
        "start_t": 33.5,
        "end_t": 38.0,
        "query": "neural network brain digital glowing technology",
        "alt_queries": ["abstract brain network connections lights", "data network nodes glowing abstract"],
        "in_point": 1.0
    },
    {
        "id": "c11_global_city_timelapse",
        "start_t": 38.0,
        "end_t": 42.6,
        "query": "aerial city night lights traffic timelapse drone",
        "alt_queries": ["city drone hyperlapse night roads", "metropolis skyline lights night vertical"],
        "in_point": 2.0
    }
]

def main():
    resolved_cuts = []
    print(f"[*] Fetching B-roll candidates for {len(CUT_DEFINITIONS)} cuts...")

    for cut_def in CUT_DEFINITIONS:
        cid = cut_def["id"]
        target_file = os.path.join(BROLL_DIR, f"{cid}.mp4")
        dur = round(cut_def["end_t"] - cut_def["start_t"], 2)

        if os.path.exists(target_file) and os.path.getsize(target_file) > 100000:
            print(f"[OK] {cid} already downloaded: {target_file}")
            resolved_cuts.append({
                "id": cid,
                "source_file": os.path.relpath(target_file).replace("\\", "/"),
                "provider": "pexels",
                "asset_id": "cached",
                "in_point": cut_def["in_point"],
                "start_t": cut_def["start_t"],
                "end_t": cut_def["end_t"],
                "speed": 1.0
            })
            continue

        queries = [cut_def["query"]] + cut_def.get("alt_queries", [])
        found_asset = None

        for q in queries:
            print(f"   Searching for '{cid}' with query: '{q}'...")
            try:
                results = search_broll_video(q, orientation="portrait", per_page=6)
            except Exception as e:
                print(f"   Error searching query '{q}': {e}")
                results = []

            for candidate in results:
                aid = str(candidate["id"])
                # Avoid rejected or reused assets
                if registry.is_rejected("pexels", aid) or registry.is_used_in_day("pexels", aid, "Gun_9"):
                    print(f"   Skipping rejected/reused asset ID={aid}")
                    continue
                # Ensure candidate duration is enough
                c_dur = candidate.get("duration", 0)
                if c_dur >= dur + cut_def["in_point"]:
                    found_asset = candidate
                    break
                elif c_dur >= dur:
                    found_asset = candidate
                    cut_def["in_point"] = 0.0
                    break

            if found_asset:
                break

        # Fallback without portrait orientation if needed
        if not found_asset:
            print(f"   No portrait match for {cid}. Trying orientation=None...")
            try:
                results = search_broll_video(cut_def["query"], orientation=None, per_page=5)
                for candidate in results:
                    aid = str(candidate["id"])
                    if not registry.is_rejected("pexels", aid) and not registry.is_used_in_day("pexels", aid, "Gun_9"):
                        found_asset = candidate
                        break
            except Exception as e:
                print(f"   Fallback error: {e}")

        if not found_asset:
            raise RuntimeError(f"Could not find valid Pexels B-roll asset for cut {cid} (queries: {queries})")

        aid = str(found_asset["id"])
        download_url = found_asset["download_url"]
        print(f"   Downloading candidate ID={aid} ({found_asset.get('width')}x{found_asset.get('height')}, {found_asset.get('duration')}s) for {cid}...")
        download_video(download_url, target_file)

        registry.register_asset(
            provider="pexels",
            asset_id=aid,
            media_type="video",
            description=f"Cut {cid} B-roll",
            query=cut_def["query"],
            tags=["podcast_experiment", "jonathan_haidt", cid],
            file_path=target_file
        )

        resolved_cuts.append({
            "id": cid,
            "source_file": os.path.relpath(target_file).replace("\\", "/"),
            "provider": "pexels",
            "asset_id": aid,
            "in_point": cut_def["in_point"],
            "start_t": cut_def["start_t"],
            "end_t": cut_def["end_t"],
            "speed": 1.0
        })

    with open(os.path.join(WORK_DIR, "resolved_cuts.json"), "w", encoding="utf-8") as f:
        json.dump(resolved_cuts, f, indent=2)
    print(f"\n[DONE] All {len(resolved_cuts)} cuts fetched and saved to resolved_cuts.json")

if __name__ == "__main__":
    main()
