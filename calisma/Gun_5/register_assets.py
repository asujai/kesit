import json
import hashlib
from datetime import datetime

registry_path = "assets/asset_registry.json"
with open(registry_path, "r", encoding="utf-8") as f:
    registry = json.load(f)

assets_data = registry.setdefault("assets", {})

brolls = [
    {
        "key": "pexels_7362704",
        "provider": "pexels",
        "asset_id": "7362704",
        "media_type": "video",
        "description": "hands typing texting smartphone screen",
        "query": "hands typing texting smartphone screen",
        "tags": ["phone", "texting", "screen"],
        "file": "calisma/Gun_5/dynamic_brolls/c01_texting_scrolling.mp4",
        "start_t": 6.2,
        "end_t": 10.8
    },
    {
        "key": "pexels_6317317",
        "provider": "pexels",
        "asset_id": "6317317",
        "media_type": "video",
        "description": "young woman taking selfie smartphone smiling outdoors",
        "query": "young woman taking selfie smartphone smiling outdoors",
        "tags": ["selfie", "social media", "smile"],
        "file": "calisma/Gun_5/dynamic_brolls/c02_selfie_social.mp4",
        "start_t": 10.8,
        "end_t": 14.8
    },
    {
        "key": "pexels_19302670",
        "provider": "pexels",
        "asset_id": "19302670",
        "media_type": "video",
        "description": "people dining restaurant looking down smartphone",
        "query": "people dining restaurant looking down smartphone",
        "tags": ["dinner", "restaurant", "smartphone"],
        "file": "calisma/Gun_5/dynamic_brolls/c03_dinner_distraction.mp4",
        "start_t": 19.8,
        "end_t": 24.5
    },
    {
        "key": "pexels_35010179",
        "provider": "pexels",
        "asset_id": "35010179",
        "media_type": "video",
        "description": "digital brain glowing neural network technology",
        "query": "digital brain glowing neural network technology",
        "tags": ["brain", "neural", "dopamine"],
        "file": "calisma/Gun_5/dynamic_brolls/c04_neural_dopamine.mp4",
        "start_t": 29.8,
        "end_t": 34.5
    },
    {
        "key": "pexels_9063506",
        "provider": "pexels",
        "asset_id": "9063506",
        "media_type": "video",
        "description": "tired exhausted person resting head hands desk indoor",
        "query": "tired exhausted person resting head hands desk indoor",
        "tags": ["burnout", "tired", "exhaustion"],
        "file": "calisma/Gun_5/dynamic_brolls/c05_burnout_fatigue.mp4",
        "start_t": 34.5,
        "end_t": 38.5
    }
]

for b in brolls:
    hasher = hashlib.sha256()
    with open(b["file"], "rb") as bf:
        while chunk := bf.read(65536):
            hasher.update(chunk)
    fhash = hasher.hexdigest()

    assets_data[b["key"]] = {
        "provider": b["provider"],
        "asset_id": b["asset_id"],
        "media_type": b["media_type"],
        "description": b["description"],
        "query": b["query"],
        "tags": b["tags"],
        "file_hash": fhash,
        "created_at": datetime.now().isoformat(),
        "used_in": [
            {
                "day": "Gun_5",
                "start_t": b["start_t"],
                "end_t": b["end_t"],
                "duration": round(b["end_t"] - b["start_t"], 2),
                "notes": b["description"],
                "timestamp": datetime.now().isoformat()
            }
        ],
        "status": "approved"
    }

with open(registry_path, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print(f"Registered {len(brolls)} assets in {registry_path}.")
