"""Blender (Cycles) renders for MARBLE MUSIC.
The wall never moves, so instead of rendering every frame we render the whole wall once as tall tiles with an
orthographic camera — twice: pads idle, and pads lit — plus a spinning-marble sprite sheet. compose.py then
films the video by sliding a 1080x1920 window down the wall, lighting each pad as it is struck.
    python3 strip.py plan/<song>.json tiles   [PCT] [SAMPLES]   -> render/<song>/idle_k.png, lit_k.png
    python3 strip.py plan/<song>.json ball                        -> render/<song>/ball_XX.png (36 frames)"""
import bpy, json, math, os, sys, time

P = json.load(open(sys.argv[1])); MODE = sys.argv[2]
PCT = int(sys.argv[3]) if len(sys.argv) > 3 else 100
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 24
OUT = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "..", "render", P["song"]); os.makedirs(OUT, exist_ok=True)
S = 0.01                                     # design px -> blender units
PAD_Z = 0.30                                 # pads (and the marble) sit 30 px off the wall
TILT = math.radians(14)                      # camera looks slightly down the wall: we see the pads' top faces
VIEW_W = 8.0                                 # the frame shows 800 design px across (1.35x zoom)
ORTHO = VIEW_W * 1920 / 1080

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 4
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .04
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"

w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.030, 0.024, 0.019, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

def principled(name, base, rough=.3, metal=0.0, coat=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    return m, b

def sun(rot, strength, col, angle=6):
    bpy.ops.object.light_add(type="SUN", rotation=rot)
    L = bpy.context.object.data; L.energy = strength; L.color = col; L.angle = math.radians(angle)

# key from the upper left (screen), a warm rim from the right
sun((math.radians(-30), math.radians(-24), 0), 3.4, (1.0, .92, .82), 10)
sun((math.radians(-20), math.radians(55), 0), 0.9, (1.0, .66, .38), 12); bpy.context.object.data.use_shadow = False

if MODE == "ball":
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 256; sc.render.resolution_percentage = 100
    r = P["ball_r"] * S
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=r, location=(0, 0, PAD_Z))
    ball = bpy.context.object; bpy.ops.object.shade_smooth()
    m, b = principled("marble", (1, 1, 1), rough=.08, coat=1.0)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"; wave.bands_direction = "X"; wave.inputs["Scale"].default_value = 1.6
    wave.inputs["Distortion"].default_value = 2.0; wave.inputs["Detail"].default_value = 1.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.05, 0.025, 0.012, 1)
    ramp.color_ramp.elements[1].position = 0.55; ramp.color_ramp.elements[1].color = (0.95, 0.45, 0.10, 1)
    e = ramp.color_ramp.elements.new(0.82); e.color = (0.98, 0.88, 0.66, 1)
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"]); nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    ball.data.materials.append(m)
    bpy.ops.object.camera_add(location=(0, 20 * math.sin(TILT), PAD_Z + 20 * math.cos(TILT)), rotation=(-TILT, 0, 0))
    cam = bpy.context.object; sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.6 * r
    for k in range(36):
        ball.rotation_euler = (math.radians(18), 0, -math.radians(10 * k))
        sc.render.filepath = os.path.join(OUT, f"ball_{k:02d}.png")
        bpy.ops.render.render(write_still=True)
    print("ball sprites done"); sys.exit()

# ---------------- the wall ----------------
pads = P["pads"]
y_lo = min(p["y"] for p in pads) - 1200; y_hi = max(p["y"] for p in pads) + 2400
wall_h = (y_hi - y_lo) * S
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -(y_lo + y_hi) / 2 * S, 0))
wall = bpy.context.object; wall.scale = (14, wall_h, 1)
wm, wb = principled("wall", (0.020, 0.016, 0.013), rough=.5)
nt = wm.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 90.0; noise.inputs["Detail"].default_value = 6.0
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12; bump.inputs["Distance"].default_value = .02
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"]); nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], wb.inputs["Normal"])
wall.data.materials.append(wm)

