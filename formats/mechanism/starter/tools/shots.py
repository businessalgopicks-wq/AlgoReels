"""One function per shot. Each builds its whole scene and keys everything from frame numbers, so it renders correctly at any frame.

Run through ./reel shots, which calls render_shot.py. The placeholder film is two meshing gears, there to show the shape of a shot:
the mechanism acts first, the camera moves to reveal it, and a graphic stays attached to the thing it explains. Replace all three
shots with your film's, and put its models in parts.py. Keep the helpers.
"""
import json
import math
import os

import bpy

import parts as P
import kit
from timeline import FPS, TIMES, count  # noqa: F401  render_shot.py uses count


def W(word, occ=0):
    """When a spoken word starts, from the narration's real timing."""
    words = json.load(open(os.path.join(kit.SOURCE, "voice/words.json")))
    hits = [w["s"] for w in words if w["w"].strip(",.!?:;").lower() == word.lower()]
    return hits[occ]


def clock(shot):
    """Turn absolute seconds into this shot's local frame numbers."""
    start = TIMES[shot][0]
    return lambda seconds: max(1, round((seconds - start) * FPS) + 1)


def look(blur=False):
    """The treatment the format was tuned on. Prove it on your own hardest frames, and keep it the same across every shot."""
    sc = bpy.context.scene
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.05
    sc.cycles.use_animated_seed = False
    sc.cycles.seed = 17
    sc.cycles.adaptive_threshold = 0.025
    sc.cycles.adaptive_min_samples = 8
    sc.render.use_motion_blur = blur
    sc.render.motion_blur_shutter = 0.28


# ---------------------------------------------------------------- the placeholder mechanism
def gear(name, teeth, radius, width, mat):
    """A spur gear standing upright, its axle along Y and its centre at the origin."""
    verts, faces = [], []
    step = 2 * math.pi / teeth
    root, tip = radius - 0.07, radius + 0.07
    outline = []
    for i in range(teeth):
        a = i * step
        outline += [(root, a - step * 0.27), (tip, a - step * 0.13), (tip, a + step * 0.13), (root, a + step * 0.27)]
    count_outline = len(outline)
    for y in (-width / 2, width / 2):
        verts += [(r * math.cos(a), y, r * math.sin(a)) for r, a in outline]
    for i in range(count_outline):
        j = (i + 1) % count_outline
        faces.append((i, j, j + count_outline, i + count_outline))
    verts += [(0, -width / 2, 0), (0, width / 2, 0)]
    for i in range(count_outline):
        j = (i + 1) % count_outline
        faces.append((2 * count_outline, j, i))
        faces.append((2 * count_outline + 1, i + count_outline, j + count_outline))
    return P.from_data(name, verts, faces, [mat], split=32)


def spin(obj, frames, turns, phase=0.0):
    """Rotate about the axle at a constant rate. Linear keys, so meshing teeth never drift apart."""
    obj.rotation_mode = "XYZ"
    for frame, value in ((1, phase), (frames, phase + turns * 360)):
        P.key_rot(obj, frame, (0, value, 0))
    kit.set_interp(obj, "LINEAR")


def gear_pair(frames):
    """A small gear driving a large one, the large one at half the speed. Returns the point where their teeth meet."""
    steel = P.metal("steel", rough=0.3)
    brass = P.metal("brass", color=(0.72, 0.5, 0.2), rough=0.34)
    small_r, large_r = 0.55, 1.10
    z = large_r + 0.12
    small = gear("small gear", 12, small_r, 0.32, steel)
    large = gear("large gear", 24, large_r, 0.32, brass)
    small.location = (-small_r, 0, z)
    large.location = (large_r, 0, z)
    turns = frames / FPS * 0.5
    spin(small, frames, turns)
    spin(large, frames, -turns / 2, phase=180 / 24)  # half a tooth out of phase, so a tooth sits in a gap
    return (0.0, 0.0, z)


# ---------------------------------------------------------------- shots
def S01(n):
    """The action first: the teeth already working, close enough to see them touch."""
    look()
    P.studio()
    contact = gear_pair(n)
    glow = P.soft_disc("contact", P.HIGHLIGHT, 3.0, 0.26)
    glow.location = (contact[0], -0.17, contact[2])
    glow.rotation_euler = (math.radians(90), 0, 0)
    cam = kit.Cam(lens=48, fstop=1.6)
    cam.key(1, (-0.5, -3.4, contact[2] + 0.5), contact)
    cam.key(n, (-0.1, -2.5, contact[2] + 0.2), contact)
    kit.ease_all(cam.obj)


def S02(n):
    """Pull back to the whole relation, with arrows that move with the parts."""
    look()
    P.studio()
    contact = gear_pair(n)
    red = kit.emission("arrow red", P.ALERT, 2.0)
    arrow = P.arrow("direction", red)
    arrow.location = (0.0, -0.3, contact[2] + 0.2)
    arrow.rotation_euler = (0, math.radians(90), 0)
    P.key_scale(arrow, 1, 0.001)
    P.key_scale(arrow, 8, 0.001)
    P.key_scale(arrow, 14, 0.6)
    cam = kit.Cam(lens=34, fstop=4.0)
    cam.key(1, (0.2, -5.0, contact[2] + 1.0), (0.2, 0, contact[2]))
    cam.key(n, (0.5, -6.2, contact[2] + 1.5), (0.5, 0, contact[2]))
    kit.ease_all(cam.obj)


def S03(n):
    """The consequence: come round to the large gear and hold long enough to read it."""
    look()
    P.studio()
    contact = gear_pair(n)
    white = kit.emission("label white", (1, 1, 1), 2.2)
    cam = kit.Cam(lens=38, fstop=2.8)
    target = (1.1, 0, contact[2])
    cam.key(1, (2.6, -4.2, contact[2] + 0.9), target)
    cam.key(n, (1.6, -3.5, contact[2] + 0.5), target)
    kit.ease_all(cam.obj)
    label = P.label("half the speed", (1.1, -0.3, contact[2] + 1.5), 0.24, white, cam)
    P.key_scale(label, 1, 0.001)
    P.key_scale(label, 18, 0.001)
    P.key_scale(label, 24, 1.0)


ALL = {"S01": S01, "S02": S02, "S03": S03}
