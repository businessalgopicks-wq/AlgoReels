"""Assemble rendered shots into one picture track, with restrained halation, a light vignette and any planned dissolves.

Run through ./reel assemble <reel> <frames folder>. Frames are <frames folder>/<shot>/<NNNN>.jpg, and shot times come from timeline.py.
AgX already compresses highlights, so this adds only a faint glow to the very brightest pixels. A broad bloom washes out skin and cloth.
"""
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from timeline import FPS, TIMES  # noqa: E402

root = pathlib.Path(sys.argv[1])
out = sys.argv[2]
order = sorted(TIMES)
end_frame = round(max(b for _, b in TIMES.values()) * FPS)


def load(shot, local):
    path = root / shot / f"{local:04d}.jpg"
    if not path.exists():
        raise FileNotFoundError(f"Missing {shot} frame {local}: {path}")
    return Image.open(path).convert("RGB")


def finish(img, w, vignette):
    k = w / 1080  # the picture may be a preview size, so blur scales with it
    a = np.asarray(img, dtype=np.float32) / 255
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    mask = np.clip((lum - 0.88) / 0.12, 0, 1)
    source = Image.fromarray(np.uint8(a * mask[..., None] * 255))
    glow = np.asarray(source.filter(ImageFilter.GaussianBlur(9 * k)), dtype=np.float32) / 255
    return np.uint8(np.clip((a + 0.045 * glow) * (1 - (1 - vignette) * 0.30), 0, 1) * 255)


first = load(order[0], 1)
W, H = first.size
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.17 * np.clip(r - 0.55, 0, 1) ** 2)[..., None].astype(np.float32)

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for g in range(1, end_frame + 1):
    t = (g - 0.5) / FPS
    live = [s for s in order if TIMES[s][0] <= t < TIMES[s][1]] or [order[-1]]
    if len(live) == 1:
        shot = live[0]
        picture = load(shot, max(1, g - round(TIMES[shot][0] * FPS)))
    else:  # two shots overlap here: a dissolve
        a, b = live[0], live[1]
        local_b = g - round(TIMES[b][0] * FPS)
        span = (TIMES[a][1] - TIMES[b][0]) * FPS
        picture = Image.blend(load(a, max(1, g - round(TIMES[a][0] * FPS))), load(b, max(1, local_b)), float((local_b - 0.5) / span))
    ff.stdin.write(finish(picture, W, VIGNETTE).tobytes())
    if g % 100 == 0:
        print("post", g, "/", end_frame, flush=True)
ff.stdin.close()
if ff.wait() != 0:
    raise RuntimeError("FFmpeg failed while assembling the picture")
print("WROTE", out, W, H, end_frame)
