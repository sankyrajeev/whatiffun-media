"""3D (Cycles) 'ONE EQUATION': a brass machine of spinning Fourier arms on a walnut desk draws a chess knight with a
glowing gold line; arm count 1 -> 4 -> 16 -> 64 -> 256 -> 1,024; then the outline rises into a polished brass knight.
Usage: python3 scene.py START END [STEP]   (renders frames to $OUT/f_XXXX.png)"""
import bpy, math, sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion import *

OUT = os.environ.get("OUT", "/home/claude/eq/frames")
PCT = int(os.environ.get("PCT", 50)); SAMPLES = int(os.environ.get("SAMPLES", 6))
MAXA = 140                                   # arms that get geometry (the rest are sub-pixel)
U, V = 48, 8                                 # ring segments, tube segments

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, PCT
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 2
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .05
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
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.008, 0.006, 1)

# walnut desk with procedural grain
desk = bpy.data.materials.new("walnut"); desk.use_nodes = True
nt = desk.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = .45; b.inputs["Coat Weight"].default_value = .5; b.inputs["Coat Roughness"].default_value = .08
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (.12, 3.2, 1); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 3.0; n1.inputs["Detail"].default_value = 12
n1.inputs["Roughness"].default_value = .62; n1.inputs["Distortion"].default_value = .35
nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); E = cr.color_ramp.elements
E[0].position = .3; E[0].color = (0.022, 0.010, 0.005, 1); E[1].position = .72; E[1].color = (0.10, 0.048, 0.022, 1)
nt.links.new(n1.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); bpy.context.object.data.materials.append(desk)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 14, 10), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("wall", (0.022, 0.018, 0.015), rough=.85))

brass = mat("brass", (0.93, 0.66, 0.33), rough=.17, metal=1, aniso=.3)
brass_dark = mat("brass2", (0.80, 0.52, 0.26), rough=.24, metal=1)

def zj(j): return 0.035 + 0.17 * np.exp(-np.asarray(j) / 4.5)

# hub: walnut puck + brass post under arm 0
hx, hy = C0.real, C0.imag
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=.2, depth=.05, location=(hx, hy, .025))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(brass_dark); puck = bpy.context.object
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.06, depth=float(zj(0)) + .03, location=(hx, hy, (float(zj(0)) + .03) / 2))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(brass)
hub_objs = [puck, bpy.context.object]

# ---- arms: one mesh with fixed topology, vertices rewritten each frame ----
nv_ring = U * V; nv_rod = 8; nv_pin = 16
NVA = nv_ring + nv_rod + nv_pin
faces = []
for j in range(MAXA):
    o = j * NVA
    for a in range(U):
        for bb in range(V):
            faces.append((o + a * V + bb, o + ((a + 1) % U) * V + bb, o + ((a + 1) % U) * V + (bb + 1) % V, o + a * V + (bb + 1) % V))
    r0 = o + nv_ring
    for q in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        faces.append(tuple(r0 + x for x in q))
    p0 = o + nv_ring + nv_rod                 # pin: 8-sided prism at the joint
    for a in range(8):
        faces.append((p0 + a, p0 + (a + 1) % 8, p0 + 8 + (a + 1) % 8, p0 + 8 + a))
    faces.append(tuple(p0 + 8 + a for a in range(8))); faces.append(tuple(p0 + a for a in range(8))[::-1])
am = bpy.data.meshes.new("arms"); am.from_pydata(np.zeros((MAXA * NVA, 3)).tolist(), [], faces); am.update()
for p in am.polygons: p.use_smooth = True
arms = bpy.data.objects.new("arms", am); sc.collection.objects.link(arms); am.materials.append(brass)
ua = np.linspace(0, 2 * np.pi, U, endpoint=False); va = np.linspace(0, 2 * np.pi, V, endpoint=False)
pa = np.linspace(0, 2 * np.pi, 8, endpoint=False)

