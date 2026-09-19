import re
from datetime import timedelta

def time_to_sec(t_str):
    parts = t_str.split(':')
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s

def sec_to_srt_time(sec):
    td = timedelta(seconds=sec)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    millis = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def sec_to_ass_time(sec):
    td = timedelta(seconds=sec)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    centis = int((td.total_seconds() - total_seconds) * 100)
    return f"{hours:1d}:{minutes:02d}:{seconds:02d}.{centis:02d}"

def generate_subtitles(vtt_file, cut_start, cut_end, out_srt, out_ass):
    with open(vtt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    time_re = re.compile(r'(\d\d:\d\d:\d\d\.\d\d\d)\s+-->\s+(\d\d:\d\d:\d\d\.\d\d\d)')
    entries = []
    start_sec = 0
    end_sec = 0
    last_text = ""

    for line in lines:
        m = time_re.search(line)
        if m:
            start_sec = time_to_sec(m.group(1))
            end_sec = time_to_sec(m.group(2))
        elif '-->' not in line and line.strip() and not line.startswith('WEBVTT') and not line.startswith('Kind') and not line.startswith('Language'):
            clean = re.sub(r'<[^>]+>', '', line).strip()
            if clean and clean != last_text:
                if start_sec >= cut_start and end_sec <= cut_end:
                    entries.append((start_sec - cut_start, end_sec - cut_start, clean))
                    last_text = clean

    # Group into clean, rhythmic subtitles (4-7 words per line for easy reading)
    merged = []
    curr_s = None
    curr_e = None
    curr_words = []

    for s, e, text in entries:
        # Skip small fragment before "Bu biraz kumara benziyor"
        if "yapmamın" in text or "benim an benim" in text:
            continue
        if curr_s is None:
            curr_s = max(0.0, s)
            curr_e = e
            curr_words = text.split()
        else:
            words = text.split()
            for w in words:
                if not curr_words or curr_words[-1] != w:
                    curr_words.append(w)
            curr_e = e

        if len(curr_words) >= 5 or (curr_e - curr_s) >= 2.2:
            merged.append((curr_s, curr_e, ' '.join(curr_words)))
            curr_s = None
            curr_e = None
            curr_words = []

    if curr_words and curr_s is not None:
        merged.append((curr_s, curr_e, ' '.join(curr_words)))

    # Write SRT
    with open(out_srt, 'w', encoding='utf-8') as f:
        for idx, (s, e, text) in enumerate(merged, 1):
            f.write(f"{idx}\n")
            f.write(f"{sec_to_srt_time(s)} --> {sec_to_srt_time(e)}\n")
            f.write(f"{text}\n\n")

    # Write ASS with stylish subtitles (Modern yellow/white, bold outline, center-bottom)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,44,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(out_ass, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        for s, e, text in merged:
            f.write(f"Dialogue: 0,{sec_to_ass_time(s)},{sec_to_ass_time(e)},Default,,0,0,0,,{text}\n")

    print(f"Generated {len(merged)} subtitle cues.")

if __name__ == '__main__':
    # 07:54 (474s) to 08:36.5 (516.5s)
    generate_subtitles('ZvATo2VApJQ.tr.vtt', 474.0, 516.5, 'kesit.srt', 'kesit.ass')
