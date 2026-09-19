import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ARTIFACTS_DIR = r"C:\Users\abdul\.gemini\antigravity\brain\ce9d2171-2110-4ab9-a115-b75a97219a05"
IMG_MAN_RAW = os.path.join(ARTIFACTS_DIR, "shorts_thumb_casino_glow_1789679107131.jpg")
IMG_EYE_RAW = os.path.join(ARTIFACTS_DIR, "shorts_thumb_eye_reflection_1789679136916.jpg")

YOUTUBE_DIR = r"c:\Users\abdul\kesiit\youtube\Gun_1"
CALISMA_DIR = r"c:\Users\abdul\kesiit\calisma\Gun_1"

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

def create_thumbnails():
    # 1. Konsept 1 (Gece telefon & Kumarhane parıltısı)
    man_img = Image.open(IMG_MAN_RAW).resize((1080, 1920), Image.Resampling.LANCZOS)
    
    # Sade versiyon
    sade_path = os.path.join(CALISMA_DIR, "Gun_1_Kapak_Man_Sade.jpg")
    man_img.save(sade_path, "JPEG", quality=95)

    # Tipografili Versiyon (YouTube Shorts Üst Güvenli Alanında)
    # Shorts'ta alttaki %20 başlık için ayrılmıştır, bu yüzden vurucu yazı üst %12-%22 arasına konur.
    thumb_with_text = man_img.copy()
    
    # Metin katmanı (2x supersampling)
    scale = 2
    W = 1080 * scale
    H = 1920 * scale
    hi_img = thumb_with_text.resize((W, H), Image.Resampling.LANCZOS)
    
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    cx = W // 2
    top_y = int(220 * scale)  # Üstten ~220px güvenli alan

    # Küçük Kategori Rozeti (Minimalist Siyah Kapsül)
    font_badge = ImageFont.truetype(FONT_BAHN, 22 * scale)
    badge_txt = "SOSYAL MEDYA TUZAĞI"
    bb = draw.textbbox((0, 0), badge_txt, font=font_badge)
    bw = (bb[2] - bb[0]) + int(28 * scale)
    bh = (bb[3] - bb[1]) + int(14 * scale)
    badge_x = cx - bw // 2
    badge_y = top_y
    draw.rounded_rectangle([badge_x, badge_y, badge_x + bw, badge_y + bh], radius=bh//2, fill=(12, 14, 18, 230), outline=(52, 211, 153, 200), width=2*scale)
    tb = draw.textbbox((0, 0), badge_txt, font=font_badge)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    draw.text((cx - tw // 2, badge_y + (bh - th) // 2 - int(2*scale)), badge_txt, font=font_badge, fill=(52, 211, 153, 255))

    # Ana Vurucu Kanca: 'KUMARHANE Mİ?'
    font_main = ImageFont.truetype(FONT_BAHN, 72 * scale)
    main_txt = "KUMARHANE Mİ?"
    mb = draw.textbbox((0, 0), main_txt, font=font_main)
    mw = mb[2] - mb[0]
    mh = mb[3] - mb[1]
    main_y = badge_y + bh + int(24 * scale)

    # Ana metin arka gölgesi (okunabilirlik)
    draw.text((cx - mw // 2 + 3*scale, main_y + 4*scale), main_txt, font=font_main, fill=(0, 0, 0, 240))
    # Ana metin (Saf Beyaz & Sarı Vurgu)
    draw.text((cx - mw // 2, main_y), main_txt, font=font_main, fill=(255, 255, 255, 255))

    # Yumuşak gölge efekti
    alpha = txt_layer.split()[3]
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(radius=6 * scale))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 200), mask=shadow_mask)

    comp = Image.alpha_composite(hi_img.convert("RGBA"), shadow)
    comp = Image.alpha_composite(comp, txt_layer).convert("RGB")
    final_a = comp.resize((1080, 1920), Image.Resampling.LANCZOS)

    # 1. Ana Vitrin Dosyası: youtube/Gun_1/Gun_1_Shorts_Kapak.jpg
    out_main = os.path.join(YOUTUBE_DIR, "Gun_1_Shorts_Kapak.jpg")
    final_a.save(out_main, "JPEG", quality=95)
    print("Nihai Kapak kaydedildi:", out_main)

    # 2. Konsept 2 (Göz Yansıması - Alternatif)
    eye_img = Image.open(IMG_EYE_RAW).resize((1080, 1920), Image.Resampling.LANCZOS)
    out_b = os.path.join(CALISMA_DIR, "Gun_1_Kapak_Goz_Alternatif.jpg")
    eye_img.save(out_b, "JPEG", quality=95)
    print("Alternatif Göz Kapağı kaydedildi:", out_b)

if __name__ == "__main__":
    create_thumbnails()
