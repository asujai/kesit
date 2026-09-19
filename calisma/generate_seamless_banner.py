import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ARTIFACTS_DIR = r"C:\Users\abdul\kesiit\assets\branding"
BANNER_RAW = os.path.join(r"C:\Users\abdul\.gemini\antigravity\brain\ce9d2171-2110-4ab9-a115-b75a97219a05", "banner_zen_surface_1789678229101.jpg")
OUTPUT_DIR = r"c:\Users\abdul\kesiit\assets\branding"

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_SEGOE = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

def create_seamless_banner():
    # 2048 x 1152 YouTube Banner
    base_banner = Image.open(BANNER_RAW).resize((2048, 1152), Image.Resampling.LANCZOS)
    
    # 2x süper örnekleme ile yazıları çizelim
    scale = 2
    W = 2048 * scale
    H = 1152 * scale
    banner_hi = base_banner.resize((W, H), Image.Resampling.LANCZOS)
    
    # Yazı katmanı
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    cx = W // 2
    # YouTube Safe Zone dikey merkezi: Y = 576 * scale = 1152
    # Slate masanın temiz negatif alanı tam bu yükseklikte
    cy = int(585 * scale)

    # 1. Üst Kategori Vurgusu (İnce, zarif, aralıklı harfler)
    font_top = ImageFont.truetype(FONT_BAHN, 16 * scale)
    top_txt = "D İ J İ T A L   F A R K I N D A L I K"
    tb = draw.textbbox((0, 0), top_txt, font=font_top)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, cy - int(68 * scale)), top_txt, font=font_top, fill=(52, 211, 153, 240))

    # 2. Ana Başlık: DİJİTAL DENGE (Geniş, otoriter, temiz)
    font_title = ImageFont.truetype(FONT_BAHN, 64 * scale)
    title_txt = "DİJİTAL DENGE"
    tb = draw.textbbox((0, 0), title_txt, font=font_title)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    title_y = cy - int(38 * scale)
    draw.text((cx - tw // 2, title_y), title_txt, font=font_title, fill=(255, 255, 255, 255))

    # 3. İnce Denge Ayracı
    line_w = int(140 * scale)
    line_y = title_y + th + int(16 * scale)
    draw.rounded_rectangle([cx - line_w//2, line_y, cx + line_w//2, line_y + 2*scale], radius=scale, fill=(16, 185, 129, 230))

    # 4. Slogan
    font_sub = ImageFont.truetype(FONT_SEGOE, 23 * scale)
    sub_txt = "Ekranının Değil, Kendi Hayatının Kontrolünü Al"
    sb = draw.textbbox((0, 0), sub_txt, font=font_sub)
    sw = sb[2] - sb[0]
    draw.text((cx - sw // 2, line_y + int(14 * scale)), sub_txt, font=font_sub, fill=(215, 225, 235, 240))

    # 5. Alt Başlıklar / Anahtar Kelimeler (Zarif nokta ayraçlı)
    font_tags = ImageFont.truetype(FONT_BAHN, 13 * scale)
    tag_txt = "ODAKLANMA  •  DİJİTAL DETOKS  •  BİLİNÇLİ YAŞAM"
    tb = draw.textbbox((0, 0), tag_txt, font=font_tags)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, line_y + int(52 * scale)), tag_txt, font=font_tags, fill=(148, 163, 184, 210))

    # Yazıların arkasına çok yumuşak bir gölge katmanı (okunabilirlik için)
    # Text layer'ın alfa kanalından gölge üretip blur yapıyoruz
    alpha = text_layer.split()[3]
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(radius=8 * scale))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Siyah gölgeyi maske ile basalım
    shadow.paste((5, 8, 12, 230), mask=shadow_mask)

    # Masanın merkezine çok hafif, geniş, algılanamaz bir koyuluk (radial ambient)
    ambient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    amb_draw = ImageDraw.Draw(ambient)
    amb_rx = int(600 * scale)
    amb_ry = int(140 * scale)
    for i in range(25, 0, -2):
        rx = int(amb_rx * (i / 25))
        ry = int(amb_ry * (i / 25))
        a = int(10 * (1 - i / 25))
        amb_draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(0, 0, 0, a))

    # Katmanları birleştir
    comp = Image.alpha_composite(banner_hi.convert("RGBA"), ambient)
    comp = Image.alpha_composite(comp, shadow)
    comp = Image.alpha_composite(comp, text_layer).convert("RGB")

    # 1x'e küçült (2048 x 1152)
    final_banner = comp.resize((2048, 1152), Image.Resampling.LANCZOS)
    out_path = os.path.join(OUTPUT_DIR, "banner_resmi_sinematik.png")
    final_banner.save(out_path, "PNG", quality=95)
    print("Sinematik banner kaydedildi:", out_path)
    return out_path

if __name__ == "__main__":
    create_seamless_banner()
