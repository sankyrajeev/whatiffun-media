"""3D (Cycles) 'ONE RULE: Every step grows a smaller crystal.' A bismuth hopper crystal grows step by step out of a
mirror pool of molten metal in an iron dish on a walnut desk; every new step sprouts a smaller crystal at its corner;
oxide colours bloom (gold -> magenta -> blue -> teal) as each bar ages.
Usage: python3 scene.py START END [STEP]   (renders frames to $OUT/f_XXXX.png)"""
import bpy, math, sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion import *

OUT = os.environ.get("OUT", "/home/claude/bi/frames")
PCT = int(os.environ.get("PCT", 50)); SAMPLES = int(os.environ.get("SAMPLES", 6))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, PCT
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 4; sc.cycles.transmission_bounces = 1
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .05
sc.cycles.blur_glossy = 1.0
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"

def mat(name, base, rough=.3, metal=0.0, coat=0.0, emit=None, aniso=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if aniso: b.inputs["Anisotropic"].default_value = aniso
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    return m

w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
wn = w.node_tree; bgc = wn.nodes["Background"]; bgc.inputs["Color"].default_value = (0.010, 0.008, 0.006, 1)
bg2 = wn.nodes.new("ShaderNodeBackground"); bg2.inputs["Color"].default_value = (0.085, 0.068, 0.052, 1)   # seen only in reflections
grd = wn.nodes.new("ShaderNodeTexGradient"); grd.gradient_type = "SPHERICAL"
lp = wn.nodes.new("ShaderNodeLightPath"); mx_ = wn.nodes.new("ShaderNodeMixShader")
wn.links.new(lp.outputs["Is Glossy Ray"], mx_.inputs[0]); wn.links.new(bgc.outputs[0], mx_.inputs[1]); wn.links.new(bg2.outputs[0], mx_.inputs[2])
wn.links.new(mx_.outputs[0], wn.nodes["World Output"].inputs["Surface"])

# walnut desk
desk = bpy.data.materials.new("walnut"); desk.use_nodes = True
nt = desk.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = .42; b.inputs["Coat Weight"].default_value = .5; b.inputs["Coat Roughness"].default_value = .08
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (.12, 3.2, 1); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 3.0; n1.inputs["Detail"].default_value = 12
n1.inputs["Roughness"].default_value = .62; n1.inputs["Distortion"].default_value = .35
nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); E = cr.color_ramp.elements
E[0].position = .3; E[0].color = (0.022, 0.010, 0.005, 1); E[1].position = .72; E[1].color = (0.10, 0.048, 0.022, 1)
nt.links.new(n1.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0)); bpy.context.object.data.materials.append(desk)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 18, 10), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("wall", (0.022, 0.018, 0.015), rough=.85))

# a small pewter seed puck on the desk
pew = mat("pewter", (0.55, 0.53, 0.52), rough=.3, metal=1, aniso=.4)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=.42, depth=.04, location=(0, 0, .0))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(pew)

# bismuth bars: one point cloud, a bevelled cube instanced on every point (scale/rotation/film from attributes)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -20)); proto = bpy.context.object
bv = proto.modifiers.new("bv", "BEVEL"); bv.width = .06; bv.segments = 2; bv.limit_method = "NONE"
bpy.ops.object.modifier_apply(modifier="bv"); proto.hide_render = True; proto.hide_viewport = True
bi = bpy.data.materials.new("bismuth"); bi.use_nodes = True; bb = bi.node_tree.nodes["Principled BSDF"]
bb.inputs["Base Color"].default_value = (0.80, 0.76, 0.78, 1); bb.inputs["Metallic"].default_value = 1
bb.inputs["Roughness"].default_value = .11; bb.inputs["Thin Film IOR"].default_value = 1.6
at = bi.node_tree.nodes.new("ShaderNodeAttribute"); at.attribute_type = "INSTANCER"; at.attribute_name = "film"
bi.node_tree.links.new(at.outputs["Fac"], bb.inputs["Thin Film Thickness"])
rmp = bi.node_tree.nodes.new("ShaderNodeMapRange"); rmp.inputs["From Min"].default_value = 60; rmp.inputs["From Max"].default_value = 450
bi.node_tree.links.new(at.outputs["Fac"], rmp.inputs["Value"])
ox = bi.node_tree.nodes.new("ShaderNodeValToRGB"); el = ox.color_ramp.elements
pal = [(0.0, (0.86, 0.82, 0.78)), (.18, (0.98, 0.74, 0.30)), (.38, (0.92, 0.28, 0.62)), (.56, (0.36, 0.34, 1.0)),
       (.74, (0.20, 0.82, 0.86)), (1.0, (0.66, 0.92, 0.36))]
el[0].position, el[0].color = pal[0][0], (*pal[0][1], 1); el[1].position, el[1].color = pal[-1][0], (*pal[-1][1], 1)
for p, col in pal[1:-1]:
    e = el.new(p); e.color = (*col, 1)
bi.node_tree.links.new(rmp.outputs["Result"], ox.inputs["Fac"]); bi.node_tree.links.new(ox.outputs["Color"], bb.inputs["Base Color"])