def arm_verts(cs, rs, n):
    P = np.zeros((MAXA, NVA, 3))
    m = min(n, MAXA)
    for j in range(MAXA):
        if j >= m or rs[j] < 4e-4:
            P[j] = [cs[min(j, len(cs) - 1)].real, cs[min(j, len(cs) - 1)].imag, -1]; continue
        r = rs[j]; tr = float(np.clip(.045 * r, .0035, .024)); z = float(zj(j))
        c = cs[j]; tip = cs[j + 1]
        cu, su = np.cos(ua)[:, None], np.sin(ua)[:, None]; cv, sv = np.cos(va)[None], np.sin(va)[None]
        rr = r + tr * cv
        ring = np.stack([c.real + rr * cu, c.imag + rr * su, z + tr * sv + 0 * cu], -1).reshape(-1, 3)
        d = tip - c; L = abs(d) + 1e-9; dx, dy = d.real / L, d.imag / L; nx, ny = -dy, dx
        wdt = tr * .9; th = tr * .7; zr = z + tr * .9
        pts = []
        for (px, py) in [(c.real, c.imag), (tip.real, tip.imag)]:
            pass
        e0 = np.array([c.real, c.imag]); e1 = np.array([tip.real, tip.imag]); nn = np.array([nx, ny]) * wdt
        quad = [e0 - nn, e1 - nn, e1 + nn, e0 + nn]
        rod = [(*q, zr - th) for q in quad] + [(*q, zr + th) for q in quad]
        pr = tr * 1.5
        pin = [(c.real + pr * math.cos(a), c.imag + pr * math.sin(a), z - tr * 1.6) for a in pa] + \
              [(c.real + pr * math.cos(a), c.imag + pr * math.sin(a), z + tr * 2.2) for a in pa]
        P[j] = np.vstack([ring, np.array(rod), np.array(pin)])
    return P.reshape(-1, 3)

# ---- gold line (current stage) + ghost (previous stage) as bevelled curves with emission ----
def gold(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, .7, .3, 1); b.inputs["Roughness"].default_value = .3; b.inputs["Metallic"].default_value = 1
    b.inputs["Emission Color"].default_value = (1, .36, .05, 1); b.inputs["Emission Strength"].default_value = 3
    return m, b
def curve_obj(name, m, depth):
    cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"; cd.bevel_depth = depth; cd.bevel_resolution = 2
    o = bpy.data.objects.new(name, cd); sc.collection.objects.link(o); cd.materials.append(m); return o, cd
gm, gb = gold("gold"); hm, hb = gold("ghost")
line, lcd = curve_obj("line", gm, .011)
ghost, gcd = curve_obj("ghost", hm, .009)
def set_curve(cd, pts, z=.012):
    cd.splines.clear()
    if pts is None or len(pts) < 2: return
    sp = cd.splines.new("POLY"); sp.points.add(len(pts) - 1)
    co = np.zeros((len(pts), 4)); co[:, 0] = pts.real; co[:, 1] = pts.imag; co[:, 2] = z; co[:, 3] = 1
    sp.points.foreach_set("co", co.ravel())

# nib: brass cone at the chain tip + a small warm light at the contact point
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=.0, radius2=.035, depth=.1, location=(0, 0, .06))
nib = bpy.context.object; bpy.ops.object.shade_smooth(); nib.data.materials.append(brass)
bpy.ops.object.light_add(type="POINT", location=(0, 0, .05)); spark = bpy.context.object; spark.data.energy = 2.5
spark.data.color = (1, .62, .25); spark.data.shadow_soft_size = .02

