from engine.candidate_ranker import CandidateRanker

cues = CandidateRanker.parse_vtt('calisma/Gun_5/huberman_subs.en.vtt')
clip_start = 38.38
clip_end = 82.50

clip_cues = []
for c in cues:
    if c['end'] >= clip_start and c['start'] <= clip_end:
        rel_s = max(0.0, c['start'] - clip_start)
        rel_e = min(clip_end - clip_start, c['end'] - clip_start)
        clip_cues.append({
            'start': round(rel_s, 2),
            'end': round(rel_e, 2),
            'orig_start': c['start'],
            'orig_end': c['end'],
            'text': c['text']
        })

for idx, cc in enumerate(clip_cues):
    print(f"[{cc['start']:5.2f}s -> {cc['end']:5.2f}s] (orig: {cc['orig_start']:5.2f}s): {cc['text']}")
