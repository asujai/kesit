import sys
import json
import re

def parse_vtt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    cues = []
    curr_time = None
    curr_text = []
    time_pat = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})")
    
    for line in lines:
        line_str = line.strip()
        m = time_pat.match(line_str)
        if m:
            if curr_time and curr_text:
                full_text = " ".join(curr_text)
                full_text = re.sub(r"<[^>]+>", "", full_text).strip()
                if full_text:
                    cues.append((curr_time[0], curr_time[1], full_text))
            curr_time = (m.group(1), m.group(2))
            curr_text = []
        elif curr_time:
            if line_str and not line_str.startswith("NOTE") and not line_str.startswith("WEBVTT"):
                curr_text.append(line_str)
                
    if curr_time and curr_text:
        full_text = " ".join(curr_text)
        full_text = re.sub(r"<[^>]+>", "", full_text).strip()
        if full_text:
            cues.append((curr_time[0], curr_time[1], full_text))
            
    # Dedup consecutive duplicate text
    clean = []
    for c in cues:
        if not clean or clean[-1][2] != c[2]:
            clean.append(c)
    return clean

def t2s(t):
    h, m, s = t.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

cues = parse_vtt("Podcast_Video/Gun_1/lembke.en.vtt")

# The audio starts at exactly 20:20.000 = 1220.0s
offset = 20 * 60 + 20.0
audio_duration = 231.99

clip_cues = []
for s, e, text in cues:
    s_sec = t2s(s) - offset
    e_sec = t2s(e) - offset
    if e_sec > 0 and s_sec < audio_duration:
        start_clamped = max(0.0, round(s_sec, 2))
        end_clamped = min(audio_duration, round(e_sec, 2))
        if end_clamped > start_clamped:
            clip_cues.append({
                "start": start_clamped,
                "end": end_clamped,
                "text": text
            })

# Merge short fragmented cues to make clean subtitles
merged = []
for c in clip_cues:
    if not merged:
        merged.append(c)
    else:
        last = merged[-1]
        # if same text or very close gap with short text
        if last["text"] == c["text"]:
            last["end"] = c["end"]
        elif c["start"] - last["end"] < 0.3 and len(last["text"]) + len(c["text"]) < 60:
            last["text"] += " " + c["text"]
            last["end"] = c["end"]
        else:
            merged.append(c)

print(f"Total raw cues: {len(clip_cues)}, merged cues: {len(merged)}")
print("First 3:")
for c in merged[:3]:
    print(c)
print("Last 3:")
for c in merged[-3:]:
    print(c)

with open("Podcast_Video/Gun_1/subtitles_raw.json", "w", encoding="utf-8") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
