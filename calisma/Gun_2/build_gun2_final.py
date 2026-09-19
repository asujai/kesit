import os
import sys
import json
import subprocess

def run_cmd(cmd, desc=""):
    print(f"\n--- {desc} ---")
    print("Executing:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if res.returncode != 0:
        print(f"ERROR in {desc}:")
        print(res.stderr)
        raise RuntimeError(f"Command failed: {desc}")
    return res

def main():
    work_dir = os.path.join('calisma', 'Gun_2')
    clean_speaker = os.path.join(work_dir, 'clean_raw_beyhan.mp4')
    base_speaker = os.path.join(work_dir, 'base_speaker_1080x1920.mp4')
    broll_car = os.path.join(work_dir, 'alt_car_36067578.mp4')
    broll_cafe = os.path.join(work_dir, 'broll2_cafe_9047387.mp4')
    broll_bed = os.path.join(work_dir, 'broll3_night_bed_28048582.mp4')
    broll_scroll = os.path.join(work_dir, 'broll4_scrolling_10374888.mp4')
    bg_music = os.path.join('assets', 'audio', 'music2_ambient.m4a')
    master_video = os.path.join(work_dir, 'master_gun2.mp4')

    # 1. Generate 1080x1920 base speaker video with blurred depth background
    if not os.path.exists(base_speaker):
        vf_base = (
            "split=2[fg_in][bg_in];"
            "[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.25[bg];"
            "[fg_in]scale=1350:-1,crop=1080:ih:(iw-1080)/2:0[fg];"
            "[bg][fg]overlay=0:(H-h)/2"
        )
        cmd_base = [
            'ffmpeg', '-y', '-i', clean_speaker,
            '-vf', vf_base,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-an', base_speaker
        ]
        run_cmd(cmd_base, "Rendering base speaker 1080x1920")

    # 2. Prepare normalized B-roll clips (1080x1920, 25fps, exact duration needed)
    # B1: Car / traffic (05.75 - 13.55 = 7.8s)
    b1_norm = os.path.join(work_dir, 'b1_norm.mp4')
    run_cmd([
        'ffmpeg', '-y', '-ss', '00:00:01', '-i', broll_car, '-t', '7.8',
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-an', b1_norm
    ], "Normalizing B-Roll 1 (Car Traffic)")

    # B2: Cafe friends (13.55 - 19.55 = 6.0s)
    b2_norm = os.path.join(work_dir, 'b2_norm.mp4')
    run_cmd([
        'ffmpeg', '-y', '-ss', '00:00:00.5', '-i', broll_cafe, '-t', '6.0',
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-an', b2_norm
    ], "Normalizing B-Roll 2 (Cafe Friends)")

    # B3: Night bed screen lit (19.55 - 26.50 = 6.95s)
    b3_norm = os.path.join(work_dir, 'b3_norm.mp4')
    run_cmd([
        'ffmpeg', '-y', '-ss', '00:00:03.5', '-i', broll_bed, '-t', '6.95',
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-an', b3_norm
    ], "Normalizing B-Roll 3 (Night Bed)")

    # B4: Fast scrolling 5000 taps (33.30 - 40.40 = 7.1s)
    b4_norm = os.path.join(work_dir, 'b4_norm.mp4')
    run_cmd([
        'ffmpeg', '-y', '-ss', '00:00:00', '-i', broll_scroll, '-t', '7.1',
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-an', b4_norm
    ], "Normalizing B-Roll 4 (Scrolling 5000 taps)")

    # 3. Build complex video filter with B-roll overlays and subtitle badges
    # Load subtitle manifest
    with open(os.path.join(work_dir, 'subtitles.json'), 'r', encoding='utf-8') as f:
        subs = json.load(f)

    # Filter graph construction
    # Inputs:
    # 0: base_speaker
    # 1: b1_norm
    # 2: b2_norm
    # 3: b3_norm
    # 4: b4_norm
    # 5..N: subtitle pngs
    # Audio inputs:
    # clean_speaker (voice)
    # bg_music

    filter_chains = []
    
    # Overlay B-rolls
    filter_chains.append("[0:v][1:v]overlay=enable='between(t,5.75,13.55)'[v_b1]")
    filter_chains.append("[v_b1][2:v]overlay=enable='between(t,13.55,19.55)'[v_b2]")
    filter_chains.append("[v_b2][3:v]overlay=enable='between(t,19.55,26.50)'[v_b3]")
    filter_chains.append("[v_b3][4:v]overlay=enable='between(t,33.30,40.40)'[v_b4]")

    last_v = "v_b4"
    inputs = [
        '-i', base_speaker,
        '-i', b1_norm,
        '-i', b2_norm,
        '-i', b3_norm,
        '-i', b4_norm
    ]

    for idx, sub in enumerate(subs):
        badge_path = os.path.join(work_dir, 'sub_badges', f"{sub['id']}.png")
        input_idx = 5 + idx
        inputs.extend(['-i', badge_path])
        out_v = f"v_sub_{idx}"
        filter_chains.append(
            f"[{last_v}][{input_idx}:v]overlay=enable='between(t,{sub['start']:.2f},{sub['end']:.2f})'[{out_v}]"
        )
        last_v = out_v

    filter_complex_str = ";".join(filter_chains)

    # 4. Render final video with visual overlays
    temp_visual = os.path.join(work_dir, 'temp_visual.mp4')
    cmd_visual = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex_str,
        '-map', f"[{last_v}]",
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-an', temp_visual
    ]
    run_cmd(cmd_visual, "Rendering composite visual video with all B-rolls and subtitles")

    # 5. Master audio with loudnorm (-14 LUFS) and ambient music mix
    # Voice track from clean_speaker, bg music from bg_music
    # amix filter: voice volume 1.0, music volume 0.08 (~-22dB), loudnorm
    cmd_audio = [
        'ffmpeg', '-y',
        '-i', clean_speaker,
        '-stream_loop', '-1', '-i', bg_music,
        '-filter_complex',
        "[0:a]volume=1.0[voice];"
        "[1:a]volume=0.08[music];"
        "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
        "[mixed]loudnorm=I=-14:TP=-1.5:LRA=11[a_master]",
        '-map', '[a_master]',
        '-c:a', 'aac', '-b:a', '192k',
        os.path.join(work_dir, 'master_audio.m4a')
    ]
    run_cmd(cmd_audio, "Mastering audio at -14 LUFS with ambient music")

    # 6. Mux visual and mastered audio into final master_gun2.mp4
    cmd_final = [
        'ffmpeg', '-y',
        '-i', temp_visual,
        '-i', os.path.join(work_dir, 'master_audio.m4a'),
        '-c:v', 'copy',
        '-c:a', 'copy',
        master_video
    ]
    run_cmd(cmd_final, "Final Mux to master_gun2.mp4")
    print(f"\nSUCCESS! Master video generated at: {master_video}")

if __name__ == '__main__':
    main()
