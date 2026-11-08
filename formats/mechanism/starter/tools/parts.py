"""Procedural parts: materials, meshes from data, lathes, boxes, tubes, arrows, labels, glows and the turquoise studio.

Add this film's own parts at the bottom. Everything is original geometry written here, with no logos or photographs.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import kit

TAU = 2 * math.pi


def lin(hex_color):
    """A hex colour as linear RGB."""
    h = hex_color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


STUDIO, FLOOR, ALERT, HIGHLIGHT, POSITIVE = lin("#28B0C8"), lin("#2FBCD3"), lin("#E3262B"), lin("#E9F54A"), lin("#72D869")


# ---------------------------------------------------------------- materials
def metal(name, color=(0.62, 0.63, 0.65), rough=0.33, bump=0.0006, scale=900.0):
    mat = kit.principled(name, color=color, rough=rough, metal=1.0)
    if bump:
        nt = mat.node_tree
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = scale
        noise.inputs["Detail"].default_value = 4.0
        bmp = nt.nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = 0.25
        bmp.inputs["Distance"].default_value = bump
        nt.links.new(noise.outputs["Fac"], bmp.inputs["Height"])
        bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        nt.links.new(bmp.outputs["Normal"], bs.inputs["Normal"])
        # Wear: broad, soft changes in shine, so the steel doesn't read as a perfect mirror
        wear = nt.nodes.new("ShaderNodeTexNoise")
        wear.inputs["Scale"].default_value = 11.0
        wear.inputs["Detail"].default_value = 3.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.36
        ramp.color_ramp.elements[0].color = (rough * 0.88, rough * 0.88, rough * 0.88, 1)
        ramp.color_ramp.elements[1].position = 0.66
        ramp.color_ramp.elements[1].color = (min(rough * 1.18, 1), min(rough * 1.18, 1), min(rough * 1.18, 1), 1)
        nt.links.new(wear.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bs.inputs["Roughness"])
    return mat


def paint(name, color, rough=0.42, spec=0.45):
    return kit.principled(name, color=color, rough=rough, metal=0.0, spec=spec)


def glass_alpha(mat, keys):
    """Key a material's alpha, for a panel that goes see-through. keys: [(frame, alpha)]."""
    bs = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for frame, value in keys:
        bs.inputs["Alpha"].default_value = value
        bs.inputs["Alpha"].keyframe_insert("default_value", frame=frame)


def key_emission(mat, keys):
    """Key an emission material's strength. keys: [(frame, strength)]."""
    node = next(n for n in mat.node_tree.nodes if n.type == "EMISSION")
    for frame, value in keys:
        node.inputs["Strength"].default_value = value
        node.inputs["Strength"].keyframe_insert("default_value", frame=frame)


def key_color_mix(mat, keys):
    """Key a principled material's base colour. keys: [(frame, rgb)]."""
    bs = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for frame, rgb in keys:
        bs.inputs["Base Color"].default_value = (*rgb, 1)
        bs.inputs["Base Color"].keyframe_insert("default_value", frame=frame)


# ---------------------------------------------------------------- mesh helpers
def from_data(name, verts, faces, mats, mat_idx=None, split=38.0, bevel=0.0, seg=2):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if mat_idx:
        bm.faces.ensure_lookup_table()
        for i, f in enumerate(bm.faces):
            f.material_index = mat_idx[i]
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    for mat in mats:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    kit.link(obj)
    if bevel > 0:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = seg
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(35)
    if split:
        mod = obj.modifiers.new("split", "EDGE_SPLIT")
        mod.split_angle = math.radians(split)
    return obj


def lathe(name, profile, mats, seg=128, arc=None, closed=True, split=38.0):
    """Spin a profile of (radius, height along Y) around the Y axis. arc=(a0, a1) in radians leaves a section with capped ends."""
    full = arc is None
    a0, a1 = (0.0, TAU) if full else arc
    rows = seg if full else seg + 1
    P = len(profile)
    verts = []
    for i in range(rows):
        a = a0 + (a1 - a0) * i / seg
        for r, h in profile:
            verts.append((r * math.cos(a), h, r * math.sin(a)))
    faces, idx = [], []
    for i in range(seg):
        i2 = (i + 1) % rows
        for j in range(P if closed else P - 1):
            j2 = (j + 1) % P
            faces.append((i * P + j, i2 * P + j, i2 * P + j2, i * P + j2))
            idx.append(0)
    if not full:
        faces.append(tuple(range(P)))
        idx.append(1 if len(mats) > 1 else 0)
        faces.append(tuple(seg * P + j for j in range(P)))
        idx.append(1 if len(mats) > 1 else 0)
    return from_data(name, verts, faces, mats, idx, split=split)


