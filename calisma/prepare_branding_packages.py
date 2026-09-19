import os
from PIL import Image, ImageDraw, ImageFont

ARTIFACTS_DIR = r"C:\Users\abdul\.gemini\antigravity\brain\ce9d2171-2110-4ab9-a115-b75a97219a05"
OUTPUT_DIR = r"c:\Users\abdul\kesiit\assets\branding"
os.makedirs(OUTPUT_DIR, exist_ok=True)

AVATAR_RAW = os.path.join(ARTIFACTS_DIR, "avatar_zen_balance_1789678213262.jpg")
BANNER_RAW = os.path.join(ARTIFACTS_DIR, "banner_zen_surface_1789678229101.jpg")

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_SEGOE = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

def process_avatar():
    # 1. Zen Taş & Filiz Profil Resmi
    img = Image.open(AVATAR_RAW)
    img_1080 = img.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    out_path = os.path.join(OUTPUT_DIR, "profil_resmi_zen.png")
    img_1080.save(out_path, "PNG", quality=95)
    print("Profil resmi kaydedildi:", out_path)
    return out_path

def process_banner():
    # YouTube Resmi Boyutu: 2048 x 1152
    base_banner = Image.open(BANNER_RAW)
    banner_2048 = base_banner.resize((2048, 1152), Image.Resampling.LANCZOS)

    # 1. Sade Fotoğraf Versiyonu (Yazısız)
    sade_path = os.path.join(OUTPUT_DIR, "banner_sade_fotograf.png")
    banner_2048.save(sade_path, "PNG", quality=95)
    print("Sade banner kaydedildi:", sade_path)

    # 2. Tipografili Versiyon (YouTube Masaüstü & Mobil Güvenli Alanında)
    # Güvenli Alan: Y: 407 - 745 px arası (Merkez = 576 px)
    banner_typed = banner_2048.copy()
    draw = ImageDraw.Draw(banner_typed)

    cx = 2048 // 2
    # Slate masa üstünde metnin tam kontrastlı durması için merkezde hafif koyu degrade / gölge bandı
    # Y = 460 - 680 aralığında
    overlay = Image.new("RGBA", (2048, 1152), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    # İnce koyu zemin rozeti (yazının taş dokusu üstünde kristal netliğinde okunması için)
    box_w = 920
    box_h = 220
    cy = 576  # Tam dikey merkez
    
    # Çok yumuşak koyu mat zemin rozeti
    ov_draw.rounded_rectangle(
        [cx - box_w//2, cy - box_h//2, cx + box_w//2, cy + box_h//2],
        radius=20,
        fill=(10, 14, 20, 200),
        outline=(50, 65, 85, 160),
        width=2
    )

    # Katmanı birleştir
    banner_typed = Image.alpha_composite(banner_typed.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(banner_typed)

    # 1. Üst Küçük Etiket
    font_top = ImageFont.truetype(FONT_BAHN, 16)
    top_txt = "D İ J İ T A L   F A R K I N D A L I K"
    tb = draw.textbbox((0, 0), top_txt, font=font_top)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, cy - 80), top_txt, font=font_top, fill=(52, 211, 153))

    # 2. Ana Başlık: DİJİTAL DENGE
    font_title = ImageFont.truetype(FONT_BAHN, 58)
    title_txt = "DİJİTAL DENGE"
    tb = draw.textbbox((0, 0), title_txt, font=font_title)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    draw.text((cx - tw // 2, cy - 54), title_txt, font=font_title, fill=(255, 255, 255))

    # 3. İnce Zümrüt Çizgi
    line_w = 120
    draw.rounded_rectangle([cx - line_w//2, cy + 18, cx + line_w//2, cy + 20], radius=1, fill=(16, 185, 129))

    # 4. Slogan
    font_sub = ImageFont.truetype(FONT_SEGOE, 22)
    sub_txt = "Ekranının Değil, Kendi Hayatının Kontrolünü Al"
    sb = draw.textbbox((0, 0), sub_txt, font=font_sub)
    sw = sb[2] - sb[0]
    draw.text((cx - sw // 2, cy + 32), sub_txt, font=font_sub, fill=(226, 232, 240))

    # 5. Alt Rozetler
    badges = ["DOOMSCROLLING", "DOPAMİN DETOKSU", "ODAKLANMA"]
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

    typed_path = os.path.join(OUTPUT_DIR, "banner_tipografili.png")
    banner_typed.save(typed_path, "PNG", quality=95)
    print("Tipografili banner kaydedildi:", typed_path)
    return typed_path

if __name__ == "__main__":
    process_avatar()
    process_banner()
