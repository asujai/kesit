import os
import json

with open("Podcast_Video/Gun_1/brolls_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

scenes = sorted(manifest.values(), key=lambda x: x["start"])
concat_file = "Podcast_Video/Gun_1/concat_list.txt"

with open(concat_file, "w", encoding="utf-8") as f:
    for sc in scenes:
        sc_id = sc["id"]
        # Use relative forward-slash path for ffmpeg concat
        f.write(f"file 'norm_cuts/{sc_id}_norm.mp4'\n")

print(f"Written {len(scenes)} entries to {concat_file}")
