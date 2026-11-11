"""Deterministic growth of a bismuth hopper-crystal cluster in a pewter dish.
Rule: every step (a square terrace of 4 bars, grown corner to corner) grows a smaller crystal at one of its corners.
Crystals are placed in time order and a sprout picks the first corner/tilt that has room (no crystal grows through another).
Bars carry age -> oxide thin-film thickness (fresh = silver-gold, older = magenta -> blue -> teal)."""
import heapq
import numpy as np
from scipy.spatial.transform import Rotation as Rot

FPS = 30
NFR = 540                      # rendered action frames (17 s)
T0 = 6.0                       # sim time at frame 0 (open mid-growth)
POOL_Z = 0.0
rng = np.random.default_rng(11)

TERR = {0: 7, 1: 6, 2: 5, 3: 4}   # terraces per crystal by depth
SCALE = .6; DUR0 = 1.45; DUR_K = .6
HK, TH, A0, DA = .15, .15, .2, .13

crystals = []   # dict(origin, R, s, t0, depth, c (centre), r (radius))
bars, steps = [], []

def geom(origin, R, s, depth):
    T = TERR[depth]; hgt = HK * s * T
    return origin + R[:, 2] * hgt * .55, s * (A0 + DA * (T - 1)) * 1.25

def free(c, r, parent):
    for i, q in enumerate(crystals):
        lim = .55 if i == parent else .65
        if np.linalg.norm(c - q["c"]) < lim * (r + q["r"]): return False
    return c[2] - r * .35 > POOL_Z - .05 and np.hypot(c[0], c[1]) + r * .8 < 2.8

def build(cid):
    C = crystals[cid]; origin, R, s, t0, depth = C["origin"], C["R"], C["s"], C["t0"], C["depth"]
    T = TERR[depth]; dur = DUR0 * DUR_K ** depth
    u, v, n = R[:, 0], R[:, 1], R[:, 2]
    h = HK * s; th = TH * s; tf = 430.0 if cid == 0 else rng.uniform(220, 440)
    out = []
    for k in range(T):
        tk = t0 + k * dur; a = s * (A0 + DA * k)
        ang = np.radians(4.0 * k)
        cu = np.cos(ang) * u + np.sin(ang) * v; cv = -np.sin(ang) * u + np.cos(ang) * v
        zc = origin + n * (h * (k + .5))
        corners = [zc + a * (sx * cu + sy * cv) for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
        Rk = np.stack([cu, cv, n], 1); film = tf - 42 * k
        if k == 0:
            bars.append(dict(c0=zc, d=cu, L=2 * a + th, wid=2 * a + th, Rk=Rk, ax=0, ts=tk, te=tk + dur * .8, s=s, cid=cid, plate=True, film=film, k=k))
        else:
            for j in range(4):
                p0, p1 = corners[j], corners[(j + 1) % 4]
                d = (p1 - p0) / np.linalg.norm(p1 - p0)
                bars.append(dict(c0=p0 - d * th / 2, d=d, L=2 * a + th, wid=th, Rk=Rk, ax=j % 2,
                                 ts=tk + j * dur / 4, te=tk + (j + 1) * dur / 4, s=s, cid=cid, plate=False, film=film, k=k))
        te = tk + dur
        steps.append((te, depth, cid, zc.copy(), s))
        if k >= 1 and depth + 1 in TERR:
            out.append((te, cid, [c.copy() for c in corners], zc.copy(), n.copy(), h, s * SCALE, depth + 1, k))
    return out

pq = []; seq = 0
crystals.append(dict(origin=np.array([0., 0., POOL_Z - .02]), R=np.eye(3), s=1.0, t0=0.0, depth=0))
crystals[0]["c"], crystals[0]["r"] = geom(crystals[0]["origin"], np.eye(3), 1.0, 0)
for item in build(0): heapq.heappush(pq, (item[0], seq, item)); seq += 1
while pq:
    _, _, (te, pid, corners, zc, n, h, s, depth, k) = heapq.heappop(pq)
    cands = []
    for cj in range(4):
        corner = corners[(cj + k + pid) % 4]
        out = corner - zc; out -= n * (out @ n); out /= np.linalg.norm(out)
        for tilt in (26, 16, 38):
            t = np.radians(tilt + rng.uniform(-4, 4))
            nc = n * np.cos(t) + out * np.sin(t)
            if nc[2] < .35: nc = nc + np.array([0, 0, .5]); nc /= np.linalg.norm(nc)
            uc = np.cross(nc, out); uc /= np.linalg.norm(uc)
            tw = np.radians(rng.uniform(-30, 30)); vc = np.cross(nc, uc)
            uc, vc = np.cos(tw) * uc + np.sin(tw) * vc, -np.sin(tw) * uc + np.cos(tw) * vc
            cands.append((corner + n * h * .3, np.stack([uc, vc, nc], 1)))
    for origin, R in cands:
        c, r = geom(origin, R, s, depth)
        if free(c, r, pid):
            crystals.append(dict(origin=origin, R=R, s=s, t0=te, depth=depth, c=c, r=r))
            for item in build(len(crystals) - 1): heapq.heappush(pq, (item[0], seq, item)); seq += 1
            break

NB = len(bars)
TS = np.array([b["ts"] for b in bars]); TE = np.array([b["te"] for b in bars])
STEP_T = np.sort(np.array([s[0] for s in steps]))
END_T = TE.max()
EULERS = np.array([Rot.from_matrix(b["Rk"]).as_euler("xyz") for b in bars])
C0 = np.array([b["c0"] for b in bars]); DD = np.array([b["d"] for b in bars]); LL = np.array([b["L"] for b in bars])
WID = np.array([b["wid"] for b in bars]); AX = np.array([b["ax"] for b in bars]); PL = np.array([b["plate"] for b in bars])
HH = np.array([HK * b["s"] for b in bars]); FILM = np.array([b["film"] for b in bars]); JIT = 20 * ((np.arange(NB) * 7919) % 13) / 13

def tsim(f): return T0 + f / FPS
def count(f): return int((STEP_T <= tsim(f)).sum())

def state(f):
    t = tsim(f)
    g = np.clip((t - TS) / (TE - TS), 0, 1)
    pos = C0 + DD * (LL * g / 2)[:, None]
    lx = np.where(AX == 0, LL * g, WID); ly = np.where(AX == 0, WID, LL * g)
    e = np.sqrt(g)
    lx = np.where(PL, LL * e, lx); ly = np.where(PL, WID * e, ly); pos[PL] = C0[PL]
    scl = np.stack([lx, ly, HH], 1)
    pos[g <= 0] = (0, 0, -5); scl[g <= 0] = 0
    age = np.maximum(0, t - TE)
    film = 60 + (FILM - 60) * (1 - np.exp(-age / 2.6)) + JIT
    return pos, scl, film

if __name__ == "__main__":
    print("crystals", len(crystals), "bars", NB, "steps", len(steps), "end", round(END_T, 2), "endframe", round((END_T - T0) * FPS))
    print([(f, count(f)) for f in range(0, NFR, 60)])
    P = C0; print("bounds", P.min(0).round(2), P.max(0).round(2))
