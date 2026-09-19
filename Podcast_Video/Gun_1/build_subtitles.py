import json
import re

from clean_transcript import extract_clean_word_stream

lines = extract_clean_word_stream("Podcast_Video/Gun_1/lembke.en.vtt", 1222.0, 1441.0)
clip_duration = 218.10

# Combine lines into logical sentences with start and end times
sentences = []
curr_start = 0.0
curr_words = []

for i, (t, text) in enumerate(lines):
    rel_t = max(0.0, min(clip_duration, round(t - 1222.4, 2)))
    if not curr_words:
        curr_start = rel_t
        curr_words.append(text)
    else:
        # Check if we should close this block:
        # duration >= 4.0s or sentence ends with punctuation/clause
        duration = rel_t - curr_start
        if duration >= 4.0 or i == len(lines) - 1:
            curr_end = rel_t if i < len(lines) - 1 else clip_duration
            if curr_end <= curr_start:
                curr_end = min(clip_duration, curr_start + 3.0)
            combined = " ".join(curr_words)
            combined = re.sub(r"\s+", " ", combined).strip()
            sentences.append({
                "start": round(curr_start, 2),
                "end": round(curr_end, 2),
                "en": combined
            })
            curr_start = rel_t
            curr_words = [text]
        else:
            curr_words.append(text)

if curr_words:
    combined = " ".join(curr_words)
    sentences.append({
        "start": round(curr_start, 2),
        "end": clip_duration,
        "en": combined
    })

# Smooth boundaries: make end of prev sentence match start of next if gap is small
for i in range(len(sentences) - 1):
    gap = sentences[i+1]["start"] - sentences[i]["end"]
    if 0 < gap < 0.8:
        sentences[i]["end"] = sentences[i+1]["start"]

print(f"Total structured subtitle blocks: {len(sentences)}")
for idx, s in enumerate(sentences[:15]):
    print(f"{idx+1:02d}. [{s['start']}s -> {s['end']}s] {s['en']}")

with open("Podcast_Video/Gun_1/subtitles_structured.json", "w", encoding="utf-8") as f:
    json.dump(sentences, f, indent=2, ensure_ascii=False)
