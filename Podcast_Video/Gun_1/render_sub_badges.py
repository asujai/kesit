import os
import json
from PIL import Image, ImageDraw, ImageFont

with open("Podcast_Video/Gun_1/subtitles_master.json", "r", encoding="utf-8") as f:
    subs = json.load(f)

tr_dir = "Podcast_Video/Gun_1/sub_badges_tr"
en_dir = "Podcast_Video/Gun_1/sub_badges_en"
os.makedirs(tr_dir, exist_ok=True)
os.makedirs(en_dir, exist_ok=True)

# Try loading high quality fonts
font_candidates = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "DejaVuSans-Bold.ttf"
]
font_path = None
for fc in font_candidates:
    if os.path.exists(fc):
        font_path = fc
        break

font_size = 36
font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

# Keywords to highlight in yellow (#FACC15)
HIGHLIGHT_WORDS = {
    "pain", "pleasure", "balance", "homeostasis", "wired", "addicted", "synthetic",
    "dopamine", "mismatched", "scarcity", "overabundance", "compensates", "neuroadaptation",
    "gremlins", "camped", "addicted brain", "joy set point", "feel normal", "withdrawal",
    "anxiety", "irritability", "insomnia", "depression", "craving",
    "acı", "haz", "denge", "homeostaz", "bağımlı", "sentetik", "kıtlık", "aşırı bolluk",
    "nöroadaptasyon", "gremlinler", "normal", "yoksunluk", "anksiyete", "huzursuzluk",
    "uykusuzluk", "depresyon", "aşerme"
}

def split_text_to_lines(text, max_chars=55):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + 1 <= max_chars:
            curr.append(w)
            curr_len += len(w) + 1
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

def render_badge(text, out_path, is_en=True):
    lines = split_text_to_lines(text, max_chars=60)
    
    # Calculate dimensions
    line_spacing = 10
    pad_x = 32
    pad_y = 18
    
    line_sizes = []
    dummy_img = Image.new("RGBA", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy_img)
    for l in lines:
        bbox = draw_dummy.textbbox((0, 0), l, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_sizes.append((w, h))
        
    max_w = max(w for w, h in line_sizes)
    total_h = sum(h for w, h in line_sizes) + (len(lines) - 1) * line_spacing
    
    badge_w = max_w + pad_x * 2
    badge_h = total_h + pad_y * 2
    
    # Create RGBA image
    img = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background: #0A0A0E at 90% opacity (alpha=230)
    # with a sleek border #FACC15 at 40% opacity (alpha=100)
    draw.rounded_rectangle(
        [(0, 0), (badge_w - 1, badge_h - 1)],
        radius=14,
        fill=(10, 10, 14, 230),
        outline=(250, 204, 21, 90),
        width=2
    )
    
    # Render lines with word highlights
    y_offset = pad_y
    for line_idx, line in enumerate(lines):
        words = line.split()
        # Measure words to center line
        bbox_l = draw.textbbox((0, 0), line, font=font)
        line_w = bbox_l[2] - bbox_l[0]
        x_offset = (badge_w - line_w) // 2
        
        for w in words:
            clean_w = w.strip(".,;:?!—\"'()").lower()
            color = (250, 204, 21, 255) if clean_w in HIGHLIGHT_WORDS else (255, 255, 255, 255)
            
            draw.text((x_offset, y_offset), w + " ", font=font, fill=color)
            w_bbox = draw.textbbox((0, 0), w + " ", font=font)
            x_offset += (w_bbox[2] - w_bbox[0])
            
        y_offset += line_sizes[line_idx][1] + line_spacing

    img.save(out_path, "PNG")

print("Rendering 16:9 cinematic subtitle badges...")
for item in subs:
    idx = item["id"]
    tr_out = os.path.join(tr_dir, f"sub_{idx:02d}.png")
    en_out = os.path.join(en_dir, f"sub_{idx:02d}.png")
    
    render_badge(item["tr"], tr_out, is_en=False)
    render_badge(item["en"], en_out, is_en=True)

print(f"Rendered {len(subs)} badges for both TR and EN!")
