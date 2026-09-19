import subprocess
import json
import re

voice_path = "Podcast_Video/Gun_1/clean_voice.m4a"
music_path = "Podcast_Video/Gun_1/soundtrack_score.m4a"
output_master = "Podcast_Video/Gun_1/master_audio.m4a"

# Pass 1: Measure loudness with amix (bgm gain 0.38)
pass1_cmd = [
    "ffmpeg", "-y",
    "-i", voice_path,
    "-i", music_path,
    "-filter_complex",
    "[1:a]volume=0.38[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14.0:LRA=11:TP=-1.0:print_format=json",
    "-f", "null", "-"
]

print("Running EBU R128 Loudnorm Pass 1...")
res = subprocess.run(pass1_cmd, capture_output=True, text=True)

# Parse measured values from stderr
m = re.search(r"\{[\s\S]*\"input_i\"[\s\S]*\}", res.stderr)
if not m:
    raise RuntimeError("Could not find loudnorm JSON stats in Pass 1 output!")

stats = json.loads(m.group(0))
print(f"Pass 1 measured: I={stats['input_i']}, TP={stats['input_tp']}, LRA={stats['input_lra']}, Thresh={stats['input_thresh']}")

# Pass 2: Linear normalized render
pass2_cmd = [
    "ffmpeg", "-y",
    "-i", voice_path,
    "-i", music_path,
    "-filter_complex",
    f"[1:a]volume=0.38[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,"
    f"loudnorm=I=-14.0:LRA=11:TP=-1.0:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
    f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:linear=true:print_format=json",
    "-c:a", "aac", "-b:a", "256k",
    output_master
]

print("Running EBU R128 Loudnorm Pass 2...")
subprocess.run(pass2_cmd, check=True)
print(f"Master audio generated: {output_master}")
