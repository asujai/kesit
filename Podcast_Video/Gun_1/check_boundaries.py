import sys
sys.path.append("Podcast_Video/Gun_1")
from search_cues import parse_vtt

cues = parse_vtt("Podcast_Video/Gun_1/lembke.en.vtt")

def t2s(t):
    h, m, s = t.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

print("--- CANDIDATE 1: 19:40 to 23:55 ---")
for s, e, t in cues:
    sec = t2s(s)
    if 19*60+30 <= sec <= 19*60+50:
        print(f"START?: [{s} -> {e}] {t}")
    if 23*60+40 <= sec <= 24*60+5:
        print(f"END?:   [{s} -> {e}] {t}")
