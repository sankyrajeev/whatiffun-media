"""'When drops touch, they become one.'
Glass drops land on a dark window pane. Small drops cling; any two that touch merge into one (volume kept).
Once a drop is heavy enough it slides, sweeping up everything below it, and pours into a gold trough.
At the end the rain fades and the pane lets go: every drop slides down and the trough fills."""
import numpy as np, pickle, math, os
from scipy.spatial import cKDTree
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 3
X0, X1, Y0, Y1 = 130.0, 950.0, 520.0, 1440.0     # pane interior
rng = np.random.default_rng(int(E("SEED", 7)))
SECS = E("SECS", 30)
RC0 = E("RC", 14.0)

NPRE = int(E("NPRE", 260))
x = np.r_[540.0, rng.uniform(X0 + 10, X1 - 10, NPRE)]; y = np.r_[560.0, rng.uniform(Y0 + 10, Y1 - 60, NPRE)]
r = np.r_[24.0, rng.uniform(4.2, 8.0, NPRE)]; born = np.full(NPRE + 1, -30)
ok = np.ones(len(x), bool)
for i in range(len(x)):
    for j in range(i):
        if ok[j] and math.hypot(x[i] - x[j], y[i] - y[j]) < r[i] + r[j] + 3: ok[i] = False; break
x, y, r, born = x[ok], y[ok], r[ok], born[ok]
ph = rng.uniform(0, 6.28, len(x))
merges = 0
frames, counts, events, drained = [], [], [], []
vol_in = 0.0
end_f = None
for f in range(int(SECS * FPS)):
    t = f / FPS
    # rain: ramps up, then fades
    if t < E("RAIN_END", 17.5):
        rate = E("R0", 25) + E("R1", 170) * min(1, t / E("RAMP", 13)) ** 1.3
        rate *= 1 - ss if (ss := max(0, (t - (E("RAIN_END", 17.5) - 2.5)) / 2.5)) else 1
        k = rng.poisson(rate / FPS)
        if k:
            nx = rng.uniform(X0 + 8, X1 - 8, k); ny = rng.uniform(Y0 + 8, Y1 - 60, k); nr = rng.uniform(4.2, 9.5, k)
            big = (rng.random(k) < E("BIGP", .02)) & (t > 3); nr[big] = rng.uniform(15.0, 19.0, big.sum())
            x = np.r_[x, nx]; y = np.r_[y, ny]; r = np.r_[r, nr]; born = np.r_[born, np.full(k, f)]
            ph = np.r_[ph, rng.uniform(0, 6.28, k)]
            for i in range(k): events.append((t + rng.uniform(0, 1 / FPS), "land", float(nx[i]), float(ny[i]), float(nr[i])))
    # pane lets go at the end
    d0 = E("DRAIN", 18.5)
    rc = RC0 - (RC0 + 16) * min(1, max(0, (t - d0) / 2.0)) ** 1.5
    for s in range(SUB):
        dt = 1 / (FPS * SUB)
        v = np.where(r > rc, 30 + 30 * (r - rc), 0.0); v = np.minimum(v, 760)
        vx = np.where(v > 0, 38 * np.sin(ph + y * .013) * np.minimum(1, v / 200), 0)
        y = y + v * dt; x = np.clip(x + vx * dt, X0 + r, X1 - r)
        # merges
        if len(x) > 1:
            tree = cKDTree(np.c_[x, y])
            pairs = tree.query_pairs(2 * r.max(), output_type="ndarray")
            if len(pairs):
                a, b = pairs[:, 0], pairs[:, 1]
                dd = np.hypot(x[a] - x[b], y[a] - y[b])
                m = dd < (r[a] + r[b]) * .92
                pairs = pairs[m]
                alive = np.ones(len(x), bool)
                order = np.argsort(-(r[pairs[:, 0]] + r[pairs[:, 1]]))
                for a, b in pairs[order]:
                    if not (alive[a] and alive[b]): continue
                    if r[b] > r[a]: a, b = b, a
                    va, vb = r[a] ** 3, r[b] ** 3
                    x[a] = (x[a] * va + x[b] * vb) / (va + vb); y[a] = max(y[a], (y[a] * va + y[b] * vb) / (va + vb))
                    r[a] = (va + vb) ** (1 / 3); alive[b] = False; merges += 1
                    events.append((t + s * dt, "merge", float(x[a]), float(y[a]), float(r[a])))
                if not alive.all():
                    x, y, r, born, ph = x[alive], y[alive], r[alive], born[alive], ph[alive]
        # pour into the trough
        out = y - r * .3 > Y1
        if out.any():
            for i in np.where(out)[0]:
                events.append((t + s * dt, "pour", float(x[i]), Y1, float(r[i])))
                vol_in += r[i] ** 3
            keep = ~out; x, y, r, born, ph = x[keep], y[keep], r[keep], born[keep], ph[keep]
    frames.append(np.c_[x, y, r, born].astype(np.float32)); counts.append(merges); drained.append(vol_in)
    if f % 60 == 0: print(f"t={t:4.1f} drops={len(x)} merges={merges} rmax={r.max() if len(r) else 0:.1f} vol={vol_in:.0f}", flush=True)
    if t > d0 and len(x) == 0 and end_f is None: end_f = f
    if end_f is not None and f > end_f + 20: break
print("frames", len(frames), "merges", merges, "empty at", end_f and round(end_f / FPS, 2))
pickle.dump(dict(frames=frames, counts=np.array(counts), events=events, drained=np.array(drained),
                 geom=dict(X0=X0, X1=X1, Y0=Y0, Y1=Y1)), open("drops.pkl", "wb"))
