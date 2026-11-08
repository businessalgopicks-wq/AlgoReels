"""Shared Blender helpers: render setup, lights, cameras and materials."""
import math
import os

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

# The reel's folder. ./reel sets this, and it falls back to where this file sits: <reel>/reel/tools/kit.py
ROOT = os.environ.get("REEL_ROOT") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "reel/.cache")
SOURCE = os.path.join(ROOT, "assets/source")
FPS = 30


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def setup_render(samples=64, percent=100, mblur=False, shutter=0.5, denoise=True, adaptive=0.02):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = dev.type == "METAL"
    cy = sc.cycles
    cy.device = "GPU"
    cy.samples = samples
    cy.use_adaptive_sampling = adaptive > 0
    if adaptive > 0:
        cy.adaptive_threshold = adaptive
    cy.use_denoising = denoise
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    cy.max_bounces = 8
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.volume_bounces = 0
    cy.transparent_max_bounces = 12
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.6
    cy.sample_clamp_indirect = 6.0
    cy.sample_clamp_direct = 0.0
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = percent
    sc.render.fps = FPS
    sc.render.use_motion_blur = mblur
    sc.render.motion_blur_shutter = shutter
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 96
    sc.render.film_transparent = False
    return sc


def world_color(rgb, strength=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("world")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*rgb, 1)
    bg.inputs[1].default_value = strength
    sc.world = w
    return w


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def look_rot(frm, to, roll=0.0):
    q = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y")
    if roll:
        q = q @ Quaternion((0, 0, 1), math.radians(roll))
    return q


def area_light(name, energy, loc, target, size=1.0, color=(1, 1, 1), size_y=None, shape="RECTANGLE"):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = energy
    light.color = color
    light.shape = shape
    light.size = size
    if size_y:
        light.size_y = size_y
    obj = bpy.data.objects.new(name, light)
    link(obj)
    obj.location = loc
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = look_rot(loc, target)
    return obj


def point_light(name, energy, loc, color=(1, 1, 1), radius=0.1):
    light = bpy.data.lights.new(name, "POINT")
    light.energy = energy
    light.color = color
    light.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, light)
    link(obj)
    obj.location = loc
    return obj


def sun_light(name, energy, direction, color=(1, 1, 1), angle=2.0):
    light = bpy.data.lights.new(name, "SUN")
    light.energy = energy
    light.color = color
    light.angle = math.radians(angle)
    obj = bpy.data.objects.new(name, light)
    link(obj)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector(direction).to_track_quat("-Z", "Y")
    return obj


class Cam:
    """A camera driven by explicit (frame, location, target, lens[, roll]) keys, with depth of field."""

    def __init__(self, name="cam", lens=28.0, fstop=4.0, sensor=36.0):
        self.data = bpy.data.cameras.new(name)
        self.data.lens = lens
        self.data.sensor_width = sensor
        self.data.sensor_fit = "VERTICAL"
        self.data.clip_start = 0.01
        self.data.clip_end = 400
        self.data.dof.use_dof = True
        self.data.dof.aperture_fstop = fstop
        self.obj = bpy.data.objects.new(name, self.data)
        link(self.obj)
        self.obj.rotation_mode = "QUATERNION"
        bpy.context.scene.camera = self.obj

    def key(self, frame, loc, target, lens=None, roll=0.0, focus=None):
        self.obj.location = loc
        self.obj.rotation_quaternion = look_rot(loc, target, roll)
        self.obj.keyframe_insert("location", frame=frame)
        self.obj.keyframe_insert("rotation_quaternion", frame=frame)
        if lens:
            self.data.lens = lens
            self.data.keyframe_insert("lens", frame=frame)
        dist = (Vector(focus if focus else target) - Vector(loc)).length
        self.data.dof.focus_distance = dist
        self.data.dof.keyframe_insert("focus_distance", frame=frame)


def ease_all(obj_or_data, kind="BEZIER"):
    ad = obj_or_data.animation_data
    if not ad or not ad.action:
        return
    for fc in fcurves_of(ad):
        for kp in fc.keyframe_points:
            kp.interpolation = kind


def fcurves_of(ad):
    """Blender 5 stores fcurves in action layers and strips."""
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def set_interp(obj_or_data, kind):
    ad = getattr(obj_or_data, "animation_data", None)
    if ad and ad.action:
        for fc in fcurves_of(ad):
            for kp in fc.keyframe_points:
                kp.interpolation = kind


# --------------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------------

def principled(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, spec=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    return mat


def emission(name, color, strength=5.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*color, 1)
    e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return mat


def image_node(nt, path, non_color=False):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    return node
