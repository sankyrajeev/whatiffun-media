"""Blender (bpy) feasibility test: our dark warm studio, a wooden pedestal, glossy marbles, key + rim light.
Renders one 1080x1920 frame with Cycles (CPU) and EEVEE if available, and prints the time each takes."""
import bpy, math, time, sys, random

ENGINE = sys.argv[-1] if sys.argv[-1] in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH") else "CYCLES"
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = int(__import__("os").environ.get("PCT", 100))

def mat(name, base, rough=.3, metal=0.0, transm=0.0, ior=1.45, coat=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = transm
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    return m

# world: warm near-black with a soft gradient
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.012, 0.009, 0.007, 1); bg.inputs["Strength"].default_value = 1.0

# backdrop: curved cyclorama (floor + wall) in warm dark grey
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.object; floor.data.materials.append(mat("floor", (0.035, 0.028, 0.022), rough=.55))
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 9, 10), rotation=(math.radians(90), 0, 0))
wall = bpy.context.object; wall.data.materials.append(mat("wall", (0.03, 0.024, 0.019), rough=.8))

# pedestal: walnut cylinder with a brass top ring
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.6, depth=1.4, location=(0, 0, .7))
ped = bpy.context.object; bpy.ops.object.shade_smooth()
ped.data.materials.append(mat("walnut", (0.13, 0.07, 0.035), rough=.38, coat=.6))
bpy.ops.mesh.primitive_torus_add(major_radius=1.6, minor_radius=.04, location=(0, 0, 1.4))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(mat("brass", (0.9, 0.62, 0.3), rough=.22, metal=1))

# glass bowl (thin sphere shell cut) -> simple: transparent cylinder
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.3, location=(0, 0, 2.7))
bowl = bpy.context.object; bpy.ops.object.shade_smooth()
bowl.data.materials.append(mat("glass", (1, 1, 1), rough=0.02, transm=1.0, ior=1.45))

# marbles inside
random.seed(2)
cols = [(0.55, 0.25, 0.95), (0.95, 0.35, 0.65), (1.0, 0.75, 0.3), (0.3, 0.75, 0.95)]
mm = [mat(f"m{i}", c, rough=.05, transm=.6, ior=1.5, coat=1) for i, c in enumerate(cols)]
for i in range(60):
    r = .13
    while True:
        x, y, z = random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)
        if x * x + y * y + z * z < .9: break
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=(x * 1.0, y * 1.0, 2.7 + z * 1.0))
    bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(mm[i % 4])

# lights: big soft key, warm rim, cool fill
def area(loc, rot, size, power, col):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.object.data; L.size = size; L.energy = power; L.color = col
area((-4, -4, 7), (math.radians(45), 0, math.radians(-45)), 5, 900, (1, .93, .85))
area((4, 5, 4), (math.radians(-70), 0, math.radians(140)), 3, 700, (1, .75, .45))
area((5, -3, 2), (math.radians(80), 0, math.radians(60)), 4, 150, (.7, .8, 1))

# camera: slightly high, 50mm, portrait
bpy.ops.object.camera_add(location=(0, -10.5, 4.6), rotation=(math.radians(80), 0, 0))
cam = bpy.context.object; cam.data.lens = 50; sc.camera = cam

sc.render.engine = ENGINE
if ENGINE == "CYCLES":
    sc.cycles.device = "CPU"; sc.cycles.samples = int(__import__("os").environ.get("SAMPLES", 48))
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = int(__import__("os").environ.get("BOUNCES", 6)); sc.cycles.transmission_bounces = int(__import__("os").environ.get("BOUNCES", 6))
    sc.cycles.denoiser = "OPENIMAGEDENOISE"; sc.render.use_persistent_data = True
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filepath = f"/home/claude/b3d/test_{ENGINE}_{__import__('os').environ.get('TAG', 'x')}.png"
t = time.time()
bpy.ops.render.render(write_still=True)
print(f"RENDER {ENGINE} took {time.time() - t:.1f}s", flush=True)
