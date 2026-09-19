import os
import sys
sys.path.insert(0, '.')
from engine.candidate_ranker import CandidateRanker

vtts = [
    ('calisma/Gun_11_test/Baris_Ozcan_Erteleme.tr.vtt', 'Baris Ozcan - Erteleme', 'oN_8J6W8iJE'),
    ('calisma/Gun_11_test/Baris_Ozcan_Zinciri_Kirma.tr.vtt', 'Baris Ozcan - Zinciri Kirma', 'oNmXH2uN0Do'),
    ('calisma/Gun_11_test/Beyhan_Budak_8_Cozum.tr.vtt', 'Beyhan Budak - 8 Cozum', 'IuM-cHQkYbs'),
    ('calisma/Gun_11_test/Beyhan_Budak_Tembellik.tr.vtt', 'Beyhan Budak - Tembellik 8 Yontem', 'kX_7pNDVwYA')
]

out_lines = []

for path, label, vid in vtts:
    cues = CandidateRanker.parse_vtt(path)
    out_lines.append(f"\n=======================================================\n{label} ({vid}) - Total Cues: {len(cues)}\n=======================================================")
    
    # We want solution-oriented segments, typically between 30s and 60s
    for i in range(len(cues)):
        start_t = cues[i]["start"]
        start_txt = cues[i]["text"]
        
        # Check window lengths between 30 and 58 seconds
        for j in range(i + 3, len(cues)):
            end_t = cues[j]["end"]
            dur = end_t - start_t
            if 30 <= dur <= 58:
                window_cues = cues[i:j+1]
                full_text = " ".join(c["text"] for c in window_cues)
                
                # Check for strong solution keywords
                sol_keywords = [
                    "çözüm", "öneri", "yöntem", "taktik", "teknik", "kural", 
                    "2 dakika", "zinciri kırma", "küçük adım", "hemen başla",
                    "erteleme", "yapmanız gereken", "ilk adım", "pratik"
                ]
                score = sum(1 for k in sol_keywords if k in full_text.lower())
                if score >= 2:
                    out_lines.append(f"\n[{start_t:.2f}s -> {end_t:.2f}s] ({dur:.1f}s) [Keywords: {score}]")
                    out_lines.append(f"HOOK: {start_txt}")
                    out_lines.append(f"TEXT: {full_text}")
                    out_lines.append(f"PUNCHLINE: {cues[j]['text']}\n" + "-"*40)
            elif dur > 58:
                break

with open("calisma/Gun_11_test/solution_candidates.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print(f"Done! Written {len(out_lines)} lines to calisma/Gun_11_test/solution_candidates.txt")
