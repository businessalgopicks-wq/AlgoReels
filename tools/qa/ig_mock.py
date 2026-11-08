#!/usr/bin/env python3
"""Darken where Instagram's interface sits over real frames of a video, to check nothing important is under it.

Usage:  python3 ig_mock.py <video> <out.jpg> <seconds> [<seconds> ...]

The rectangles are an estimate on 1080 x 1920: top bar, right action rail, bottom caption block. Check them against the
current app now and then, because they are not published numbers.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

BOXES = [((0, 0, 1080, 150), 70), ((955, 1020, 1080, 1700), 110), ((0, 1640, 950, 1920), 110)]
video, out, times = sys.argv[1], sys.argv[2], sys.argv[3:]
if not times:
    sys.exit(__doc__)
frames = []
with tempfile.TemporaryDirectory() as tmp:
    for t in times:
        p = Path(tmp) / f"{t}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", video, "-frames:v", "1", str(p)], check=True)
        im = Image.open(p).convert("RGBA")
        over = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(over)
        for box, alpha in BOXES:
            draw.rectangle(box, fill=(0, 0, 0, alpha))
        frames.append(Image.alpha_composite(im, over).convert("RGB").resize((486, 864)))
sheet = Image.new("RGB", (len(frames) * 492, 870), (30, 30, 30))
for i, im in enumerate(frames):
    sheet.paste(im, (i * 492, 3))
sheet.save(out, quality=90)
print(out)
