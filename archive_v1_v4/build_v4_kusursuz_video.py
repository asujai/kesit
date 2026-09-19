import os
import subprocess
import time

def build_v4():
    cwd = os.path.dirname(os.path.abspath(__file__))
    output_video = os.path.join(cwd, "sosyal_medya_kesit_v4_kusursuz.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.join(cwd, "clean_raw_v4.mp4"),                         # 0: base video (41.08s)
        "-stream_loop", "-1", "-i", os.path.join(cwd, "stock_casino.mp4"),  # 1: Pexels casino roulette
        "-loop", "1", "-i", os.path.join(cwd, "popup_facebook.png"),         # 2: Facebook popup badge
        "-loop", "1", "-i", os.path.join(cwd, "popup_instagram.png"),        # 3: Instagram popup badge
        "-ignore_loop", "0", "-i", os.path.join(cwd, "sticker_heart_like.gif"), # 4: GIPHY animated heart reaction
        "-loop", "1", "-i", os.path.join(cwd, "test_pixabay_crop.jpg"),      # 5: Pixabay mobile addiction photo
        "-stream_loop", "-1", "-i", os.path.join(cwd, "pexels_social_4k.mp4"), # 6: Pexels 4K reel scroll
        "-i", os.path.join(cwd, "music2_ambient.m4a"),                       # 7: Ambient background music
        "-filter_complex",
        (
            # Base video: Crop 9:16 portrait
            "[0:v]crop=w=ih*9/16:h=ih:x=(iw-ih*9/16)/2:y=0,scale=1080:1920,fps=30[v_base];"
            
            # 1. Pexels Roulette B-roll (5.5 - 7.8s)
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+5.5/TB[v_casino];"
            
            # 2. Facebook Badge (7.8 - 9.5s)
            "[2:v]scale=1080:1920,fps=30,setpts=PTS-STARTPTS[v_fb];"
            
            # 3. Instagram Badge (9.5 - 11.4s)
            "[3:v]scale=1080:1920,fps=30,setpts=PTS-STARTPTS[v_ig];"
            
            # 4. GIPHY Animated Heart Sticker: scaled to 360px, PTS offset to 14.0s
            "[4:v]scale=360:-1,fps=30,setpts=PTS-STARTPTS+14.0/TB[v_heart];"
            
            # 5. Pixabay Visual (19.5 - 23.4s)
            "[5:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS[v_pixabay];"
            
            # 6. Pexels 4K Feed Scroll (23.4 - 27.5s)
            "[6:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setpts=PTS-STARTPTS+23.4/TB[v_scroll];"
            
            # Overlay chaining
            "[v_base][v_casino]overlay=0:0:enable='between(t,5.5,7.8)'[v_step1];"
            "[v_step1][v_fb]overlay=0:0:enable='between(t,7.8,9.5)'[v_step2];"
            "[v_step2][v_ig]overlay=0:0:enable='between(t,9.5,11.4)'[v_step3];"
            "[v_step3][v_heart]overlay=x=W-w-80:y=80:enable='between(t,14.0,18.5)'[v_step4];"
            "[v_step4][v_pixabay]overlay=0:0:enable='between(t,19.5,23.4)'[v_step5];"
            "[v_step5][v_scroll]overlay=0:0:enable='between(t,23.4,27.5)'[v_step6];"
            
            # Video Fade to Black after 'Sizi bu bağımlı yapıyor!' finishes at 40.35s
            "[v_step6]fade=t=out:st=40.35:d=0.73[v_final];"
            
            # Audio Pipeline: Voice + Ambient Music + Loudness Normalization (-14 LUFS) + Fade Out
            "[0:a]volume=1.0[a_voice];"
            "[7:a]volume=0.14,afade=t=in:st=0:d=1.0[a_bgm];"
            "[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:LRA=7:tp=-1,afade=t=out:st=40.35:d=0.73[a_final]"
        ),
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "19",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "41.08",
        output_video
    ]

    print("Executing FFmpeg v4 Kusursuz Render Pipeline...")
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
    build_v4()
