"""Render one shot. ./reel shots runs this. By hand: ./reel blender <reel> tools/render_shot.py -- S01 [options]

Options:
  --stills a,b,c   local frames to render, as fractions 0..1 of the shot (default: whole shot)
  --percent P      resolution percentage (default 100)
  --samples N      Cycles samples (default 32)
  --out DIR        output directory (default reel/.cache/frames/<shot>)
  --from N         resume whole-shot render at local frame N
  --save-blend P   save an editable scene before rendering
  --no-render      build the scene and stop, to catch errors cheaply
"""
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots  # noqa: E402
import kit  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
name = args[0]


def opt(flag, default=None):
    return args[args.index(flag) + 1] if flag in args else default


stills = opt("--stills")
percent = int(opt("--percent", 100))
samples = int(opt("--samples", 32))
out = opt("--out", os.path.join(kit.CACHE, "frames", name))
start_from = int(opt("--from", 1))
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
n = shots.count(name)
sc = kit.setup_render(samples=samples, percent=percent, adaptive=0.025)
shots.ALL[name](n)
sc.frame_start = 1
sc.frame_end = n
if opt("--save-blend"):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt("--save-blend")), compress=True)
if "--no-render" in args:
    print("BUILT", name, n, flush=True)
    raise SystemExit(0)

targets = []
if stills:
    for token in stills.split(","):
        targets.append(max(1, min(n, round(1 + float(token) * (n - 1)))))
else:
    targets = list(range(start_from, n + 1))

t0 = time.time()
# Off: with persistent data, a shot turned black partway through a run of keyed material changes.
sc.render.use_persistent_data = False
for f in targets:
    path = os.path.join(out, f"{f:04d}.jpg")
    if os.path.exists(path) and os.path.getsize(path) > 0 and not stills:
        continue
    sc.frame_set(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"DONE {name} {f}/{n} {time.time() - t0:.1f}s", flush=True)
