import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

out_dir = "Podcast_Video/Gun_1"
bg_source = "Podcast_Video/Gun_1/norm_cuts/s08_norm.mp4"

# Extract a high quality frame from s08 (face illuminated by phone screen) or s21 (brass balance scale)
frame_path = os.path.join(out_dir, "cover_raw_frame.jpg")
os.system(f'ffmpeg -y -ss 00:00:02 -i "{bg_source}" -vframes 1 -q:v 1 "{frame_path}"')

# Also extract scale frame from s21
scale_frame = os.path.join(out_dir, "scale_frame.jpg")
os.system(f'ffmpeg -y -ss 00:00:02 -i "Podcast_Video/Gun_1/norm_cuts/s21_norm.mp4" -vframes 1 -q:v 1 "{scale_frame}"')

# Load base image
base_img = Image.open(frame_path).convert("RGB")
if base_img.size != (1920, 1080):
    base_img = base_img.resize((1920, 1080), Image.Resampling.LANCZOS)

# Enhance contrast and add cinematic vignette
enhancer = ImageEnhance.Contrast(base_img)
base_img = enhancer.enhance(1.2)

# Load fonts
font_heavy = "C:/Windows/Fonts/impact.ttf"
font_bold = "C:/Windows/Fonts/arialbd.ttf"
font_title = ImageFont.truetype(font_heavy, 108) if os.path.exists(font_heavy) else ImageFont.load_default()
font_sub = ImageFont.truetype(font_bold, 48) if os.path.exists(font_bold) else ImageFont.load_default()
font_badge = ImageFont.truetype(font_bold, 30) if os.path.exists(font_bold) else ImageFont.load_default()

def create_thumbnail(title_line1, title_line2, sub_text, badge_text, out_file):
    canvas = base_img.copy()
    
    # Overlay dark gradient on left side for text readability
    gradient = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    
    # Left-to-right dark gradient
    for x in range(1200):
        alpha = int(230 * (1.0 - (x / 1200.0) ** 1.5))
        g_draw.line([(x, 0), (x, 1080)], fill=(8, 8, 12, alpha))
        
    # Top and bottom cinematic letterbox vignetting
    for y in range(200):
        alpha = int(180 * (1.0 - (y / 200.0)))
        g_draw.line([(0, y), (1920, y)], fill=(5, 5, 8, alpha))
        g_draw.line([(0, 1079 - y), (1920, 1079 - y)], fill=(5, 5, 8, alpha))
        
    canvas.paste(gradient, (0, 0), gradient)
    draw = ImageDraw.Draw(canvas)
    
    # Top badge pill
    badge_x, badge_y = 100, 120
    b_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    b_w, b_h = b_bbox[2] - b_bbox[0], b_bbox[3] - b_bbox[1]
    
    # Draw badge background (gold accent)
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + b_w + 36, badge_y + b_h + 20)],
        radius=8,
        fill=(250, 204, 21, 230),
        outline=(255, 255, 255, 120),
        width=2
    )
    draw.text((badge_x + 18, badge_y + 8), badge_text, font=font_badge, fill=(10, 10, 14))
    
    # Big Title Line 1 (Bright Yellow)
    title_y1 = 250
    draw.text((100, title_y1), title_line1, font=font_title, fill=(250, 204, 21), stroke_width=4, stroke_fill=(10, 10, 14))
    
    # Big Title Line 2 (Pure White)
    title_y2 = title_y1 + 125
    draw.text((100, title_y2), title_line2, font=font_title, fill=(255, 255, 255), stroke_width=4, stroke_fill=(10, 10, 14))
    
    # Subtitle with accent line
    sub_y = title_y2 + 150
    draw.line([(100, sub_y - 15), (320, sub_y - 15)], fill=(250, 204, 21), width=5)
    draw.text((100, sub_y), sub_text, font=font_sub, fill=(220, 225, 235), stroke_width=2, stroke_fill=(10, 10, 14))
    
    # Bottom callout pill (Duration / Speaker tag)
    tag_text = "DR. ANNA LEMBKE | STANFORD MEDICINE"
    draw.text((100, 940), tag_text, font=font_badge, fill=(180, 190, 205))
    
    canvas.save(out_file, quality=95)
    print(f"Thumbnail created: {out_file}")

# Turkish Thumbnail
create_thumbnail(
    title_line1="DOPAMİN TUZAĞI",
    title_line2="BEYNİNİZ NEDEN ÇÖKTÜ?",
    sub_text="Aşırı Bolluk Çağında Haz-Acı Terazisi",
    badge_text="BİLİMSEL PODCAST ESSAY",
    out_file="Podcast_Video/Gun_1/Gun_1_Kapak.jpg"
)

# English Thumbnail
create_thumbnail(
    title_line1="THE DOPAMINE TRAP",
    title_line2="HOW ABUNDANCE BROKE US",
    sub_text="The Pleasure-Pain Balance in Modern Life",
    badge_text="SCIENTIFIC VIDEO ESSAY",
    out_file="Podcast_Video/Gun_1/Gun_1_Kapak_EN.jpg"
)
