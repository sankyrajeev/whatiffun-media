"""Sample C — 'Touch it and you stick.'
Beads rain from the top. Anything that touches the crystal sticks to it (ballistic aggregation from one
seed). Beads that miss fall away. The crystal branches upward until it reaches the rain line."""
import numpy as np, pickle, math, os
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 4
BR = E("BR", 6.0)
TOP_LINE, SEED_Y, CX = 600.0, 1440.0, 540.0
G = 2200.0
rng = np.random.default_rng(int(E("SEED", 4)))
SECS = E("SECS", 30)
SIGMA = E("SIGMA", 170)

cell = 2 * BR
grid = {}
stuck = []        # (x, y, t_frame)
def gkey(x, y): return (int(x // cell), int(y // cell))
def add_stuck(x, y, f):
    stuck.append((x, y, f)); grid.setdefault(gkey(x, y), []).append(len(stuck) - 1)
def near(x, y):
    kx, ky = gkey(x, y)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in grid.get((kx + dx, ky + dy), ()):
                sx, sy, _ = stuck[j]
                if (sx - x) ** 2 + (sy - y) ** 2 < (2 * BR) ** 2: return j
    return None
# seed: a small brass pin at the bottom centre
add_stuck(CX, SEED_Y, 0)

falling = []      # [x, y, vx, vy]
frames_fall, frames_n, events = [], [], []
done_at = None
for f in range(int(SECS * FPS)):
    t = f / FPS
    rate = E("RATE0", 3) + E("RATE1", 26) * min(1, t / E("RAMP", 12)) ** 1.4   # spawns per frame
    if done_at is None:
        k = rng.poisson(rate)
        for _ in range(k):
            x = rng.normal(CX, SIGMA); x = min(max(x, 140), 940)
            falling.append([x, rng.uniform(480, 540), rng.normal(0, 25), rng.uniform(200, 420)])
    keep = []
    for b in falling:
        hit = None
        for s in range(SUB):
            dt = 1 / (FPS * SUB)
            b[3] += G * dt; b[0] += b[2] * dt; b[1] += b[3] * dt
            j = near(b[0], b[1])
            if j is not None:
                sx, sy, _ = stuck[j]
                dx, dy = b[0] - sx, b[1] - sy; dd = math.hypot(dx, dy) or 1
                x2, y2 = sx + dx / dd * 2 * BR, sy + dy / dd * 2 * BR
                add_stuck(x2, y2, f)
                events.append((f / FPS + s * dt, x2, y2, math.hypot(b[2], b[3])))
                hit = True
                if done_at is None and y2 < TOP_LINE + 40: done_at = f
                break
        if not hit and b[1] < 2000: keep.append(b)
    falling = keep
    frames_fall.append(np.array([[b[0], b[1]] for b in falling], np.float32).reshape(-1, 2))
    frames_n.append(len(stuck))
    if f % 60 == 0: print(f"t={t:4.1f} stuck={len(stuck)} falling={len(falling)} top_y={min(s[1] for s in stuck):.0f}", flush=True)
    if done_at is not None and f > done_at + 45 and not falling: break
print("frames", len(frames_fall), "stuck", len(stuck), "reached top at", done_at and round(done_at / FPS, 1))
pickle.dump(dict(stuck=np.array(stuck, np.float32), falling=frames_fall, n=np.array(frames_n), events=events,
                 done=done_at, geom=dict(BR=BR, TOP=TOP_LINE, SEED_Y=SEED_Y, CX=CX)), open("stick.pkl", "wb"))
