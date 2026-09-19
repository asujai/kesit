import os
import sys
import json
sys.path.insert(0, '.')
from engine.candidate_ranker import CandidateRanker
from core.jev_client import JevClient

vtts = [
    ('calisma/Gun_11_test/Baris_Ozcan_Erteleme.tr.vtt', 'Baris Ozcan', 'Erteleme Hastalığı Çözümü', 'oN_8J6W8iJE'),
    ('calisma/Gun_11_test/Baris_Ozcan_Zinciri_Kirma.tr.vtt', 'Baris Ozcan', 'Zinciri Kırma Yöntemi', 'oNmXH2uN0Do'),
    ('calisma/Gun_11_test/Beyhan_Budak_8_Cozum.tr.vtt', 'Beyhan Budak', 'Ertelemeye 8 Çözüm', 'IuM-cHQkYbs'),
    ('calisma/Gun_11_test/Beyhan_Budak_Tembellik.tr.vtt', 'Beyhan Budak', 'Tembellikten Kurtulma 8 Yöntem', 'kX_7pNDVwYA')
]

top_candidates = []

for path, speaker, topic, vid in vtts:
    cues = CandidateRanker.parse_vtt(path)
    
    # We look for cohesive windows
    for i in range(len(cues)):
        start_t = cues[i]["start"]
        start_txt = cues[i]["text"].strip()
        
        # Avoid starting mid-sentence or with connecting conjunctions
        if start_txt.lower().startswith(('ve ', 'ama ', 'fakat ', 'çünkü ', 'yani ', 'veya ', 'oysa ')):
            continue
            
        for j in range(i + 2, len(cues)):
            end_t = cues[j]["end"]
            dur = end_t - start_t
            if dur > 58.0:
                break
            if 32.0 <= dur <= 55.0:
                window_cues = cues[i:j+1]
                full_text = " ".join(c["text"] for c in window_cues)
                
                # Check for concrete practical advice words
                action_words = ["yap", "başla", "kural", "yöntem", "taktik", "çözüm", "adım", "dakika", "zincir", "tavsiye", "öneri", "hedef"]
                action_count = sum(1 for w in action_words if w in full_text.lower())
                
                # Punchline check (ends with full stop, exclamation, question mark, or decisive tone)
                last_txt = cues[j]["text"].strip()
                if action_count >= 2 and (last_txt.endswith(('.', '!', '?', '"', '”')) or len(last_txt.split()) > 3):
                    top_candidates.append({
                        "speaker": speaker,
                        "topic": topic,
                        "video_id": vid,
                        "start": round(start_t, 2),
                        "end": round(end_t, 2),
                        "duration": round(dur, 2),
                        "hook": start_txt,
                        "punchline": last_txt,
                        "text": full_text,
                        "action_count": action_count
                    })

# Sort by action count and filter overlapping
top_candidates.sort(key=lambda x: x["action_count"], reverse=True)

unique_candidates = []
for c in top_candidates:
    # Check overlap with already selected
    overlap = False
    for u in unique_candidates:
        if u["video_id"] == c["video_id"] and abs(u["start"] - c["start"]) < 20.0:
            overlap = True
            break
    if not overlap:
        unique_candidates.append(c)
        if len(unique_candidates) >= 12:
            break

with open("calisma/Gun_11_test/ranked_top_candidates.json", "w", encoding="utf-8") as f:
    json.dump(unique_candidates, f, ensure_ascii=False, indent=2)

print(f"Selected {len(unique_candidates)} unique top candidate clips.")
for idx, c in enumerate(unique_candidates[:6], 1):
    print(f"\n#{idx} [{c['speaker']} - {c['topic']}] ({c['start']}s -> {c['end']}s, {c['duration']}s, Actions: {c['action_count']}):")
    print(f"  HOOK: {c['hook']}")
    print(f"  TEXT: {c['text'][:180]}...")
    print(f"  PUNCHLINE: {c['punchline']}")
