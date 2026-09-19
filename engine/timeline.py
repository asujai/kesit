import os
import subprocess
import hashlib
import json
from typing import Dict, Any, List, Optional
from engine.spec import VideoSpec
from engine.subtitle_engine import SubtitleEngine

class TimelineCompiler:
    """
    Compiles declarative VideoSpec into an FFmpeg command with guaranteed
    timestamp synchronization, fluid motion (anti-freeze setpts), parameter-based
    cache invalidation, photo media support, and ergonomic subtitle overlay.
    """
    def __init__(self, spec: VideoSpec, work_dir: str):
        self.spec = spec
        self.work_dir = work_dir
        self.norm_cuts_dir = os.path.join(work_dir, "norm_cuts")
        self.badges_dir = os.path.join(work_dir, "sub_badges")
        os.makedirs(self.norm_cuts_dir, exist_ok=True)
        os.makedirs(self.badges_dir, exist_ok=True)

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        s = json.dumps(data, sort_keys=True)
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    @staticmethod
    def _is_cache_valid(target_path: str, expected_hash: str) -> bool:
        if not os.path.exists(target_path) or os.path.getsize(target_path) < 5000:
            return False
        cache_key_file = target_path + ".cache_key"
        if not os.path.exists(cache_key_file):
            return False
        try:
            with open(cache_key_file, "r", encoding="utf-8") as f:
                saved_hash = f.read().strip()
            return saved_hash == expected_hash
        except Exception:
            return False

    @staticmethod
    def _save_cache_key(target_path: str, cache_hash: str):
        cache_key_file = target_path + ".cache_key"
        with open(cache_key_file, "w", encoding="utf-8") as f:
            f.write(cache_hash)

    def collect_and_normalize_cuts(self, force: bool = False) -> List[Dict[str, Any]]:
        """Normalizes B-roll video and photo cuts to 1080x1920 25fps. Omit speaker_cut fallbacks."""
        fps = self.spec.source.get("fps", 25)
        normalized_cuts = []
        for idx, cut in enumerate(self.spec.cuts):
            cid = cut.get("id", f"c{idx+1:02d}")
            
            # Explicit fallback or missing file -> remain on base speaker
            if cut.get("fallback") == "speaker_cut" or not cut.get("source_file"):
                print(f"[Timeline] Cut {cid} marked as speaker_cut -> omitting B-roll overlay (showing base speaker).")
                continue

            src_file = cut["source_file"]
            if not os.path.exists(src_file):
                print(f"[Timeline] Warning: Cut {cid} source file '{src_file}' not found -> falling back to base speaker.")
                continue

            media_type = cut.get("media_type", "video")
            ss = cut.get("in_point", 0.0)
            st = cut["start_t"]
            et = cut["end_t"]
            dur = et - st
            speed = cut.get("speed", 1.0)
            src_dur = dur * speed
            src_mtime = os.path.getmtime(src_file) if os.path.exists(src_file) else 0

            norm_path = os.path.join(self.norm_cuts_dir, f"{cid}.mp4")
            cut_params = {
                "source_file": os.path.abspath(src_file) if os.path.exists(src_file) else src_file,
                "media_type": media_type,
                "in_point": ss,
                "start_t": st,
                "end_t": et,
                "speed": speed,
                "fps": fps,
                "mtime": src_mtime
            }
            cut_hash = self._compute_hash(cut_params)

            if force or not self._is_cache_valid(norm_path, cut_hash):
                vf_filters = []
                if media_type == "photo":
                    vf_filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
                    vf_filters.append("crop=1080:1920")
                    vf_filters.append(f"fps={fps}")
                    vf = ",".join(vf_filters)
                    cmd_norm = [
                        "ffmpeg", "-y",
                        "-loop", "1", "-framerate", str(fps),
                        "-i", src_file,
                        "-t", f"{dur:.2f}",
                        "-vf", vf,
                        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                        "-pix_fmt", "yuv420p",
                        "-an", norm_path
                    ]
                else:
                    if speed != 1.0:
                        setpts_val = 1.0 / speed
                        vf_filters.append(f"setpts={setpts_val:.3f}*PTS")
                    vf_filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
                    vf_filters.append("crop=1080:1920")
                    vf_filters.append(f"fps={fps}")
                    vf = ",".join(vf_filters)

                    cmd_norm = [
                        "ffmpeg", "-y",
                        "-ss", str(ss), "-i", src_file,
                        "-t", f"{src_dur:.2f}",
                        "-vf", vf,
                        "-t", f"{dur:.2f}",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                        "-an", norm_path
                    ]

                res = subprocess.run(cmd_norm, capture_output=True, text=True)
                if res.returncode != 0:
                    raise RuntimeError(f"Cut {cid} normalization failed: {res.stderr}")
                self._save_cache_key(norm_path, cut_hash)

            normalized_cuts.append({
                "id": cid,
                "path": norm_path,
                "start_t": st,
                "end_t": et,
                "dur": dur,
                "media_type": media_type
            })
        return normalized_cuts

    def compile_visual(self, out_visual_path: str, subtitles: Optional[List[Dict[str, Any]]] = None, badges_dir: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(os.path.abspath(out_visual_path)), exist_ok=True)
        fps = self.spec.source.get("fps", 25)
        in_pt = self.spec.source.get("in_point", 0.0)
        out_pt = self.spec.source.get("out_point", 0.0)
        total_dur = out_pt - in_pt
        fade_dur = self.spec.audio.get("fade_out_duration", 0.73)
        fade_start = max(0.0, total_dur - fade_dur)

        # 1. Base Speaker Video Crop & Preparation with Cache Key
        raw_v = self.spec.source["raw_video_path"]
        raw_mtime = os.path.getmtime(raw_v) if os.path.exists(raw_v) else 0
        crop_filter = self.spec.source.get("crop_filter")
        if not crop_filter:
            crop_filter = f"crop=w=ih*9/16:h=ih:x=(iw-ih*9/16)/2:y=0,scale=1080:1920,fps={fps}"
        elif f"fps={fps}" not in crop_filter:
            crop_filter = f"{crop_filter},fps={fps}"

        base_params = {
            "raw_video_path": os.path.abspath(raw_v),
            "in_point": in_pt,
            "out_point": out_pt,
            "fps": fps,
            "mtime": raw_mtime,
            "crop_filter": crop_filter
        }
        base_hash = self._compute_hash(base_params)
        base_video_path = os.path.join(self.work_dir, "base_speaker_1080x1920.mp4")

        if force or not self._is_cache_valid(base_video_path, base_hash):
            print(f"[Timeline] Preparing base speaker video (9:16 portrait crop) [Hash: {base_hash[:8]}]...")
            cmd_base = [
                "ffmpeg", "-y",
                "-ss", str(in_pt), "-to", str(out_pt),
                "-i", raw_v,
                "-vf", crop_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-an", base_video_path
            ]
            res = subprocess.run(cmd_base, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Base speaker prep failed: {res.stderr}")
            self._save_cache_key(base_video_path, base_hash)

        # 2. Normalize Each B-Roll Cut with Cache Key
        normalized_cuts = self.collect_and_normalize_cuts(force=force)

        # 3. Generate Subtitles Badges
        target_subs = subtitles if subtitles is not None else self.spec.subtitles
        target_badges_dir = badges_dir if badges_dir is not None else self.badges_dir
        os.makedirs(target_badges_dir, exist_ok=True)
        sub_engine = SubtitleEngine()
        processed_subs = sub_engine.generate_all_badges(target_subs, target_badges_dir)

        # 4. Assemble Master FFmpeg Filtergraph
        inputs = ["-i", base_video_path]
        filter_chains = []
        last_v = "0:v"

        # B-Roll Cuts with Anti-Freeze setpts
        for idx, cut in enumerate(normalized_cuts):
            inputs.extend(["-stream_loop", "-1", "-i", cut["path"]])
            cut_idx = 1 + idx
            st = cut["start_t"]
            et = cut["end_t"]
            shifted_v = f"v_shift_{idx}"
            out_v = f"v_cut_{idx}"

            # CRITICAL FIX: Shift PTS so clip starts playing at st and enable between st and et
            filter_chains.append(f"[{cut_idx}:v]setpts=PTS-STARTPTS+{st:.2f}/TB[{shifted_v}]")
            filter_chains.append(f"[{last_v}][{shifted_v}]overlay=enable='between(t,{st:.2f},{et:.2f})':eof_action=pass[{out_v}]")
            last_v = out_v

        # Subtitle Badges Overlay
        sub_start_idx = 1 + len(normalized_cuts)
        for s_idx, sub in enumerate(processed_subs):
            inputs.extend(["-i", sub["badge_path"]])
            badge_idx = sub_start_idx + s_idx
            st = sub["start"]
            et = sub["end"]
            out_sub_v = f"v_sub_{s_idx}"

            # Ergonomic placement: center horizontally, Y=1440
            filter_chains.append(f"[{last_v}][{badge_idx}:v]overlay=(W-w)/2:1440:enable='between(t,{st:.2f},{et:.2f})'[{out_sub_v}]")
            last_v = out_sub_v

        # Watermark Overlay (Brand Identity & Anti-Piracy Protection)
        watermark_config = getattr(self.spec, "watermark", None)
        if watermark_config and watermark_config.get("enabled", True):
            wm_path = watermark_config.get("image_path")
            if wm_path and os.path.exists(wm_path):
                wm_idx = sub_start_idx + len(processed_subs)
                inputs.extend(["-i", wm_path])
                wm_x = watermark_config.get("x", "W-w-40")
                wm_y = watermark_config.get("y", "H-h-130")
                out_wm_v = "v_watermark"
                filter_chains.append(f"[{last_v}][{wm_idx}:v]overlay={wm_x}:{wm_y}[{out_wm_v}]")
                last_v = out_wm_v

        # Fade out to black at the end
        final_v = "v_final"
        filter_chains.append(f"[{last_v}]fade=t=out:st={fade_start:.2f}:d={fade_dur:.2f}[{final_v}]")

        filter_complex_str = ";".join(filter_chains)

        cmd_render = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex_str,
            "-map", f"[{final_v}]",
            "-t", f"{total_dur:.2f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-an", out_visual_path
        ]

        print(f"[Timeline] Rendering full visual pipeline ({len(normalized_cuts)} B-rolls, {len(processed_subs)} subtitles)...")
        res = subprocess.run(cmd_render, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Visual render failed: {res.stderr}")

        return {
            "path": out_visual_path,
            "duration": total_dur,
            "cuts_count": len(normalized_cuts),
            "subtitles_count": len(processed_subs)
        }