me = bpy.data.meshes.new("pts"); me.vertices.add(NB)
me.attributes.new("scl", "FLOAT_VECTOR", "POINT"); me.attributes.new("rot", "FLOAT_VECTOR", "POINT")
me.attributes.new("film", "FLOAT", "POINT")
pts = bpy.data.objects.new("pts", me); sc.collection.objects.link(pts)
gn = bpy.data.node_groups.new("inst", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N = gn.nodes; Lk = gn.links
gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = proto; oi.transform_space = "ORIGINAL"
sm = N.new("GeometryNodeSetShadeSmooth"); Lk.new(oi.outputs["Geometry"], sm.inputs["Geometry"])
sm.inputs["Shade Smooth"].default_value = False
a_s = N.new("GeometryNodeInputNamedAttribute"); a_s.data_type = "FLOAT_VECTOR"; a_s.inputs["Name"].default_value = "scl"
a_r = N.new("GeometryNodeInputNamedAttribute"); a_r.data_type = "FLOAT_VECTOR"; a_r.inputs["Name"].default_value = "rot"
e2r = N.new("FunctionNodeEulerToRotation"); Lk.new(a_r.outputs["Attribute"], e2r.inputs["Euler"])
iop = N.new("GeometryNodeInstanceOnPoints")
Lk.new(gi.outputs["Geometry"], iop.inputs["Points"]); Lk.new(sm.outputs["Geometry"], iop.inputs["Instance"])
Lk.new(a_s.outputs["Attribute"], iop.inputs["Scale"]); Lk.new(e2r.outputs["Rotation"], iop.inputs["Rotation"])
setm = N.new("GeometryNodeSetMaterial"); Lk.new(iop.outputs["Instances"], setm.inputs["Geometry"])
setm.inputs["Material"].default_value = bi
Lk.new(setm.outputs["Geometry"], go.inputs["Geometry"])
mod = pts.modifiers.new("inst", "NODES"); mod.node_group = gn
me.attributes["rot"].data.foreach_set("vector", EULERS.astype(np.float32).ravel())

def area(loc, rot, size, power, col, sy=None):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    o = bpy.context.object; L = o.data; L.energy = power; L.color = col
    if sy: L.shape = "RECTANGLE"; L.size = size; L.size_y = sy
    else: L.size = size
    return o
key = area((-4.0, -4.5, 7.5), (math.radians(40), 0, math.radians(-40)), 4.5, 900, (1, .94, .87))
rim = area((4.0, 5.0, 4.5), (math.radians(-62), 0, math.radians(140)), 3.5, 700, (1, .70, .40))
fill = area((5.0, -3.5, 2.2), (math.radians(78), 0, math.radians(55)), 4, 140, (.72, .82, 1))
def strip(loc, rot, sx, sy, strength, col):   # soft-box strips: only seen in reflections
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object
    o.scale = (sx, sy, 1); o.data.materials.append(mat("strip", (0, 0, 0), emit=(col, strength)))
    o.visible_camera = False; o.visible_shadow = False; return o
strip((-5.5, 1.0, 3.0), (0, math.radians(-75), 0), 1.0, 7.0, 4.0, (1, .92, .82))
strip((5.5, 2.0, 3.2), (0, math.radians(75), 0), .8, 7.0, 3.0, (1, .78, .55))
strip((0, 6.0, 5.5), (math.radians(-60), 0, 0), 7.0, .9, 2.5, (1, .88, .75))

bpy.ops.object.camera_add(); cam = bpy.context.object; cam.data.lens = 50; sc.camera = cam
bpy.ops.object.empty_add(); tgt = bpy.context.object
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

def smooth(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
CAMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campath.npy")
CP = np.load(CAMP) if os.path.exists(CAMP) else None
def cam_at(f, path=None):
    u = f / 479                                     # orbit timed on the first 480 frames, keeps gliding after
    az = math.radians(-30 + 55 * u)                 # slow orbit
    p = path if path is not None else (CP[min(f, len(CP) - 1)] if CP is not None else (.0, .0, .45, 6.0))
    tx, ty, tz, dist = p[:4]; cam.data.shift_x = p[4] if len(p) > 4 else 0.0
    el = math.radians(34 + 20 * smooth(u / .8))
    cam.location = (tx + dist * math.cos(el) * math.sin(az), ty - dist * math.cos(el) * math.cos(az), tz + dist * math.sin(el))
    tgt.location = (tx, ty, tz)
    g = smooth((f - 390) / 90)                      # key light glides at the end: a glint sweep
    key.rotation_euler = (math.radians(40), 0, math.radians(-40 + 45 * g))

def place(f):
    pos, scl, film = state(f)
    me.vertices.foreach_set("co", pos.astype(np.float32).ravel())
    me.attributes["scl"].data.foreach_set("vector", scl.astype(np.float32).ravel())
    me.attributes["film"].data.foreach_set("value", film.astype(np.float32))
    me.update(); cam_at(f)

if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2]); st = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    os.makedirs(OUT, exist_ok=True)
    for f in range(a, b, st):
        out = f"{OUT}/f_{f:04d}.png"
        if os.path.exists(out): continue
        place(f)
        sc.render.filepath = out
        t = time.time(); bpy.ops.render.render(write_still=True)
        print(f"frame {f} {time.time() - t:.1f}s", flush=True)
