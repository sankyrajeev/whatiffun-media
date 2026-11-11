"""Fit the camera path: target follows the cluster's centre; per frame, find the distance + lens shift that keeps every
bar end inside x 0.13-0.87 of the frame; then smooth (distance never decreases)."""
import sys, os; sys.argv = ['x', '0', '0']; sys.path.insert(0, '/home/claude/bi')
exec(open('/home/claude/bi/scene.py').read().split('if __name__')[0])
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from scipy.ndimage import gaussian_filter1d
FS = list(range(0, NFR, 4)) + [NFR - 1]
raw = []
for f in FS:
    pos, scl, film = state(f); vis = scl[:, 0] > 0
    P = pos[vis]; Lh = np.max(scl[vis][:, :2], 1)[:, None] / 2; Dv = DD[vis]
    pts = np.vstack([P + Dv * Lh, P - Dv * Lh])
    if len(pts) > 600: pts = pts[::len(pts) // 600 + 1]
    lo, hi = P.min(0), P.max(0); c = (lo + hi) / 2
    path = [c[0], c[1], .4 + .45 * (c[2] - .2), 6.0, 0.0]
    for it in range(10):
        cam_at(f, path); bpy.context.view_layer.update()
        xs = np.array([world_to_camera_view(sc, cam, Vector(p)).x for p in pts])
        mid = (xs.max() + xs.min()) / 2; hw = (xs.max() - xs.min()) / 2
        path[4] += (mid - .5) / 1.86; path[3] *= hw / .37
    raw.append(path)
raw = np.array(raw); Fi = np.arange(NFR)
full = np.stack([np.interp(Fi, FS, raw[:, j]) for j in range(5)], 1)
out = full.copy()
for j in (0, 1, 2): out[:, j] = gaussian_filter1d(full[:, j], 20, mode="nearest")
d = np.maximum.accumulate(full[:, 3] * 1.03)
out[:, 3] = np.maximum(gaussian_filter1d(d, 8, mode="nearest"), d * .99)
out[:, 4] = gaussian_filter1d(full[:, 4], 8, mode="nearest")
np.save(CAMP, out)
for f in range(0, NFR, 40): print(f, out[f].round(2))