def box(name, size, loc, mats, bevel=0.0, seg=2, split=38.0):
    sx, sy, sz = (s / 2 for s in size)
    x, y, z = loc
    verts = [(x + a * sx, y + b * sy, z + c * sz) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return from_data(name, verts, faces, mats, split=split, bevel=bevel, seg=seg)


def parent_keep(child, parent):
    """Parent while keeping the child's world position, given the parent's pose at the time of the call."""
    bpy.context.view_layer.update()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def empty(name, loc=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    kit.link(obj)
    obj.location = loc
    return obj


def tube(name, points, mat, radius, closed=False):
    """A polyline tube that can grow, by keying its curve's bevel_factor_end."""
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 2
    data.use_fill_caps = True
    data.bevel_factor_mapping_start = "SPLINE"
    data.bevel_factor_mapping_end = "SPLINE"
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    spline.use_cyclic_u = closed
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    kit.link(obj)
    return obj


def key_hide(obj, frame, hidden):
    obj.hide_render = hidden
    obj.keyframe_insert("hide_render", frame=frame)


def grow(curve_obj, keys):
    """keys: [(frame, end factor)]."""
    for frame, value in keys:
        curve_obj.data.bevel_factor_end = value
        curve_obj.data.keyframe_insert("bevel_factor_end", frame=frame)


def arrow(name, mat):
    """One unit long, along +Z, with its base at the origin."""
    prof = [(0.0001, 0), (0.055, 0), (0.055, 0.68), (0.14, 0.68), (0.0001, 1.0)]
    obj = lathe(name, prof, [mat], seg=32, closed=False, split=38)
    obj.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    # lathe builds along +Y; the rotation above sends +Y to +Z
    obj.data.update()
    return obj


def key_loc(obj, frame, loc):
    obj.location = loc
    obj.keyframe_insert("location", frame=frame)


def key_rot(obj, frame, euler_deg):
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = tuple(math.radians(a) for a in euler_deg)
    obj.keyframe_insert("rotation_euler", frame=frame)


def key_scale(obj, frame, s):
    obj.scale = (s, s, s) if isinstance(s, (int, float)) else s
    obj.keyframe_insert("scale", frame=frame)


def label(text, loc, size, mat, cam=None, align="CENTER"):
    """Flat text in the scene, turned to the camera."""
    data = bpy.data.curves.new(text[:12], "FONT")
    data.body = text
    data.size = size
    data.align_x = align
    data.align_y = "CENTER"
    font = os.path.join(kit.SOURCE, "fonts/OpenSans-Bold.ttf")
    if os.path.exists(font):
        data.font = bpy.data.fonts.load(font, check_existing=True)
    data.materials.append(mat)
    obj = bpy.data.objects.new("label " + text[:12], data)
    kit.link(obj)
    obj.location = loc
    if cam is not None:
        con = obj.constraints.new("TRACK_TO")
        con.target = cam.obj
        con.track_axis = "TRACK_Z"
        con.up_axis = "UP_Y"
    return obj


def soft_disc(name, color, strength=6.0, radius=0.2):
    """A round glow that fades to nothing at its edge, for a contact point. Lies flat by default."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    nt = mat.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    length = nt.nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], length.inputs[0])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.interpolation_type = "SMOOTHSTEP"
    nt.links.new(length.outputs["Value"], ramp.inputs["Value"])
    ramp.inputs["From Min"].default_value = radius * 0.25
    ramp.inputs["From Max"].default_value = radius
    ramp.inputs["To Min"].default_value = 1.0
    ramp.inputs["To Max"].default_value = 0.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color, 1)
    em.inputs[1].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    seg = 40
    verts = [(0, 0, 0)] + [(radius * math.cos(TAU * i / seg), radius * math.sin(TAU * i / seg), 0) for i in range(seg)]
    faces = [(0, i + 1, (i + 1) % seg + 1) for i in range(seg)]
    return from_data(name, verts, faces, [mat], split=0)


def studio():
    """The turquoise studio, floor at z = 0, lit by suns so the light is the same wherever the subject moves to."""
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    path = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value = (0.58, 0.60, 0.62, 1)  # what light and reflections see: a neutral room
    mix.inputs[2].default_value = (*(c * 1.34 for c in FLOOR), 1)  # what the camera sees, matched to the lit floor so the horizon melts away
    nt.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(mix.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.88
    bpy.context.scene.world = world
    mat = paint("studio floor", FLOOR, rough=0.62, spec=0.25)
    tree = mat.node_tree
    bsdf = tree.nodes["Principled BSDF"]
    outn = next(n for n in tree.nodes if n.type == "OUTPUT_MATERIAL")
    camd = tree.nodes.new("ShaderNodeCameraData")
    fade = tree.nodes.new("ShaderNodeMapRange")
    fade.interpolation_type = "SMOOTHSTEP"
    fade.inputs["From Min"].default_value = 9.0
    fade.inputs["From Max"].default_value = 26.0
    tree.links.new(camd.outputs["View Distance"], fade.inputs["Value"])
    far = tree.nodes.new("ShaderNodeEmission")
    far.inputs[0].default_value = (*(c * 1.34 for c in FLOOR), 1)
    far.inputs[1].default_value = 0.88
    mixs = tree.nodes.new("ShaderNodeMixShader")
    tree.links.new(fade.outputs[0], mixs.inputs[0])
    tree.links.new(bsdf.outputs[0], mixs.inputs[1])
    tree.links.new(far.outputs[0], mixs.inputs[2])
    tree.links.new(mixs.outputs[0], outn.inputs[0])
    size = 400.0
    verts = [(-size, -size, 0), (size, -size, 0), (size, size, 0), (-size, size, 0)]
    floor = from_data("floor", verts, [(0, 1, 2, 3)], [mat], split=0)
    kit.sun_light("key", 2.3, (0.38, 0.62, -0.78), color=(1.0, 0.96, 0.91), angle=24.0)
    kit.sun_light("rim", 0.9, (-0.5, -0.65, -0.45), color=(0.93, 0.98, 1.0), angle=30.0)
    return floor
