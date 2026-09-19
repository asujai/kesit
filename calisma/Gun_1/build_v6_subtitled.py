# -*- coding: utf-8 -*-
import os
import json
import subprocess
import time
from PIL import Image, ImageDraw, ImageFont

def generate_badges(json_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(json_path, 'r', encoding='utf-8') as f:
        subtitles = json.load(f)

    font_path = 'C:/Windows/Fonts/segoeuib.ttf'
    font = ImageFont.truetype(font_path, 44)
    pad_x = 32
    pad_y = 18
    center_x = 540
    center_y = 1450
    line_height = 64

    badge_records = []
    for idx, (start, end, text) in enumerate(subtitles):
        im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        lines = text.split('\n')
        total_h = (len(lines) - 1) * line_height

        boxes = []
        for i, line in enumerate(lines):
            cy = center_y - total_h // 2 + i * line_height
            bbox = dr.textbbox((center_x, cy), line, font=font, anchor='mm')
            boxes.append(bbox)

        # Unified capsule bounding box around the text block
        min_x = min(b[0] for b in boxes) - pad_x
        max_x = max(b[2] for b in boxes) + pad_x
        min_y = min(b[1] for b in boxes) - pad_y
        max_y = max(b[3] for b in boxes) + pad_y

        # Minimalist Black Pill Badge (~93% dark capsule #0C0C0E)
        dr.rounded_rectangle([min_x, min_y, max_x, max_y], radius=24, fill=(12, 12, 14, 238))

        # Pure white sharp text (#FFFFFF)
        for i, line in enumerate(lines):
            cy = center_y - total_h // 2 + i * line_height
            dr.text((center_x, cy), line, font=font, fill=(255, 255, 255, 255), anchor='mm')

        out_path = os.path.join(output_dir, f'sub_{idx:02d}.png')
        im.save(out_path)
        badge_records.append((start, end, out_path))

    print(f'{len(badge_records)} subtitle pill badges generated cleanly!')
    return badge_records

def render_subtitled_video():
    cwd = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(cwd, '..', '..'))
    json_path = os.path.join(cwd, 'subtitles.json')
    badge_dir = os.path.join(cwd, 'sub_badges')
    badge_records = generate_badges(json_path, badge_dir)

    base_video = os.path.join(project_root, 'youtube', 'Gun_1', 'Gun_1_Sosyal_Medya_Shorts.mp4')
    output_video = os.path.join(cwd, 'Gun_1_Sosyal_Medya_Altyazili.mp4')

    cmd = ['ffmpeg', '-y', '-i', base_video]
    for _, _, p in badge_records:
        cmd.extend(['-loop', '1', '-i', p])

    fc_parts = []
    last_v = '[0:v]'
    for idx, (start, end, _) in enumerate(badge_records):
        sub_idx = 1 + idx
        next_v = f'[v{idx}]'
        fc_parts.append(f'{last_v}[{sub_idx}:v]overlay=0:0:enable=\'between(t,{start:.2f},{end:.2f})\'{next_v};')
        last_v = next_v

    # Strip trailing semicolon from last filter
    fc_parts[-1] = fc_parts[-1].rstrip(';')

    cmd.extend([
        '-filter_complex', ''.join(fc_parts),
        '-map', last_v,
        '-map', '0:a',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'copy',
        '-t', '41.08',
        output_video
    ])

    print('Rendering subtitled video onto master video...')
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print('FFmpeg Error:', res.stderr)
        return False
    else:
        print(f'Render completed in {time.time()-t0:.2f}s!')
        print(f'Output video: {output_video}')
        return True

if __name__ == '__main__':
    render_subtitled_video()
