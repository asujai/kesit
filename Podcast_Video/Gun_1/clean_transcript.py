import re
import json

def extract_clean_word_stream(vtt_path, start_sec, end_sec):
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match time cue lines and following lines
    blocks = content.split("\n\n")
    words_timeline = []
    seen_cues = set()

    time_pat = re.compile(r"^(\d{2}):(\d{2}):(\d{2}\.\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}\.\d{3})")

    for b in blocks:
        lines = b.strip().split("\n")
        if not lines:
            continue
        m = time_pat.match(lines[0])
        if not m:
            continue
        s_time = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        e_time = int(m.group(4))*3600 + int(m.group(5))*60 + float(m.group(6))

        if e_time < start_sec or s_time > end_sec:
            continue

        # Look for word-level timestamps in line: word<00:00:00.000><c> next_word</c>
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("NOTE") or line.startswith("align"):
                continue
            # Extract words and word timestamps if present
            # Format: there's<00:00:00.480><c> a</c><00:00:00.680><c> very</c>
            cleaned = re.sub(r"<[^>]+>", "", line).strip()
            if cleaned and cleaned not in seen_cues:
                seen_cues.add(cleaned)

    # Let's inspect the actual clean dialogue text in this range
    # Audio starts at 1222.4s (20:22.400) and ends at 1440.5s (24:00.500)
    # Let's collect lines between 1220 and 1442
    lines_in_range = []
    curr_t = 0
    for b in blocks:
        lines = b.strip().split("\n")
        if not lines:
            continue
        m = time_pat.match(lines[0])
        if m:
            curr_t = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
            if 1222.0 <= curr_t <= 1441.0:
                for l in lines[1:]:
                    l = re.sub(r"<[^>]+>", "", l).strip()
                    if l and not l.startswith("align"):
                        lines_in_range.append((curr_t, l))

    # Deduplicate sliding window lines
    clean_lines = []
    for t, l in lines_in_range:
        if not clean_lines or clean_lines[-1][1] != l:
            # check if l extends clean_lines[-1]
            if clean_lines and l.startswith(clean_lines[-1][1]):
                clean_lines[-1] = (t, l)
            elif clean_lines and clean_lines[-1][1].endswith(l):
                continue
            else:
                clean_lines.append((t, l))

    return clean_lines

res = extract_clean_word_stream("Podcast_Video/Gun_1/lembke.en.vtt", 1222.0, 1441.0)
print(f"Total clean lines: {len(res)}")
for t, l in res[:20]:
    rel_t = round(t - 1222.4, 2)
    print(f"[{rel_t}s] {l}")
