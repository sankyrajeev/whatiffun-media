"""Brand mark: a polished brass italic serif 'w' standing on a walnut disc, dark warm studio.
Usage: python3 monogram.py OUT.png W H SAMPLES [cam_dist]"""
import bpy, math, sys

out, W, H, SAMPLES = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
DIST = float(sys.argv[5]) if len(sys.argv) > 5 else 5.2
FONT = "/home/claude/whatiffun-media/fonts/InstrumentSerif-Italic.ttf"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"

def mat(name, base, rough=.3, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    return m

w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.009, 0.007, 1)

bpy.ops.mesh.primitive_plane_add(size=60)
bpy.context.object.data.materials.append(mat("floor", (0.03, 0.024, 0.019), rough=.55))
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 9, 15), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("wall", (0.03, 0.024, 0.019), rough=.85))

walnut = mat("walnut", (0.12, 0.065, 0.032), rough=.3, coat=.8)
brass = mat("brass", (0.95, 0.66, 0.33), rough=.16, metal=1)
bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=1.9, depth=.32, location=(0, 0, .16))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(walnut)
bpy.ops.mesh.primitive_torus_add(major_radius=1.9, minor_radius=.035, major_segments=160, location=(0, 0, .32))
bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(brass)

bpy.ops.object.text_add(location=(0, 0, .32))
t = bpy.context.object
t.data.body = "w"
t.data.font = bpy.data.fonts.load(FONT)
t.data.size = 3.6; t.data.extrude = .22; t.data.bevel_depth = .022; t.data.bevel_resolution = 4
t.data.align_x = "CENTER"; t.data.resolution_u = 24
t.rotation_euler = (math.radians(90), 0, 0)
t.data.materials.append(brass)
bpy.context.view_layer.update()
bb = [t.matrix_world @ __import__("mathutils").Vector(c) for c in t.bound_box]
zmin = min(v.z for v in bb); t.location.z += .32 - zmin + .002
xs = [v.x for v in bb]; t.location.x -= (min(xs) + max(xs)) / 2

def area(loc, rot, size, power, col):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.object.data; L.size = size; L.energy = power; L.color = col
area((-3.2, -3.8, 5.2), (math.radians(45), 0, math.radians(-40)), 3.5, 900, (1, .93, .85))
area((3.4, 2.6, 3.2), (math.radians(-62), 0, math.radians(130)), 2.5, 520, (1, .7, .4))
area((3.8, -3.6, 1.6), (math.radians(78), 0, math.radians(48)), 3, 90, (.7, .8, 1))

el = math.radians(16)
bpy.ops.object.camera_add(location=(0, -DIST * math.cos(el), 1.25 + DIST * math.sin(el)))
cam = bpy.context.object; cam.data.lens = 50; sc.camera = cam
bpy.ops.object.empty_add(location=(float(__import__("os").environ.get("TX", 0)), 0, 1.35)); tgt = bpy.context.object
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

sc.render.filepath = out
bpy.ops.render.render(write_still=True)
