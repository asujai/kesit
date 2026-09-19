import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ARTIFACTS_DIR = r"C:\Users\abdul\.gemini\antigravity\brain\ce9d2171-2110-4ab9-a115-b75a97219a05"
SLOT_RAW = os.path.join(ARTIFACTS_DIR, "shorts_slot_social_icons_1789680124411.jpg")
YOUTUBE_DIR = r"c:\Users\abdul\kesiit\youtube\Gun_1"

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"

def prepare_covers():
    raw = Image.open(SLOT_RAW)
    # 1080 x 1920 Lanczos
    slot_1080 = raw.resize((1080, 1920), Image.Resampling.LANCZOS)
    
    # 1. Temiz Orijinal Kapak (Yazısız - Görsel metafor zaten her şeyi anlatıyor)
    clean_path = os.path.join(YOUTUBE_DIR, "Gun_1_Shorts_Kapak.jpg")
    slot_1080.save(clean_path, "JPEG", quality=95)
    print("Kaydedildi (Temiz):", clean_path)

    # 2. Vurucu Başlıklı Versiyon (Üstte 'KUMARHANE Mİ?' kancasıyla)
    scale = 2
    W = 1080 * scale
    H = 1920 * scale
    hi_img = slot_1080.resize((W, H), Image.Resampling.LANCZOS)
    
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    cx = W // 2
    top_y = int(90 * scale)

    # Küçük Rozet
    font_badge = ImageFont.truetype(FONT_BAHN, 18 * scale)
    badge_txt = "DİJİTAL TUZAK"
    bb = draw.textbbox((0, 0), badge_txt, font=font_badge)
    bw = (bb[2] - bb[0]) + int(24 * scale)
    bh = (bb[3] - bb[1]) + int(12 * scale)
    badge_x = cx - bw // 2
    draw.rounded_rectangle([badge_x, top_y, badge_x + bw, top_y + bh], radius=bh//2, fill=(15, 18, 24, 220), outline=(236, 72, 153, 220), width=2*scale)
    tb = draw.textbbox((0, 0), badge_txt, font=font_badge)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    draw.text((cx - tw // 2, top_y + (bh - th) // 2 - int(2*scale)), badge_txt, font=font_badge, fill=(244, 114, 182, 255))

    # Ana Kanca: 'KOLU ÇEKEN SİZSİNİZ!'
    font_main = ImageFont.truetype(FONT_BAHN, 54 * scale)
    main_txt = "KOLU ÇEKEN SİZSİNİZ!"
    mb = draw.textbbox((0, 0), main_txt, font=font_main)
    mw = mb[2] - mb[0]
    main_y = top_y + bh + int(16 * scale)
    draw.text((cx - mw // 2, main_y), main_txt, font=font_main, fill=(255, 255, 255, 255))

    # Gölge
    alpha = txt_layer.split()[3]
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(radius=6 * scale))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 220), mask=shadow_mask)

    comp = Image.alpha_composite(hi_img.convert("RGBA"), shadow)
    comp = Image.alpha_composite(comp, txt_layer).convert("RGB")
    
    titled_img = comp.resize((1080, 1920), Image.Resampling.LANCZOS)
    titled_path = os.path.join(YOUTUBE_DIR, "Gun_1_Shorts_Kapak_Metinli.jpg")
    titled_img.save(titled_path, "JPEG", quality=95)
    print("Kaydedildi (Metinli):", titled_path)

if __name__ == "__main__":
    prepare_covers()
