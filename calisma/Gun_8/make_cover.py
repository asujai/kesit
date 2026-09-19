import os
from PIL import Image, ImageDraw, ImageFont

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
    work_dir = os.path.join('calisma', 'Gun_8')
    raw_cover_path = os.path.join(work_dir, 'candidate_cover_4.5.jpg')
    is_en = (lang == 'en')
    output_cover_path = os.path.join(work_dir, 'Gun_8_Shorts_Kapak_EN.jpg' if is_en else 'Gun_8_Shorts_Kapak.jpg')

    target_w, target_h = 1080, 1920
    img = Image.open(raw_cover_path).convert('RGBA')

    # Enhance contrast and color saturation slightly for high-CTR punch
    from PIL import ImageEnhance
    enh_contrast = ImageEnhance.Contrast(img)
    img = enh_contrast.enhance(1.15)
    enh_color = ImageEnhance.Color(img)
    img = enh_color.enhance(1.10)

    # Dark gradient overlay for top 44% text area and bottom 15%
    overlay = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    # Top dark vignette
    for y in range(860):
        alpha = int(230 * (1.0 - y / 860.0))
        d_over.line([(0, y), (target_w, y)], fill=(10, 12, 16, alpha))
        
    # Bottom subtle vignette
    for y in range(1600, target_h):
        alpha = int(180 * ((y - 1600) / 320.0))
        d_over.line([(0, y), (target_w, y)], fill=(10, 12, 16, alpha))

    bg = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(bg)

    font_bold = 'C:\\Windows\\Fonts\\segoeuib.ttf'
    if not os.path.exists(font_bold):
        font_bold = 'C:\\Windows\\Fonts\\arialbd.ttf'

    font_badge = ImageFont.truetype(font_bold, 36)

    if is_en:
        badge_text = 'DEEP WORK'
        line1 = 'QUIT SOCIAL MEDIA'
        line2 = 'BE RARE & VALUABLE!'
    else:
        badge_text = 'DERİN ÇALIŞMA'
        line1 = 'SOSYAL MEDYAYI BIRAKINCA'
        line2 = 'GERÇEKTEN DEĞERLİ OL!'

    max_text_width = 960
    font_hook = get_fitted_font(draw, line1, font_bold, 58, max_text_width)
    font_huge = get_fitted_font(draw, line2, font_bold, 66, max_text_width)

    # 1. Top pill badge (Y=270)
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox_b[2] - bbox_b[0] + 52
    bh = bbox_b[3] - bbox_b[1] + 22
    bx = (target_w - bw) // 2
    by = 270

    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(15, 15, 20, 240), outline=(245, 158, 11, 255), width=3)
    d_bx = bx + 26
    d_by = by + 10
    draw.text((d_bx, d_by), badge_text, font=font_badge, fill=(245, 158, 11, 255))

    # 2. Line 1 (Y=380)
    bbox_1 = draw.textbbox((0, 0), line1, font=font_hook)
    w1 = bbox_1[2] - bbox_1[0]
    x1 = (target_w - w1) // 2
    y1 = 380

    for ox, oy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2),(-2,2),(2,-2)]:
        draw.text((x1+ox, y1+oy), line1, font=font_hook, fill=(0, 0, 0, 255))
    draw.text((x1, y1), line1, font=font_hook, fill=(255, 255, 255, 255))

    # 3. Line 2 (Y=470)
    bbox_2 = draw.textbbox((0, 0), line2, font=font_huge)
    w2 = bbox_2[2] - bbox_2[0]
    x2 = (target_w - w2) // 2
    y2 = 470

    for ox, oy in [(-4,0),(4,0),(0,-4),(0,4),(-3,-3),(3,3),(-3,3),(3,-3)]:
        draw.text((x2+ox, y2+oy), line2, font=font_huge, fill=(0, 0, 0, 255))
    draw.text((x2, y2), line2, font=font_huge, fill=(250, 204, 21, 255))

    bg_rgb = bg.convert('RGB')
    bg_rgb.save(output_cover_path, 'JPEG', quality=95)
    print(f'Thumbnail generated: {output_cover_path} ({os.path.getsize(output_cover_path)} bytes)')

if __name__ == '__main__':
    create_shorts_thumbnail('tr')
    create_shorts_thumbnail('en')
