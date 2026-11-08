#!/usr/bin/env python3
"""Assemble the final frame set from render revisions, and record where every shot's frames came from.

Run from reel/ after a correction:  ../../../.venv/bin/python tools/merge_revisions.py
Later revisions win. Frames are hard linked, not re-encoded, so a reused frame stays byte-identical.
Writes .cache/frames_final/ and ../qa/render-origins.json. Then:  ./reel assemble <reel> .cache/frames_final
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timeline import FPS, TIMES, count  # noqa: E402, F401

REVISIONS = sorted((str(p) for p in Path(".cache").glob("picture-v*") if p.is_dir()), key=lambda r: int(r.rsplit("v", 1)[1]))
FINAL = Path(".cache/frames_final")
if not REVISIONS:
    raise SystemExit("No .cache/picture-v* folders here. Run this from reel/.")
if FINAL.exists():
    shutil.rmtree(FINAL)
FINAL.mkdir(parents=True)
origins = {"revisions": {rev: json.loads((Path(rev) / "render-settings.json").read_text()) for rev in REVISIONS}, "shots": {}}
total = 0
for shot in sorted(TIMES):
    frames = count(shot)
    source = next((rev for rev in reversed(REVISIONS) if len(list((Path(rev) / shot).glob("*.jpg"))) == frames), None)
    if source is None:
        raise SystemExit(f"No revision holds all {frames} frames of {shot}.")
    (FINAL / shot).mkdir()
    digest = hashlib.sha256()
    for f in range(1, frames + 1):
        src = Path(source) / shot / f"{f:04d}.jpg"
        with Image.open(src) as im:
            if im.size != (1080, 1920):
                raise SystemExit(f"{src} is {im.size}, not 1080 x 1920.")
            im.verify()
        os.link(src, FINAL / shot / src.name)
        digest.update(src.read_bytes())
    origins["shots"][shot] = {"source": source, "frames": frames, "time": list(TIMES[shot]), "sha256_of_frames": digest.hexdigest()}
    total += frames
origins["frames_total"] = total
Path("../qa/render-origins.json").write_text(json.dumps(origins, indent=2) + "\n")
print("frames", total, {s: v["source"].rsplit("/", 1)[1] for s, v in origins["shots"].items()})
