import subprocess
from PIL import Image

# Extract a frame at 39.5s
subprocess.run([
    "ffmpeg", "-y", "-ss", "39.5", "-i", "calisma/Gun_5/huberman_full.mp4",
    "-vframes", "1", "calisma/Gun_5/test_huberman_frame.jpg"
], capture_output=True)

# Test centered 9:16 crop
with Image.open("calisma/Gun_5/test_huberman_frame.jpg") as im:
    w, h = im.size
    print(f"Original frame size: {w}x{h}")
    # 16:9 1920x1080 -> 9:16 crop needs width = 1080 * 9 / 16 = 607.5
    crop_w = int(h * 9 / 16)
    left = (w - crop_w) // 2
    cropped = im.crop((left, 0, left + crop_w, h)).resize((1080, 1920))
    cropped.save("calisma/Gun_5/chk_crop_huberman.jpg")
    print(f"Cropped to 1080x1920, saved to calisma/Gun_5/chk_crop_huberman.jpg (left={left}, crop_w={crop_w})")
