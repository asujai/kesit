import os
import subprocess
import time

def build_v5():
    cwd = os.path.dirname(os.path.abspath(__file__))
    output_video = os.path.join(cwd, "sosyal_medya_kesit_v5_cinematic.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.join(cwd, "clean_raw_v4.mp4"),                           # 0: base video (41.08s)
        "-stream_loop", "-1", "-i", os.path.join(cwd, "stock_casino.mp4"),    # 1: Pexels casino roulette
        "-stream_loop", "-1", "-i", os.path.join(cwd, "broll_addict_7824433.mp4"), # 2: 4K Cafe social addiction
        "-stream_loop", "-1", "-i", os.path.join(cwd, "broll_dark_bed_7986737.mp4"), # 3: 4K Dark bed glowing screen
        "-stream_loop", "-1", "-i", os.path.join(cwd, "pexels_social_4k.mp4"), # 4: 4K Reel endless doom-scroll
        "-i", os.path.join(cwd, "music2_ambient.m4a"),                         # 5: Ambient background music
        "-filter_complex",
        (
            # Base video: Crop 9:16 portrait
            "[0:v]crop=w=ih*9/16:h=ih:x=(iw-ih*9/16)/2:y=0,scale=1080:1920,fps=30[v_base];"
            
            # 1. Pexels Roulette B-roll (5.5 - 7.8s)
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+5.5/TB[v_casino];"
            
            # 2. 4K Cafe Social Addiction B-roll (7.8 - 12.0s)
            "[2:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+7.8/TB[v_cafe];"
            
            # 3. 4K Dark Bed Face Glow B-roll (19.5 - 23.4s)
            "[3:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+19.5/TB[v_bed];"
            
            # 4. 4K Endless Reels Scroll B-roll (23.4 - 27.5s)
            "[4:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+23.4/TB[v_scroll];"
            
            # Overlay chaining - pure video cuts, zero artificial badges/stickers
            "[v_base][v_casino]overlay=0:0:enable='between(t,5.5,7.8)'[v_step1];"
            "[v_step1][v_cafe]overlay=0:0:enable='between(t,7.8,12.0)'[v_step2];"
            "[v_step2][v_bed]overlay=0:0:enable='between(t,19.5,23.4)'[v_step3];"
            "[v_step3][v_scroll]overlay=0:0:enable='between(t,23.4,27.5)'[v_step4];"
            
            # Video Fade to Black after 'Sizi bu bağımlı yapıyor!' finishes at 40.35s
            "[v_step4]fade=t=out:st=40.35:d=0.73[v_final];"
            
            # Audio Pipeline: Voice + Ambient Music + Loudness Normalization (-14 LUFS) + Fade Out
            "[0:a]volume=1.0[a_voice];"
            "[5:a]volume=0.14,afade=t=in:st=0:d=1.0[a_bgm];"
            "[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:LRA=7:tp=-1,afade=t=out:st=40.35:d=0.73[a_final]"
        ),
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "41.08",
        output_video
    ]

    print("Executing FFmpeg v5 Cinematic Render Pipeline...")
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:")
        print(res.stderr)
        return False
    else:
        print(f"Render completed successfully in {time.time()-t0:.2f}s!")
        print(f"Output: {output_video}")
        return True

if __name__ == "__main__":
    build_v5()
