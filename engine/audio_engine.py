import os
import re
import json
import hashlib
import subprocess
from typing import Dict, Any

class AudioEngine:
    """
    Handles speech audio extraction, BGM mixing, dip-to-black fade-out,
    parameter-based cache validation, and EBU R128 (-14.0 LUFS) mastering.
    """
    @classmethod
    def compute_audio_cache_key(cls, raw_video: str, in_point: float, out_point: float,
                                bgm_path: str, bgm_gain: float, target_lufs: float,
                                fade_out_duration: float = 0.73) -> str:
        raw_mtime = os.path.getmtime(raw_video) if os.path.exists(raw_video) else 0
        bgm_mtime = os.path.getmtime(bgm_path) if bgm_path and os.path.exists(bgm_path) else 0
        params = {
            "raw_video": os.path.abspath(raw_video) if os.path.exists(raw_video) else raw_video,
            "raw_mtime": raw_mtime,
            "in_point": round(float(in_point), 3),
            "out_point": round(float(out_point), 3),
            "bgm_path": os.path.abspath(bgm_path) if bgm_path and os.path.exists(bgm_path) else bgm_path,
            "bgm_mtime": bgm_mtime,
            "bgm_gain": round(float(bgm_gain), 4),
            "target_lufs": round(float(target_lufs), 2),
            "fade_out_duration": round(float(fade_out_duration), 4)
        }
        s = json.dumps(params, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    @classmethod
    def is_audio_cache_valid(cls, audio_file: str, expected_key: str) -> bool:
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 5000:
            return False
        key_file = audio_file + ".cache_key"
        if not os.path.exists(key_file):
            return False
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                return f.read().strip() == expected_key
        except Exception:
            return False

    @classmethod
    def build_master_audio(cls, raw_video: str, in_point: float, out_point: float,
                           bgm_path: str, bgm_gain: float, target_lufs: float,
                           out_audio_path: str, fade_out_duration: float = 0.73) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(os.path.abspath(out_audio_path)), exist_ok=True)
        total_dur = out_point - in_point
        fade_start = max(0.0, total_dur - fade_out_duration)

        # Two-pass FFmpeg EBU R128 mastering for exact integrated loudness & True Peak
        pass1_filter = (
            f"[0:a]volume=1.0[a_voice];"
            f"[1:a]volume={bgm_gain:.2f},afade=t=in:st=0:d=1.0,afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[a_bgm];"
            f"[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2,"
            f"loudnorm=I={target_lufs}:LRA=7:tp=-1.5:print_format=json"
        )
        pass1_cmd = [
            "ffmpeg", "-y",
            "-ss", str(in_point), "-to", str(out_point), "-i", raw_video,
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex", pass1_filter,
            "-t", f"{total_dur:.2f}",
            "-f", "null", "-"
        ]
        res1 = subprocess.run(pass1_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        p1 = None
        if res1.returncode == 0:
            try:
                m = re.search(r'\{\s*"input_i"\s*:\s*"[^"]+".*?\}', res1.stderr, re.DOTALL)
                if m:
                    p1 = json.loads(m.group(0))
            except Exception:
                p1 = None

        if p1:
            filter_str = (
                f"[0:a]volume=1.0[a_voice];"
                f"[1:a]volume={bgm_gain:.2f},afade=t=in:st=0:d=1.0,afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[a_bgm];"
                f"[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2,"
                f"loudnorm=I={target_lufs}:LRA=7:tp=-1.5:"
                f"measured_I={p1.get('input_i', '-24.0')}:"
                f"measured_LRA={p1.get('input_lra', '7.0')}:"
                f"measured_tp={p1.get('input_tp', '-2.0')}:"
                f"measured_thresh={p1.get('input_thresh', '-34.0')}:"
                f"offset={p1.get('target_offset', '0.0')},"
                f"afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[a_out]"
            )
        else:
            filter_str = (
                f"[0:a]volume=1.0[a_voice];"
                f"[1:a]volume={bgm_gain:.2f},afade=t=in:st=0:d=1.0,afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[a_bgm];"
                f"[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2,"
                f"loudnorm=I={target_lufs}:LRA=7:tp=-1.5,"
                f"afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[a_out]"
            )

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(in_point), "-to", str(out_point), "-i", raw_video,
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex", filter_str,
            "-map", "[a_out]",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total_dur:.2f}",
            out_audio_path
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode != 0:
            raise RuntimeError(f"Audio mastering failed: {res.stderr}")

        # Write cache key alongside master audio file
        cache_key = cls.compute_audio_cache_key(
            raw_video, in_point, out_point, bgm_path, bgm_gain, target_lufs, fade_out_duration
        )
        with open(out_audio_path + ".cache_key", "w", encoding="utf-8") as f:
            f.write(cache_key)

        # Measure master audio with ebur128
        metrics = cls.measure_loudness(out_audio_path)
        return {
            "path": out_audio_path,
            "duration": total_dur,
            "integrated_lufs": metrics.get("integrated_lufs"),
            "true_peak": metrics.get("true_peak"),
            "target_lufs": target_lufs
        }

    @classmethod
    def measure_loudness(cls, audio_file: str) -> Dict[str, float]:
        cmd = [
            "ffmpeg", "-i", audio_file,
            "-af", "ebur128=framelog=quiet:peak=true",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        output = res.stderr

        lufs = None
        tp = None

        m_i = re.search(r"Integrated loudness:\s+I:\s+([-\d\.]+)\s+LUFS", output)
        if m_i:
            lufs = float(m_i.group(1))

        m_tp = re.search(r"Peak:\s+([-\d\.]+)\s+dBFS", output)
        if m_tp:
            tp = float(m_tp.group(1))

        return {"integrated_lufs": lufs, "true_peak": tp}
