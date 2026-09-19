from search_cues import parse_vtt

cues = parse_vtt("Podcast_Video/Gun_1/lembke.en.vtt")

def time_to_sec(t_str):
    h, m, s = t_str.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

print("--- FULL TRANSCRIPT: 20:30 to 22:00 ---")
last_text = ""
for s, e, t in cues:
    sec = time_to_sec(s)
    if 20*60 + 30 <= sec <= 22*60:
        if t != last_text:
            print(f"[{s} -> {e}] {t}")
            last_text = t
