"""3D (Cycles) version of 'Every bounce splits it in two': the 2D sim drives glossy marbles on a walnut
tray on a pedestal; when gravity kicks in the tray tilts and the marbles roll to the low side.
Usage: python3 split3d.py START END   (renders frames [START, END) to frames/f_XXXX.png)"""
import bpy, math, pickle, sys, os, time, colorsys
import numpy as np

d = pickle.load(open("/home/claude/notes/split.pkl", "rb"))
FR, RF, GRAV = d["frames"], d["radf"], d["gravity_at"]
G = d["geom"]; CX, CY, RPX, R0 = G["CX"], G["CY"], G["R"], G["R0"]
NF = len(FR)
NMAX = max(len(f) for f in FR)
S = 1.55 / RPX                       # px -> blender units
TRAY_Z = 1.85
PCT = int(os.environ.get("PCT", 50)); SAMPLES = int(os.environ.get("SAMPLES", 8))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, PCT
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 3
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .05
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"

def mat(name, base, rough=.3, metal=0.0, coat=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    return m

w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.008, 0.006, 1)

bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat("floor", (0.03, 0.024, 0.019), rough=.6))
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 12, 15), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("wall", (0.026, 0.021, 0.017), rough=.85))

walnut = mat("walnut", (0.12, 0.065, 0.032), rough=.35, coat=.7)
brass = mat("brass", (0.92, 0.64, 0.32), rough=.2, metal=1)
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=1.25, depth=1.35, location=(0, 0, .675))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(walnut)
bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=.03, location=(0, 0, 1.35))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(brass)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.16, depth=.5, location=(0, 0, 1.55))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(brass)

# tray group (tilts at the end)
bpy.ops.object.empty_add(location=(0, 0, TRAY_Z)); tray = bpy.context.object
bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=1.72, depth=.12, location=(0, 0, TRAY_Z - .06))
td = bpy.context.object; bpy.ops.object.shade_smooth(); td.data.materials.append(mat("traywood", (0.075, 0.042, 0.022), rough=.28, coat=.9))
td.parent = tray; td.matrix_parent_inverse = tray.matrix_world.inverted()
bpy.ops.mesh.primitive_torus_add(major_radius=1.6, minor_radius=.06, major_segments=160, location=(0, 0, TRAY_Z + .05))
rim = bpy.context.object; bpy.ops.object.shade_smooth(); rim.data.materials.append(brass)
rim.parent = tray; rim.matrix_parent_inverse = tray.matrix_world.inverted()

# marble materials by generation
def gen_of(r): return int(round(2 * math.log2(R0 / r)))
MAXG = gen_of(float(min(RF[-1])))
def gcol(g):
    u = g / max(1, MAXG); h = ((268 + 140 * u) % 360) / 360
    return colorsys.hsv_to_rgb(h, .78 - .1 * u, .9 + .1 * u)

# one point cloud, a sphere instanced on every point (fast); colour + radius as point attributes
me = bpy.data.meshes.new("pts"); me.vertices.add(NMAX)
me.attributes.new("radius", "FLOAT", "POINT"); me.attributes.new("col", "FLOAT_COLOR", "POINT")
pts = bpy.data.objects.new("pts", me); sc.collection.objects.link(pts); pts.parent = tray
gn = bpy.data.node_groups.new("inst", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N = gn.nodes; Lk = gn.links
gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
sph = N.new("GeometryNodeMeshUVSphere"); sph.inputs["Segments"].default_value = 24; sph.inputs["Rings"].default_value = 12
sm = N.new("GeometryNodeSetShadeSmooth"); Lk.new(sph.outputs["Mesh"], sm.inputs["Geometry"])
ra = N.new("GeometryNodeInputNamedAttribute"); ra.data_type = "FLOAT"; ra.inputs["Name"].default_value = "radius"
iop = N.new("GeometryNodeInstanceOnPoints")
Lk.new(gi.outputs["Geometry"], iop.inputs["Points"]); Lk.new(sm.outputs["Geometry"], iop.inputs["Instance"])
Lk.new(ra.outputs["Attribute"], iop.inputs["Scale"])
setm = N.new("GeometryNodeSetMaterial"); Lk.new(iop.outputs["Instances"], setm.inputs["Geometry"])
Lk.new(setm.outputs["Geometry"], go.inputs["Geometry"])
mod = pts.modifiers.new("inst", "NODES"); mod.node_group = gn
bm = bpy.data.materials.new("marble"); bm.use_nodes = True
bsdf = bm.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = .06; bsdf.inputs["Coat Weight"].default_value = 1.0
at = bm.node_tree.nodes.new("ShaderNodeAttribute"); at.attribute_type = "INSTANCER"; at.attribute_name = "col"
bm.node_tree.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
setm.inputs["Material"].default_value = bm
COLS = np.array([gcol(g) for g in range(MAXG + 1)], np.float32)

def area(loc, rot, size, power, col):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.object.data; L.size = size; L.energy = power; L.color = col
area((-3.5, -4.5, 7.5), (math.radians(40), 0, math.radians(-38)), 4.5, 1000, (1, .93, .85))
area((3.5, 4, 4.5), (math.radians(-65), 0, math.radians(140)), 3, 650, (1, .72, .42))
area((4.5, -4, 2.5), (math.radians(75), 0, math.radians(50)), 4, 120, (.7, .8, 1))

bpy.ops.object.camera_add(location=(0, -6.6, 6.3)); cam = bpy.context.object
cam.data.lens = 36; sc.camera = cam
bpy.ops.object.empty_add(location=(0, 0.15, 1.3)); tgt = bpy.context.object
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def place(f):
    k = min(f, NF - 1)
    pos, rad = FR[k], RF[k]
    tilt = math.radians(9) * ss((k - GRAV) / 34) if GRAV is not None and k >= GRAV else 0
    tray.rotation_euler = (tilt, 0, 0)           # near side (sim "down") dips toward the camera
    n = len(pos)
    co = np.zeros((NMAX, 3), np.float32); rr = np.zeros(NMAX, np.float32); cc = np.zeros((NMAX, 4), np.float32)
    r = rad[:n].astype(np.float32) * S
    co[:n, 0] = (pos[:, 0] - CX) * S; co[:n, 1] = -(pos[:, 1] - CY) * S; co[:n, 2] = r
    rr[:n] = r
    g = np.clip(np.round(2 * np.log2(R0 / rad[:n])).astype(int), 0, MAXG)
    cc[:n, :3] = COLS[g]; cc[:n, 3] = 1
    me.vertices.foreach_set("co", co.ravel()); me.attributes["radius"].data.foreach_set("value", rr)
    me.attributes["col"].data.foreach_set("color", cc.ravel()); me.update()

if __name__ == "__main__":
    a, b = int(sys.argv[-2]), int(sys.argv[-1])
    os.makedirs("/home/claude/b3d/frames", exist_ok=True)
    for f in range(a, b):
        out = f"/home/claude/b3d/frames/f_{f:04d}.png"
        if os.path.exists(out): continue
        place(f)
        sc.render.filepath = out
        t = time.time(); bpy.ops.render.render(write_still=True)
        print(f"frame {f} {time.time() - t:.1f}s", flush=True)
