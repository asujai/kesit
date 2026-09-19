import os
import re
import json
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

class SubtitleEngine:
    """
    Unified, robust subtitle badge generator (Minimalist Black Pill style).
    Handles automatic word-limit enforcement, line-wrapping, highlight matching,
    and ergonomic safe-zone positioning.
    """
    def __init__(self, font_size: int = 52, max_words: int = 5, max_pixel_width: int = 880):
        self.font_size = font_size
        self.max_words = max_words
        self.max_pixel_width = max_pixel_width
        self.font = self._load_font()

    def _load_font(self):
        font_paths = [
            "C:\\Windows\\Fonts\\segoeuib.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\calibrib.ttf"
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, self.font_size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def wrap_or_split_text(self, text: str) -> List[str]:
        """Ensures lines do not exceed max_words (strict <= 5 words) and max_pixel_width."""
        # Handle explicit newlines first
        if "\n" in text:
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            if len(parts) <= 2:
                valid = True
                for p in parts:
                    if len(p.split()) > self.max_words or self._get_text_width(p) > self.max_pixel_width:
                        valid = False
                        break
                if valid:
                    return parts
            text = " ".join(parts)

        words = text.split()
        if len(words) <= self.max_words:
            w = self._get_text_width(text)
            if w <= self.max_pixel_width:
                return [text]
        
        # Balance into 2 lines if possible
        mid = (len(words) + 1) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        if (len(words[:mid]) <= self.max_words and len(words[mid:]) <= self.max_words and
            self._get_text_width(line1) <= self.max_pixel_width and self._get_text_width(line2) <= self.max_pixel_width):
            return [line1, line2]

        # Multi-line greedily bounded by max_words and pixel width
        lines = []
        cur_line_words = []
        for word in words:
            test_line = " ".join(cur_line_words + [word])
            if len(cur_line_words) < self.max_words and self._get_text_width(test_line) <= self.max_pixel_width:
                cur_line_words.append(word)
            else:
                if cur_line_words:
                    lines.append(" ".join(cur_line_words))
                    cur_line_words = [word]
                else:
                    lines.append(word)
                    cur_line_words = []
        if cur_line_words:
            lines.append(" ".join(cur_line_words))

        # STRICT ENFORCEMENT: Subtitle badge MUST NEVER exceed 2 lines
        if len(lines) > 2:
            if len(words) <= self.max_words * 2:
                half = (len(words) + 1) // 2
                return [" ".join(words[:half]), " ".join(words[half:])]
            else:
                return lines[:2]

        return lines

    @classmethod
    def validate_subtitles(cls, subtitles: List[Dict[str, Any]]) -> List[str]:
        """Validates all subtitle cues to ensure strict <=5 words per line and <=2 lines per badge."""
        engine = cls()
        errors = []
        for idx, sub in enumerate(subtitles):
            sid = sub.get("id", f"s{idx+1:02d}")
            text = sub.get("text", "")
            lines = engine.wrap_or_split_text(text)
            if len(lines) > 2:
                errors.append(f"Subtitle {sid} exceeds max 2 lines ({len(lines)} lines generated)")
            for l_idx, l in enumerate(lines):
                w_count = len(l.split())
                if w_count > 5:
                    errors.append(f"Subtitle {sid} line {l_idx+1} has {w_count} words (max is 5)")
        return errors

    def _get_text_width(self, text: str) -> int:
        dummy = Image.new("RGBA", (10, 10))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=self.font)
        return bbox[2] - bbox[0]

    def render_badge(self, text_lines: List[str], highlight_phrase: str, out_path: str):
        """Renders a minimalist Black Pill rounded capsule PNG with transparent background."""
        try:
            ascent, descent = self.font.getmetrics()
            line_height = ascent + descent
        except Exception:
            line_height = int(self.font_size * 1.3)

        line_spacing = 10
        pad_x = 36
        pad_y = 20
        radius = 24
        
        # Measure dimensions
        dummy = Image.new("RGBA", (10, 10))
        draw_dummy = ImageDraw.Draw(dummy)
        
        line_widths = []
        for line in text_lines:
            bbox = draw_dummy.textbbox((0, 0), line, font=self.font)
            w = bbox[2] - bbox[0]
            line_widths.append(w)

        max_w = max(line_widths) if line_widths else 200
        total_text_h = len(text_lines) * line_height + max(0, len(text_lines) - 1) * line_spacing

        badge_w = max_w + pad_x * 2
        badge_h = total_text_h + pad_y * 2

        img = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background: #0A0A0C at 94% opacity with subtle sleek border
        bg_color = (10, 10, 12, 240)
        border_color = (255, 255, 255, 35)
        draw.rounded_rectangle([0, 0, badge_w - 1, badge_h - 1], radius=radius, fill=bg_color, outline=border_color, width=2)

        # Draw text lines
        cur_y = pad_y
        hl_clean = re.sub(r'[^\w\s]', '', highlight_phrase.lower()).strip() if highlight_phrase else ""

        for line, w in zip(text_lines, line_widths):
            cur_x = (badge_w - w) // 2
            words = line.split()

            for word in words:
                word_clean = re.sub(r'[^\w\s]', '', word.lower()).strip()
                # Check highlight match
                is_hl = False
                if hl_clean and (word_clean in hl_clean.split() or word_clean in hl_clean):
                    is_hl = True

                word_color = (255, 220, 0, 255) if is_hl else (255, 255, 255, 255)
                draw.text((cur_x, cur_y), word, font=self.font, fill=word_color)

                w_bbox = draw.textbbox((0, 0), word + " ", font=self.font)
                cur_x += (w_bbox[2] - w_bbox[0])

            cur_y += line_height + line_spacing

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        img.save(out_path, "PNG")

    def generate_all_badges(self, subtitles: List[Dict[str, Any]], out_dir: str) -> List[Dict[str, Any]]:
        os.makedirs(out_dir, exist_ok=True)
        processed = []

        for idx, sub in enumerate(subtitles):
            sid = sub.get("id", f"sub_{idx+1:02d}")
            text = sub.get("text", "").strip()
            hl = sub.get("highlight", "")
            st = float(sub.get("start", sub.get("start_t", 0.0)))
            et = float(sub.get("end", sub.get("end_t", 0.0)))

            lines = self.wrap_or_split_text(text)
            badge_file = os.path.join(out_dir, f"{sid}.png")
            self.render_badge(lines, hl, badge_file)

            processed.append({
                "id": sid,
                "start": st,
                "end": et,
                "text": text,
                "lines": lines,
                "highlight": hl,
                "badge_path": badge_file
            })

        return processed
