import os
import sys
import json
import subprocess
import shutil

def run_cmd(cmd, desc=""):
    print(f"\n--- {desc} ---")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if res.returncode != 0:
        print(f"ERROR in {desc}:")
        print(res.stderr)
        raise RuntimeError(f"Command failed: {desc}")
    return res

def main():
    work_dir = os.path.join('calisma', 'Gun_2')
    dyn_dir = os.path.join(work_dir, 'dynamic_brolls')
    base_speaker = os.path.join(work_dir, 'base_speaker_1080x1920.mp4')
    master_video = os.path.join(work_dir, 'master_gun2.mp4')
    norm_cuts_dir = os.path.join(work_dir, 'norm_cuts')
    os.makedirs(norm_cuts_dir, exist_ok=True)

    # Cut definitions: (name, source_file, ss, duration, start_t, end_t, speed_factor)
    cuts_def = [
        # 1. Yatakta telefona uzanan kişi (1.7s)
        ('c01_bed_dark', os.path.join(dyn_dir, 'cut_05_night_bedroom_dark.mp4'), 2.0, 1.7, 2.00, 3.70, 1.0),
        # 2. Yastık yanında parlayan telefon ekranı (1.8s)
        ('c02_bed_screen', os.path.join(work_dir, 'broll3_night_bed_28048582.mp4'), 4.0, 1.8, 3.70, 5.50, 1.0),
        # 3. Otobüste telefona bakan yolcu (1.6s)
        ('c03_bus_passenger', os.path.join(dyn_dir, 'cut_01_bus_phone.mp4'), 3.0, 1.6, 5.50, 7.10, 1.0),
        # 4. Kırmızı ışıkta bekleyen araba & fren lambası (1.7s)
        ('c04_red_light', os.path.join(dyn_dir, 'cut_02_red_light.mp4'), 1.0, 1.7, 7.10, 8.80, 1.0),
        # 5. Konsoldaki telefona uzanan el (1.7s)
        ('c05_car_hand', os.path.join(work_dir, 'alt_car_36067578.mp4'), 2.0, 1.7, 8.80, 10.50, 1.0),
        # [10.50 - 12.10: Konuşmacı Beyhan Budak - 1.6s]
        # 6. Direksiyon başında telefona bakan sürücü (1.7s)
        ('c06_driver_look', os.path.join(work_dir, 'alt_car_36067578.mp4'), 8.0, 1.7, 12.10, 13.80, 1.0),
        # 7. Kafede oturan ve telefona bakan genç (1.7s)
        ('c07_cafe1', os.path.join(work_dir, 'broll2_cafe_9047387.mp4'), 0.5, 1.7, 13.80, 15.50, 1.0),
        # 8. Ekranda gelen bildirim / mesaj (1.5s)
        ('c08_notif_phone', os.path.join(dyn_dir, 'notif_7822022.mp4'), 3.2, 1.5, 15.50, 17.00, 1.0),
        # 9. İkinci kafe sahnesi masada telefona bakan kız (1.6s)
        ('c09_cafe2', os.path.join(dyn_dir, 'cafe_7817089.mp4'), 1.5, 1.6, 17.00, 18.60, 1.0),
        # [18.60 - 20.10: Konuşmacı Beyhan Budak - 1.5s]
        # 10. Gece karanlık oda / telefon uykusuzluğu (1.7s)
        ('c10_night_dark', os.path.join(dyn_dir, 'cut_05_night_bedroom_dark.mp4'), 6.0, 1.7, 20.10, 21.80, 1.0),
        # 11. Yastıkta parlayan ekran (1.7s)
        ('c11_pillow_screen', os.path.join(work_dir, 'broll3_night_bed_28048582.mp4'), 7.0, 1.7, 21.80, 23.50, 1.0),
        # 12. Karanlıkta yüzüne telefonun mavi ışığı vuran kişi (1.7s)
        ('c12_blue_face', os.path.join(dyn_dir, 'cut_06_blue_light_face.mp4'), 1.5, 1.7, 23.50, 25.20, 1.0),
        # [25.20 - 32.40: Konuşmacı Beyhan Budak doruk sorusu ve cevabı: "Neden bahsediyorum sence? Tabii ki de akıllı telefonlardan!"]
        # 13. Akıllı telefon bağımlılığı metaforu (1.8s)
        ('c13_phone_chains', os.path.join(dyn_dir, 'cut_09_phone_chains.mp4'), 2.0, 1.8, 32.40, 34.20, 1.0),
        # 14. Hızlı başparmak kaydırma - 2x speed ramp (1.8s)
        ('c14_scroll_fast1', os.path.join(work_dir, 'broll4_scrolling_10374888.mp4'), 0.5, 1.8, 34.20, 36.00, 2.0),
        # 15. Feed kaydırma yakın plan - 2x speed ramp (1.6s)
        ('c15_scroll_feed', os.path.join(dyn_dir, 'scroll_10374885.mp4'), 1.0, 1.6, 36.00, 37.60, 2.0),
        # 16. Ekrana hızlı parmak dokunuşları (5.000 kez dokunma) (1.8s)
        ('c16_scroll_fast2', os.path.join(work_dir, 'broll4_scrolling_10374888.mp4'), 4.0, 1.8, 37.60, 39.40, 1.5)
        # [39.40 - 46.85: Konuşmacı Beyhan Budak doruk noktası ve punchline]
    ]

    print(f"Normalizing {len(cuts_def)} dynamic micro-cuts (strictly <= 1.8s each)...")
    normalized_files = []
    for name, src_file, ss, dur, start_t, end_t, speed in cuts_def:
        out_norm = os.path.join(norm_cuts_dir, f"{name}.mp4")
        normalized_files.append((out_norm, start_t, end_t))
        
        # Source read duration depends on speed ramp
        src_dur = dur * speed
        vf_filters = []
        if speed != 1.0:
            setpts = 1.0 / speed
            vf_filters.append(f"setpts={setpts:.3f}*PTS")
        vf_filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
        vf_filters.append("crop=1080:1920")
        vf_filters.append("fps=25")
        vf = ",".join(vf_filters)

        cmd = [
            'ffmpeg', '-y', '-ss', str(ss), '-i', src_file,
            '-t', f"{src_dur:.2f}",
            '-vf', vf,
            '-t', f"{dur:.2f}",
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-an', out_norm
        ]
        run_cmd(cmd, f"Normalizing {name}")

    print(f"\nAll {len(normalized_files)} micro-cuts normalized successfully!")

    # Build complex filter chain
    inputs = ['-i', base_speaker]
    filter_chains = []
    last_v = "0:v"

    # Micro-cuts overlay
    for idx, (cut_path, start_t, end_t) in enumerate(normalized_files):
        inputs.extend(['-i', cut_path])
        cut_input_idx = 1 + idx
        out_v = f"v_cut_{idx}"
        filter_chains.append(
            f"[{last_v}][{cut_input_idx}:v]overlay=enable='between(t,{start_t:.2f},{end_t:.2f})'[{out_v}]"
        )
        last_v = out_v

    # Subtitles overlay
    with open(os.path.join(work_dir, 'subtitles.json'), 'r', encoding='utf-8') as f:
        subs = json.load(f)

    sub_start_idx = 1 + len(normalized_files)
    for s_idx, sub in enumerate(subs):
        badge_path = os.path.join(work_dir, 'sub_badges', f"{sub['id']}.png")
        inputs.extend(['-i', badge_path])
        badge_input_idx = sub_start_idx + s_idx
        out_sub_v = f"v_sub_{s_idx}"
        filter_chains.append(
            f"[{last_v}][{badge_input_idx}:v]overlay=enable='between(t,{sub['start']:.2f},{sub['end']:.2f})'[{out_sub_v}]"
        )
        last_v = out_sub_v

    filter_complex_str = ";".join(filter_chains)

    # Render visual
    temp_visual = os.path.join(work_dir, 'temp_dynamic_visual.mp4')
    cmd_visual = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex_str,
        '-map', f"[{last_v}]",
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-an', temp_visual
    ]
    run_cmd(cmd_visual, "Rendering fast dynamic visual video")

    # Mux with master audio
    master_audio = os.path.join(work_dir, 'master_audio.m4a')
    cmd_final = [
        'ffmpeg', '-y',
        '-i', temp_visual,
        '-i', master_audio,
        '-c:v', 'copy',
        '-c:a', 'copy',
        master_video
    ]
    run_cmd(cmd_final, "Final Mux to master_gun2.mp4")

    # Copy to showcases
    yt_dest = os.path.join('youtube', 'Gun_2', 'Gun_2_Shorts.mp4')
    ig_dest = os.path.join('instagram', 'Gun_2', 'Gun_2_Reels.mp4')
    shutil.copyfile(master_video, yt_dest)
    shutil.copyfile(master_video, ig_dest)
    print(f"\nCopied to YouTube showcase: {yt_dest}")
    print(f"Copied to Instagram showcase: {ig_dest}")
    print("\nSUCCESS: Fast dynamic micro-cut edition rendered!")

if __name__ == '__main__':
    main()
