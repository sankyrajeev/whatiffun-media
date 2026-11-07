"""No. 9 — 'Whatever it touches becomes a magnet.'
A round dish of pearly steel beads (top-down, table friction). One gold magnet rolls in. Any bead that
touches a magnet becomes one and starts pulling its neighbours. Chains spread, clusters snap together,
and the whole dish gathers into one glittering cluster."""
import pymunk, numpy as np, pickle, math, os
from scipy.spatial import cKDTree
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 4
DT = 1 / (FPS * SUB)
CX, CY, RD = 540.0, 1050.0, E("RD", 415)
BR = E("BR", 8.0)
N = int(E("N", 900))
K = E("K", 2.2e6)        # pull strength
RANGE = E("RANGE", 70)  # pull reach (centre-to-centre)
RANGE1 = E("RANGE1", 150)
RT0, RT1 = E("RT0", 12), E("RT1", 20)   # reach widens late so no bead is left behind
SECS = E("SECS", 30)
rng = np.random.default_rng(int(E("SEED", 7)))

space = pymunk.Space(); space.damping = E("DAMP", 1.0); space.iterations = 10; space.collision_slop = .2
st = space.static_body
M = 72
for i in range(M):
    a0, a1 = 2 * math.pi * i / M, 2 * math.pi * (i + 1) / M
    s = pymunk.Segment(st, (CX + (RD + 6) * math.cos(a0), CY + (RD + 6) * math.sin(a0)),
                       (CX + (RD + 6) * math.cos(a1), CY + (RD + 6) * math.sin(a1)), 6)
    s.elasticity = 1.0; s.friction = .05; s.collision_type = 3; space.add(s)

# poisson-ish scatter
r = RD - BR - 4; MIN = 2 * BR + E("GAP", 7)
cand = rng.uniform(-r, r, (60000, 2)); cand = cand[(cand ** 2).sum(1) < r * r]
pts = []; tr = None; grid = {}
for p in cand:
    kx, ky = int(p[0] // MIN), int(p[1] // MIN); ok = True
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for q in grid.get((kx + dx, ky + dy), ()):
                if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < MIN * MIN: ok = False; break
            if not ok: break
        if not ok: break
    if ok:
        pts.append(p); grid.setdefault((kx, ky), []).append(p)
        if len(pts) >= N: break
pts = np.array(pts) + [CX, CY]
# the first magnet starts at the rim, rolling inward
start = np.array([CX - RD * .62, CY - RD * .6])
keep = np.sum((pts - start) ** 2, 1) > (4 * BR) ** 2
pts = np.vstack([start, pts[keep]])
N = len(pts)
bodies, shapes = [], []
for i, p in enumerate(pts):
    b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR)); b.position = tuple(p)
    s = pymunk.Circle(b, BR); s.elasticity = E('EB', .97); s.friction = .05; s.collision_type = 1; s.idx = i
    space.add(b, s); bodies.append(b); shapes.append(s)
    if i > 0:
        a = rng.uniform(0, 2 * math.pi); v = E("V", 110) * rng.uniform(.6, 1.3)
        b.velocity = (v * math.cos(a), v * math.sin(a))
dv0 = np.array([CX - 60, CY + 40]) - start; dv0 = dv0 / np.linalg.norm(dv0) * E("V0", 150)
bodies[0].velocity = (float(dv0[0]), float(dv0[1]))

mag = np.zeros(N, bool); mag[0] = True
order = np.full(N, -1); order[0] = 0; tmag = np.full(N, -1.0); tmag[0] = 0
clock = {"t": 0.0}; conv, clacks = [], []
def on_bead(arb, sp, d):
    a, b = arb.shapes
    i, j = a.idx, b.idx
    if mag[i] != mag[j]:
        k = j if mag[i] else i
        mag[k] = True; order[k] = int(mag.sum()) - 1; tmag[k] = clock["t"]
        p = bodies[k].position
        conv.append((clock["t"], p.x, p.y, k, order[k], arb.total_impulse.length))
    elif arb.is_first_contact and arb.total_impulse.length > 15:
        p = arb.contact_point_set.points[0].point_a
        clacks.append((clock["t"], p.x, p.y, arb.total_impulse.length, bool(mag[i])))
space.on_collision(1, 1, post_solve=on_bead)
def on_wall(arb, sp, d):
    if arb.is_first_contact and arb.total_impulse.length > 20:
        p = arb.contact_point_set.points[0].point_a
        clacks.append((clock["t"], p.x, p.y, arb.total_impulse.length, False))
space.on_collision(1, 3, post_solve=on_wall)

frames, counts = [], []
full_at = None
gather_t = None
for f in range(int(SECS * FPS)):
    t = f / FPS
    if gather_t is None and (mag.mean() > E("GF", .985) or t > E("GT", 21)): gather_t = t
    gu = 0 if gather_t is None else min(1, (t - gather_t) / E("GR", 2.5))
    reach = RANGE + (RANGE1 - RANGE) * gu
    Kt = K * (E("K0", .05) + (1 - E("K0", .05)) * gu)
    md = 1 - (1 - E("MD", .985)) * (E("MD0", 0.0) + (1 - E("MD0", 0.0)) * gu)
    for s_ in range(SUB):
        clock["t"] = t + s_ * DT
        if s_ % 2 == 0:
            P = np.array([b.position for b in bodies])
            mi = np.nonzero(mag)[0]
            F = np.zeros((N, 2))
            if len(mi):
                Pm = P[mi]
                dv = (Pm[None, :, :] - P[:, None, :]).astype(np.float32)        # N x M, from bead to magnet
                dd = np.sqrt((dv ** 2).sum(2)); 
                w = (dd < reach) & (dd > 1e-3)
                ddc = np.maximum(dd, 2 * BR)
                fm = np.where(w, Kt / ddc ** 2 * (1 - (dd / reach) ** 2), 0) / np.maximum(dd, 1e-3)
                fv = (dv * fm[:, :, None]).sum(1)
                F += fv

            Fc = F
        for i in np.nonzero((np.abs(Fc).sum(1)) > 0)[0]:
            bodies[i].force = tuple(Fc[i])
        space.step(DT)
        for i in np.nonzero(mag)[0]:
            v = bodies[i].velocity; bodies[i].velocity = (v.x * md, v.y * md)
    P = np.array([b.position for b in bodies], np.float32)
    frames.append(P); counts.append(int(mag.sum()))
    if full_at is None and mag.all(): full_at = f
    if f % 30 == 0:
        print(f"t={t:4.1f} magnets={mag.sum():4d}/{N} conv/s={sum(1 for c in conv if c[0] > t - 1):4d}", flush=True)
    if gather_t is not None and t > gather_t + E("TAIL", 6): break
print("frames", len(frames), "N", N, "all at", full_at and round(full_at / FPS, 1), "gather", gather_t)
pickle.dump(dict(frames=frames, counts=np.array(counts), order=order, tmag=tmag, conv=conv, clacks=clacks,
                 full=full_at, gather=gather_t, geom=dict(CX=CX, CY=CY, RD=RD, BR=BR, N=N)), open("magnet.pkl", "wb"))
