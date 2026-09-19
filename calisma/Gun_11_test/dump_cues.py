import sys
sys.path.insert(0, '.')
from engine.candidate_ranker import CandidateRanker

cues = CandidateRanker.parse_vtt('calisma/Gun_11_test/Beyhan_Budak_Tembellik.tr.vtt')
with open('calisma/Gun_11_test/beyhan_cues_350_460.txt', 'w', encoding='utf-8') as f:
    for c in cues:
        if 350.0 <= c['start'] <= 460.0:
            f.write(f"{c['start']:.2f} -> {c['end']:.2f}: {c['text']}\n")

print("Wrote cues to calisma/Gun_11_test/beyhan_cues_350_460.txt")
