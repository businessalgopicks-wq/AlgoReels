"""Every-frame motion audit. Runs inside Blender on saved scenes, after --.

./reel blender <reel> tools/audit_objects.py -- ../qa/motion.json scenes/S01.blend scenes/S02.blend ...

This walks every frame of every saved shot and
measures each animated object's world position and rotation against the frame before it, so a one-frame jump shows up in the numbers.
Fast authored action can exceed a screening limit. Each flagged object is then looked at in the rendered strips.
"""
import json
import math
import sys
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
out, scenes = Path(args[0]), args[1:]
report = {"scenes": {}, "note": "Largest frame to frame change per shot, in scene units of world position and in degrees."}
for path in scenes:
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    moving = [o for o in sc.objects if o.animation_data or (o.parent and o.parent.animation_data) or (o.parent and o.parent.parent and o.parent.parent.animation_data)]
    prev, rows = {}, {}
    frames = 0
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
        frames += 1
        for o in moving:
            m = o.matrix_world
            loc, rot = m.translation.copy(), m.to_quaternion()
            if o.name in prev:
                ploc, prot = prev[o.name]
                d = (loc - ploc).length
                a = math.degrees(prot.rotation_difference(rot).angle)
                r = rows.setdefault(o.name, {"max_step": 0.0, "step_frame": f, "max_rotation": 0.0, "rotation_frame": f})
                if d > r["max_step"]:
                    r.update(max_step=round(d, 4), step_frame=f)
                if a > r["max_rotation"]:
                    r.update(max_rotation=round(a, 2), rotation_frame=f)
            prev[o.name] = (loc, rot)
    top = sorted(rows.items(), key=lambda kv: -kv[1]["max_step"])[:4]
    spin = sorted(rows.items(), key=lambda kv: -kv[1]["max_rotation"])[:3]
    report["scenes"][Path(path).stem] = {"frames": frames, "objects_checked": len(moving), "largest_steps": dict(top), "largest_rotations": dict(spin)}
    print(Path(path).stem, frames, len(moving), flush=True)
out.write_text(json.dumps(report, indent=1) + "\n")
print("WROTE", out)
