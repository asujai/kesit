import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUTPUT_DIR = r"c:\Users\abdul\kesiit\ingilizce\branding"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BANNER_RAW = r"C:\Users\abdul\.gemini\antigravity\brain\ce9d2171-2110-4ab9-a115-b75a97219a05\banner_zen_surface_1789678229101.jpg"
AVATAR_RAW = r"C:\Users\abdul\.gemini\antigravity\brain\ce9d2171-2110-4ab9-a115-b75a97219a05\avatar_zen_balance_1789678213262.jpg"

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_SEGOE = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

def create_avatars():
    # 1. Zen Taş & Filiz (1080x1080)
    img = Image.open(AVATAR_RAW)
    img_1080 = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    zen_path = os.path.join(OUTPUT_DIR, "profil_resmi_zen.png")
    img_1080.save(zen_path, "PNG", quality=95)
    print("Kaydedildi:", zen_path)

    # 2. Minimalist Geometrik Denge İkonu (1080x1080)
    size = 1080
    scale = 2
    S = size * scale
    img_geo = Image.new("RGB", (S, S), (13, 16, 23))
    draw = ImageDraw.Draw(img_geo)
    center = S // 2

    # Kılavuz halkalar
    guide_color = (22, 28, 40)
    for gr in [int(S * 0.44), int(S * 0.38), int(S * 0.26)]:
        draw.ellipse([center - gr, center - gr, center + gr, center + gr], outline=guide_color, width=2*scale)

    outer_r = int(S * 0.32)
    line_w = int(S * 0.036)
    bbox_outer = [center - outer_r, center - outer_r, center + outer_r, center + outer_r]

    # Sol yay (Gümüş / Beyaz)
    draw.arc(bbox_outer, start=110, end=250, fill=(241, 245, 249), width=line_w)
    # Sağ yay (Zümrüt Yeşili)
    draw.arc(bbox_outer, start=290, end=430, fill=(16, 185, 129), width=line_w)

    def draw_cap(angle_deg, r_dist, fill_color):
        rad = math.radians(angle_deg)
        cx = center + r_dist * math.cos(rad)
        cy = center + r_dist * math.sin(rad)
        cr = line_w // 2
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=fill_color)

    draw_cap(110, outer_r, (241, 245, 249))
    draw_cap(250, outer_r, (241, 245, 249))
    draw_cap(290, outer_r, (16, 185, 129))
    draw_cap(430, outer_r, (16, 185, 129))

    beam_w = int(S * 0.44)
    beam_h = int(S * 0.024)
    draw.rounded_rectangle(
        [center - beam_w//2, center - beam_h//2, center + beam_w//2, center + beam_h//2],
        radius=beam_h//2,
        fill=(255, 255, 255)
    )

    node_r = int(S * 0.056)
    draw.ellipse([center - beam_w//2 - node_r, center - node_r, center - beam_w//2 + node_r, center + node_r], fill=(248, 250, 252))
    draw.ellipse([center + beam_w//2 - node_r, center - node_r, center + beam_w//2 + node_r, center + node_r], fill=(16, 185, 129))

    pivot_outer = int(S * 0.046)
    draw.ellipse([center - pivot_outer, center - pivot_outer, center + pivot_outer, center + pivot_outer], fill=(13, 16, 23))
    pivot_inner = int(S * 0.026)
    draw.ellipse([center - pivot_inner, center - pivot_inner, center + pivot_inner, center + pivot_inner], fill=(255, 255, 255))

    final_geo = img_geo.resize((size, size), Image.Resampling.LANCZOS)
    geo_path = os.path.join(OUTPUT_DIR, "profil_resmi_geometrik.png")
    final_geo.save(geo_path, "PNG")
    print("Kaydedildi:", geo_path)

def create_banner_cinematic():
    base_banner = Image.open(BANNER_RAW).resize((2048, 1152), Image.Resampling.LANCZOS)
    
    scale = 2
    W = 2048 * scale
    H = 1152 * scale
    banner_hi = base_banner.resize((W, H), Image.Resampling.LANCZOS)
    
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    cx = W // 2
    cy = int(585 * scale)

    # 1. Top Category (Digital Awareness)
    font_top = ImageFont.truetype(FONT_BAHN, 16 * scale)
    top_txt = "D I G I T A L   A W A R E N E S S"
    tb = draw.textbbox((0, 0), top_txt, font=font_top)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, cy - int(68 * scale)), top_txt, font=font_top, fill=(52, 211, 153, 240))

    # 2. Main Title: DIGITAL BALANCE
    font_title = ImageFont.truetype(FONT_BAHN, 64 * scale)
    title_txt = "DIGITAL BALANCE"
    tb = draw.textbbox((0, 0), title_txt, font=font_title)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    title_y = cy - int(38 * scale)
    draw.text((cx - tw // 2, title_y), title_txt, font=font_title, fill=(255, 255, 255, 255))

    # 3. Emerald Divider Line
    line_w = int(140 * scale)
    line_y = title_y + th + int(16 * scale)
    draw.rounded_rectangle([cx - line_w//2, line_y, cx + line_w//2, line_y + 2*scale], radius=scale, fill=(16, 185, 129, 230))

    # 4. Slogan
    font_sub = ImageFont.truetype(FONT_SEGOE, 23 * scale)
    sub_txt = "Take Control of Your Life, Not Your Screen"
    sb = draw.textbbox((0, 0), sub_txt, font=font_sub)
    sw = sb[2] - sb[0]
    draw.text((cx - sw // 2, line_y + int(14 * scale)), sub_txt, font=font_sub, fill=(215, 225, 235, 240))

    # 5. Bottom Keywords
    font_tags = ImageFont.truetype(FONT_BAHN, 13 * scale)
    tag_txt = "DEEP FOCUS  •  DOPAMINE DETOX  •  MINDFUL LIVING"
    tb = draw.textbbox((0, 0), tag_txt, font=font_tags)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, line_y + int(52 * scale)), tag_txt, font=font_tags, fill=(148, 163, 184, 210))

    alpha = text_layer.split()[3]
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(radius=8 * scale))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((5, 8, 12, 230), mask=shadow_mask)

    ambient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    amb_draw = ImageDraw.Draw(ambient)
    amb_rx = int(600 * scale)
    amb_ry = int(140 * scale)
    for i in range(25, 0, -2):
        rx = int(amb_rx * (i / 25))
        ry = int(amb_ry * (i / 25))
        a = int(10 * (1 - i / 25))
        amb_draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(0, 0, 0, a))

    comp = Image.alpha_composite(banner_hi.convert("RGBA"), ambient)
    comp = Image.alpha_composite(comp, shadow)
    comp = Image.alpha_composite(comp, text_layer).convert("RGB")

    final_banner = comp.resize((2048, 1152), Image.Resampling.LANCZOS)
    out_path = os.path.join(OUTPUT_DIR, "banner_sinematik_en.png")
    final_banner.save(out_path, "PNG", quality=95)
    print("Kaydedildi:", out_path)

def create_banner_badge():
    base_banner = Image.open(BANNER_RAW).resize((2048, 1152), Image.Resampling.LANCZOS)
    banner_typed = base_banner.copy()
    cx = 2048 // 2
    cy = 576

    overlay = Image.new("RGBA", (2048, 1152), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    box_w = 960
    box_h = 220
    ov_draw.rounded_rectangle(
        [cx - box_w//2, cy - box_h//2, cx + box_w//2, cy + box_h//2],
        radius=20,
        fill=(10, 14, 20, 200),
        outline=(50, 65, 85, 160),
        width=2
    )

    banner_typed = Image.alpha_composite(banner_typed.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(banner_typed)

    # 1. Top Small Tag
    font_top = ImageFont.truetype(FONT_BAHN, 16)
    top_txt = "D I G I T A L   A W A R E N E S S"
    tb = draw.textbbox((0, 0), top_txt, font=font_top)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, cy - 80), top_txt, font=font_top, fill=(52, 211, 153))

    # 2. Main Title
    font_title = ImageFont.truetype(FONT_BAHN, 58)
    title_txt = "DIGITAL BALANCE"
    tb = draw.textbbox((0, 0), title_txt, font=font_title)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, cy - 54), title_txt, font=font_title, fill=(255, 255, 255))

    # 3. Line
    line_w = 120
    draw.rounded_rectangle([cx - line_w//2, cy + 18, cx + line_w//2, cy + 20], radius=1, fill=(16, 185, 129))

    # 4. Slogan
    font_sub = ImageFont.truetype(FONT_SEGOE, 22)
    sub_txt = "Take Control of Your Life, Not Your Screen"
    sb = draw.textbbox((0, 0), sub_txt, font=font_sub)
    sw = sb[2] - sb[0]
    draw.text((cx - sw // 2, cy + 32), sub_txt, font=font_sub, fill=(226, 232, 240))

    # 5. Badges
    badges = ["DOOMSCROLLING", "DOPAMINE DETOX", "DEEP FOCUS"]
    font_badge = ImageFont.truetype(FONT_BAHN, 11)
    
    total_w = 0
    b_list = []
    pad_x = 14
    pad_y = 5
    gap = 10
    
    for b in badges:
        bb = draw.textbbox((0, 0), b, font=font_badge)
        bw = (bb[2] - bb[0]) + pad_x * 2
        bh = (bb[3] - bb[1]) + pad_y * 2
        b_list.append((b, bw, bh))
        total_w += bw
    total_w += gap * (len(badges) - 1)

    cur_x = cx - total_w // 2
    by = cy + 70
    for b, bw, bh in b_list:
        draw.rounded_rectangle([cur_x, by, cur_x + bw, by + bh], radius=bh//2, fill=(20, 26, 36), outline=(60, 75, 95), width=1)
        bb = draw.textbbox((0, 0), b, font=font_badge)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        draw.text((cur_x + (bw - tw)//2, by + (bh - th)//2 - 1), b, font=font_badge, fill=(148, 163, 184))
        cur_x += bw + gap

    out_path = os.path.join(OUTPUT_DIR, "banner_tipografili_en.png")
    banner_typed.save(out_path, "PNG", quality=95)
    print("Kaydedildi:", out_path)

def create_banner_clean():
    base_banner = Image.open(BANNER_RAW).resize((2048, 1152), Image.Resampling.LANCZOS)
    sade_path = os.path.join(OUTPUT_DIR, "banner_sade_fotograf.png")
    base_banner.save(sade_path, "PNG", quality=95)
    print("Kaydedildi:", sade_path)

if __name__ == "__main__":
    create_avatars()
    create_banner_cinematic()
    create_banner_badge()
    create_banner_clean()
    print("Tüm İngilizce marka varlıkları başarıyla üretildi!")
