import subprocess

# Let's create a seamless 218.10s ambient soundtrack score using acrossfade
# Order: music2_ambient (60s) -> acrossfade -> music3_tension (55s) -> acrossfade -> music1_eternity (60s) -> acrossfade -> music1_eternity (60s)
# Total duration ~218.1s

cmd = [
    "ffmpeg", "-y",
    "-i", "assets/audio/music2_ambient.m4a",
    "-i", "assets/audio/music3_tension.m4a",
    "-i", "assets/audio/music1_eternity.m4a",
    "-filter_complex",
    # crossfade ambient -> tension at 54s
    "[0:a][1:a]acrossfade=d=4:c1=tri:c2=tri[a1];"
    # crossfade a1 -> eternity
    "[a1][2:a]acrossfade=d=4:c1=tri:c2=tri[a2];"
    # loop eternity to cover the rest of 218s
    "[a2]aloop=loop=-1:size=2e+09,atrim=0:218.10,afade=t=in:ss=0:d=1.0,afade=t=out:st=214.0:d=4.1[outa]",
    "-map", "[outa]",
    "-c:a", "aac", "-b:a", "192k",
    "Podcast_Video/Gun_1/soundtrack_score.m4a"
]

print("Generating cinematic soundtrack score...")
subprocess.run(cmd, check=True)
print("Soundtrack score generated successfully!")
