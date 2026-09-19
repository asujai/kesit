import re

def parse_vtt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    cues = []
    curr_time = None
    curr_text = []
    
    time_pat = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})")
    
    for line in lines:
        line_str = line.strip()
        m = time_pat.match(line_str)
        if m:
            if curr_time and curr_text:
                full_text = " ".join(curr_text)
                full_text = re.sub(r"<[^>]+>", "", full_text).strip()
                if full_text:
                    cues.append((curr_time[0], curr_time[1], full_text))
            curr_time = (m.group(1), m.group(2))
            curr_text = []
        elif curr_time:
            if line_str and not line_str.startswith("NOTE") and not line_str.startswith("WEBVTT"):
                curr_text.append(line_str)
                
    if curr_time and curr_text:
        full_text = " ".join(curr_text)
        full_text = re.sub(r"<[^>]+>", "", full_text).strip()
        if full_text:
            cues.append((curr_time[0], curr_time[1], full_text))
            
    # Dedup consecutive duplicate text
    clean = []
    for c in cues:
        if not clean or clean[-1][2] != c[2]:
            clean.append(c)
    return clean

cues = parse_vtt("Podcast_Video/Gun_1/lembke.en.vtt")
print(f"Total cues parsed: {len(cues)}")

# Let's search sections
for i, (s, e, t) in enumerate(cues):
    t_low = t.lower()
    if any(w in t_low for w in ["teeter", "balance", "pleasure and pain", "gremlin", "neuroadaptation"]):
        print(f"[{s} -> {e}] {t}")

