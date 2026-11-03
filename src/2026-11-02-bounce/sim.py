"""Deterministic simulation: one ball in a ring; every wall bounce can split it.
Writes per-frame state + sound events to sim.npz."""
import numpy as np, math, pickle

W, H = 1080, 1920
FPS = 30
SUB = 4
DT = 1.0 / (FPS * SUB)
C = np.array([540.0, 1010.0])
R = 440.0
TARGET = 1000
T_GROW = 25.0          # seconds to reach TARGET (pacing curve)
SPEED = 1000.0

rng = np.random.default_rng(7)

def radius(n):
    return 30.0 * n ** -0.22

def target(t):
    if t <= 0:
        return 1
    return int(round(TARGET ** min(1.0, (t / T_GROW) ** 0.6)))

def rot(v, a):
    c, s = np.cos(a), np.sin(a)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c], 1)

pos = np.array([[C[0] - 120.0, C[1] - 60.0]])
ang0 = math.radians(-58)
vel = np.array([[math.cos(ang0) * SPEED, math.sin(ang0) * SPEED]])
hue = np.array([190.0])
born = np.array([0])

frames = []
events = []   # (time, x, angle, split, n)
f = 0
done_frame = None
while True:
    t = f / FPS
    n = len(pos)
    r = radius(n)
    for s in range(SUB):
        ts = t + s * DT
        pos = pos + vel * DT
        d = pos - C
        dist = np.linalg.norm(d, axis=1)
        hit = np.nonzero(dist + r > R)[0]
        if len(hit) == 0:
            continue
        nrm = d[hit] / dist[hit, None]
        v = vel[hit]
        v = v - 2 * np.sum(v * nrm, 1, keepdims=True) * nrm
        pos[hit] = C + nrm * (R - r - 0.5)
        allow = max(0, target(ts) - len(pos))
        order = rng.permutation(len(hit))
        split_mask = np.zeros(len(hit), bool)
        split_mask[order[:allow]] = True
        # bounce jitter
        v = v * rng.uniform(0.98, 1.02, (len(hit), 1))
        sp = np.linalg.norm(v, axis=1, keepdims=True)
        v = v / sp * np.clip(sp, 900, 1100)
        new_p, new_v, new_h = [], [], []
        if split_mask.any():
            idx = np.nonzero(split_mask)[0]
            a = rng.uniform(math.radians(9), math.radians(24), len(idx))
            vp = rot(v[idx], a)
            vc = rot(v[idx], -a)
            nn = nrm[idx]
            spd = np.linalg.norm(v[idx], axis=1)
            okp = np.sum(vp * nn, 1) < -0.15 * spd
            okc = np.sum(vc * nn, 1) < -0.15 * spd
            vp[~okp] = v[idx][~okp]
            vc[~okc] = v[idx][~okc]
            v[idx] = vp
            new_p = pos[hit[idx]].copy()
            new_v = vc
            new_h = hue[hit[idx]] + 9.0
        vel[hit] = v
        for k, hi in enumerate(hit):
            a = math.atan2(nrm[k, 1], nrm[k, 0])
            events.append((ts, float(pos[hi, 0]), a, bool(split_mask[k]), len(pos)))
        if len(new_p):
            pos = np.vstack([pos, new_p])
            vel = np.vstack([vel, new_v])
            hue = np.concatenate([hue, new_h % 360])
            born = np.concatenate([born, np.full(len(new_p), f)])
        if len(pos) >= TARGET:
            break
    frames.append(dict(pos=pos.astype(np.float32).copy(), hue=hue.astype(np.float32).copy(),
                       born=born.copy(), n=len(pos)))
    f += 1
    if len(pos) >= TARGET:
        done_frame = f - 1
        break
    if f > FPS * 60:
        raise SystemExit("never reached target")

print("reached", TARGET, "at frame", done_frame, "t=%.2fs" % (done_frame / FPS), "events", len(events))
with open("sim.pkl", "wb") as fh:
    pickle.dump(dict(frames=frames, events=events, done=done_frame, C=C, R=R, W=W, H=H, FPS=FPS), fh)