# ---- the knight: extruded + bevelled outline in polished brass, pivoting up on its base line ----
kz = TARGET[::4]
kcd = bpy.data.curves.new("knight", "CURVE"); kcd.dimensions = "2D"; kcd.fill_mode = "BOTH"
sp = kcd.splines.new("POLY"); sp.points.add(len(kz) - 1)
co = np.zeros((len(kz), 4)); co[:, 0] = kz.real; co[:, 1] = kz.imag; co[:, 3] = 1; sp.points.foreach_set("co", co.ravel())
sp.use_cyclic_u = True; kcd.bevel_depth = .025; kcd.bevel_resolution = 3; kcd.extrude = .001
knight = bpy.data.objects.new("knight", kcd); sc.collection.objects.link(knight)
kmat = mat("kbrass", (0.95, 0.68, 0.34), rough=.24, metal=1); kcd.materials.append(kmat)
YB = float(kz.imag.min())
bpy.ops.object.empty_add(location=(0, YB, 0)); piv = bpy.context.object
knight.parent = piv; knight.location = (0, -YB, 0)

def area(loc, rot, size, power, col):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.object.data; L.size = size; L.energy = power; L.color = col; return bpy.context.object
area((-4.5, -3.0, 7.0), (math.radians(40), 0, math.radians(-55)), 3.0, 700, (1, .93, .85))
area((4, 5, 4.5), (math.radians(-60), 0, math.radians(140)), 3.5, 750, (1, .72, .42))
area((5, -4, 2.5), (math.radians(75), 0, math.radians(50)), 4, 110, (.7, .8, 1))
soft = area((-4, -9, 5.5), (math.radians(65), 0, math.radians(-24)), 5, 0, (1, .9, .78))

bpy.ops.object.camera_add(location=(0, -6, 8)); cam = bpy.context.object; cam.data.lens = 40; sc.camera = cam
bpy.ops.object.empty_add(location=(0, 0, 0)); tgt = bpy.context.object
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
CAM_D = float(os.environ.get("CAM_D", 7.0))

def place(f):
    st = state(f)
    cs, rs = chain(st)
    am.vertices.foreach_set("co", arm_verts(cs, rs, st["n"]).astype(np.float32).ravel()); am.update()
    vis = 1 - st["retract"]
    for o in hub_objs: o.scale = (1, 1, max(.02, vis)) if o is hub_objs[1] else (max(.02, vis),) * 3
    tip = cs[-1]
    nib.location = (tip.real, tip.imag, .062 * vis - .01); nib.scale = (vis,) * 3
    spark.location = (tip.real, tip.imag, .03); spark.data.energy = 2.5 * vis * (st["frac"] > 0 or f < S0)
    rise = st["extrude"]
    set_curve(lcd, trail(st))
    gb.inputs["Emission Strength"].default_value = (3 + 14 * st["glow"]) * (1 - .9 * rise)
    line.hide_render = bool(st["stand"] > .35)
    if st["ghostN"] is not None and st["ghost"] > .01:
        set_curve(gcd, CURVES[st["ghostN"]][::2]); hb.inputs["Emission Strength"].default_value = 3 * st["ghost"]; ghost.hide_render = False
    else:
        ghost.hide_render = True
    knight.hide_render = bool(rise <= 0)
    kcd.extrude = max(.001, .16 * rise); knight.location = (0, -YB, kcd.extrude + .002)
    soft.data.energy = 320 * st['extrude']
    piv.rotation_euler = (math.radians(90) * st["stand"], 0, 0)
    # camera glide: high three-quarter view -> low hero view of the standing knight
    u = st["cam"]
    el = math.radians(64 - 46 * u); az = math.radians(-4 + 10 * u)
    tz = 0.0 + 1.75 * u; ty = 0.05 + (YB - .05) * u
    D = CAM_D * (1 + .012 * u)
    tx = 0.14 - .09 * u
    tgt.location = (tx, ty, tz)
    cam.location = (tx + D * math.cos(el) * math.sin(az), ty - D * math.cos(el) * math.cos(az), tz + D * math.sin(el))
    return st

if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2]); step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    os.makedirs(OUT, exist_ok=True)
    for f in range(a, b, step):
        out = f"{OUT}/f_{f:04d}.png"
        if os.path.exists(out): continue
        place(f); sc.render.filepath = out
        t = time.time(); bpy.ops.render.render(write_still=True)
        print(f"frame {f} {time.time() - t:.1f}s", flush=True)
