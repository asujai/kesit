import subprocess

cmd = [
    'ffmpeg', '-y', '-ss', '40', '-to', '50', '-i', 'calisma/Gun_2/beyhan_raw.mp4',
    '-af', 'silencedetect=noise=-28dB:d=0.2', '-f', 'null', '-'
]
res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
for line in res.stderr.splitlines():
    if 'silence' in line:
        print(line)
