import re
from typing import List, Dict, Any, Optional

class SemanticFidelityChecker:
    """
    Audits subtitles, hooks, cover text, and publication copy against the source transcript
    to guarantee fidelity, preventing scope creeping, sensationalism, hedging erosion, or distortion.
    Granularly evaluates YouTube titles, Instagram hooks, captions, descriptions, and cover texts.
    """
    QUALIFIERS_TO_PRESERVE = [
        "biri", "birisi", "birçoğu", "bazıları", "bazı", "neredeyse", 
        "genellikle", "olabilir", "gibi", "fazlaca", "yakın olan"
    ]

    NEGATIVES_TO_PRESERVE = [
        "değil", "yok", "asla", "olamaz", "çıkmış", "haberdar bile değil"
    ]

    HEDGING_MARKERS = [
        "belki", "neredeyse", "yaklaşık", "tahminen", "ihtimalle", "galiba", "sanırım"
    ]

    SENSATIONAL_ROOTS = [
        "çürü", "felç", "zehir", "yok et", "mahvet", "öldür", "delirt", "kabus"
    ]

    @classmethod
    def audit_fidelity(
        cls, 
        subtitles: List[Dict[str, Any]], 
        transcript_text: str, 
        publish_data: Optional[Dict[str, Any]] = None,
        cover_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not transcript_text or len(transcript_text.strip()) < 30:
            return {
                "passed": False,
                "subtitles_audited": 0,
                "violations": [{
                    "field": "transcript",
                    "type": "MISSING_TRANSCRIPT_REJECTED",
                    "message": "Reference transcript is missing or empty; semantic fidelity cannot be verified without grounding source text."
                }],
                "warnings": [],
                "summary": "FAILED: Missing reference transcript"
            }

        transcript_clean = re.sub(r'\s+', ' ', transcript_text.lower())
        violations = []
        warnings = []
        verified_count = 0

        # 1. Audit Subtitles Individually
        for sub in subtitles:
            sub_text = sub.get("text", "")
            sub_lower = sub_text.lower()
            sid = sub.get("id", "unknown")

            # Check critical qualifier retention
            for q in cls.QUALIFIERS_TO_PRESERVE:
                if q in transcript_clean:
                    if ("en büyük bağımlılık" in sub_lower or "en büyük bağımlılığı" in sub_lower) and "birisi" not in sub_lower and "biri" not in sub_lower:
                        violations.append({
                            "field": f"subtitle:{sid}",
                            "type": "SCOPE_EXAGGERATION",
                            "message": f"Subtitle '{sub_text}' changed 'bağımlılıklarından birisi' to absolute superlative without qualifier.",
                            "recommended": "hayatımızın en büyük bağımlılıklarından biri!"
                        })

            # Check negative polarity retention
            for neg in ["haberdar değil", "farkında değil", "bırakabileceği bir şey olmaktan"]:
                if neg in transcript_clean and neg.split()[0] in sub_lower:
                    if "değil" not in sub_lower and "yok" not in sub_lower:
                        violations.append({
                            "field": f"subtitle:{sid}",
                            "type": "POLARITY_FLIP",
                            "message": f"Negative qualifier missing in '{sub_text}' for thought containing '{neg}'."
                        })

            verified_count += 1

        # 2. Gather All Editorial Publication & Cover Fields
        fields_to_audit = []
        if publish_data:
            yt = publish_data.get("youtube", {})
            ig = publish_data.get("instagram", {})

            for k in ["title", "title_1", "title_2", "title_3", "description"]:
                val = yt.get(k, "")
                if val:
                    fields_to_audit.append((f"youtube.{k}", val))

            for k in ["hook", "caption"]:
                val = ig.get(k, "")
                if val:
                    fields_to_audit.append((f"instagram.{k}", val))

        if cover_data:
            for k in ["title", "badge", "punch_line"]:
                val = cover_data.get(k, "")
                if val:
                    fields_to_audit.append((f"cover.{k}", val))

        # 3. Generalized Auditing on Each Field
        for field_name, text_val in fields_to_audit:
            text_lower = text_val.lower()

            # A. Sensational / Extreme Ungrounded Claim Detection
            for s_root in cls.SENSATIONAL_ROOTS:
                if s_root in text_lower:
                    # Check if the root exists in the source transcript
                    if s_root not in transcript_clean:
                        violations.append({
                            "field": field_name,
                            "type": "UNGROUNDED_SENSATIONAL_CLAIM_REJECTED",
                            "message": f"Field '{field_name}' asserts extreme sensational claim containing '{s_root}' which has no grounding in speaker transcript.",
                            "recommended": "Frame the topic around the speaker's actual vocabulary (e.g. hareketsizlik, oturmak, bedelin farkında olmak)."
                        })

            # B. Hedging Erosion Detection (Stripping 'belki', 'yaklaşık', etc.)
            for hedge in cls.HEDGING_MARKERS:
                pattern = rf"\b{hedge}\s+([\wçğıöşü]+(?:\s+[\wçğıöşü]+){{1,2}})"
                for m in re.finditer(pattern, transcript_clean):
                    hedged_phrase = m.group(1).strip()
                    if len(hedged_phrase) > 5 and hedged_phrase in text_lower:
                        # Check if the field retained the hedge or any valid qualifier
                        has_hedge = any(h in text_lower for h in cls.HEDGING_MARKERS + ["gibi", "neredeyse", "bazı"])
                        if not has_hedge:
                            violations.append({
                                "field": field_name,
                                "type": "HEDGING_STRIPPED_REJECTED",
                                "message": f"Field '{field_name}' asserts '{hedged_phrase}' as absolute fact, but speaker in transcript hedged it with '{hedge}'.",
                                "recommended": f"Restore qualifier: '{hedge} {hedged_phrase}'"
                            })

            # C. Quantitative Claims & Attribution Audit
            # Find numbers with optional decimals/separators
            found_nums = re.findall(r'\b\d{1,3}(?:[.,]\d{3})*(?:\s*bin)?\b', text_lower)
            has_attribution = any(x in text_lower for x in [
                "uzman", "uzmanlar", "psikolog", "araştırma", "araştırmalar", "klinik", "canan", "budak", "hoca", "prof"
            ])
            has_qualifier = any(x in text_lower for x in [
                "yakın olan", "yoğun", "kullanıcı", "bazı", "neredeyse", "fazlaca", "çoğu", "ortalama"
            ])

            for num in found_nums:
                num_clean = num.replace(".", "").replace(",", "").strip()
                if not num_clean.isdigit():
                    continue
                val = int(num_clean)
                if val >= 100:  # Quantitative statistical claim (e.g. 5000, 1000)
                    is_in_transcript = (
                        num in transcript_clean or
                        num_clean in transcript_clean
                    )
                    if not is_in_transcript and val >= 1000 and val % 1000 == 0:
                        k_val = val // 1000
                        if f"{k_val} bin" in transcript_clean or f"{k_val}bin" in transcript_clean:
                            is_in_transcript = True
                        elif val == 1000 and " bin" in transcript_clean:
                            is_in_transcript = True
                    if not is_in_transcript and val >= 1000000 and val % 1000000 == 0:
                        m_val = val // 1000000
                        if f"{m_val} milyon" in transcript_clean or f"{m_val}milyon" in transcript_clean:
                            is_in_transcript = True

                    if not is_in_transcript:
                        violations.append({
                            "field": field_name,
                            "type": "FABRICATED_STATISTIC_REJECTED",
                            "message": f"Field '{field_name}' asserts quantitative statistic '{num}' which is absent from transcript.",
                            "recommended": "Remove fabricated statistic or verify exact transcript cue."
                        })
                    else:
                        # Number is in transcript: check if transcript restricted it to a subpopulation
                        transcript_restricts_population = any(p in transcript_clean for p in ["yakın olan", "yoğun", "bazı"])
                        if transcript_restricts_population:
                            if not has_attribution:
                                violations.append({
                                    "field": field_name,
                                    "type": "UNATTRIBUTED_CLAIM_REJECTED",
                                    "message": f"Field '{field_name}' asserts quantitative statistic ({num}) without speaker/study attribution.",
                                    "recommended": "Attribute the source: 'Uzmanlar/Prof. Dr. Sinan Canan uyarıyor...'"
                                })
                            if not has_qualifier:
                                violations.append({
                                    "field": field_name,
                                    "type": "DROPPED_QUALIFIER_REJECTED",
                                    "message": f"Field '{field_name}' asserts {num} claim without population scope qualifier.",
                                    "recommended": "Include qualifying condition: 'Yoğun kullanıcılar günde ...'"
                                })

            # D. Superlative Distortion check
            if "en büyük" in text_lower or "en tehlikeli" in text_lower:
                if "en büyük" in transcript_clean and any(x in transcript_clean for x in ["biri", "birisi", "parçası"]):
                    if not any(x in text_lower for x in ["biri", "birisi", "parçası"]):
                        violations.append({
                            "field": field_name,
                            "type": "SUPERLATIVE_DISTORTION",
                            "message": f"Field '{field_name}' asserts absolute superlative instead of transcript's qualified superlative ('biri / birisi').",
                            "recommended": "Use 'en büyük ... biri'."
                        })

        passed = len(violations) == 0
        return {
            "passed": passed,
            "subtitles_audited": verified_count,
            "violations": violations,
            "warnings": warnings,
            "summary": "PASSED: High semantic fidelity to transcript" if passed else f"FAILED: {len(violations)} fidelity violations found"
        }
