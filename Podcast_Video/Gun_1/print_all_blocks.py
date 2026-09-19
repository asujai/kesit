import json

with open("Podcast_Video/Gun_1/subtitles_structured.json", "r", encoding="utf-8") as f:
    blocks = json.load(f)

for idx, b in enumerate(blocks[15:]):
    print(f"{idx+16:02d}. [{b['start']}s -> {b['end']}s] {b['en']}")
