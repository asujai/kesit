import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

def get_fitted_font(draw, text, font_path, max_size, max_width):
    size = max_size
    while size > 24:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 24)

def create_shorts_thumbnail(lang='tr'):
    work_dir = os.path.join('calisma', 'Gun_10')
    raw_cover_path = os.path.join(work_dir, 'candidate_cover_hari_40.jpg')
    is_en = (lang == 'en')
    output_cover_path = os.path.join(work_dir, 'Gun_10_Shorts_Kapak_EN.jpg' if is_en else 'Gun_10_Shorts_Kapak.jpg')

    target_w, target_h = 1080, 1920
    img = Image.open(raw_cover_path).convert('RGBA')

    # Ensure exact 1080x1920 size
    if img.size != (target_w, target_h):
        ratio = max(target_w / img.width, target_h / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

    # Enhance contrast and saturation for high-CTR mobile feed visibility
    enh_contrast = ImageEnhance.Contrast(img)
    img = enh_contrast.enhance(1.22)
    enh_color = ImageEnhance.Color(img)
    img = enh_color.enhance(1.15)

    # Dark gradient overlay for upper 45% text area and bottom 15%
    overlay = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    # Top dark vignette for text contrast
    for y in range(860):
        alpha = int(235 * (1.0 - y / 860.0))
        d_over.line([(0, y), (target_w, y)], fill=(8, 10, 15, alpha))
        
    # Bottom subtle vignette
    for y in range(1600, target_h):
        alpha = int(180 * ((y - 1600) / 320.0))
        d_over.line([(0, y), (target_w, y)], fill=(8, 10, 15, alpha))

    bg = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(bg)

    font_bold = 'C:\\Windows\\Fonts\\segoeuib.ttf'
    if not os.path.exists(font_bold):
        font_bold = 'C:\\Windows\\Fonts\\arialbd.ttf'

    font_badge = ImageFont.truetype(font_bold, 36)

    if is_en:
        badge_text = 'PODCAST SPECIAL'
        line1 = 'THE INTERRUPT TRAP'
        line2 = 'DROPS YOUR IQ BY 10 POINTS!'
    else:
        badge_text = 'PODCAST ÖZEL'
        line1 = 'BİLDİRİMLERİN BÜYÜK ZARARI'
        line2 = 'IQ SEVİYENİZ 10 PUAN DÜŞÜYOR!'

    max_text_width = 960
    font_hook = get_fitted_font(draw, line1, font_bold, 58, max_text_width)
    font_huge = get_fitted_font(draw, line2, font_bold, 62, max_text_width)

    # 1. Top pill badge (Y=260)
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 52
    bh = bbox_b[3] - bbox_b[1] + 22
    bx = (target_w - bw) // 2
    by = 260

    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(15, 15, 20, 240), outline=(245, 158, 11, 255), width=3)
    d_bx = bx + 26
    d_by = by + 10
    draw.text((d_bx, d_by), badge_text, font=font_badge, fill=(245, 158, 11, 255))

    # 2. Line 1 (Y=370)
    bbox_1 = draw.textbbox((0, 0), line1, font=font_hook)
    w1 = bbox_1[2] - bbox_1[0]
    x1 = (target_w - w1) // 2
    y1 = 370

    for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2),(-2,2),(2,-2)]:
        draw.text((x1+ox, y1+oy), line1, font=font_hook, fill=(0, 0, 0, 255))
    draw.text((x1, y1), line1, font=font_hook, fill=(255, 255, 255, 255))

    # 3. Line 2 (Y=460) with Amber-Yellow highlight
    bbox_2 = draw.textbbox((0, 0), line2, font=font_huge)
    w2 = bbox_2[2] - bbox_2[0]
    x2 = (target_w - w2) // 2
    y2 = 460

    for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2),(-2,2),(2,-2)]:
        draw.text((x2+ox, y2+oy), line2, font=font_huge, fill=(0, 0, 0, 255))
    draw.text((x2, y2), line2, font=font_huge, fill=(251, 191, 36, 255))

    # Convert to RGB and save
    final_rgb = bg.convert('RGB')
    final_rgb.save(output_cover_path, quality=95)
    print(f"[Cover] Saved {lang.upper()} thumbnail to: {output_cover_path}")

if __name__ == '__main__':
    create_shorts_thumbnail('tr')
    create_shorts_thumbnail('en')
