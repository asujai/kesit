import json
import re

with open("Podcast_Video/Gun_1/subtitles_en.json", "r", encoding="utf-8") as f:
    subs = json.load(f)

# Group adjacent cues into clean speech blocks of 3-6 seconds
blocks = []
curr_block = {"start": subs[0]["start"], "end": subs[0]["end"], "words": []}

def clean_txt(t):
    t = re.sub(r"\b(\w+)\s+\1\b", r"\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t

for s in subs:
    txt = clean_txt(s["text"])
    if not txt:
        continue
    # If adding this would make duration > 4.5s or if there is a gap > 0.8s
    if s["start"] - curr_block["end"] > 0.8 or (s["end"] - curr_block["start"] > 4.5 and curr_block["words"]):
        full_text = " ".join(curr_block["words"])
        full_text = re.sub(r"\b(\w+)\s+\1\b", r"\1", full_text, flags=re.IGNORECASE)
        blocks.append({
            "start": round(curr_block["start"], 2),
            "end": round(curr_block["end"], 2),
            "text_en": full_text
        })
        curr_block = {"start": s["start"], "end": s["end"], "words": [txt]}
    else:
        curr_block["end"] = s["end"]
        # avoid duplicating words
        if not curr_block["words"] or curr_block["words"][-1] != txt:
            curr_block["words"].append(txt)

if curr_block["words"]:
    full_text = " ".join(curr_block["words"])
    blocks.append({
        "start": round(curr_block["start"], 2),
        "end": round(curr_block["end"], 2),
        "text_en": full_text
    })

print(f"Generated {len(blocks)} speech blocks.")
for i, b in enumerate(blocks[:10]):
    print(f"[{b['start']} - {b['end']}] {b['text_en']}")

with open("Podcast_Video/Gun_1/speech_blocks.json", "w", encoding="utf-8") as f:
    json.dump(blocks, f, indent=2, ensure_ascii=False)
