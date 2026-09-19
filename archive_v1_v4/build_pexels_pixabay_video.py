import os
import subprocess
import time

def build_video():
    cwd = os.path.dirname(os.path.abspath(__file__))
    output_video = os.path.join(cwd, "sosyal_medya_kesit_pexels_pixabay.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.join(cwd, "clean_raw.mp4"),                           # 0: base video (38.98s)
        "-stream_loop", "-1", "-i", os.path.join(cwd, "stock_casino.mp4"), # 1: Pexels casino roulette
        "-loop", "1", "-i", os.path.join(cwd, "popup_facebook.png"),        # 2: Facebook popup
        "-loop", "1", "-i", os.path.join(cwd, "popup_instagram.png"),       # 3: Instagram popup
        "-loop", "1", "-i", os.path.join(cwd, "test_pixabay_crop.jpg"),     # 4: Pixabay mobile addiction photo
        "-stream_loop", "-1", "-i", os.path.join(cwd, "pexels_social_4k.mp4"), # 5: Pexels 4K reel scroll
        "-i", os.path.join(cwd, "music2_ambient.m4a"),                      # 6: Ambient background music
        "-filter_complex",
        (
            "[0:v]crop=w=ih*9/16:h=ih:x=(iw-ih*9/16)/2:y=0,scale=1080:1920,fps=30[v_base];"
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+5.5/TB[v_casino];"
            "[2:v]scale=1080:1920,fps=30,setpts=PTS-STARTPTS[v_fb];"
            "[3:v]scale=1080:1920,fps=30,setpts=PTS-STARTPTS[v_ig];"
            "[4:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS[v_pixabay];"
            "[5:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+23.4/TB[v_scroll];"
            
            # Step 1: Roulette B-roll (5.5 - 7.8s)
            "[v_base][v_casino]overlay=0:0:enable='between(t,5.5,7.8)'[v_step1];"
            # Step 2: Facebook popup badge (7.8 - 9.5s)
            "[v_step1][v_fb]overlay=0:0:enable='between(t,7.8,9.5)'[v_step2];"
            # Step 3: Instagram popup badge (9.5 - 11.4s)
            "[v_step2][v_ig]overlay=0:0:enable='between(t,9.5,11.4)'[v_step3];"
            # Step 4: Pixabay phone addiction visual (19.5 - 23.4s)
            "[v_step3][v_pixabay]overlay=0:0:enable='between(t,19.5,23.4)'[v_step4];"
            # Step 5: Pexels 4K feed scrolling B-roll (23.4 - 27.5s)
            "[v_step4][v_scroll]overlay=0:0:enable='between(t,23.4,27.5)'[v_step5];"
            # Step 6: Smooth fade to black at the end (36.5 - 38.98s)
            "[v_step5]fade=t=out:st=36.5:d=2.48[v_final];"
            
            # Audio pipeline: Voice + Ambient Music ducked + fade-out
            "[0:a]volume=1.05,afade=t=out:st=36.5:d=2.48[a_voice];"
            "[6:a]volume=0.14,afade=t=in:st=0:d=1.0,afade=t=out:st=36.5:d=2.48[a_bgm];"
            "[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2[a_final]"
        ),
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "38.98",
        output_video
    ]

    print("Executing FFmpeg render pipeline...")
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
    build_video()
