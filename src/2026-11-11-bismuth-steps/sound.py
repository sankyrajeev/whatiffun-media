"""Soundtrack from the growth itself: a crisp metallic tink as every bar snaps to its corner (pitch by crystal size and
step, pentatonic), a fine crystallising crackle that follows how much is growing, a struck-metal note per finished step,
a soft thump + chord at count milestones, a shimmer under the closing glint, and a resolving chord under the end card."""
import sys, numpy as np
sys.path.insert(0, "/home/claude/whatiffun-media/src/2026-11-05-asmr-samples")
from kit import Mix, glass_click, mallet, thud, note, SR
from scipy.signal import butter, sosfilt
from motion import *

HOLD, CARD, XF = 24, 84, 18
TOTAL = NFR + HOLD + CARD + XF
T = TOTAL / 30
mx = Mix(T)
rng = np.random.default_rng(7)
def tsec(simt): return (simt - T0)
def X(x): return 540 + 170 * float(x)

def tink(f0, dec=38, dur=.35):
    t = np.arange(int(dur * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + m) * np.exp(-t * dec * d) for m, a, d in
            [(1, 1, 1), (2.32, .55, 1.6), (4.25, .3, 2.4), (6.8, .18, 3.5)])
    n = rng.standard_normal(len(t)) * np.exp(-t * 2200) * .35
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 9000)
def noise_band(dur, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), rng.standard_normal(int(dur * SR)))

# ---- bar tinks, gain normalised by local event density ----
te = np.array([b["te"] for b in bars]); tt = np.array([tsec(x) for x in te])
ok = (tt > -.05) & (tt < NFR / 30)
hist, edges = np.histogram(tt[ok], bins=np.arange(0, NFR / 30 + .5, .5))
def dens(t): i = min(len(hist) - 1, max(0, int(t / .5))); return max(1, hist[i] * 2)
for i, b in enumerate(bars):
    t = tt[i]
    if not ok[i]: continue
    s = b["s"]; dep = {1.0: 0}.get(s, int(round(np.log(s) / np.log(SCALE))))
    nn = 2 + b["k"] + 3 * dep + (i % 2)
    f0 = note(nn, 392.0) * (1 + .004 * rng.standard_normal())
    g = (.16 + .2 * s) / max(1, dens(t) / 6) ** .32
    mx.add(tink(f0, 30 + 25 * dep), max(0, t), g, X(b["c0"][0]))

# ---- crystallising crackle: sparse micro-clicks, rate follows the growing length ----
grow_rate = np.zeros(int(T * 30) + 2)
for b in bars:
    a, z = tsec(b["ts"]) * 30, tsec(b["te"]) * 30
    for f in range(max(0, int(a)), min(NFR, int(z) + 1)): grow_rate[f] += b["s"]
for f in range(NFR):
    lam = min(140, 10 * grow_rate[f]) / 30
    for _ in range(rng.poisson(lam)):
        t = f / 30 + rng.random() / 30
        mx.add(glass_click(rng.uniform(3800, 7600), rng.uniform(500, 900), .03, .8), t, .035 * rng.uniform(.5, 1), rng.uniform(150, 930))

# ---- struck metal per finished step (bigger crystal = lower) ----
for (t_, depth, cid, zc, s) in steps:
    t = tsec(t_)
    if t < 0 or t > NFR / 30: continue
    k = sum(1 for x in steps if x[2] == cid and x[0] <= t_) - 1
    g = (.13 if depth == 0 else .09 * s / SCALE) / max(1, dens(t) / 10) ** .35
    mx.add(mallet(note(k + 2 * depth, 196.0), 1.4, .8), t, g, X(zc[0]))
# new crystal sprouts from the main crystal: a soft low thump
for C in crystals[1:]:
    t = tsec(C["t0"])
    if 0 <= t < NFR / 30 and C["depth"] == 1: mx.add(thud(62, .5), t, .32, X(C["origin"][0]))

# ---- milestones: thump + rising chord ----
CNT = [count(f) for f in range(NFR)]
CH = [[0, 2, 4], [1, 3, 5], [2, 4, 6], [3, 5, 7]]
MS = []
for i, m in enumerate([10, 50, 100, 200]):
    f = next(f for f in range(NFR) if CNT[f] >= m); MS.append(f)
    mx.add(thud(55, .7), f / 30, .55, 540)
    for j, nn in enumerate(CH[i]): mx.add(mallet(note(nn + 2, 196.0), 2.0, .7), f / 30 + .03 * j, .14, 400 + 140 * j)

# ---- low warm bed so the opening isn't thin: a quiet metallic hum that swells with growth ----
n = int(NFR / 30 * SR); tp = np.arange(n) / SR
bed = sum(np.sin(2 * np.pi * note(nn, 65.41) * tp) for nn in (0, 2, 4)) * (.6 + .4 * np.sin(2 * np.pi * .2 * tp))
env = np.interp(tp, np.arange(NFR) / 30, np.minimum(1, grow_rate[:NFR] / 6) * .7 + .3)
mx.add(bed * env * np.minimum(1, tp / .3) * np.minimum(1, (NFR / 30 + .5 - tp) / 1.5), 0, .025, 540)

# ---- glint sweep: rising shimmer of high notes ----
for j in range(10):
    mx.add(mallet(note(6 + j, 261.63), 1.8, .9), (372 + j * 10) / 30, .13, 300 + 50 * j)
n = int(3 * SR); s = noise_band(3, 5000, 11000) * np.sin(np.linspace(0, np.pi, n)) ** 2
mx.add(s, 380 / 30, .09, 600)

# ---- cooling: the finished cluster keeps ticking softly as it cools (sparse high tinks, a warm swell) ----
for j, t in enumerate(np.arange(15.2, 18.6, .23)):
    mx.add(tink(note(int(rng.integers(8, 16)), 392.0), 34), t + rng.uniform(-.05, .05), .16 * rng.uniform(.6, 1), rng.uniform(200, 880))
n = int(3.4 * SR); tp2 = np.arange(n) / SR; sw = np.zeros(n)
for nn in (2, 4, 7): sw += np.sin(2 * np.pi * note(nn, 196.0) * tp2)
mx.add(sw * np.sin(np.linspace(0, np.pi, n)) ** 2, 15.0, .05, 540)

# ---- end card: resolving chord + pad ----
t0 = (NFR + HOLD) / 30
for j, nn in enumerate([0, 4, 7, 9]): mx.add(mallet(note(nn, 130.81), 3.0, .6), t0 + .08 * j, .22, 440 + 70 * j)
n = int(3.6 * SR); tp = np.arange(n) / SR; pad = np.zeros(n)
for nn in [0, 4, 7, 12]: pad += np.sin(2 * np.pi * note(nn, 130.81) * tp) * (1 + .3 * np.sin(2 * np.pi * 3.1 * tp))
pad *= np.minimum(1, tp / .6) * np.exp(-tp * .55)
mx.add(pad, t0 - .2, .07, 540)
import json; json.dump(MS, open("/home/claude/bi/milestones.json", "w"))
print(mx.save("/home/claude/bi/bi.wav"))
