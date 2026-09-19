import os
import json
from typing import Dict, Any

DEFAULT_PREFERENCES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "editorial_preferences.json")

class EditorialPreferences:
    """
    Loads and provides user-defined editorial and pacing rules across builds.
    Guarantees user constraints accumulated across day-by-day evaluation feedback
    (e.g. strict word-level B-roll synchrony, surreal high-CTR covers without speaker name/screenshots,
    boosted BGM levels >= 0.20, and clean standalone hooks).
    """
    _cached_prefs: Dict[str, Any] = None

    @classmethod
    def load(cls, path: str = DEFAULT_PREFERENCES_PATH) -> Dict[str, Any]:
        if cls._cached_prefs is not None:
            return cls._cached_prefs
        
        defaults = {
            "pacing": {
                "max_photo_duration": 3.0,
                "target_photo_duration": 2.0,
                "min_photo_duration": 1.0,
                "max_broll_cut_duration": 4.5,
                "target_broll_cut_duration": 3.0,
                "min_broll_cut_duration": 1.2,
                "golden_speaker_ratio_min": 0.40,
                "golden_speaker_ratio_max": 0.50,
                "strict_word_level_broll_sync": True
            },
            "audio": {
                "target_lufs": -14.0,
                "min_bgm_gain": 0.20,
                "target_bgm_gain": 0.23
            },
            "covers": {
                "allow_video_screenshot": False,
                "show_speaker_name": False,
                "style": "surreal_conceptual_high_ctr"
            },
            "subtitles": {
                "max_lines_per_badge": 2,
                "max_words_per_line": 5,
                "font_size": 44
            },
            "watermark": {
                "enabled": True,
                "image_path": "assets/branding/watermark_zen_circle.png",
                "x": "W-w-40",
                "y": "H-h-130"
            }
        }

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    defaults.update(data)
            except Exception as e:
                print(f"[EditorialPreferences] Warning reading preferences: {e}")
        
        cls._cached_prefs = defaults
        return cls._cached_prefs

    @classmethod
    def get_max_photo_duration(cls) -> float:
        return float(cls.load().get("pacing", {}).get("max_photo_duration", 3.0))

    @classmethod
    def get_max_broll_duration(cls) -> float:
        return float(cls.load().get("pacing", {}).get("max_broll_cut_duration", 4.5))

    @classmethod
    def get_target_bgm_gain(cls) -> float:
        return float(cls.load().get("audio", {}).get("target_bgm_gain", 0.23))

    @classmethod
    def get_cover_preferences(cls) -> Dict[str, Any]:
        return dict(cls.load().get("covers", {}))

    @classmethod
    def get_max_subtitle_lines(cls) -> int:
        return int(cls.load().get("subtitles", {}).get("max_lines_per_badge", 2))

    @classmethod
    def get_max_words_per_line(cls) -> int:
        return int(cls.load().get("subtitles", {}).get("max_words_per_line", 5))

    @classmethod
    def get_watermark_config(cls) -> Dict[str, Any]:
        return dict(cls.load().get("watermark", {
            "enabled": True,
            "image_path": "assets/branding/watermark_zen_circle.png",
            "x": "W-w-40",
            "y": "H-h-130"
        }))
