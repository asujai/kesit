import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import Optional


try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from engine.spec import VideoSpec
from engine.audio_engine import AudioEngine
from engine.timeline import TimelineCompiler
from engine.quality_gate import QualityGate
from engine.candidate_ranker import CandidateRanker
from core.semantic_selector import SemanticSelector, VisualNeed

def resolve_spec_assets(spec: VideoSpec, work_dir: str, day: str):
    """
    Evaluates and resolves any cuts requiring semantic B-roll retrieval or fallback.
    """
    selector = SemanticSelector(log_path=os.path.join(work_dir, "semantic_selection_log.json"))
    target_broll_dir = os.path.join(work_dir, "dynamic_brolls")

    for cut in spec.cuts:
        cid = cut.get("id", "unnamed_cut")
        need = cut.get("visual_need")
        src = cut.get("source_file")

        # If cut provides a visual_need and source_file doesn't exist or is missing
        if need and (not src or not os.path.exists(src)):
            print(f"[Runner] Resolving semantic B-roll for cut {cid}...")
            v_need = VisualNeed(
                scene_id=cid,
                spoken_text=need.get("spoken_text", ""),
                subject_action=need.get("subject_action", ""),
                environment=need.get("environment", ""),
                emotion=need.get("emotion", ""),
                media_type=cut.get("media_type", "video"),
                avoid=need.get("avoid", ["3d", "animation", "cartoon", "render", "drawing", "cgi"]),
                queries=need.get("queries", []),
                required_duration=cut.get("end_t", 2.0) - cut.get("start_t", 0.0)
            )
            res = selector.select_asset(v_need, current_day=day, target_dir=target_broll_dir)
            if res.get("file_path"):
                cut["source_file"] = res["file_path"]
                cut["provider"] = res["provider"]
                cut["asset_id"] = res["asset_id"]
                cut["selection_source"] = "automated_selector"
                print(f"[Runner] Cut {cid} resolved -> {res['file_path']} (Score: {res.get('score')})")
            elif res.get("fallback_action") == "speaker_cut":
                print(f"[Runner] Cut {cid} fallback -> Reverting to speaker cut.")
                cut["fallback"] = "speaker_cut"
                cut["selection_source"] = "automated_fallback"
        elif src:
            if not cut.get("selection_source"):
                cut["selection_source"] = "agent_editorial"

