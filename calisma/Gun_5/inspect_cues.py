from engine.candidate_ranker import CandidateRanker

cues = CandidateRanker.parse_vtt('calisma/Gun_5/huberman_subs.en.vtt')
for c in cues:
    if 200 <= c['start'] <= 340:
        print(f"[{c['start']:.2f} - {c['end']:.2f}]: {c['text']}")
