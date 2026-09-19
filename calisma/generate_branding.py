import math
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"c:\Users\abdul\kesiit\assets\branding"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_SEGOE_REG = r"C:\Windows\Fonts\segoeui.ttf"

def create_avatar_v1(size=1080):
    """
    Tasarım 1: 'Minimalist Denge & Odak İkonu'
    Koyu antrasit/obsidyen zemin üzerinde kusursuz geometrik denge halkası ve odak noktası.
    """
    scale = 2
    S = size * scale
    # RGB olarak çalışıyoruz - saydamlık hatası olmasın
    img = Image.new("RGB", (S, S), (13, 16, 23))
    draw = ImageDraw.Draw(img)

    center = S // 2

    # İnce dairesel arka plan dokusu (halka kılavuzlar)
    guide_color = (22, 28, 40)
    for gr in [int(S * 0.44), int(S * 0.38), int(S * 0.26)]:
        draw.ellipse([center - gr, center - gr, center + gr, center + gr], outline=guide_color, width=2*scale)

    # 1. Dış Denge Arkı (Döngüyü kıran iki simetrik kavis)
    outer_r = int(S * 0.32)
    line_w = int(S * 0.036)
    bbox_outer = [center - outer_r, center - outer_r, center + outer_r, center + outer_r]

    # Sol yay (Gümüş / Beyaz: Gerçek Yaşam)
    draw.arc(bbox_outer, start=110, end=250, fill=(241, 245, 249), width=line_w)
    # Sağ yay (Canlı Zümrüt Yeşili: Dijital Denge / Reset)
    draw.arc(bbox_outer, start=290, end=430, fill=(16, 185, 129), width=line_w)

    # Yuvarlak uçlar
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

    # 2. Yatay Denge Ekseni (Minimalist terazi çubuğu)
    beam_w = int(S * 0.44)
    beam_h = int(S * 0.024)
    draw.rounded_rectangle(
        [center - beam_w//2, center - beam_h//2, center + beam_w//2, center + beam_h//2],
        radius=beam_h//2,
        fill=(255, 255, 255)
    )

    # 3. İki uçtaki denge küreleri
    node_r = int(S * 0.056)
    # Sol küre (Beyaz)
    draw.ellipse([center - beam_w//2 - node_r, center - node_r, center - beam_w//2 + node_r, center + node_r], fill=(248, 250, 252))
    # Sağ küre (Zümrüt Yeşili)
    draw.ellipse([center + beam_w//2 - node_r, center - node_r, center + beam_w//2 + node_r, center + node_r], fill=(16, 185, 129))

    # 4. Merkez Odak & Mola Noktası
    pivot_outer = int(S * 0.046)
    draw.ellipse([center - pivot_outer, center - pivot_outer, center + pivot_outer, center + pivot_outer], fill=(13, 16, 23))
    pivot_inner = int(S * 0.026)
    draw.ellipse([center - pivot_inner, center - pivot_inner, center + pivot_inner, center + pivot_inner], fill=(255, 255, 255))

    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    path = os.path.join(OUTPUT_DIR, "profil_resmi_v1_denge.png")
    final_img.save(path, "PNG")
    print(f"Kaydedildi: {path}")
    return path

def create_banner_v1(width=2048, height=1152):
    """
    YouTube Banner: 2048 x 1152 px (16:9)
    Güvenli Alan: Merkezdeki 1235 x 338 px
    """
    scale = 2
    W = width * scale
    H = height * scale
    img = Image.new("RGB", (W, H), (11, 14, 20))
    draw = ImageDraw.Draw(img)

    center_x = W // 2
    center_y = H // 2

    # İnce estetik kılavuz ızgara çizgileri (çok koyu, sadece derinlik verir)
    grid_color = (18, 23, 33)
    step = int(60 * scale)
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1*scale)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1*scale)

    # Merkezde içeriği aydınlatan koyu mat zemin kutusu
    box_w = int(1100 * scale)
    box_h = int(300 * scale)
    draw.rounded_rectangle(
        [center_x - box_w//2, center_y - box_h//2, center_x + box_w//2, center_y + box_h//2],
        radius=24*scale,
        fill=(15, 19, 28),
        outline=(30, 41, 59),
        width=2*scale
    )

    # 1. Küçük Üst Kategori Vurgusu
    font_top = ImageFont.truetype(FONT_BOLD, 13 * scale)
    top_text = "D İ J İ T A L   F A R K I N D A L I K   &   D E T O K S"
    tb_box = draw.textbbox((0, 0), top_text, font=font_top)
    tb_w = tb_box[2] - tb_box[0]
    top_y = center_y - int(85 * scale)
    draw.text((center_x - tb_w // 2, top_y), top_text, font=font_top, fill=(16, 185, 129))

    # 2. Ana Kanal Başlığı: 'DİJİTAL DENGE'
    font_title = ImageFont.truetype(FONT_BOLD, 50 * scale)
    title_text = "DİJİTAL DENGE"
    t_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    title_y = top_y + int(24 * scale)
    draw.text((center_x - t_w // 2, title_y), title_text, font=font_title, fill=(255, 255, 255))

    # 3. İnce Denge İkonu (Başlığın hemen altında simetrik çizgi)
    bar_w = int(180 * scale)
    bar_y = title_y + t_h + int(18 * scale)
    draw.line([(center_x - bar_w//2, bar_y), (center_x + bar_w//2, bar_y)], fill=(51, 65, 85), width=2*scale)
    # Ortadaki zümrüt nokta
    draw.ellipse([center_x - 4*scale, bar_y - 4*scale, center_x + 4*scale, bar_y + 4*scale], fill=(16, 185, 129))

    # 4. Slogan
    font_sub = ImageFont.truetype(FONT_SEGOE_REG, 20 * scale)
    sub_text = "Ekranının Değil, Kendi Hayatının Kontrolünü Al"
    s_bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    s_w = s_bbox[2] - s_bbox[0]
    sub_y = bar_y + int(16 * scale)
    draw.text((center_x - s_w // 2, sub_y), sub_text, font=font_sub, fill=(203, 213, 225))

    # 5. Alt Kapsül Etiketler
    badges = ["DOOMSCROLLING", "DOPAMİN DETOKSU", "ODAKLANMA"]
    font_b = ImageFont.truetype(FONT_BOLD, 10 * scale)
    b_y = sub_y + int(36 * scale)
    pad_x = 14 * scale
    pad_y = 5 * scale
    gap = 12 * scale

    # Rozetlerin toplam genişliği
    total_bw = 0
    b_items = []
    for b in badges:
        bb = draw.textbbox((0, 0), b, font=font_b)
        bw = (bb[2] - bb[0]) + pad_x * 2
        bh = (bb[3] - bb[1]) + pad_y * 2
        b_items.append((b, bw, bh))
        total_bw += bw
    total_bw += gap * (len(badges) - 1)

    cur_x = center_x - total_bw // 2
    for b, bw, bh in b_items:
        draw.rounded_rectangle([cur_x, b_y, cur_x + bw, b_y + bh], radius=bh//2, fill=(24, 32, 47), outline=(51, 65, 85), width=1*scale)
        tb = draw.textbbox((0, 0), b, font=font_b)
        tw = tb[2] - tb[0]
        th = tb[3] - tb[1]
        draw.text((cur_x + (bw - tw)//2, b_y + (bh - th)//2 - int(1*scale)), b, font=font_b, fill=(148, 163, 184))
        cur_x += bw + gap

    final_img = img.resize((width, height), Image.Resampling.LANCZOS)
    path = os.path.join(OUTPUT_DIR, "banner_resmi_v1_studio.png")
    final_img.save(path, "PNG")
    print(f"Kaydedildi: {path}")
    return path

if __name__ == "__main__":
    create_avatar_v1()
    create_banner_v1()
