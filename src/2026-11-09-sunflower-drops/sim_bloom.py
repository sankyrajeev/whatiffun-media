"""No. 14 — 'Every bead pushes / the others away.'
Glossy glass beads well up one at a time from the centre of a dark pool. Each newcomer squeezes in where the
push from its neighbours is weakest, and nudges every older bead outward. The drip speeds up in stages
(1 -> 10 -> 100 -> 1,000 -> 2,584) and a sunflower of interlocking spirals appears that nobody drew.

Physics: older beads glide outward at constant packing density, r_k = c * sqrt(rank + r0), and each newcomer
lands at the golden angle (137.508 deg) from the last. A repulsion search (E = sum 1/d^3, Douady & Couder's
magnetic-droplet model) converges near it (~138-139 deg) but drifts enough to draw spokes in this
constant-density variant, so we use the angle real growing systems settle on.
Writes bloom.pkl: birth times, angles, smooth count curve N(t)."""
import numpy as np, math, pickle
from scipy.interpolate import PchipInterpolator

FPS = 30
OFF = 1.2                                     # birth radius (in rank units)
LOCK = 1                                      # pure golden angle (search drifts off; see note)
GOLD = math.radians(137.50776)
# smooth count curve (log-pchip through ladder knots, flat at the end so the glide eases to rest)
KT = [0.0, 1.3, 4.0, 9.0, 14.5, 19.4, 20.9, 22.0, 40.0]
KN = [1.0, 3.2, 10.4, 101, 1010, 2380, 2584, 2584, 2584]
_lp = PchipInterpolator(KT, np.log(KN))
def Ncont(t): return float(np.exp(_lp(min(max(t, 0.0), 40.0))))
NEND = 2584

# birth times: bead i is born when N(t) reaches i+1
ts = np.arange(0, 22.0, 1 / 3000)
Nt = np.exp(_lp(ts))
tb = np.zeros(NEND)
for i in range(1, NEND):
    tb[i] = ts[np.searchsorted(Nt, i + 1)]

phi = np.zeros(NEND)
r0 = math.sqrt(OFF)
for n in range(1, NEND):
    if n >= LOCK:
        phi[n] = (phi[n - 1] + GOLD) % (2 * math.pi); continue
    j = np.arange(n); R = np.sqrt(n - j + OFF)
    a = np.linspace(0, 2 * np.pi, 2880, endpoint=False)[:, None]
    d2 = r0 ** 2 + R ** 2 - 2 * r0 * R * np.cos(a - phi[:n])
    phi[n] = float(a[np.argmin((d2 ** -1.5).sum(1)), 0])
dv = np.degrees(np.diff(phi)) % 360
print("first steps", np.round(np.minimum(dv, 360 - dv)[:16], 1))
for m in (10, 100, 1000, NEND):
    print(m, "at", round(float(tb[m - 1]), 2), "s")

# min neighbour spacing of the final pattern (rank units) -> safe bead radius
from scipy.spatial import cKDTree
rk = np.sqrt(NEND - 1 - np.arange(NEND) + OFF)
P = np.c_[rk * np.cos(phi), rk * np.sin(phi)]
dd, _ = cKDTree(P).query(P, 2)
print("nn min", dd[:, 1].min().round(3), "median", np.median(dd[:, 1]).round(3))
pickle.dump(dict(tb=tb, phi=phi, KT=KT, KN=KN, OFF=OFF, NEND=NEND), open("bloom.pkl", "wb"))