MATS = {
    "tube":   principled("brass", (0.93, 0.66, 0.34), rough=.16, metal=1.0),
    "wood":   principled("walnut", (0.20, 0.10, 0.05), rough=.32, coat=.8),
    "glass":  principled("amberglass", (1.0, 0.62, 0.22), rough=.04, trans=1.0, ior=1.5),
    "saucer": principled("copper", (0.95, 0.52, 0.36), rough=.2, metal=1.0),
}
LIT = {"tube": ((1.0, .78, .42), 2.2), "wood": ((1.0, .66, .32), 1.4), "glass": ((1.0, .62, .2), 7.0),
       "saucer": ((1.0, .55, .32), 2.6)}
chrome, _ = principled("chrome", (0.86, 0.86, 0.88), rough=.12, metal=1.0)

def add_pad(pd):
    f, L, h = pd["fam"], pd["len"] * S, pd["half"] * S
    x, y, a = (pd["x"] - 540) * S, -pd["y"] * S, pd["ang"]
    if f == "tube":
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=h, depth=L, location=(x, y, PAD_Z), rotation=(0, math.radians(90), 0))
        ob = bpy.context.object; bpy.ops.object.shade_smooth()
        ob.rotation_euler = (0, math.radians(90), -a)      # Rz(-a)·Ry(90): lay it along X, then tilt in the wall plane
    elif f == "saucer":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(x, y, PAD_Z))
        ob = bpy.context.object; bpy.ops.object.shade_smooth(); ob.scale = (L / 2, h, 0.2)
        ob.rotation_euler = (0, 0, -a)
    else:
        depth = 0.26 if f == "wood" else 0.18
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, PAD_Z))
        ob = bpy.context.object; ob.scale = (L, 2 * h, depth); ob.rotation_euler = (0, 0, -a)
        bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.025; bv.segments = 4
        bpy.ops.object.shade_smooth()
    ob.data.materials.append(MATS[f][0])
    # a short chrome pin into the wall
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=.035, depth=PAD_Z, location=(x, y, PAD_Z / 2))
    bpy.context.object.data.materials.append(chrome)
for pd in pads: add_pad(pd)

from bpy_extras.object_utils import world_to_camera_view
bpy.ops.object.camera_add(rotation=(-TILT, 0, 0)); cam = bpy.context.object; sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = ORTHO; cam.data.clip_end = 200
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, PCT
STEP = ORTHO / math.cos(TILT)                       # wall length (BU) one tile covers
def place_cam(k):
    # aim at the wall point (x=0, y=-(y_lo/100) - (k+0.5)*STEP); camera 60 BU away along the tilted view axis
    cy = -y_lo * S - (k + 0.5) * STEP
    cam.location = (0, cy + 60 * math.sin(TILT), PAD_Z + 60 * math.cos(TILT))
    bpy.context.view_layer.update()
n_tiles = int(math.ceil((y_hi - y_lo) * S / STEP))
# design (x, y) on the pad/marble plane -> strip pixels (tile 0 top = 0): fit from the camera itself
place_cam(0)
from mathutils import Vector
def px(xd, yd):
    v = world_to_camera_view(sc, cam, Vector(((xd - 540) * S, -yd * S, PAD_Z)))
    return v.x * 1080, (1 - v.y) * 1920
(xa0, ya0), (xa1, ya1) = px(140, y_lo + 300), px(940, y_lo + 1300)
ax = (xa1 - xa0) / 800.0; bx = xa0 - ax * 140
ay = (ya1 - ya0) / 1000.0; by = ya0 - ay * (y_lo + 300)
json.dump({"tiles": n_tiles, "tile_h": 1920, "pct": PCT, "ax": ax, "bx": bx, "ay": ay, "by": by,
           "ball_px": 2 * P["ball_r"] * ax}, open(os.path.join(OUT, "tiles.json"), "w"))
print("mapping", ax, bx, ay, by, "tiles", n_tiles, flush=True)
for state in ("idle", "lit"):
    for f, (m, b) in MATS.items():
        col, st = LIT[f]
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = st if state == "lit" else 0.0
    for k in range(n_tiles):
        out = os.path.join(OUT, f"{state}_{k:02d}.png")
        if os.path.exists(out): continue
        place_cam(k)
        sc.render.filepath = out
        t0 = time.time(); bpy.ops.render.render(write_still=True)
        print(f"{state} tile {k + 1}/{n_tiles} {time.time() - t0:.0f}s", flush=True)
