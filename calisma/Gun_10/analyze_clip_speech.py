import sys, os
sys.path.insert(0, r"c:\Users\abdul\kesiit")
from engine.candidate_ranker import CandidateRanker

cues = CandidateRanker.parse_vtt("calisma/hari_sub.en.vtt")
target_cues = [c for c in cues if 2373.0 <= c["start"] <= 2436.5]

# base_source was cut from 2370.0
# in_point in base_source is 3.10s
# let's calculate relative timestamps from in_point (which corresponds to t=0 in the output video)
ref_point = 2370.0 + 3.10

print("=== TIMESTAMPS RELATIVE TO CLIP START (0.0s) ===")
full_text_en = []
for c in target_cues:
    t_start = max(0.0, round(c["start"] - ref_point, 2))
    t_end = max(0.0, round(c["end"] - ref_point, 2))
    print(f"[{t_start:5.2f}s -> {t_end:5.2f}s] {c['text']}")
    full_text_en.append(c['text'])

print("\nFull English text:")
print(" ".join(full_text_en))
