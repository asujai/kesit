import os
from PIL import Image, ImageDraw, ImageFont

def create_shorts_thumbnail(lang="tr"):
    work_dir = os.path.join("calisma", "Gun_5")
    raw_cover_path = os.path.join(work_dir, "cover_bg.jpg")
    is_en = (lang == "en")
    output_cover_path = os.path.join(work_dir, "Gun_5_Shorts_Kapak_EN.jpg" if is_en else "Gun_5_Shorts_Kapak.jpg")

    target_w, target_h = 1080, 1920
    img = Image.open(raw_cover_path).convert("RGBA")

    # Resize/crop to fill 1080x1920 exactly
    src_w, src_h = img.size
    ratio = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    bg = img_resized.crop((left, top, left + target_w, top + target_h))

    # Dark gradient overlay for the top 35% text area to ensure 100% legibility
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    for y in range(850):
        alpha = int(220 * (1.0 - y / 850.0))
        d_over.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))

    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)

    font_bold = "C:\\Windows\\Fonts\\segoeuib.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:\\Windows\\Fonts\\arialbd.ttf"

    font_badge = ImageFont.truetype(font_bold, 36)
    font_hook = ImageFont.truetype(font_bold, 68)
    font_huge = ImageFont.truetype(font_bold, 92)

    if is_en:
        badge_text = "SMARTPHONE & BRAIN"
        line1 = "THE DOPAMINE TRAP"
        line2 = "RUINING MOTIVATION!"
    else:
        badge_text = "AKILLI TELEFON & BEYİN"
        line1 = "DOPAMİN DENGESİNİ"
        line2 = "BOZUYORUZ!"

    # 1. Top pill badge (Y=300)
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 52
    bh = bbox_b[3] - bbox_b[1] + 22
    bx = (target_w - bw) // 2
    by = 300
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=(235, 40, 40, 240))
    draw.text((bx + 26, by + 11 - bbox_b[1]), badge_text, font=font_badge, fill=(255, 255, 255, 255))

    # 2. Main hook line 1 (Y=400)
    bbox1 = draw.textbbox((0, 0), line1, font=font_hook)
    w1 = bbox1[2] - bbox1[0]
    x1 = (target_w - w1) // 2
    y1 = 400
    # Bold shadow
    for off in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 4)]:
        draw.text((x1 + off[0], y1 + off[1]), line1, font=font_hook, fill=(0, 0, 0, 240))
    draw.text((x1, y1), line1, font=font_hook, fill=(255, 255, 255, 255))

    # 3. Main hook line 2 (Y=500)
    bbox2 = draw.textbbox((0, 0), line2, font=font_huge)
    w2 = bbox2[2] - bbox2[0]
    x2 = (target_w - w2) // 2
    y2 = 500
    for off in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 5)]:
        draw.text((x2 + off[0], y2 + off[1]), line2, font=font_huge, fill=(0, 0, 0, 240))
    draw.text((x2, y2), line2, font=font_huge, fill=(255, 215, 0, 255)) # Gold!

    # Convert and save
    bg = bg.convert("RGB")
    bg.save(output_cover_path, "JPEG", quality=95)
    print(f"Shorts Thumbnail created ({lang}): {output_cover_path}")

if __name__ == "__main__":
    create_shorts_thumbnail("tr")
    create_shorts_thumbnail("en")
