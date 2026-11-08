"""Make the paper ground and the stamp's ink mask. The generator calls this if they're missing. Run from reel/."""
import pathlib

import numpy as np
from PIL import Image

out = pathlib.Path("assets/stills")
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(21)

# Paper: #F1EFEA with low grain and a faint dot grid.
W, H = 1080, 1920
img = np.ones((H, W, 3), dtype=np.float32) * np.array([241, 239, 234], dtype=np.float32)
img += rng.normal(0, 1.5, (H, W, 1))
yy, xx = np.mgrid[0:H, 0:W]
img[(((xx % 12) - 6) ** 2 + ((yy % 12) - 6) ** 2) <= 1.3] -= 7
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out / "paper.jpg", quality=92)

# Stamp grunge: an alpha mask with speckled gaps in the ink.
noise = np.array(Image.fromarray((rng.random((400, 800)) * 255).astype(np.uint8)), dtype=np.float32) / 255
coarse = np.array(Image.fromarray((rng.random((50, 100)) * 255).astype(np.uint8)).resize((800, 400), Image.BICUBIC), dtype=np.float32) / 255
rgba = np.zeros((400, 800, 4), dtype=np.uint8)
rgba[..., 3] = np.where(noise * 0.55 + coarse * 0.45 < 0.27, 0, 255).astype(np.uint8)
Image.fromarray(rgba).save(out / "grunge.png")
print("textures ok")
