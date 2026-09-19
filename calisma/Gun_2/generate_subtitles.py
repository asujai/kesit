import os
import json
from PIL import Image, ImageDraw, ImageFont

# Subtitle definitions with precise timing matching Beyhan Budak ground truth
SUBTITLE_SEGMENTS = [
    {
        "id": "sub_01",
        "start": 0.10,
        "end": 1.85,
        "text": "Sabah kalktığın zaman",
        "highlight": "Sabah"
    },
    {
        "id": "sub_02",
        "start": 1.85,
        "end": 3.70,
        "text": "ilk olarak elin ona uzanıyor.",
        "highlight": "elin ona uzanıyor"
    },
    {
        "id": "sub_03",
        "start": 3.70,
        "end": 5.75,
        "text": "Yastığının her daim yanı başında.",
        "highlight": "yanı başında"
    },
    {
        "id": "sub_04",
        "start": 5.75,
        "end": 8.20,
        "text": "Otobüste giderken, araba sürerken...",
        "highlight": "araba sürerken"
    },
    {
        "id": "sub_05",
        "start": 8.20,
        "end": 10.70,
        "text": "Frene basıp kırmızı ışıkta durduğunda bile,",
        "highlight": "kırmızı ışıkta"
    },
    {
        "id": "sub_06",
        "start": 10.70,
        "end": 13.55,
        "text": "her zaman ilk olarak elin ona uzanıyor.",
        "highlight": "elin ona uzanıyor"
    },
    {
        "id": "sub_07",
        "start": 13.55,
        "end": 16.50,
        "text": "Bir arkadaşınla sohbet ediyorsun;",
        "highlight": "sohbet ediyorsun"
    },
    {
        "id": "sub_08",
        "start": 16.50,
        "end": 19.55,
        "text": "gözün onda, yeni bir şey var mı diye.",
        "highlight": "gözün onda"
    },
    {
        "id": "sub_09",
        "start": 19.55,
        "end": 22.30,
        "text": "Gece tuvalete kalkıyorsun, döndüğünde...",
        "highlight": "Gece"
    },
    {
        "id": "sub_10",
        "start": 22.30,
        "end": 25.45,
        "text": "Kafanı yastığa koyduğun an,",
        "highlight": "kafanı yastığa koyduğun"
    },
    {
        "id": "sub_11",
        "start": 25.45,
        "end": 28.50,
        "text": "bir bakıyorsun yine gözün onda!",
        "highlight": "gözün onda!"
    },
    {
        "id": "sub_12",
        "start": 28.50,
        "end": 30.85,
        "text": "Neden bahsediyorum sence?",
        "highlight": "Neden bahsediyorum?"
    },
    {
        "id": "sub_13",
        "start": 30.85,
        "end": 33.30,
        "text": "Tabii ki de akıllı telefonlardan!",
        "highlight": "akıllı telefonlardan!"
    },
    {
        "id": "sub_14",
        "start": 33.30,
        "end": 36.80,
        "text": "Bugün telefonla biraz yakın olan bir insan,",
        "highlight": "yakın olan bir insan"
    },
    {
        "id": "sub_15",
        "start": 36.80,
        "end": 40.40,
        "text": "günde 5 BİNDEN FAZLA kez dokunuyor!",
        "highlight": "5 BİNDEN FAZLA"
    },
    {
        "id": "sub_16",
        "start": 40.40,
        "end": 43.50,
        "text": "Bu öyle bir hale geliyor ki artık,",
        "highlight": "öyle bir hale geliyor"
    },
    {
        "id": "sub_17",
        "start": 43.50,
        "end": 46.80,
        "text": "hayatımızın en büyük bağımlılığı!",
        "highlight": "en büyük bağımlılığı!"
    }
]

def render_pill_subtitles():
    badge_dir = os.path.join('calisma', 'Gun_2', 'sub_badges')
    os.makedirs(badge_dir, exist_ok=True)

    # Fonts to try
    font_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf"
    ]
    font_path = None
    for p in font_paths:
        if os.path.exists(p):
            font_path = p
            break
    
    font_size = 44
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

    # Colors
    bg_color = (12, 12, 16, 238)      # Deep dark slate with 93% opacity
    text_color = (255, 255, 255, 255) # Pure white
    gold_color = (255, 215, 0, 255)   # Punchy gold for key hook words
    border_color = (255, 255, 255, 35) # Subtle frosted rim

    padding_x = 34
    padding_y = 16
    radius = 24
    screen_w = 1080
    screen_h = 1920
    target_y = 1440  # Ergonomic reading zone for 9:16 Shorts/Reels

    for sub in SUBTITLE_SEGMENTS:
        text = sub['text']
        highlight = sub.get('highlight', '')
        
        # Transparent canvas 1080x1920
        img = Image.new('RGBA', (screen_w, screen_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Measure text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pill_w = text_w + padding_x * 2
        pill_h = text_h + padding_y * 2
        pill_x1 = (screen_w - pill_w) // 2
        pill_y1 = target_y
        pill_x2 = pill_x1 + pill_w
        pill_y2 = pill_y1 + pill_h

        # Draw rounded pill background
        draw.rounded_rectangle(
            [pill_x1, pill_y1, pill_x2, pill_y2],
            radius=radius,
            fill=bg_color,
            outline=border_color,
            width=2
        )

        # Draw text centered inside pill
        tx = pill_x1 + padding_x
        ty = pill_y1 + padding_y - bbox[1]

        # Check if highlight is in text
        if highlight and highlight in text:
            parts = text.split(highlight, 1)
            # part1
            draw.text((tx, ty), parts[0], font=font, fill=text_color)
            w_part1 = draw.textbbox((0, 0), parts[0], font=font)[2] - draw.textbbox((0, 0), parts[0], font=font)[0] if parts[0] else 0
            # highlight in gold
            draw.text((tx + w_part1, ty), highlight, font=font, fill=gold_color)
            w_hl = draw.textbbox((0, 0), highlight, font=font)[2] - draw.textbbox((0, 0), highlight, font=font)[0]
            # part2
            draw.text((tx + w_part1 + w_hl, ty), parts[1], font=font, fill=text_color)
        else:
            draw.text((tx, ty), text, font=font, fill=text_color)

        out_path = os.path.join(badge_dir, f"{sub['id']}.png")
        img.save(out_path, "PNG")

    # Save timing manifest JSON
    json_path = os.path.join('calisma', 'Gun_2', 'subtitles.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(SUBTITLE_SEGMENTS, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(SUBTITLE_SEGMENTS)} subtitle overlays in {badge_dir}")
    print(f"Saved manifest to {json_path}")

if __name__ == '__main__':
    render_pill_subtitles()