def run_pipeline(spec_path: str, force: bool = False, apply_candidate: Optional[str] = None, lang: str = "all"):
    print(f"\n=======================================================")
    print(f"[*] VIDEO AUTOMATION PIPELINE RUNNER")
    print(f"   Spec: {spec_path} (Force: {force}, Candidate: {apply_candidate}, Lang: {lang})")
    print(f"=======================================================")

    spec = VideoSpec.from_file(spec_path)
    work_dir = os.path.dirname(os.path.abspath(spec_path))
    day = spec.meta.get("day", "UnknownDay")
    transcript_path = spec.meta.get("transcript_path")

    # 0. Apply candidate dynamically if requested
    if apply_candidate:
        if not transcript_path or not os.path.exists(transcript_path):
            print(f"\n[CRITICAL ERROR] --apply-candidate requires valid transcript_path in spec: {transcript_path}")
            sys.exit(1)
        evaluation = CandidateRanker.evaluate_candidates(transcript_path, goal="viral_awareness")
        candidates = evaluation.get("candidates", [])
        if not candidates:
            print(f"\n[CRITICAL ERROR] No viable candidates found in transcript: {transcript_path}")
            sys.exit(1)

        chosen = None
        if apply_candidate in ("best", "top"):
            chosen = candidates[0]
        else:
            for c in candidates:
                if c["id"] == apply_candidate:
                    chosen = c
                    break
            if not chosen and apply_candidate.isdigit():
                idx = int(apply_candidate) - 1
                if 0 <= idx < len(candidates):
                    chosen = candidates[idx]

        if not chosen:
            print(f"\n[CRITICAL ERROR] Specified candidate '{apply_candidate}' not found.")
            sys.exit(1)

        print(f"[Runner] Applying candidate {chosen['id']} ({chosen['start']}s -> {chosen['end']}s, dur: {chosen['duration']}s)...")
        CandidateRanker.apply_candidate_to_spec(spec, chosen, transcript_path)

    # Ensure baseline provenance exists if not set
    prov = spec.meta.setdefault("provenance", {})
    if not prov.get("source_video"):
        prov["source_video"] = {
            "raw_video_path": spec.source.get("raw_video_path"),
            "in_point": spec.source.get("in_point"),
            "out_point": spec.source.get("out_point"),
            "duration": spec.source.get("duration", round(spec.source.get("out_point", 0.0) - spec.source.get("in_point", 0.0), 2))
        }
    if not prov.get("candidate"):
        prov["candidate"] = {
            "selection_mode": "agent_editorial",
            "in_point": spec.source.get("in_point"),
            "out_point": spec.source.get("out_point"),
            "duration": spec.source.get("duration", round(spec.source.get("out_point", 0.0) - spec.source.get("in_point", 0.0), 2)),
            "rationale": "Direct editorial selection by agent/user"
        }

    # Initial Validation (allowing unresolved cuts that have visual_need)
    initial_errors = spec.validate(allow_unresolved=True)
    if initial_errors:
        print("\n[CRITICAL SPEC INITIAL VALIDATION ERRORS]")
        for err in initial_errors:
            print(f"  [X] {err}")
        sys.exit(1)

    # 1. Candidate Evaluation Log (if transcript available and not yet saved)
    transcript_text = ""
    if transcript_path and os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8-sig") as f:
            transcript_text = f.read()
        cand_log = os.path.join(work_dir, "candidate_evaluation.json")
        CandidateRanker.evaluate_candidates(transcript_path, goal="viral_awareness", out_log_path=cand_log)
        print(f"[Runner] Candidate ranking evaluation saved to: {cand_log}")

    # 2. Semantic Asset Resolution
    resolve_spec_assets(spec, work_dir, day)

    # Post-Resolution Validation (ensures every cut has source_file or speaker_cut fallback)
    post_errors = spec.validate_post_resolution()
    if post_errors:
        print("\n[CRITICAL SPEC POST-RESOLUTION VALIDATION ERRORS]")
        for err in post_errors:
            print(f"  [X] {err}")
        sys.exit(1)

    # 3. Audio Engine: Mastering Voice + BGM (-14 LUFS) with Parameter Caching
    master_audio_path = os.path.join(work_dir, "master_audio.m4a")
    in_pt = spec.source["in_point"]
    out_pt = spec.source["out_point"]
    bgm_path = spec.audio.get("bgm_path")
    bgm_gain = spec.audio.get("bgm_gain", 0.14)
    target_lufs = spec.audio.get("target_lufs", -14.0)
    fade_dur = spec.audio.get("fade_out_duration", 0.73)

    print("\n--- STAGE 1: AUDIO MASTERING & DUCKING ---")
    cache_key = AudioEngine.compute_audio_cache_key(
        raw_video=spec.source["raw_video_path"],
        in_point=in_pt,
        out_point=out_pt,
        bgm_path=bgm_path,
        bgm_gain=bgm_gain,
        target_lufs=target_lufs,
        fade_out_duration=fade_dur
    )
    is_audio_valid = AudioEngine.is_audio_cache_valid(master_audio_path, cache_key)

    if force or not is_audio_valid:
        print(f"[Runner] Audio cache miss/invalidated (force={force}, key={cache_key[:12]}...). Rebuilding audio...")
        audio_meta = AudioEngine.build_master_audio(
            raw_video=spec.source["raw_video_path"],
            in_point=in_pt,
            out_point=out_pt,
            bgm_path=bgm_path,
            bgm_gain=bgm_gain,
            target_lufs=target_lufs,
            out_audio_path=master_audio_path,
            fade_out_duration=fade_dur
        )
    else:
        print(f"[Runner] Audio cache hit (valid key {cache_key[:12]}...). Reusing master audio.")
        audio_meta = AudioEngine.measure_loudness(master_audio_path)

    print(f"[Runner] Master audio ready: {audio_meta.get('integrated_lufs')} LUFS, True Peak: {audio_meta.get('true_peak')} dBFS")

    # Determine target languages
    target_langs = []
    if lang in ("all", "tr"):
        target_langs.append("tr")
    if lang in ("all", "en"):
        en_subs_file = os.path.join(work_dir, "subtitles_en.json")
        has_en_subs = bool(spec.meta.get("subtitles_en") or os.path.exists(en_subs_file))
        if has_en_subs or lang == "en":
            target_langs.append("en")

    compiler = TimelineCompiler(spec, work_dir)
    qgate = QualityGate(spec, work_dir)
    all_releases_passed = True

    for t_lang in target_langs:
        print(f"\n=======================================================")
        print(f"--- PROCESSING LANGUAGE: {t_lang.upper()} ---")
        print(f"=======================================================")

        # Resolve subtitles & badges directory for language
        if t_lang == "en":
            en_subs_file = os.path.join(work_dir, "subtitles_en.json")
            if os.path.exists(en_subs_file):
                with open(en_subs_file, "r", encoding="utf-8-sig") as sf:
                    target_subs = json.load(sf)
            else:
                target_subs = spec.meta.get("subtitles_en", spec.subtitles)
            target_badges_dir = os.path.join(work_dir, "sub_badges_en")
            temp_visual_path = os.path.join(work_dir, "temp_visual_engine_en.mp4")
            master_video_path = os.path.join(work_dir, f"master_{day.lower()}_en.mp4")
        else:
            target_subs = spec.subtitles
            target_badges_dir = os.path.join(work_dir, "sub_badges")
            temp_visual_path = os.path.join(work_dir, "temp_visual_engine.mp4")
            master_video_path = os.path.join(work_dir, f"master_{day.lower()}.mp4")

        # 4. Visual Timeline Compilation
        print(f"\n--- STAGE 2 ({t_lang.upper()}): VISUAL TIMELINE COMPILATION ---")
        visual_meta = compiler.compile_visual(
            temp_visual_path,
            subtitles=target_subs,
            badges_dir=target_badges_dir,
            force=force
        )
        print(f"[Runner] Visual stream compiled ({visual_meta['cuts_count']} dynamic cuts, {visual_meta['subtitles_count']} badges).")

        # 5. Final Muxing (Visual + Master Audio)
        print(f"\n--- STAGE 3 ({t_lang.upper()}): FINAL MULTIPLEXING ---")
        cmd_mux = [
            "ffmpeg", "-y",
            "-i", temp_visual_path,
            "-i", master_audio_path,
            "-c:v", "copy",
            "-c:a", "copy",
            master_video_path
        ]
        res = subprocess.run(cmd_mux, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Multiplexing failed for {t_lang}: {res.stderr}")
        print(f"[Runner] Master video muxed: {master_video_path}")

        # 6. Independent QA & Release Gate (Staged Deployment)
        print(f"\n--- STAGE 4 ({t_lang.upper()}): QUALITY & RELEASE GATE ---")
        qa_results = qgate.verify_and_release(
            master_video_path,
            transcript_text=transcript_text,
            lang=t_lang
        )

        if qa_results.get("overall_status") != "PASSED" or qa_results.get("delivery_status") not in ("DEPLOYED", "RELEASED"):
            print(f"\n>>> PIPELINE REJECTED FOR {t_lang.upper()}: QA Status={qa_results.get('overall_status')}, Delivery Status={qa_results.get('delivery_status')}. <<<")
            all_releases_passed = False
        else:
            print(f"[Runner] Language {t_lang.upper()} verified & released successfully!")

    if all_releases_passed:
        print("\n>>> PIPELINE EXECUTION FINISHED: ALL TARGET LANGUAGES DEPLOYED! <<<")
    else:
        print("\n>>> PIPELINE FINISHED WITH FAILURES: ONE OR MORE LANGUAGES REJECTED. <<<")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Video Pipeline Runner & Jev Viral Radar")
    parser.add_argument("--spec", required=False, default=None, help="Path to spec.json")
    parser.add_argument("--force", action="store_true", help="Force rebuild all assets")
    parser.add_argument("--lang", choices=["all", "tr", "en"], default="all", help="Target language to render ('all', 'tr', 'en')")
    parser.add_argument("--apply-candidate", nargs="?", const="best", default=None,
                        help="Candidate ID or index ('best', '1', 'cand_0.0_46.9') to apply to spec before building")
    parser.add_argument("--preflight", action="store_true", help="1 saniyede proje hafıza & JEV karar sentezini çalıştırır")
    parser.add_argument("--hunt-topic", default=None, help="Trigger Jev ViralRadar multi-video search for topic")
    parser.add_argument("--hunt-mode", choices=["shorts", "essay"], default="shorts", help="Radar duration mode (shorts: 28-60s, essay: 120-300s)")
    parser.add_argument("--hunt-target", type=int, default=10, help="Target valid transcripts to collect before ranking")
    parser.add_argument("--hunt-min-score", type=float, default=90.0, help="90+ viralite kalite eşiği (sağlanana dek arama sürer)")
    parser.add_argument("--hunt-max-rounds", type=int, default=5, help="Maksimum arama turu sayısı")
    args = parser.parse_args()

    if args.preflight:
        from engine.preflight import run_preflight
        run_preflight()
    elif args.hunt_topic:
        from engine.viral_radar import ViralRadar
        radar = ViralRadar(target_valid_transcripts=args.hunt_target, mode=args.hunt_mode, min_score=args.hunt_min_score, max_rounds=args.hunt_max_rounds)
        manifest_out = os.path.join(os.getcwd(), "calisma", "viral_radar_manifest.json")
        radar.hunt_best_clip(args.hunt_topic, output_manifest_path=manifest_out, min_score=args.hunt_min_score, max_rounds=args.hunt_max_rounds)
    elif args.spec:
        run_pipeline(args.spec, force=args.force, apply_candidate=args.apply_candidate, lang=args.lang)
    else:
        parser.print_help()
        sys.exit(1)

