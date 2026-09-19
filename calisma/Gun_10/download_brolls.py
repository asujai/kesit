import os, sys
sys.path.insert(0, r"c:\Users\abdul\kesiit")
from core.pexels_client import search_broll_video, download_video

broll_queries = [
    ("c01_corporate_office_workers", "corporate office workers teamwork", 4.0),
    ("c02_smartphone_distracted_worker", "checking smartphone texting desk", 5.0),
    ("c03_brain_intelligence_scan", "brain neuron glowing network", 5.0),
    ("c04_stressed_headache_overwhelmed", "stressed worker headache desk", 5.5),
    ("c05_smoke_rising_cinematic", "smoke rising slow motion dark", 5.5),
    ("c06_social_media_phone_scroll", "phone addiction scrolling", 5.5),
    ("c07_deep_work_single_focus", "focused person working laptop desk", 4.0),
]

out_dir = "calisma/Gun_10/dynamic_brolls"
os.makedirs(out_dir, exist_ok=True)

selected_cuts = []

for cut_id, query, dur in broll_queries:
    print(f"\nSearching for '{query}' (Cut: {cut_id}, Duration: {dur}s)...")
    results = search_broll_video(query, orientation='portrait', per_page=4)
    if not results:
        print(f"Fallback searching 'all' orientation for '{query}'...")
        results = search_broll_video(query, orientation='all', per_page=4)
    
    if results:
        best = results[0]
        out_file = os.path.join(out_dir, f"{cut_id}.mp4")
        print(f"  -> Selected ID {best['id']} ({best.get('width')}x{best.get('height')}, {best.get('duration')}s)")
        print(f"  -> Downloading to {out_file}...")
        download_video(best['download_url'], out_file)
        selected_cuts.append({
            "id": cut_id,
            "source_file": out_file,
            "provider": "pexels",
            "asset_id": str(best['id']),
            "width": best.get('width'),
            "height": best.get('height'),
            "duration": best.get('duration')
        })
    else:
        print(f"  [!] No results for '{query}'")

print(f"\nSuccessfully downloaded {len(selected_cuts)} / {len(broll_queries)} B-rolls!")
