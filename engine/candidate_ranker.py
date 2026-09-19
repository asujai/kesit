import os
import re
import json
from typing import List, Dict, Any, Optional

from core.jev_client import JevClient, get_openrouter_api_key

NICHE_PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "niche_profile.json")

class CandidateRanker:
    """
    Dynamically scans, segments, scores, and ranks video clip candidates (30-50s)
    from arbitrary VTT transcripts using natural speech boundaries and niche alignment.
    """
    @classmethod
    def load_niche_keywords(cls, profile_path: str = NICHE_PROFILE_PATH) -> Dict[str, Any]:
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[CandidateRanker] Warning reading niche profile: {e}")
        return {}

    @classmethod
    def parse_vtt(cls, vtt_path: str) -> List[Dict[str, Any]]:
        """Parses VTT cues, stripping timestamp tags and normalizing text."""
        if not os.path.exists(vtt_path):
            raise FileNotFoundError(f"Transcript file not found: {vtt_path}")

        with open(vtt_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

        cues = []
        blocks = re.split(r'\n\s*\n', content.strip())

        for b in blocks:
            lines = [l.strip() for l in b.split("\n") if l.strip()]
            time_line_idx = -1
            for idx, line in enumerate(lines):
                if "-->" in line:
                    time_line_idx = idx
                    break

            if time_line_idx != -1:
                parts = lines[time_line_idx].split("-->")
                start_s = cls._parse_timestamp(parts[0].strip())
                end_s = cls._parse_timestamp(parts[1].strip().split()[0])

                raw_text = " ".join(lines[time_line_idx + 1:])
                # Clean inline VTT tags like <00:00:01.000><c> or <v Speaker>
                clean_text = re.sub(r'<[^>]+>', '', raw_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                if clean_text and not clean_text.startswith("Kind:") and not clean_text.startswith("Language:"):
                    # Avoid duplicated consecutive cue texts
                    if not cues or cues[-1]["text"] != clean_text:
                        cues.append({
                            "start": start_s,
                            "end": end_s,
                            "text": clean_text
                        })

        return cls._deduplicate_rolling_cues(cues)

    @classmethod
    def _deduplicate_rolling_cues(cls, cues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cleans YouTube/Whisper rolling progressive subtitles where cues repeat prefixes/suffixes.
        Eliminates duplicate word tokens and joins partial continuations smoothly.
        """
        if not cues:
            return []

        cleaned = []
        for cue in cues:
            text = cue["text"].strip()
            if not text:
                continue
            if not cleaned:
                cleaned.append(dict(cue))
                continue

            prev = cleaned[-1]
            prev_text = prev["text"].strip()

            # 1. Exact duplicate
            if text.lower() == prev_text.lower():
                prev["end"] = max(prev["end"], cue["end"])
                continue

            # 2. Rolling prefix expansion: current text starts with previous text
            if text.lower().startswith(prev_text.lower()):
                remainder = text[len(prev_text):].strip()
                if remainder:
                    cleaned.append({
                        "start": max(prev["end"], cue["start"]),
                        "end": cue["end"],
                        "text": remainder
                    })
                else:
                    prev["end"] = max(prev["end"], cue["end"])
                continue

            # 3. Word-level overlap: suffix of prev matches prefix of current
            prev_words = prev_text.split()
            curr_words = text.split()

            max_overlap = 0
            for l in range(min(len(prev_words), len(curr_words)), 0, -1):
                if [w.lower() for w in prev_words[-l:]] == [w.lower() for w in curr_words[:l]]:
                    max_overlap = l
                    break

            if max_overlap > 0:
                remainder_words = curr_words[max_overlap:]
                if remainder_words:
                    cleaned.append({
                        "start": max(prev["end"], cue["start"]),
                        "end": cue["end"],
                        "text": " ".join(remainder_words)
                    })
                else:
                    prev["end"] = max(prev["end"], cue["end"])
                continue

            cleaned.append(dict(cue))

        return cleaned

    @classmethod
    def evaluate_candidates(
        cls,
        vtt_path: str,
        goal: str = "viral_awareness",
        out_log_path: str = None,
        min_duration: float = 28.0,
        max_duration: float = 60.0,
        use_jev: bool = True
    ) -> Dict[str, Any]:
        cues = cls.parse_vtt(vtt_path)
        if not cues:
            return {"campaign_goal": goal, "selected_candidate": None, "candidates": []}

        niche_data = cls.load_niche_keywords()
        niche_keywords = set()
        for pillar in niche_data.get("content_pillars", []):
            for word in pillar.get("theme", "").lower().split():
                niche_keywords.add(word)
        for point in niche_data.get("target_audience", {}).get("pain_points", []):
            for word in re.findall(r'\w+', point.lower()):
                if len(word) > 3:
                    niche_keywords.add(word)

        # Generate candidates using dynamic sliding windows across cues
        raw_candidates = []
        num_cues = len(cues)

        for i in range(num_cues):
            start_t = cues[i]["start"]
            start_text = cues[i]["text"]

            # Filter unpromising start phrases (e.g. single conjunctions or continuation fragments)
            if start_text.lower().startswith(("ve ", "ama ", "fakat ", "çünkü ")) and len(start_text.split()) < 3:
                continue

            for j in range(i + 1, num_cues):
                end_t = cues[j]["end"]
                dur = end_t - start_t

                if dur > max_duration:
                    break
                if dur >= min_duration:
                    end_text = cues[j]["text"]
                    # Candidate window identified: collect full text
                    window_cues = cues[i:j+1]
                    full_text = " ".join(c["text"] for c in window_cues)

                    # Calculate scores based on ACTUAL transcript text
                    hook_score = cls._score_hook(window_cues[:3])
                    punchline_score = cls._score_punchline(window_cues[-2:])
                    context_score = cls._score_context(start_text, end_text, full_text=full_text)
                    niche_score = cls._score_niche(full_text, niche_keywords)

                    if goal == "viral_awareness":
                        composite = round(hook_score * 0.35 + punchline_score * 0.30 + context_score * 0.20 + niche_score * 0.15, 2)
                    else:
                        composite = round(niche_score * 0.40 + punchline_score * 0.30 + hook_score * 0.20 + context_score * 0.10, 2)

                    raw_candidates.append({
                        "id": f"cand_{start_t:.1f}_{end_t:.1f}",
                        "start": round(start_t, 2),
                        "end": round(end_t, 2),
                        "duration": round(dur, 2),
                        "hook_text": window_cues[0]["text"],
                        "punchline_text": window_cues[-1]["text"],
                        "scores": {
                            "hook_power": hook_score,
                            "punchline_power": punchline_score,
                            "standalone_context": context_score,
                            "niche_alignment": niche_score
                        },
                        "composite_score": composite,
                        "full_text_sample": full_text[:200] + "...",
                        "full_text": full_text
                    })

        # Non-maximum suppression to filter heavily overlapping windows
        raw_candidates.sort(key=lambda x: x["composite_score"], reverse=True)
        selected_candidates = []

        for cand in raw_candidates:
            overlap = False
            for sc in selected_candidates:
                # Check overlap in seconds
                overlap_start = max(cand["start"], sc["start"])
                overlap_end = min(cand["end"], sc["end"])
                if overlap_end > overlap_start:
                    overlap_dur = overlap_end - overlap_start
                    if overlap_dur / min(cand["duration"], sc["duration"]) > 0.40:
                        overlap = True
                        break
            if not overlap:
                selected_candidates.append(cand)
                if len(selected_candidates) >= 5:
                    break

        # Jev Sistem 1 Karar Motoru ile Semantik Doğrulama & Puanlama (Codex Denetim P1/P2)
        if use_jev and get_openrouter_api_key() and selected_candidates:
            try:
                jev = JevClient(enable_cache=True)
                for c in selected_candidates:
                    eval_text = c.get("full_text", c.get("full_text_sample", ""))
                    jev_res = jev.evaluate_viral_candidate(eval_text)
                    ans = jev_res.get("answers", {})

                    hook_prob = ans.get("is_strong_hook", {}).get("noul", 0.5)
                    norm_viral = ans.get("viral_score", {}).get("normalized_1_to_5", 3.0)
                    emotion = ans.get("primary_emotion", {}).get("choice", "bilgi")

                    c["jev_scores"] = {
                        "hook_prob": round(hook_prob, 2),
                        "viral_score_1_to_5": norm_viral,
                        "primary_emotion": emotion,
                        "latency_ms": jev_res.get("_latency_ms", 0)
                    }
                    # Hibrit skor: %60 kural tabanlı + %40 Jev karar motoru
                    c["composite_score"] = round(c["composite_score"] * 0.60 + (norm_viral * 2.0) * 0.40, 2)

                # Jev puanı eklendikten sonra yeniden sırala
                selected_candidates.sort(key=lambda x: x["composite_score"], reverse=True)
            except Exception as e:
                print(f"[CandidateRanker] Jev puanlama atlandı, kural tabanlı sıralama kullanılıyor: {e}")

        if selected_candidates:
            selected_candidates[0]["status"] = "ACCEPTED"
            selected_candidates[0]["rationale"] = f"Top-ranked segment with highest combined hook ({selected_candidates[0]['scores']['hook_power']}/10) and punchline ({selected_candidates[0]['scores']['punchline_power']}/10) score."
            for c in selected_candidates[1:]:
                c["status"] = "REJECTED"
                c["rationale"] = f"Alternative candidate with lower composite score ({c['composite_score']} vs {selected_candidates[0]['composite_score']})."

        result = {
            "campaign_goal": goal,
            "selected_candidate": selected_candidates[0]["id"] if selected_candidates else None,
            "candidates": selected_candidates
        }

        if out_log_path:
            os.makedirs(os.path.dirname(os.path.abspath(out_log_path)), exist_ok=True)
            with open(out_log_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        return result

    @classmethod
    def rank_transcript_candidates(cls, vtt_path: str, goal: str = "viral_awareness", top_n: int = 5) -> List[Dict[str, Any]]:
        res = cls.evaluate_candidates(vtt_path, goal=goal)
        cands = res.get("candidates", [])
        out = []
        for c in cands[:top_n]:
            out.append({
                "id": c["id"],
                "start_t": c["start"],
                "end_t": c["end"],
                "duration": c["duration"],
                "score": c["composite_score"],
                "status": c.get("status", "CONSIDERED"),
                "hook_text": c.get("hook_text", ""),
                "punchline_text": c.get("punchline_text", "")
            })
        return out

    @classmethod
    def apply_candidate_to_spec(cls, spec: Any, candidate: Dict[str, Any], vtt_path: Optional[str] = None):
        """
        Dynamically drives timeline and subtitle synchronization from selected candidate.
        Updates in_point, out_point, total duration, clamps cuts, and updates/resynchronizes subtitles.
        """
        cand_start = float(candidate.get("start", candidate.get("start_t", 0.0)))
        cand_end = float(candidate.get("end", candidate.get("end_t", 0.0)))
        new_dur = round(cand_end - cand_start, 2)

        # 1. Update source boundaries & duration
        if isinstance(spec, dict):
            src = spec.setdefault("source", {})
            meta = spec.setdefault("meta", {})
            cuts = spec.setdefault("cuts", [])
            subs = spec.setdefault("subtitles", [])
        else:
            src = spec.source
            meta = spec.meta
            cuts = spec.cuts
            subs = spec.subtitles

        src["in_point"] = cand_start
        src["out_point"] = cand_end
        src["duration"] = new_dur
        meta["duration"] = new_dur

        # 2. Synchronize cuts: clamp or discard cuts outside the candidate duration
        valid_cuts = []
        for c in cuts:
            st = float(c.get("start_t", 0.0))
            et = float(c.get("end_t", 0.0))
            if st >= new_dur:
                continue
            if et > new_dur:
                c["end_t"] = new_dur
            if float(c.get("end_t", 0.0)) > st:
                valid_cuts.append(c)

        if isinstance(spec, dict):
            spec["cuts"] = valid_cuts
        else:
            spec.cuts = valid_cuts

        # 3. Synchronize subtitles
        transcript_file = vtt_path or meta.get("transcript_path")
        if transcript_file and os.path.exists(transcript_file):
            try:
                cues = cls.parse_vtt(transcript_file)
                new_subs = []
                sub_idx = 1
                for cue in cues:
                    if cue["end"] > cand_start and cue["start"] < cand_end:
                        rel_st = max(0.0, round(cue["start"] - cand_start, 2))
                        rel_et = min(new_dur, round(cue["end"] - cand_start, 2))
                        if rel_et > rel_st:
                            new_subs.append({
                                "id": f"s{sub_idx:02d}",
                                "start": rel_st,
                                "end": rel_et,
                                "start_t": rel_st,
                                "end_t": rel_et,
                                "text": cue["text"]
                            })
                            sub_idx += 1
                if new_subs:
                    if isinstance(spec, dict):
                        spec["subtitles"] = new_subs
                    else:
                        spec.subtitles = new_subs
            except Exception as e:
                print(f"[CandidateRanker] Warning syncing subtitles from VTT: {e}")
        elif subs:
            # Fallback: clamp existing subtitles to new_dur
            valid_subs = []
            for s in subs:
                st = float(s.get("start_t", s.get("start", 0.0)))
                et = float(s.get("end_t", s.get("end", 0.0)))
                if st >= new_dur:
                    continue
                if et > new_dur:
                    s["end_t"] = new_dur
                    if "end" in s:
                        s["end"] = new_dur
                if float(s.get("end_t", s.get("end", 0.0))) > st:
                    valid_subs.append(s)
            if isinstance(spec, dict):
                spec["subtitles"] = valid_subs
            else:
                spec.subtitles = valid_subs

        # 4. Provenance tracking: Record unbroken link from candidate to spec
        prov = meta.setdefault("provenance", {})
        prov["candidate"] = {
            "candidate_id": candidate.get("id"),
            "selection_mode": "automated_candidate_ranker",
            "original_start_t": cand_start,
            "original_end_t": cand_end,
            "duration": new_dur,
            "hook_text": candidate.get("hook_text", ""),
            "punchline_text": candidate.get("punchline_text", ""),
            "composite_score": candidate.get("composite_score", candidate.get("score")),
            "rationale": candidate.get("rationale", "Selected via CandidateRanker")
        }


    @classmethod
    def _score_hook(cls, first_cues: List[Dict[str, Any]]) -> float:
        text = " ".join(c["text"] for c in first_cues).lower()
        score = 5.0
        if "?" in text or any(w in text for w in ["sence", "neden", "nasıl", "biliyor musun"]):
            score += 2.5
        if any(w in text for w in ["sen", "senin", "sana", "kendini", "elin"]):
            score += 1.5
        if any(w in text for w in ["sabah", "ilk", "uyanır", "gece", "her zaman", "günde"]):
            score += 1.0
        return min(10.0, score)

    @classmethod
    def _score_punchline(cls, last_cues: List[Dict[str, Any]]) -> float:
        text = " ".join(c["text"] for c in last_cues).lower()
        score = 5.0
        if any(w in text for w in ["bağımlılık", "tuzak", "kaçırıyoruz", "kaybediyoruz", "farkında bile değil"]):
            score += 2.5
        if "!" in text or "." in text:
            score += 1.5
        if any(w in text for w in ["en büyük", "aslında", "sonuç", "artık"]):
            score += 1.0
        return min(10.0, score)

    DEPENDENT_STARTERS = [
        "oraya katılamadım", "ve ", "ama ", "fakat ", "çünkü ", "halbuki ", 
        "oysa ki ", "dolayısıyla ", "yani ", "böylece ", "bu yüzden ", 
        "bundan dolayı ", "onun için ", "zaten ", "diğer yandan ", "oysa "
    ]

    INCOMPLETE_ENDERS = [
        "aslında", "için", "diye", "gibi", "ve", "ile", "ki", "çünkü", 
        "fakat", "ama", "yani", "şey", "bir", "kadar", "göre", "rağmen", 
        "ise", "ancak", "bu", "şu", "o"
    ]

    @classmethod
    def _score_context(cls, start_text: str, end_text: str, full_text: str = "") -> float:
        score = 6.0
        start_lower = start_text.strip().lower()
        end_clean = end_text.strip()
        end_lower = end_clean.lower()

        # 1. Dependent openers deduction (e.g. 'Oraya katılamadım...', 'Ve...')
        for dep in cls.DEPENDENT_STARTERS:
            if start_lower.startswith(dep):
                score -= 4.0
                break

        # If starts with lowercase, minor deduction
        if start_text and start_text[0].islower():
            score -= 1.0

        # 2. Incomplete thought / trailing conjunction deduction (e.g. '...dediğimiz şey aslında')
        words = end_lower.split()
        if words:
            last_word = re.sub(r'[^\wçğıöşü]', '', words[-1])
            if last_word in cls.INCOMPLETE_ENDERS:
                score -= 4.5

            # 3. Turkish SOV finite verb completion & terminal punctuation bonus
            is_finite_verb = bool(re.search(r'(d[ıiuü]|t[ıiuü]|m[ıiuü]ş|yor|acak|ecek|r|[ae]r|[ıiuü]r|m[az]ez|mal[ıi]|mel[ıi]|d[ıiuü]r|t[ıiuü]r)(lar|ler|m|n|k|n[ıi]z)?$', last_word))
            has_terminal_punct = any(end_clean.endswith(p) for p in [".", "!", "?"])

            if is_finite_verb and has_terminal_punct:
                score += 2.5
            elif has_terminal_punct:
                score += 1.5

        # 4. Penalty for repeated words / stutter artifacts in text
        if full_text:
            stutters = re.findall(r'\b(\w{3,})\s+\1\b', full_text.lower())
            if stutters:
                score -= min(3.0, len(stutters) * 1.5)

        return max(1.0, min(10.0, score))

    @classmethod
    def _score_niche(cls, text: str, niche_keywords: set) -> float:
        score = 5.0
        words = set(re.findall(r'\w+', text.lower()))
        matches = words.intersection(niche_keywords)
        score += min(5.0, len(matches) * 0.8)
        return min(10.0, score)

    @classmethod
    def _parse_timestamp(cls, ts_str: str) -> float:
        parts = ts_str.strip().split(":")
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m = float(parts[0])
            s = float(parts[1])
            return m * 60 + s
        return float(ts_str)
