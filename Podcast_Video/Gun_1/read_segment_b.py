from search_cues import parse_vtt

cues = parse_vtt("Podcast_Video/Gun_1/lembke.en.vtt")

def time_to_sec(t_str):
    h, m, s = t_str.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

print("=== SEGMENT B: 16:30 to 20:35 ===")
for s, e, t in cues:
    sec = time_to_sec(s)
    if 16*60 + 30 <= sec <= 20*60 + 35:
        print(f"[{s} -> {e}] {t}")
