import os
import json
import subprocess
import sys

with open("Podcast_Video/Gun_1/subtitles_master.json", "r", encoding="utf-8") as f:
    subs = json.load(f)

video_in = "Podcast_Video/Gun_1/raw_video_concat.mp4"
audio_in = "Podcast_Video/Gun_1/master_audio.m4a"

def build_overlay_command(badge_dir, output_file):
    cmd = ["ffmpeg", "-y", "-i", video_in, "-i", audio_in]
    
    # Add all 41 badge images as inputs
    for idx, s in enumerate(subs):
        badge_path = os.path.join(badge_dir, f"sub_{s['id']:02d}.png")
        cmd.extend(["-i", badge_path])
        
    # Build filter complex
    fc_parts = []
    prev_v = "0:v"
    
    for idx, s in enumerate(subs):
        input_idx = idx + 2  # inputs 0 is video, 1 is audio, 2+ are badges
        out_v = f"v{idx+1}" if idx < len(subs) - 1 else "v_final"
        # Center horizontally, position at y=910
        fc_parts.append(
            f"[{prev_v}][{input_idx}:v]overlay=(W-w)/2:910:enable='between(t,{s['start']},{s['end']})'[{out_v}]"
        )
        prev_v = out_v
        
    filter_complex_str = ";".join(fc_parts)
    
    cmd.extend([
        "-filter_complex", filter_complex_str,
        "-map", "[v_final]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-t", "218.10",
        output_file
    ])
    
    return cmd

lang = sys.argv[1] if len(sys.argv) > 1 else "tr"

if lang == "tr":
    out_video = "Podcast_Video/Gun_1/Gun_1_Podcast_Video.mp4"
    badge_dir = "Podcast_Video/Gun_1/sub_badges_tr"
    print(f"Building Turkish Master Video: {out_video}...")
else:
    out_video = "Podcast_Video/Gun_1/Gun_1_Podcast_Video_EN.mp4"
    badge_dir = "Podcast_Video/Gun_1/sub_badges_en"
    print(f"Building English Master Video: {out_video}...")

cmd = build_overlay_command(badge_dir, out_video)
subprocess.run(cmd, check=True)
print(f"Successfully rendered: {out_video}")
