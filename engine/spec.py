import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from engine.subtitle_engine import SubtitleEngine

@dataclass
class VideoSpec:
    meta: Dict[str, Any]
    source: Dict[str, Any]
    audio: Dict[str, Any]
    cuts: List[Dict[str, Any]]
    subtitles: List[Dict[str, Any]]
    cover: Optional[Dict[str, Any]] = None
    publish: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    watermark: Optional[Dict[str, Any]] = None

    @classmethod
    def from_file(cls, spec_path: str) -> "VideoSpec":
        if not os.path.exists(spec_path):
            raise FileNotFoundError(f"Spec file not found: {spec_path}")
        with open(spec_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VideoSpec":
        return cls(
            meta=data.get("meta", {}),
            source=data.get("source", {}),
            audio=data.get("audio", {}),
            cuts=data.get("cuts", []),
            subtitles=data.get("subtitles", []),
            cover=data.get("cover"),
            publish=data.get("publish"),
            provenance=data.get("provenance") or data.get("meta", {}).get("provenance"),
            watermark=cls._resolve_watermark_config(data)
        )

    @classmethod
    def _resolve_watermark_config(cls, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from engine.preferences import EditorialPreferences
        wm = data.get("watermark") or data.get("meta", {}).get("watermark")
        if wm is None:
            return EditorialPreferences.get_watermark_config()
        if isinstance(wm, dict):
            if wm.get("enabled", True):
                default_wm = EditorialPreferences.get_watermark_config()
                merged = dict(default_wm)
                merged.update(wm)
                return merged
            return wm
        return None

    def validate(self, allow_unresolved: bool = False) -> List[str]:
        errors = []
        # Meta validation
        if not self.meta.get("day"):
            errors.append("Spec meta.day is required (e.g. 'Gun_2')")

        # Source validation
        src = self.source
        if not src.get("raw_video_path"):
            errors.append("Spec source.raw_video_path is required")
        elif not os.path.exists(src["raw_video_path"]):
            errors.append(f"Source video not found: {src['raw_video_path']}")

        in_pt = src.get("in_point", 0.0)
        out_pt = src.get("out_point", 0.0)
        if out_pt <= in_pt:
            errors.append(f"Source out_point ({out_pt}) must be > in_point ({in_pt})")
        
        total_duration = out_pt - in_pt

        # Cuts validation
        for i, cut in enumerate(self.cuts):
            cid = cut.get("id", f"cut_{i}")
            st = cut.get("start_t", 0.0)
            et = cut.get("end_t", 0.0)
            if et <= st:
                errors.append(f"Cut {cid} end_t ({et}) must be > start_t ({st})")
            if et > total_duration + 0.1:
                errors.append(f"Cut {cid} end_t ({et}) exceeds total duration ({total_duration:.2f})")
            
            cut_dur = et - st
            media_type = cut.get("media_type", "video")
            if media_type == "photo" and cut_dur > 3.0:
                errors.append(f"Cut {cid} is a static photo with duration {cut_dur:.2f}s, exceeding strict limit of 3.0s (target: 2.0s).")
            
            src_file = cut.get("source_file")
            has_visual_need = bool(cut.get("visual_need"))
            is_fallback = cut.get("fallback") == "speaker_cut"

            if not allow_unresolved and not is_fallback:
                if not src_file:
                    errors.append(f"Cut {cid} missing 'source_file'")
                elif not os.path.exists(src_file):
                    errors.append(f"Cut {cid} source_file does not exist: {src_file}")
            elif allow_unresolved:
                if not has_visual_need and not is_fallback and src_file and not os.path.exists(src_file):
                    errors.append(f"Cut {cid} source_file does not exist: {src_file}")

        # Subtitles validation
        for i, sub in enumerate(self.subtitles):
            sid = sub.get("id", f"sub_{i}")
            st = sub.get("start_t", sub.get("start", 0.0))
            et = sub.get("end_t", sub.get("end", 0.0))
            if et <= st:
                errors.append(f"Subtitle {sid} end_t ({et}) must be > start_t ({st})")
            if not sub.get("text"):
                errors.append(f"Subtitle {sid} text is empty")

        # Subtitle layout & word limit enforcement (<=5 words per line, <=2 lines per badge)
        errors.extend(SubtitleEngine.validate_subtitles(self.subtitles))

        # Audio validation
        bgm = self.audio.get("bgm_path")
        if bgm and not os.path.exists(bgm):
            errors.append(f"BGM audio file not found: {bgm}")

        # Watermark validation
        if self.watermark and self.watermark.get("enabled", True):
            wm_img = self.watermark.get("image_path")
            if not wm_img:
                errors.append("Watermark enabled but 'image_path' is missing")
            elif not os.path.exists(wm_img):
                errors.append(f"Watermark image not found: {wm_img}")

        return errors

    def validate_post_resolution(self) -> List[str]:
        """Ensures every cut is either properly backed by a real file or explicitly marked as speaker_cut."""
        errors = []
        for i, cut in enumerate(self.cuts):
            cid = cut.get("id", f"cut_{i}")
            src_file = cut.get("source_file")
            is_fallback = cut.get("fallback") == "speaker_cut"
            if not is_fallback:
                if not src_file:
                    errors.append(f"Cut {cid} unresolved: no source_file and no speaker_cut fallback")
                elif not os.path.exists(src_file):
                    errors.append(f"Cut {cid} source_file missing on disk: {src_file}")
        return errors
