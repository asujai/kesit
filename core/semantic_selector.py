import os
import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from core.pexels_client import search_broll_video as pexels_search_video, search_broll_photo as pexels_search_photo, download_video as pexels_dl_video
from core.pixabay_client import search_pixabay_videos, search_pixabay_images, download_file as pixabay_dl
from core.giphy_client import search_gifs, download_file as giphy_dl
from core.asset_registry import registry
from core.jev_client import JevClient, get_openrouter_api_key

@dataclass
class VisualNeed:
    scene_id: str
    spoken_text: str
    subject_action: str
    environment: str
    emotion: str
    media_type: str = "video"
    avoid: List[str] = field(default_factory=lambda: ["3d", "animation", "cartoon", "render", "drawing", "cgi", "watermark"])
    queries: List[str] = field(default_factory=list)
    required_duration: float = 2.0

class SemanticSelector:
    """
    Content-driven semantic asset selector.
    Compares all candidate assets, enforces negative avoid filters, evaluates
    resolution and candidate-intrinsic metadata relevance, checks hash deduplication,
    tracks in-flight reservations across scenes, and applies explicit fallback.
    """
    def __init__(self, log_path: Optional[str] = None, enable_jev: bool = True):
        self.log_path = log_path
        self.selection_log = []
        self.active_reservations = set()
        self.enable_jev = enable_jev
        self.jev = JevClient(enable_cache=True) if (enable_jev and get_openrouter_api_key()) else None

    def score_candidate(self, cand: Dict[str, Any], visual_need: VisualNeed, current_day: str, query: str) -> Dict[str, Any]:
        provider = cand.get("provider", "pexels")
        cand_id = str(cand.get("id"))
        duration = float(cand.get("duration", 0) or 0)
        width = int(cand.get("width", 0) or 0)
        height = int(cand.get("height", 0) or 0)
        
        # Tags, title, and description text from candidate's OWN provider metadata
        text_metadata = f"{cand.get('tags', '')} {cand.get('title', '')} {cand.get('description', '')} {cand.get('url', '')}".lower()

        reasons = []
        score = 5.0  # baseline

        # 0. Check in-flight reservation (cannot select same asset in multiple scenes in same run)
        key = f"{provider}_{cand_id}"
        if key in self.active_reservations or cand_id in self.active_reservations:
            return {
                "id": cand_id, "provider": provider, "score": -100.0,
                "reasons": ["CRITICAL: Asset already reserved by another cut in current build (-100.0)"],
                "cand": cand, "query": query
            }

        # 1. Check if asset was explicitly rejected previously in AssetRegistry
        reg_entry = registry.data.get("assets", {}).get(key, {})
        if reg_entry.get("status") == "rejected":
            return {
                "id": cand_id, "provider": provider, "score": -100.0,
                "reasons": [f"Blacklisted in registry: {reg_entry.get('rejection_reason', 'rejected')}"],
                "cand": cand, "query": query
            }

        # 2. Content & Semantic Relevance Matching (STRICTLY CANDIDATE'S OWN METADATA, NOT QUERY)
        semantic_targets = []
        for phrase in [visual_need.subject_action, visual_need.environment, visual_need.emotion]:
            for word in re.findall(r'\w+', phrase.lower()):
                if len(word) > 2:
                    semantic_targets.append(word)

        matches = [w for w in semantic_targets if w in text_metadata]
        if matches:
            bonus = min(6.0, len(matches) * 1.5)
            score += bonus
            reasons.append(f"Semantic metadata match: {', '.join(matches[:4])} (+{bonus})")
        else:
            score -= 4.0
            reasons.append("No direct semantic keyword match in candidate metadata (-4.0)")

        # 2b. Spoken Text & Context Alignment (Codex Denetim P1 Düzeltmesi)
        if visual_need.spoken_text:
            spoken_words = [w for w in re.findall(r'\w+', visual_need.spoken_text.lower()) if len(w) > 3]
            spoken_matches = [w for w in spoken_words if w in text_metadata]
            if spoken_matches:
                bonus_spoken = min(4.0, len(spoken_matches) * 1.0)
                score += bonus_spoken
                reasons.append(f"Spoken text alignment: {', '.join(spoken_matches[:3])} (+{bonus_spoken})")

        # Uncertainty penalty if candidate metadata is extremely sparse
        if len(text_metadata.strip()) < 10:
            score -= 4.0
            reasons.append("Metadata sparse or missing (-4.0 uncertainty discount)")

        # 3. Negative Avoid List Enforcement
        avoid_hits = [a for a in visual_need.avoid if a.lower() in text_metadata]
        if avoid_hits:
            score -= 15.0
            reasons.append(f"CRITICAL: Avoid keywords triggered ({', '.join(avoid_hits)}) (-15.0)")

        # 4. Anti-Repetition & History Memory
        used_days = registry.get_recent_usage_days(provider, cand_id)
        if current_day in used_days:
            score -= 20.0
            reasons.append(f"CRITICAL: Already used in {current_day} (-20.0)")
        elif len(used_days) > 0:
            score -= 5.0
            reasons.append(f"Used recently in {used_days} (-5.0)")

        # 5. Duration Sufficiency
        if visual_need.media_type == "video":
            if duration > 0 and duration < visual_need.required_duration:
                score -= 6.0
                reasons.append(f"Too short ({duration}s < {visual_need.required_duration}s) (-6.0)")
            elif duration >= visual_need.required_duration:
                score += 1.5
                reasons.append("Duration sufficient (+1.5)")

        # 6. Resolution & Framing Quality
        if width > 0 and height > 0:
            if width < 720 or height < 720:
                score -= 8.0
                reasons.append(f"Low resolution ({width}x{height}) (-8.0)")
            elif height > width and height >= 1280:
                score += 3.0
                reasons.append("Native vertical HD/4K (+3.0)")
            elif width >= 1920 and height >= 1080:
                score += 2.0
                reasons.append("Horizontal 1080p/4K croppable (+2.0)")

        return {
            "id": cand_id,
            "provider": provider,
            "score": round(score, 2),
            "duration": duration,
            "resolution": f"{width}x{height}",
            "reasons": reasons,
            "cand": cand,
            "query": query
        }

    def select_asset(self, visual_need: VisualNeed, current_day: str, target_dir: str) -> Dict[str, Any]:
        """
        Gathers ALL candidates across queries and providers, ranks them,
        checks SHA-256 hash deduplication post-download, reserves chosen assets,
        and either selects the highest-scoring candidate or triggers explicit fallback.
        """
        os.makedirs(target_dir, exist_ok=True)
        all_evaluations = []

        for q in visual_need.queries:
            candidates = []
            if visual_need.media_type == "video":
                # Pexels adayları
                try:
                    p_cands = pexels_search_video(q, orientation="portrait", per_page=5)
                    if not p_cands:
                        p_cands = pexels_search_video(q, orientation="all", per_page=5)
                    candidates.extend(p_cands or [])
                except Exception as e:
                    print(f"[SemanticSelector] Pexels search error for '{q}': {e}")

                # Pixabay adayları (aynı anda havuza eklenir - Codex Denetimi)
                try:
                    pix_cands = search_pixabay_videos(q, per_page=5)
                    candidates.extend(pix_cands or [])
                except Exception as e:
                    print(f"[SemanticSelector] Pixabay search error for '{q}': {e}")

            elif visual_need.media_type == "photo":
                try:
                    p_photos = pexels_search_photo(q, orientation="portrait", per_page=5)
                    candidates.extend(p_photos or [])
                except Exception:
                    pass
                try:
                    pix_photos = search_pixabay_images(q, orientation="vertical", per_page=5)
                    candidates.extend(pix_photos or [])
                except Exception:
                    pass

            elif visual_need.media_type in ("gif", "animation"):
                try:
                    candidates = search_gifs(q, limit=5)
                except Exception as e:
                    print(f"[SemanticSelector] GIPHY search error for '{q}': {e}")

            for cand in candidates:
                eval_record = self.score_candidate(cand, visual_need, current_day, q)
                all_evaluations.append(eval_record)

        # Jev Sistem 1 Semantik Seçim Katmanı (Codex Denetim P1/P2 Düzeltmesi)
        if self.jev and len(all_evaluations) >= 2 and visual_need.spoken_text:
            top_cands = [ce for ce in all_evaluations if ce["score"] >= 2.0][:6]
            if len(top_cands) >= 2:
                jev_dict = {}
                for ce in top_cands:
                    key = f"{ce['provider']}_{ce['id']}"
                    desc = f"{ce['cand'].get('title', '')} {ce['cand'].get('tags', '')}".strip() or "B-roll video"
                    jev_dict[key] = desc[:120]

                try:
                    jev_res = self.jev.select_best_broll(
                        sentence=f"{visual_need.spoken_text} (Görsel İhtiyaç: {visual_need.subject_action})",
                        broll_candidates=jev_dict,
                        verify_match=True
                    )
                    chosen_key = jev_res.get("answers", {}).get("selected_broll", {}).get("choice")
                    is_fit = jev_res.get("answers", {}).get("is_accurate_fit", {}).get("noul", 1.0)

                    for ce in all_evaluations:
                        if f"{ce['provider']}_{ce['id']}" == chosen_key:
                            if is_fit >= 0.5:
                                ce["score"] += 6.0
                                ce["reasons"].append(f"Jev System 1 En İyi Aday (Uyum: {is_fit:.2f}) (+6.0)")
                            else:
                                ce["reasons"].append(f"Jev Zayıf Uyum Uyarısı (Olasılık: {is_fit:.2f})")
                except Exception as e:
                    print(f"[SemanticSelector] Jev b-roll seçim uyarısı: {e}")

        # Rank all candidates by score
        all_evaluations.sort(key=lambda x: x["score"], reverse=True)

        chosen = None
        fallback_action = None

        # Iterate down candidate list to find top candidate that passes download & hash deduplication
        for candidate_eval in all_evaluations:
            if candidate_eval["score"] < 6.0:
                break

            cand_data = candidate_eval["cand"]
            provider = candidate_eval["provider"]
            cand_id = candidate_eval["id"]
            ext = "mp4" if visual_need.media_type != "photo" else "jpg"
            dest_filename = f"{visual_need.scene_id}_{provider}_{cand_id}.{ext}"
            dest_path = os.path.join(target_dir, dest_filename)

            # Check if file exists or download to temporary file
            target_to_check = dest_path
            tmp_dl = None

            if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
                dl_url = cand_data.get("download_url") or cand_data.get("mp4_url")
                if not dl_url:
                    continue
                
                tmp_dl = dest_path + ".cand_tmp"
                try:
                    print(f"[SemanticSelector] Downloading candidate {provider} ID={cand_id} (Score: {candidate_eval['score']})...")
                    if provider == "pexels":
                        pexels_dl_video(dl_url, tmp_dl)
                    elif provider == "pixabay":
                        pixabay_dl(dl_url, tmp_dl)
                    elif provider == "giphy":
                        giphy_dl(dl_url, tmp_dl)
                except Exception as e:
                    print(f"[SemanticSelector] Download failed for candidate {cand_id}: {e}")
                    if os.path.exists(tmp_dl):
                        os.remove(tmp_dl)
                    continue
                target_to_check = tmp_dl

            # Unconditional SHA-256 Hash Deduplication Check (Runs on BOTH cached and downloaded files)
            fhash = registry.compute_file_hash(target_to_check)
            existing_asset = registry.find_asset_by_hash(fhash)
            
            # Check collision in active reservations or registry history
            if fhash in self.active_reservations:
                print(f"[SemanticSelector] REJECTED: Content hash {fhash[:8]} already reserved in current build!")
                if tmp_dl and os.path.exists(tmp_dl):
                    os.remove(tmp_dl)
                continue

            if existing_asset:
                used_days = [u.get("day") for u in existing_asset.get("used_in", [])]
                if current_day in used_days:
                    print(f"[SemanticSelector] REJECTED: Content hash {fhash[:8]} was already used in {current_day} (original ID: {existing_asset['asset_id']})!")
                    if tmp_dl and os.path.exists(tmp_dl):
                        os.remove(tmp_dl)
                    continue
                if existing_asset.get("status") == "rejected":
                    print(f"[SemanticSelector] REJECTED: Content hash {fhash[:8]} is blacklisted in registry!")
                    if tmp_dl and os.path.exists(tmp_dl):
                        os.remove(tmp_dl)
                    continue

            if tmp_dl and os.path.exists(tmp_dl):
                os.replace(tmp_dl, dest_path)

            # Candidate successfully acquired & verified
            chosen = candidate_eval
            chosen_hash = registry.compute_file_hash(dest_path)
            
            # Add to in-flight reservations
            self.active_reservations.add(f"{provider}_{cand_id}")
            if chosen_hash:
                self.active_reservations.add(chosen_hash)

            # Register into registry
            registry.register_asset(
                provider=provider,
                asset_id=cand_id,
                media_type=visual_need.media_type,
                description=visual_need.subject_action,
                query=candidate_eval.get("query", ""),
                file_path=dest_path
            )
            break

        if not chosen:
            # Explicit Fallback: No candidate met the bar or all were duplicates
            fallback_action = "speaker_cut"
            print(f"[SemanticSelector] Fallback triggered for scene {visual_need.scene_id}: No valid candidate met threshold >= 6.0 or hash deduplication passed. Reverting to speaker cut.")
            result = {
                "scene_id": visual_need.scene_id,
                "file_path": None,
                "provider": None,
                "asset_id": None,
                "duration": 0,
                "score": all_evaluations[0]["score"] if all_evaluations else 0,
                "fallback_action": fallback_action
            }
        else:
            result = {
                "scene_id": visual_need.scene_id,
                "file_path": dest_path,
                "provider": chosen["provider"],
                "asset_id": chosen["id"],
                "duration": chosen["duration"],
                "score": chosen["score"],
                "fallback_action": None
            }

        # Log selection decision
        decision_log = {
            "scene_id": visual_need.scene_id,
            "spoken_text": visual_need.spoken_text,
            "subject_action": visual_need.subject_action,
            "selected": chosen["id"] if chosen else "FALLBACK",
            "fallback_action": fallback_action,
            "candidates_evaluated": [
                {
                    "id": c["id"],
                    "provider": c["provider"],
                    "score": c["score"],
                    "query": c["query"],
                    "reasons": "; ".join(c["reasons"])
                } for c in all_evaluations[:6]
            ]
        }
        self.selection_log.append(decision_log)

        if self.log_path:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(self.selection_log, f, indent=2, ensure_ascii=False)

        return result
