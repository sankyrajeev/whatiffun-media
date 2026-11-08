"""'Every one that falls / tips the next.'  Glossy glass dominoes stand on a dark round table in a
branching spiral that grows from one centre domino. The centre one tips; every domino that falls knocks
over whatever stands in front of it (at forks, two). Deterministic layout growth + event times."""
import numpy as np, math, pickle, os
E = lambda k, d: float(os.environ.get(k, d))
rng = np.random.default_rng(int(E("SEED", 3)))
CX, CY, R = 540.0, 1060.0, E("R", 425)
S = E("S", 24.0)          # spacing along a line
DMIN = E("DMIN", 26.0)    # clearance to any other domino
ALPHA = math.radians(E("ALPHA", 62))   # spiral pitch: heading = radial angle + ALPHA
STEER = E("STEER", .22)
PF = E("PF", .55)         # fork chance per step when there is room
FORK = math.radians(E("FORK", 38))
DT = E("DT", .27)         # seconds per domino-to-domino step (slow, calm topple)
JIT = E("JIT", .05)

pos, head, parent, tstart, depth = [], [], [], [], []
cell = 32.0; grid = {}
def gk(x, y): return (int(x // cell), int(y // cell))
def free(x, y, skip):
    if (x - CX) ** 2 + (y - CY) ** 2 > R * R: return False
    kx, ky = gk(x, y)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in grid.get((kx + dx, ky + dy), ()):
                if j in skip: continue
                if (pos[j][0] - x) ** 2 + (pos[j][1] - y) ** 2 < DMIN * DMIN: return False
    return True
def add(x, y, h, p, t):
    i = len(pos); pos.append((x, y)); head.append(h); parent.append(p); tstart.append(t)
    depth.append(0 if p < 0 else depth[p] + 1); grid.setdefault(gk(x, y), []).append(i); return i
def steer(x, y, h):
    a = math.atan2(y - CY, x - CX) + ALPHA
    d = (a - h + math.pi) % (2 * math.pi) - math.pi
    return h + STEER * d
add(CX, CY, -math.pi / 2, -1, 0.0)
tips = [0]
while tips:
    rng.shuffle(tips); new = []
    for i in tips:
        x, y = pos[i]; h = head[i]
        skip = {i, parent[i]} if parent[i] >= 0 else {i}
        kids = []
        r0 = math.hypot(x - CX, y - CY)
        hs = steer(x, y, h) if r0 > 30 else h
        for dh in (0, .2, -.2, .4, -.4):
            nh = hs + dh; nx, ny = x + S * math.cos(nh), y + S * math.sin(nh)
            if free(nx, ny, skip):
                kids.append(add(nx, ny, nh, i, tstart[i] + DT * (1 + rng.normal(0, JIT)))); break
        # fork: a second domino set at an angle, also inside the falling one's reach
        if rng.random() < (1.0 if r0 < E("RIN", 90) else PF):
            for sgn in rng.permutation([-1, 1]):
                nh = hs + sgn * FORK; nx, ny = x + S * 1.05 * math.cos(nh), y + S * 1.05 * math.sin(nh)
                if free(nx, ny, skip | set(kids)):
                    kids.append(add(nx, ny, nh, i, tstart[i] + DT * (1 + rng.normal(0, JIT)))); break
        new += kids
    tips = new
P = np.array(pos); T = np.array(tstart); Hh = np.array(head); PA = np.array(parent)
nkids = np.bincount(PA[PA >= 0], minlength=len(P))
print("dominoes", len(P), "last fall starts", round(T.max(), 2), "s  leaves", int((nkids == 0).sum()))
for s in range(0, int(T.max()) + 2, 2): print(f"t={s:2d} fallen={(T <= s).sum():4d}")
pickle.dump(dict(P=P, T=T, H=Hh, PA=PA, NK=nkids, geom=dict(CX=CX, CY=CY, R=R, S=S, DT=DT)), open("tip.pkl", "wb"))
