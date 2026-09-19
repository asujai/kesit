import json

with open("Podcast_Video/Gun_1/subtitles_raw.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Offset in raw_voice was 2.4s
clip_duration = 218.10

subs = []
for c in raw:
    s = round(c["start"] - 2.4, 2)
    e = round(c["end"] - 2.4, 2)
    if e > 0 and s < clip_duration:
        subs.append({
            "start": max(0.0, s),
            "end": min(clip_duration, e),
            "text": c["text"]
        })

print(f"Total adjusted cues: {len(subs)}")
print("First adjusted:", subs[0])
print("Last adjusted:", subs[-1])

with open("Podcast_Video/Gun_1/subtitles_en.json", "w", encoding="utf-8") as f:
    json.dump(subs, f, indent=2, ensure_ascii=False)
