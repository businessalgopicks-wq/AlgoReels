"""Render shots in Blender with a frozen source, bounded retries and exact frame checks. Run through ./reel shots.

./reel shots <reel> -- --out ../.cache/look-v1 --percent 50 --samples 24 --stills 0,.5,1 --workers 2
./reel shots <reel> -- --out ../.cache/picture-v1 --percent 100 --samples 32 --workers 2 --save-scenes
./reel shots <reel> -- S02 S03 --out ../.cache/picture-v2

An output folder belongs to one source revision and one quality setting. To change either, use a new folder, and merge afterwards with
tools/merge_revisions.py. A stopped run resumes by rendering only the frames that are missing or invalid.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # the reel's folder
sys.path.insert(0, str(HERE))
import timeline  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("shots", nargs="*")
parser.add_argument("--out", required=True, type=Path)
parser.add_argument("--percent", default=100, type=int)
parser.add_argument("--samples", default=32, type=int)
parser.add_argument("--workers", default=2, type=int, choices=(1, 2))
parser.add_argument("--stills")
parser.add_argument("--save-scenes", action="store_true")
args = parser.parse_args()
args.out = args.out.resolve()
args.out.mkdir(parents=True, exist_ok=True)
selected = args.shots or sorted(timeline.TIMES)
unknown = [s for s in selected if s not in timeline.TIMES]
if unknown:
    raise SystemExit(f"Not in timeline.py: {unknown}")

# Every generator file and the word timing. Extend this with external assets when a film depends on them.
sources = sorted(HERE.glob("*.py")) + [ROOT / "assets/source/voice/words.json"]
source_hash = hashlib.sha256(b"".join(p.read_bytes() for p in sources if p.exists())).hexdigest()
settings = dict(source_hash=source_hash, percent=args.percent, samples=args.samples, stills=args.stills)
manifest = args.out / "render-settings.json"
if manifest.exists() and json.loads(manifest.read_text()) != settings:
    raise SystemExit("This output folder holds another source revision or quality setting. Use a fresh --out folder.")
manifest.write_text(json.dumps(settings, indent=2) + "\n")

env = os.environ.copy()
env["REEL_ROOT"] = str(ROOT)
env.setdefault("BLENDER_USER_RESOURCES", str(ROOT.parents[1] / ".cache/blender-profile"))
Path(env["BLENDER_USER_RESOURCES"]).mkdir(parents=True, exist_ok=True)
blender = next((b for b in (env.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender")) if b and Path(b).exists()), None)
if not blender:
    raise SystemExit("Blender isn't installed. On a Mac: brew install --cask blender")
size = (1080 * args.percent // 100, 1920 * args.percent // 100)


def frames(shot):
    n = timeline.count(shot)
    if args.stills:
        return [max(1, min(n, round(1 + float(x) * (n - 1)))) for x in args.stills.split(",")]
    return list(range(1, n + 1))


def missing(shot):
    result = []
    for f in frames(shot):
        path = args.out / shot / f"{f:04d}.jpg"
        try:
            with Image.open(path) as im:
                if im.size != size:
                    raise ValueError("wrong resolution")
                im.verify()
        except (OSError, ValueError):
            result.append(f)
    return result


def render(shot):
    folder = args.out / shot
    folder.mkdir(exist_ok=True)
    start = time.monotonic()
    for attempt in range(1, 5):
        todo = missing(shot)
        if not todo:
            break
        for f in todo:  # remove only unusable outputs before resuming
            path = folder / f"{f:04d}.jpg"
            if path.exists():
                path.unlink()
        cmd = [blender, "-b", "--python", str(HERE / "render_shot.py"), "--", shot, "--percent", str(args.percent), "--samples", str(args.samples), "--out", str(folder)]
        if args.stills:
            cmd += ["--stills", args.stills]
        if args.save_scenes:
            scenes = ROOT / "reel/scenes"
            scenes.mkdir(exist_ok=True)
            cmd += ["--save-blend", str(scenes / f"{shot}.blend")]
        print(f"START {shot} attempt={attempt} remaining={len(todo)}", flush=True)
        with (folder / "render.log").open("a") as log:
            run = subprocess.run(cmd, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT)
        if run.returncode not in (0, -6, -11):  # Metal startup sometimes aborts, which the retry covers
            print(f"ERROR {shot} exit={run.returncode}. See {folder / 'render.log'}", flush=True)
    todo = missing(shot)
    if todo:
        raise RuntimeError(f"{shot}: {len(todo)} frames missing after bounded retries. See {folder / 'render.log'}")
    print(f"DONE {shot} frames={len(frames(shot))} seconds={time.monotonic() - start:.1f}", flush=True)
    return shot


with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
    results = list(pool.map(render, selected))
report = dict(settings=settings, shots=results, frame_count=sum(len(frames(s)) for s in selected), dimensions=size)
(args.out / "complete.json").write_text(json.dumps(report, indent=2) + "\n")
print("COMPLETE", json.dumps(report), flush=True)
