"""ONE GAP: one ball circles a track around a sealed wall of blocks, nearly finding the single gap
again and again; once it gets in, every block it breaks adds a ball and the swarm clears the board."""
import sys, math
import numpy as np, skia
sys.path.insert(0, "/home/claude/notes")
from kit import *

CELL = 20
AX0, AY0 = 130, 590
NC, NR = 41, 47
AX1, AY1 = AX0 + NC * CELL, AY0 + NR * CELL
CH = 3                     # channel width in cells
R = 4.5                    # ball radius
SPEED = 640.0
SUB = 8                    # physics substeps per frame
DT = 1 / (FPS * SUB)
MAXB = 1600
EMPTY, RING, PINK = 0, 1, 2

def make_grid(gap=None):
    g = np.zeros((NC, NR), np.int8)
    a, b = CH, NC - 1 - CH
    c, d = CH, NR - 1 - CH
    g[a, c:d + 1] = RING; g[b, c:d + 1] = RING; g[a:b + 1, c] = RING; g[a:b + 1, d] = RING
    g[a + 1:b, c + 1:d] = PINK
    if gap is not None: g[gap] = EMPTY
    return g

def run(gap, T, record_ring=False, angle=20.7, pspawn=1.0):
    g = make_grid(gap)
    rng = np.random.default_rng(4)
    ang = math.radians(angle)
    P = np.zeros((MAXB, 2)); V = np.zeros((MAXB, 2)); n = 1
    P[0] = (AX0 + 1.5 * CELL, AY0 + 1.2 * CELL); V[0] = (SPEED * math.cos(ang), SPEED * math.sin(ang))
    frames, events, broken = [], [], []
    ring_hits = []
    def cell(x, y):
        i = np.floor((x - AX0) / CELL).astype(int); j = np.floor((y - AY0) / CELL).astype(int)
        out = (i < 0) | (i >= NC) | (j < 0) | (j >= NR)
        return i, j, out
    nf = int(T * FPS)
    for f in range(nf):
        for s in range(SUB):
            t = (f * SUB + s) * DT
            for ax in (0, 1):
                p, v = P[:n], V[:n]
                nx = p[:, ax] + v[:, ax] * DT
                probe = nx + np.sign(v[:, ax]) * R
                if ax == 0: i, j, out = cell(probe, p[:, 1])
                else: i, j, out = cell(p[:, 0], probe)
                ic, jc = np.clip(i, 0, NC - 1), np.clip(j, 0, NR - 1)
                kind = np.where(out, -1, g[ic, jc])
                hit = (kind != EMPTY)
                p[~hit, ax] = nx[~hit]
                v[hit, ax] *= -1
                for k in np.where(hit)[0]:
                    kk = kind[k]
                    if kk == -1: events.append((t, "wall", p[k, 0], p[k, 1]))
                    elif kk == RING:
                        events.append((t, "ring", p[k, 0], p[k, 1]))
                        if record_ring: ring_hits.append((t, int(ic[k]), int(jc[k])))
                    elif kk == PINK and g[ic[k], jc[k]] == PINK:
                        g[ic[k], jc[k]] = EMPTY
                        broken.append((t, int(ic[k]), int(jc[k])))
                        events.append((t, "pop", p[k, 0], p[k, 1], int(jc[k])))
                        if n < MAXB and (len(broken) == 1 or rng.random() < pspawn):
                            th = rng.uniform(-.65, .65)
                            c_, s_ = math.cos(th), math.sin(th)
                            vx, vy = V[k]
                            if ax == 0: vx = -vx
                            else: vy = -vy
                            P[n] = (AX0 + (ic[k] + .5) * CELL, AY0 + (jc[k] + .5) * CELL); V[n] = (vx * c_ - vy * s_, vx * s_ + vy * c_); n += 1
            if gap is not None and broken and g[gap] == EMPTY:
                gx, gy = AX0 + gap[0] * CELL, AY0 + gap[1] * CELL
                inside = (P[:n, 0] > gx - R) & (P[:n, 0] < gx + CELL + R) & (P[:n, 1] > gy - R) & (P[:n, 1] < gy + CELL + R)
                if not inside.any(): g[gap] = RING; events.append((t, "seal", gx + CELL / 2, gy + CELL / 2))
        frames.append((P[:n].copy(), len(broken)))
    return frames, events, broken, ring_hits

def choose_gap():
    _, _, _, hits = run(None, 22, record_ring=True)
    first = {}
    for t, i, j in hits: first.setdefault((i, j), t)
    a, b, c, d = CH, NC - 1 - CH, CH, NR - 1 - CH
    best = None
    for (i, j), T in first.items():
        corner = (i in (a, b)) and (j in (c, d))
        nearc = (i in (a, b) and j in (c, c + 1, d - 1, d)) or (j in (c, d) and i in (a, a + 1, b - 1, b))
        if corner or nearc or not (11.5 <= T <= 14.5): continue
        near = sum(1 for t, ii, jj in hits if t < T and abs(ii - i) + abs(jj - j) in (1, 2))
        if best is None or near > best[0]: best = (near, (i, j), T)
    return best

if __name__ == "__main__" and sys.argv[1] == "plan":
    print(choose_gap())

GAP = (19, 43)
ANG = 58.5
PSP = 0.36
if __name__ == "__main__" and sys.argv[1] == "sim":
    import pickle, time
    t0 = time.time()
    frames, events, broken, _ = run(GAP, 25, angle=ANG, pspawn=PSP)
    nb = [len(f[0]) for f in frames]; nbr = [f[1] for f in frames]
    total = int(make_grid(GAP).__eq__(PINK).sum())
    clear = next((k for k, x in enumerate(nbr) if x >= total), None)
    print("blocks", total, "entered", next(k for k, x in enumerate(nbr) if x > 0) / FPS, "cleared",
          clear and clear / FPS, "max balls", max(nb), "sim s", round(time.time() - t0, 1))
    for s in range(12, 26, 1): print(s, nb[s * FPS], nbr[s * FPS])
    pickle.dump((frames, events, broken), open("sim.pkl", "wb"))
