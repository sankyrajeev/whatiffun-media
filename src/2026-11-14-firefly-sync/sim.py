"""FAMOUS DEMO: firefly synchrony (pulse-coupled oscillators, Mirollo-Strogatz style).
Every firefly charges at its own natural rate and flashes when full. When it sees a neighbour flash, its own
charge is nudged up a little (more if it is already nearly full, less if far away). Fireflies nudged past full
flash at once - so flashes cascade, and patches that drift close enough get swallowed in one go."""
import numpy as np, pickle, sys, math

DT = 1 / 600

def make(seed, N=300):
    rng = np.random.default_rng(seed)
    # meadow homes: jittered poisson-ish scatter in an ellipse-ish band
    pts = []
    # an organic swarm: the union of three soft blobs over the grass (left, right, low middle)
    blobs = [(330, 1030, 230, 400), (760, 1070, 215, 390), (545, 1290, 400, 200)]
    def inside(x, y):
        return any(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1 for cx, cy, rx, ry in blobs)
    tries = 0
    while len(pts) < N:
        tries += 1
        x, y = rng.uniform(125, 955), rng.uniform(630, 1480)
        md = 34 if tries < 200000 else 26
        if inside(x, y) and all((x - a) ** 2 + (y - b) ** 2 > md ** 2 for a, b in pts): pts.append((x, y))
    P = np.array(pts)
    return rng, P

def run(seed=3, N=300, f0=0.92, fsd=0.035, lam=150.0, eps=(0.004, 0.030), T=24.0, ramp=(0.0, 14.0),
        left_df=0.0, refr=0.18, conc=1.6):
    rng, P = make(seed, N)
    f = f0 + fsd * rng.standard_normal(N) + left_df * np.tanh((540 - P[:, 0]) / 120)
    phi = rng.uniform(0, 1, N)
    d = np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))
    Wm = np.exp(-d / lam); np.fill_diagonal(Wm, 0); Wm /= Wm.sum(1, keepdims=True).mean()
    ref = np.zeros(N)
    flashes = []                       # (t, i)
    steps = int(T / DT)
    for k in range(steps):
        t = k * DT
        u = min(1, max(0, (t - ramp[0]) / (ramp[1] - ramp[0])))
        e = eps[0] + (eps[1] - eps[0]) * (u * u * (3 - 2 * u))
        phi += f * DT
        ref -= DT
        fired = np.zeros(N, bool)
        new = phi >= 1
        while new.any():
            fired |= new
            phi[new] = 0; ref[new] = refr
            kick = e * Wm[:, new].sum(1)
            ok = (~fired) & (ref <= 0)
            # concave charge curve -> kick grows with charge
            phi[ok] += kick[ok] * (1 + conc * phi[ok])
            new = ok & (phi >= 1)
        for i in np.nonzero(fired)[0]: flashes.append((t, int(i)))
    return P, f, flashes

def clusters(flashes, T, win=0.07):
    """largest flash burst (number of distinct fireflies within win) in each 1/30 s frame's last 1.2 s"""
    ts = np.array([a for a, b in flashes]); ids = np.array([b for a, b in flashes])
    out = []
    for fr in range(int(T * 30)):
        t = fr / 30
        m = (ts > t - 1.15) & (ts <= t)
        best = 0
        tt = ts[m]
        if len(tt):
            j = 0
            for i in range(len(tt)):
                while tt[i] - tt[j] > win: j += 1
                best = max(best, i - j + 1)
        out.append(best)
    return out

def bursts(flashes, gap=0.02):
    out = []; cur = []
    for t, i in flashes:
        if cur and t - cur[-1][0] > gap:
            out.append((cur[0][0], len(cur), np.mean([P_X[j] for _, j in cur]))); cur = []
        cur.append((t, i))
    if cur: out.append((cur[0][0], len(cur), np.mean([P_X[j] for _, j in cur])))
    return out

if __name__ == "__main__":
    import json
    kw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    T = kw.get("T", 24.0)
    P, f, fl = run(**kw)
    c = clusters(fl, T)
    print([c[i] for i in range(0, len(c), 15)])
