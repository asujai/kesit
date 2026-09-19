import os
from PIL import Image, ImageDraw, ImageFont

def create_shorts_thumbnail(lang="tr"):
    work_dir = os.path.join("calisma", "Gun_2")
    raw_cover_path = os.path.join(work_dir, "cover_raw_12660640.jpg")
    is_en = (lang == "en")
    output_cover_path = os.path.join(work_dir, "Gun_2_Shorts_Kapak_EN.jpg" if is_en else "Gun_2_Shorts_Kapak.jpg")

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
    
    for y in range(800):
        alpha = int(180 * (1.0 - y / 800.0))
        d_over.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))

    for y in range(1500, target_h):
        alpha = int(160 * ((y - 1500) / (target_h - 1500)))
        d_over.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))

    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)

    font_bold = "C:\\Windows\\Fonts\\segoeuib.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:\\Windows\\Fonts\\arialbd.ttf"

    font_badge = ImageFont.truetype(font_bold, 36)
    font_hook = ImageFont.truetype(font_bold, 64)
    font_huge = ImageFont.truetype(font_bold, 92)

    if is_en:
        badge_text = "5,000 TOUCHES EVERY DAY"
        line1 = "YOU DON'T EVEN"
        line2 = "REALIZE IT!"
    else:
        badge_text = "GÜNDE 5.000 KEZ DOKUNUYORUZ"
        line1 = "FARKINDA BİLE"
        line2 = "DEĞİLSİNİZ!"

    # 1. Top pill badge (Y=340)
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 48
    bh = bbox_b[3] - bbox_b[1] + 20
    bx = (target_w - bw) // 2
    by = 340
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=(235, 40, 40, 235))
    draw.text((bx + 24, by + 10 - bbox_b[1]), badge_text, font=font_badge, fill=(255, 255, 255, 255))

    # 2. Main hook lines (Y=440, 535)
    bbox1 = draw.textbbox((0, 0), line1, font=font_hook)
    w1 = bbox1[2] - bbox1[0]
    x1 = (target_w - w1) // 2
    y1 = 440
    draw.text((x1 + 4, y1 + 4), line1, font=font_hook, fill=(0, 0, 0, 220))
    draw.text((x1, y1), line1, font=font_hook, fill=(255, 255, 255, 255))

    bbox2 = draw.textbbox((0, 0), line2, font=font_huge)
    w2 = bbox2[2] - bbox2[0]
    x2 = (target_w - w2) // 2
    y2 = 535
    for off in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 5)]:
        draw.text((x2 + off[0], y2 + off[1]), line2, font=font_huge, fill=(0, 0, 0, 240))
    draw.text((x2, y2), line2, font=font_huge, fill=(255, 215, 0, 255))

    bg = bg.convert("RGB")
    bg.save(output_cover_path, "JPEG", quality=95)
    print(f"Shorts Thumbnail created ({lang}): {output_cover_path}")

if __name__ == "__main__":
    create_shorts_thumbnail("tr")
    create_shorts_thumbnail("en")
