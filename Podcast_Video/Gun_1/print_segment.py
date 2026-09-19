from search_cues import parse_vtt

cues = parse_vtt("Podcast_Video/Gun_1/lembke.en.vtt")

def time_to_sec(t_str):
    h, m, s = t_str.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

print("--- SEGMENT -1: 08:00 to 15:00 ---")
for s, e, t in cues:
    sec = time_to_sec(s)
    if 8*60 <= sec <= 15*60:
        if any(k in t.lower() for k in ["balance", "teeter", "pain", "pleasure", "seesaw"]):
            print(f"[{s}] {t}")
