import os
from PIL import Image, ImageDraw, ImageFont

def create_shorts_thumbnail(lang="tr"):
    work_dir = os.path.join("calisma", "Gun_4")
    raw_cover_path = os.path.join(work_dir, "chk_broll_c05.jpg")
    is_en = (lang == "en")
    output_cover_path = os.path.join(work_dir, "Gun_4_Shorts_Kapak_EN.jpg" if is_en else "Gun_4_Shorts_Kapak.jpg")

    target_w, target_h = 1080, 1920
    img = Image.open(raw_cover_path).convert("RGBA")

    src_w, src_h = img.size
    ratio = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    bg = img_resized.crop((left, top, left + target_w, top + target_h))

    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    for y in range(880):
        alpha = int(210 * (1.0 - y / 880.0))
        d_over.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))

    for y in range(1450, target_h):
        alpha = int(180 * ((y - 1450) / (target_h - 1450)))
        d_over.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))

    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)

    font_bold = "C:\\Windows\\Fonts\\segoeuib.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:\\Windows\\Fonts\\arialbd.ttf"

    font_badge = ImageFont.truetype(font_bold, 36)
    font_hook = ImageFont.truetype(font_bold, 66)
    font_huge = ImageFont.truetype(font_bold, 86)
    font_sub = ImageFont.truetype(font_bold, 38)

    if is_en:
        badge_text = "CHEAP DOPAMINE TRAP"
        line1 = "WHY CAN'T YOU"
        line2 = "GET THINGS DONE?"
        speaker_text = "Clinical Psych. Beyhan Budak"
    else:
        badge_text = "UCUZ DOPAMİN TUZAĞI"
        line1 = "NEDEN HİÇBİR ŞEY"
        line2 = "YAPAMIYORSUN?"
        speaker_text = "Klinik Psk. Beyhan Budak"

    # 1. Top pill badge (Y=330)
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 52
    bh = bbox_b[3] - bbox_b[1] + 22
    bx = (target_w - bw) // 2
    by = 330
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=(235, 40, 40, 240))
    draw.text((bx + 26, by + 11 - bbox_b[1]), badge_text, font=font_badge, fill=(255, 255, 255, 255))

    # 2. Main hook lines (Y=430, 525)
    bbox1 = draw.textbbox((0, 0), line1, font=font_hook)
    w1 = bbox1[2] - bbox1[0]
    x1 = (target_w - w1) // 2
    y1 = 430
    draw.text((x1 + 4, y1 + 4), line1, font=font_hook, fill=(0, 0, 0, 230))
    draw.text((x1, y1), line1, font=font_hook, fill=(255, 255, 255, 255))

    bbox2 = draw.textbbox((0, 0), line2, font=font_huge)
    w2 = bbox2[2] - bbox2[0]
    x2 = (target_w - w2) // 2
    y2 = 525
    for off in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 6)]:
        draw.text((x2 + off[0], y2 + off[1]), line2, font=font_huge, fill=(0, 0, 0, 250))
    draw.text((x2, y2), line2, font=font_huge, fill=(255, 215, 0, 255))

    # 3. Speaker info pill (Y=1680)
    bbox_s = draw.textbbox((0, 0), speaker_text, font=font_sub)
    sw = bbox_s[2] - bbox_s[0] + 44
    sh = bbox_s[3] - bbox_s[1] + 22
    sx = (target_w - sw) // 2
    sy = 1680
    draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=20, fill=(12, 12, 16, 235), outline=(255, 255, 255, 50), width=2)
    draw.text((sx + 22, sy + 11 - bbox_s[1]), speaker_text, font=font_sub, fill=(245, 245, 245, 255))

    bg = bg.convert("RGB")
    bg.save(output_cover_path, "JPEG", quality=95)
    print(f"Shorts Thumbnail created ({lang}): {output_cover_path}")

if __name__ == "__main__":
    create_shorts_thumbnail("tr")
    create_shorts_thumbnail("en")
