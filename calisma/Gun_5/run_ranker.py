from engine.candidate_ranker import CandidateRanker
import json

eval_res = CandidateRanker.evaluate_candidates(
    'calisma/Gun_5/huberman_subs.en.vtt',
    goal="viral_awareness",
    out_log_path='calisma/Gun_5/candidate_evaluation.json'
)

print(f"Total candidates evaluated: {len(eval_res['candidates'])}")
for idx, c in enumerate(eval_res['candidates'][:8]):
    print(f"\n--- Candidate #{idx+1} (Score: {c['score']:.1f}) ---")
    print(f"ID: {c['id']} | [{c['start']:.1f}s -> {c['end']:.1f}s] ({c['duration']:.1f}s)")
    print(f"Hook: {c.get('hook_cue', '')}")
    print(f"Summary: {c['text'][:140]}...")
