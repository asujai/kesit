import os
import shutil
import time
import hashlib
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

from engine.spec import VideoSpec
from engine.audio_engine import AudioEngine
from engine.fidelity import SemanticFidelityChecker

class QualityGate:
    """
    Independent Quality & Release Gate.
    Verifies container integrity, audio sync, loudness, semantic fidelity,
    and conducts automated pixel-variance anti-freeze testing on all B-rolls.
    Guarantees showcase directories are NEVER touched by failing or unverified builds.
    """
    def __init__(self, spec: VideoSpec, work_dir: str):
        self.spec = spec
        self.work_dir = work_dir

    def calculate_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def extract_frame_pixels(self, video_path: str, timestamp: float, crop_box=(0, 0, 1080, 1200)) -> np.ndarray:
        frame_tmp = os.path.join(self.work_dir, f"_qa_tmp_{timestamp:.2f}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", f"{timestamp:.2f}",
            "-i", video_path,
            "-vframes", "1",
            frame_tmp
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0 or not os.path.exists(frame_tmp):
            return np.zeros((10, 10))
        
        try:
            im = Image.open(frame_tmp).crop(crop_box)
            arr = np.array(im, dtype=float)
            return arr
        finally:
            if os.path.exists(frame_tmp):
                try:
                    os.remove(frame_tmp)
                except OSError:
                    pass

    def verify_and_release(self, master_video_path: str, transcript_text: str = "") -> Dict[str, Any]:
        day = self.spec.meta.get("day", "UnknownDay")
        file_hash = self.calculate_file_hash(master_video_path)
        build_id = f"{day}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
        
        print(f"\n=======================================================")
        print(f"--- RUNNING QUALITY & RELEASE GATE [Build: {build_id}] ---")
        print(f"=======================================================")

        checks = {}
        failures = []

        # 1. Technical Container & Stream Probe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height,codec_name,pix_fmt,duration",
            "-of", "json", master_video_path
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
        probe_data = json.loads(probe_res.stdout) if probe_res.returncode == 0 else {}
        
        streams = probe_data.get("streams", [])
        v_stream = next((s for s in streams if s.get("width")), None)
        a_stream = next((s for s in streams if not s.get("width")), None)

        if not v_stream or not a_stream:
            failures.append("Missing video or audio stream in rendered file")
        else:
            w = int(v_stream.get("width", 0))
            h = int(v_stream.get("height", 0))
            if w != 1080 or h != 1920:
                failures.append(f"Resolution is {w}x{h}, expected 1080x1920 (9:16 portrait)")
            else:
                checks["resolution"] = "PASSED (1080x1920)"

        # 2. Audio-Video Duration Sync
        v_dur = float(v_stream.get("duration", 0)) if v_stream else 0
        a_dur = float(a_stream.get("duration", 0)) if a_stream else 0
        dur_delta = abs(v_dur - a_dur)
        if dur_delta > 0.15:
            failures.append(f"A/V sync drift: video={v_dur:.2f}s, audio={a_dur:.2f}s (delta {dur_delta:.2f}s > 0.15s)")
        else:
            checks["av_sync"] = f"PASSED (delta: {dur_delta:.3f}s)"

    def generate_and_verify_cover(self, master_video_path: str, cover_output_path: str, timestamp: float = 28.8, lang: str = "tr") -> bool:
        """Generates 9:16 portrait thumbnail from punchline / high-impact frame or copies existing cover."""
        os.makedirs(os.path.dirname(os.path.abspath(cover_output_path)), exist_ok=True)
        day = self.spec.meta.get("day", "UnknownDay")
        is_en = lang in ("en", "ingilizce")
        
        lang_cover = os.path.join(self.work_dir, f"{day}_Shorts_Kapak_EN.jpg" if is_en else f"{day}_Shorts_Kapak.jpg")
        default_cover = os.path.join(self.work_dir, f"{day}_Shorts_Kapak.jpg")

        if os.path.exists(lang_cover) and os.path.getsize(lang_cover) >= 10000:
            shutil.copyfile(lang_cover, cover_output_path)
        elif os.path.exists(default_cover) and os.path.getsize(default_cover) >= 10000:
            shutil.copyfile(default_cover, cover_output_path)
        elif not os.path.exists(cover_output_path) or os.path.getsize(cover_output_path) < 10000:
            cmd = [
                "ffmpeg", "-y", "-ss", f"{timestamp:.2f}",
                "-i", master_video_path,
                "-vframes", "1",
                "-q:v", "2",
                cover_output_path
            ]
            subprocess.run(cmd, capture_output=True)
        
        if not os.path.exists(cover_output_path) or os.path.getsize(cover_output_path) < 10000:
            return False
        
        try:
            with Image.open(cover_output_path) as im:
                w, h = im.size
                return (w == 1080 and h == 1920)
        except Exception:
            return False

    def _write_publication_docs(self, yt_dir: str, ig_dir: Optional[str], day: str, lang: str = "tr"):
        pub = self.spec.publish or {}
        is_en = lang in ("en", "ingilizce")

        if is_en:
            yt = pub.get("youtube_en") or pub.get("youtube", {})
            yt_file = os.path.join(yt_dir, "YOUTUBE_POST_BILGILERI.md")
            yt_content = f"""# YOUTUBE SHORTS PUBLISHING PACKAGE ({day} - ENGLISH)

## 🎯 Title Options (High CTR & Source-Faithful)
1. **{yt.get('title_1', yt.get('title', ''))}**
2. **{yt.get('title_2', '')}**
3. **{yt.get('title_3', '')}**

## 📝 SEO Description
{yt.get('description', '')}

## 🏷️ Tags
`{', '.join(yt.get('tags', []))}`

## 📌 Pinned Comment Strategy
> "{yt.get('pinned_comment', '')}"
"""
            with open(yt_file, "w", encoding="utf-8") as f:
                f.write(yt_content)

            if ig_dir:
                ig = pub.get("instagram_en") or pub.get("instagram", {})
                ig_file = os.path.join(ig_dir, "INSTAGRAM_POST_BILGILERI.md")
                ig_content = f"""# INSTAGRAM REELS PUBLISHING PACKAGE ({day} - ENGLISH)

## 🎣 Caption Hook (First 2 Lines)
**{ig.get('hook', '')}**

## 📖 Caption Text
{ig.get('caption', '')}

## 🏷️ 30 Niche Hashtags
{ig.get('hashtags', '')}

## 💬 Comment & Story CTA
{ig.get('cta', '')}
"""
                with open(ig_file, "w", encoding="utf-8") as f:
                    f.write(ig_content)
        else:
            yt = pub.get("youtube", {})
            ig = pub.get("instagram", {})

            # YouTube Post Info
            yt_file = os.path.join(yt_dir, "YOUTUBE_POST_BILGILERI.md")
            yt_content = f"""# YOUTUBE SHORTS YAYIN BİLGİLERİ ({day})

## 🎯 Başlık Alternatifleri (Yüksek CTR & Kaynağa Sadık)
1. **{yt.get('title_1', yt.get('title', ''))}**
2. **{yt.get('title_2', '')}**
3. **{yt.get('title_3', '')}**

## 📝 SEO Açıklaması
{yt.get('description', '')}

## 🏷️ Etiketler (Tags)
`{', '.join(yt.get('tags', []))}`

## 📌 Sabit Yorum Stratejisi
> "{yt.get('pinned_comment', '')}"
"""
            with open(yt_file, "w", encoding="utf-8") as f:
                f.write(yt_content)

            if ig_dir:
                # Instagram Post Info
                ig_file = os.path.join(ig_dir, "INSTAGRAM_POST_BILGILERI.md")
                ig_content = f"""# INSTAGRAM REELS YAYIN BİLGİLERİ ({day})

## 🎣 İlk 2 Satırlık Kanca (Caption Hook)
**{ig.get('hook', '')}**

## 📖 Caption Metni
{ig.get('caption', '')}

## 🏷️ 30 Niş Hashtag
{ig.get('hashtags', '')}

## 💬 Yorum & Hikaye CTA
{ig.get('cta', '')}
"""
                with open(ig_file, "w", encoding="utf-8") as f:
                    f.write(ig_content)

    @staticmethod
    def _safe_move_or_replace(src: str, dst: str, max_retries: int = 4, delay: float = 0.4):
        """Safely moves or replaces a directory on Windows with retry and fallback."""
        for attempt in range(max_retries):
            try:
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst, ignore_errors=True)
                    else:
                        os.remove(dst)
                shutil.move(src, dst)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt fallback: try os.replace
                    try:
                        os.replace(src, dst)
                        return
                    except Exception:
                        raise e
                time.sleep(delay)

    def _transactional_deploy(self, yt_staging: str, yt_dir: str, ig_staging: Optional[str] = None, ig_dir: Optional[str] = None) -> bool:
        """
        Atomically swaps staging packages to production showcases with rollback protection.
        Supports single platform (YouTube-only) or dual platform (YouTube + Instagram).
        """
        day = self.spec.meta.get("day", "UnknownDay")
        yt_backup = os.path.abspath(yt_dir) + ".backup"
        ig_backup = (os.path.abspath(ig_dir) + ".backup") if ig_dir else None
        
        # Clean any stale backups
        if os.path.exists(yt_backup):
            shutil.rmtree(yt_backup, ignore_errors=True)
        if ig_backup and os.path.exists(ig_backup):
            shutil.rmtree(ig_backup, ignore_errors=True)

        yt_existed = os.path.exists(yt_dir)
        ig_existed = os.path.exists(ig_dir) if ig_dir else False
        yt_promoted = False
        ig_promoted = False

        try:
            # 1. Verify staging packages are 100% complete and non-empty
            req_yt = [f"{day}_Shorts.mp4", f"{day}_Shorts_Kapak.jpg", "YOUTUBE_POST_BILGILERI.md"]
            for f in req_yt:
                p = os.path.join(yt_staging, f)
                if not os.path.exists(p) or os.path.getsize(p) < 100:
                    raise RuntimeError(f"Incomplete YouTube staging package: missing or invalid '{f}'")

            if ig_staging and ig_dir:
                req_ig = [f"{day}_Reels.mp4", "INSTAGRAM_POST_BILGILERI.md"]
                for f in req_ig:
                    p = os.path.join(ig_staging, f)
                    if not os.path.exists(p) or os.path.getsize(p) < 100:
                        raise RuntimeError(f"Incomplete Instagram staging package: missing or invalid '{f}'")

            # 2. Backup existing showcase directories
            if yt_existed:
                self._safe_move_or_replace(yt_dir, yt_backup)
            if ig_existed and ig_dir and ig_backup:
                self._safe_move_or_replace(ig_dir, ig_backup)

            # 3. Promote staging to production
            os.makedirs(os.path.dirname(os.path.abspath(yt_dir)), exist_ok=True)
            self._safe_move_or_replace(yt_staging, yt_dir)
            yt_promoted = True

            if ig_staging and ig_dir:
                os.makedirs(os.path.dirname(os.path.abspath(ig_dir)), exist_ok=True)
                self._safe_move_or_replace(ig_staging, ig_dir)
                ig_promoted = True

            # 4. Success -> remove backups
            if os.path.exists(yt_backup):
                shutil.rmtree(yt_backup, ignore_errors=True)
            if ig_backup and os.path.exists(ig_backup):
                shutil.rmtree(ig_backup, ignore_errors=True)

            return True

        except Exception as e:
            print(f"[QualityGate] TRANSACTIONAL DEPLOYMENT FAILED: {e}")
            print(f"[QualityGate] INITIATING AUTOMATIC ROLLBACK...")
            
            # Rollback YouTube: restore backup if existed, or delete newly created folder
            if yt_promoted:
                if yt_existed and os.path.exists(yt_backup):
                    if os.path.exists(yt_dir):
                        shutil.rmtree(yt_dir, ignore_errors=True)
                    os.replace(yt_backup, yt_dir)
                else:
                    # Fresh day where yt_dir was newly created -> MUST DELETE yt_dir to prevent partial state!
                    if os.path.exists(yt_dir):
                        shutil.rmtree(yt_dir, ignore_errors=True)
            elif yt_existed and os.path.exists(yt_backup) and not os.path.exists(yt_dir):
                os.replace(yt_backup, yt_dir)

            # Rollback Instagram
            if ig_dir:
                if ig_promoted:
                    if ig_existed and ig_backup and os.path.exists(ig_backup):
                        if os.path.exists(ig_dir):
                            shutil.rmtree(ig_dir, ignore_errors=True)
                        os.replace(ig_backup, ig_dir)
                    else:
                        if os.path.exists(ig_dir):
                            shutil.rmtree(ig_dir, ignore_errors=True)
                elif ig_existed and ig_backup and os.path.exists(ig_backup) and not os.path.exists(ig_dir):
                    os.replace(ig_backup, ig_dir)
            
            # Clean staging
            if os.path.exists(yt_staging):
                shutil.rmtree(yt_staging, ignore_errors=True)
            if ig_staging and os.path.exists(ig_staging):
                shutil.rmtree(ig_staging, ignore_errors=True)

            return False

    def verify_and_release(self, master_video_path: str, transcript_text: str = "", lang: str = "tr") -> Dict[str, Any]:
        day = self.spec.meta.get("day", "UnknownDay")
        file_hash = self.calculate_file_hash(master_video_path)
        build_id = f"{day}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
        
        print(f"\n=======================================================")
        print(f"--- RUNNING QUALITY & RELEASE GATE [Build: {build_id}] ---")
        print(f"=======================================================")

        checks = {}
        failures = []

        # 1. Technical Container & Stream Probe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height,codec_name,pix_fmt,duration",
            "-of", "json", master_video_path
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
        probe_data = json.loads(probe_res.stdout) if probe_res.returncode == 0 else {}
        
        streams = probe_data.get("streams", [])
        v_stream = next((s for s in streams if s.get("width")), None)
        a_stream = next((s for s in streams if not s.get("width")), None)

        if not v_stream or not a_stream:
            failures.append("Missing video or audio stream in rendered file")
        else:
            w = int(v_stream.get("width", 0))
            h = int(v_stream.get("height", 0))
            if w != 1080 or h != 1920:
                failures.append(f"Resolution is {w}x{h}, expected 1080x1920 (9:16 portrait)")
            else:
                checks["resolution"] = "PASSED (1080x1920)"

        # 2. Audio-Video Duration Sync
        v_dur = float(v_stream.get("duration", 0)) if v_stream else 0
        a_dur = float(a_stream.get("duration", 0)) if a_stream else 0
        dur_delta = abs(v_dur - a_dur)
        if dur_delta > 0.15:
            failures.append(f"A/V sync drift: video={v_dur:.2f}s, audio={a_dur:.2f}s (delta {dur_delta:.2f}s > 0.15s)")
        else:
            checks["av_sync"] = f"PASSED (delta: {dur_delta:.3f}s; container stream duration alignment)"

        # 3. Automated Anti-Freeze Motion Gate (Pixel Variance Test) & Photo Duration Limit
        print("[QualityGate] Testing B-roll motion dynamics (Anti-Freeze) & pacing rules...")
        frozen_cuts = []
        motion_log = []

        for idx, cut in enumerate(self.spec.cuts):
            cid = cut.get("id", f"c{idx+1:02d}")
            
            # If cut is explicit speaker fallback, it was not overlaid; speaker played
            if cut.get("fallback") == "speaker_cut" or not cut.get("source_file"):
                motion_log.append({
                    "cut_id": cid,
                    "interval": f"{cut.get('start_t', 0.0):.2f}s - {cut.get('end_t', 0.0):.2f}s",
                    "media_type": "speaker_cut",
                    "status": "fallback_base_speaker_active"
                })
                continue

            mtype = cut.get("media_type", "video")
            st = cut["start_t"]
            et = cut["end_t"]
            dur = et - st
            src_file = cut.get("source_file", "")

            if mtype == "photo":
                # Static photo is intentional. Enforce strict duration limit (<= 3.0s)
                if dur > 3.0:
                    failures.append(f"Cut {cid} static photo duration ({dur:.2f}s) exceeds strict maximum limit of 3.0s (target: 2.0s).")

                if not os.path.exists(src_file) or os.path.getsize(src_file) < 5000:
                    failures.append(f"Photo asset for Cut {cid} missing or too small: {src_file}")
                else:
                    try:
                        with Image.open(src_file) as im:
                            im.verify()
                        motion_log.append({
                            "cut_id": cid,
                            "interval": f"{st:.2f}s - {et:.2f}s",
                            "media_type": "photo",
                            "status": "valid_intentional_static_photo"
                        })
                    except Exception as e:
                        failures.append(f"Photo asset for Cut {cid} corrupted: {e}")
                continue

            # Standard video cut: test pixel variance inside the cut
            t1 = st + min(0.3, dur * 0.25)
            t2 = et - min(0.3, dur * 0.25)

            arr1 = self.extract_frame_pixels(master_video_path, t1)
            arr2 = self.extract_frame_pixels(master_video_path, t2)

            pixel_diff = float(np.abs(arr1 - arr2).mean())
            motion_log.append({
                "cut_id": cid,
                "interval": f"{st:.2f}s - {et:.2f}s",
                "media_type": "video",
                "pixel_diff": round(pixel_diff, 4)
            })

            # If pixel diff is extremely low (< 0.2), motion is frozen!
            if pixel_diff < 0.2:
                frozen_cuts.append(f"Cut {cid} ({st:.2f}-{et:.2f}s): delta={pixel_diff:.4f}")

        if frozen_cuts:
            failures.append(f"CRITICAL: Frozen B-roll detected in {len(frozen_cuts)} scenes: {', '.join(frozen_cuts)}")
        else:
            checks["motion_anti_freeze"] = f"PASSED (All {len(self.spec.cuts)} cuts dynamic/valid; frame pixel variance delta)"

        # Record Provenance Audit
        provenance_data = {
            "build_id": build_id,
            "day": day,
            "source_video": self.spec.source.get("raw_video_path"),
            "in_point": self.spec.source.get("in_point"),
            "out_point": self.spec.source.get("out_point"),
            "duration": self.spec.source.get("duration"),
            "provenance": getattr(self.spec, "provenance", None) or self.spec.meta.get("provenance", {}),
            "cuts_provenance": [
                {
                    "id": c.get("id"),
                    "media_type": c.get("media_type", "video"),
                    "start_t": c.get("start_t"),
                    "end_t": c.get("end_t"),
                    "duration": round(c.get("end_t", 0.0) - c.get("start_t", 0.0), 2),
                    "selection_source": c.get("selection_source", "automated_selector" if c.get("visual_need") else "agent_editorial"),
                    "source_file": c.get("source_file"),
                    "content_hash": self.calculate_file_hash(c["source_file"]) if c.get("source_file") and os.path.exists(c["source_file"]) else None
                }
                for c in self.spec.cuts
            ]
        }
        prov_path = os.path.join(self.work_dir, "provenance_audit.json")
        try:
            with open(prov_path, "w", encoding="utf-8") as f:
                json.dump(provenance_data, f, indent=2, ensure_ascii=False, default=str)
            checks["provenance_audit"] = f"RECORDED ({prov_path})"
        except Exception as e:
            print(f"[QualityGate] Warning recording provenance audit: {e}")

        # 4. Audio Mastering & Loudness Gate (Strict EBU R128: +/- 0.5 LUFS, TP <= -1.0 dBFS)
        print("[QualityGate] Measuring integrated loudness & True Peak (EBU R128)...")
        audio_metrics = AudioEngine.measure_loudness(master_video_path)
        lufs = audio_metrics.get("integrated_lufs")
        tp = audio_metrics.get("true_peak")
        target_lufs = self.spec.audio.get("target_lufs", -14.0)

        if lufs is None or abs(lufs - target_lufs) > 0.5:
            failures.append(f"Loudness out of spec: {lufs} LUFS (target {target_lufs} +/- 0.5)")
        elif tp is None or tp > -1.0:
            failures.append(f"True Peak out of spec: {tp} dBFS (target <= -1.0 dBFS and not None)")
        else:
            checks["loudness_ebu_r128"] = f"PASSED (Integrated: {lufs} LUFS, True Peak: {tp} dBFS)"

        # 5. Semantic Fidelity Audit (Subtitles, Publication Docs, and Cover Text)
        print("[QualityGate] Auditing semantic fidelity against transcript...")
        fidelity_res = SemanticFidelityChecker.audit_fidelity(
            self.spec.subtitles, transcript_text, self.spec.publish, self.spec.cover
        )
        if not fidelity_res["passed"]:
            for v in fidelity_res["violations"]:
                failures.append(f"Fidelity Violation ({v['field']}): {v['message']}")
        else:
            checks["semantic_fidelity"] = f"PASSED ({fidelity_res.get('summary', 'OK')})"
        checks["fidelity_warnings"] = fidelity_res.get("warnings", [])

        # 6. Staging Preparation & Cover Verification
        is_en = lang in ("en", "ingilizce")
        base_lang_dir = "ingilizce" if is_en else "turkce"

        yt_dir = os.path.join(base_lang_dir, "youtube", day)
        yt_staging = os.path.join(base_lang_dir, "youtube", f"{day}.staging")

        if os.path.exists(yt_staging):
            shutil.rmtree(yt_staging, ignore_errors=True)
        os.makedirs(yt_staging, exist_ok=True)

        yt_stage_video = os.path.join(yt_staging, f"{day}_Shorts.mp4")
        yt_stage_cover = os.path.join(yt_staging, f"{day}_Shorts_Kapak.jpg")
        shutil.copyfile(master_video_path, yt_stage_video)

        if not is_en:
            ig_dir = os.path.join(base_lang_dir, "instagram", day)
            ig_staging = os.path.join(base_lang_dir, "instagram", f"{day}.staging")
            if os.path.exists(ig_staging):
                shutil.rmtree(ig_staging, ignore_errors=True)
            os.makedirs(ig_staging, exist_ok=True)
            ig_stage_video = os.path.join(ig_staging, f"{day}_Reels.mp4")
            shutil.copyfile(master_video_path, ig_stage_video)
        else:
            ig_dir = None
            ig_staging = None

        # Generate & rigorously verify cover thumbnail
        cover_ok = self.generate_and_verify_cover(master_video_path, yt_stage_cover, lang=lang)
        if not cover_ok:
            failures.append("YouTube Shorts cover thumbnail generation or verification failed (expected 1080x1920 JPG)")
        else:
            checks["thumbnail_cover"] = "PASSED (1080x1920 verified)"

        # Write publication docs into staging
        self._write_publication_docs(yt_staging, ig_staging, day, lang=lang)

        # 7. Gate Decision & Transactional Deployment
        qa_passed = len(failures) == 0
        checks["qa_status"] = "PASSED" if qa_passed else "FAILED"
        checks["failures"] = failures
        checks["build_id"] = build_id
        checks["sha256"] = file_hash
        checks["motion_analysis"] = motion_log
        checks["timestamp"] = datetime.now().isoformat()
        checks["language"] = lang

        if qa_passed:
            deployed = self._transactional_deploy(yt_staging, yt_dir, ig_staging, ig_dir)
            if deployed:
                checks["delivery_status"] = "DEPLOYED"
                checks["overall_status"] = "PASSED"
                try:
                    from core.asset_registry import registry
                    registry.record_build_usage(self.spec, build_id)
                    print(f"[QualityGate] Asset registry updated with build {build_id}.")
                except Exception as e:
                    print(f"[QualityGate] Warning updating registry: {e}")

                print(f"[QualityGate] RELEASE SUCCESSFUL ({lang.upper()})! Verified video deployed to:")
                print(f"  -> YouTube Showcase:   {os.path.join(yt_dir, f'{day}_Shorts.mp4')}")
                print(f"  -> YouTube Thumbnail:  {os.path.join(yt_dir, f'{day}_Shorts_Kapak.jpg')}")
                if ig_dir:
                    print(f"  -> Instagram Showcase: {os.path.join(ig_dir, f'{day}_Reels.mp4')}")
            else:
                checks["delivery_status"] = "ROLLED_BACK"
                checks["overall_status"] = "FAILED"
                failures.append("Showcase deployment transaction failed; previous files restored via rollback")
        else:
            checks["delivery_status"] = "ABORTED"
            checks["overall_status"] = "FAILED"
            if os.path.exists(yt_staging):
                shutil.rmtree(yt_staging, ignore_errors=True)
            if ig_staging and os.path.exists(ig_staging):
                shutil.rmtree(ig_staging, ignore_errors=True)
            print(f"[QualityGate] RELEASE BLOCKED! Build rejected due to {len(failures)} failures:")
            for f in failures:
                print(f"  [X] {f}")
            print("[QualityGate] Showcase folders remain PROTECTED and untouched.")

        # Save QA Report in work_dir
        report_path = os.path.join(self.work_dir, f"QA_REPORT_{build_id}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(checks, f, indent=2, ensure_ascii=False)
        print(f"[QualityGate] Detailed QA report saved to: {report_path}")

        return checks
