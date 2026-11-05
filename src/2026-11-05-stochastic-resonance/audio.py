"""Soundtrack from the simulation's own events.
- every bead flip = a tiny glass tick, panned by the bead's x; up-flips a touch higher than down-flips.
  Dense flips (the hard-shaken side) are thinned and turned down, so they become a crackle.
- the middle third flipping together each half-beat = a deep thump, its weight = how many flipped together.
- freeze = silence + swell; noise switched off = a final thump, then only the room."""
import math, wave
import numpy as np
from scipy.signal import butter, sosfilt
D = np.load("sr.npz"); EV = D["EV"]; TS = D["TS"]; T = float(D["T"])
TOTAL, FPS, SR = 750, 30, 48000
F_FRZ, F_RES, F_OFF, F_CARD = 100, 145, 560, 650
NS = int(TOTAL / FPS * SR)
rng = np.random.default_rng(7)
L = np.zeros(NS); R = np.zeros(NS)
def pan(p): return math.cos((p + 1) * math.pi / 4), math.sin((p + 1) * math.pi / 4)
def add(sig, t0, g, p=0.0):
    i = int(t0 * SR)
    if i >= NS or i < 0: return
    sig = sig[:NS - i]; gl, gr = pan(p)
    L[i:i + len(sig)] += sig * g * gl; R[i:i + len(sig)] += sig * g * gr
BP = butter(2, [2500, 10000], btype="bandpass", fs=SR, output="sos")
def tick(fc):
    t = np.arange(int(.05 * SR)) / SR
    n = sosfilt(BP, rng.standard_normal(len(t))) * np.exp(-t * 900)
    return (np.sin(2 * np.pi * fc * t) * np.exp(-t * 110) + .35 * np.sin(2 * np.pi * fc * 2.76 * t) * np.exp(-t * 160) + .6 * n) * np.minimum(1, t * 8000)
BANK = {d: [tick(fc) for fc in rng.uniform(*((2600, 3100) if d > 0 else (2000, 2400)), 12)] for d in (1, -1)}
# thin events: per 10 ms block keep at most 6, scale gain by density
tf = EV[:, 0] / FPS; blk = (tf * 100).astype(int)
order = rng.permutation(len(EV)); seen = {}
for j in order:
    b = blk[j]; seen[b] = seen.get(b, 0) + 1
cnt = np.array([seen[b] for b in blk]); kept = {}
for j in order:
    b = blk[j]
    if kept.get(b, 0) >= 6: continue
    kept[b] = kept.get(b, 0) + 1
    i = int(EV[j, 1]); d = int(EV[j, 2])
    g = .28 / (1 + .08 * cnt[j]) * (1.0 if 333 <= i < 667 else .45 if i >= 667 else .9)
    add(BANK[d][rng.integers(12)], tf[j] + rng.uniform(0, .01), g, (i / 999 - .5) * 1.6)
# groove: thump per half-beat from the middle group's collective flips
def thump(f0=50, dur=0.9, k=5.0):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * (f0 * t + 40 * (1 - np.exp(-t * 18)) / 18)) * np.exp(-t * k) * np.minimum(1, t * 400)
B = (EV[:, 1] >= 333) & (EV[:, 1] < 667)
hb = np.floor(np.interp(EV[:, 0], np.arange(TOTAL), TS) / (T / 2)).astype(int)
for h in np.unique(hb[B]):
    m = B & (hb == h)
    if m.sum() < 8: continue
    t0 = float(np.median(tf[m])); up = EV[m, 2].mean() > 0
    add(thump(55 if up else 47), t0, min(.9, .03 * m.sum()))
# the beat itself: a soft muted wood tock at each peak of the weak drive (paused during the freeze)
def tock():
    t = np.arange(int(.18 * SR)) / SR
    return (np.sin(2 * np.pi * 180 * t) * np.exp(-t * 38) + .3 * np.sin(2 * np.pi * 410 * t) * np.exp(-t * 60)) * np.minimum(1, t * 3000)
ft = np.arange(TOTAL)
for f in range(1, TOTAL):
    a, b = TS[f - 1] / T, TS[f] / T
    for q in (0.25, 0.75):
        if math.floor(b - q) > math.floor(a - q):
            add(tock(), f / FPS, .32 if q == .25 else .22, 0)
# freeze swell, release, switch-off
n = int((F_RES - F_FRZ) / FPS * SR); tt = np.arange(n) / SR
add(sosfilt(butter(2, 900, btype="low", fs=SR, output="sos"), rng.standard_normal(n)) * (tt / tt[-1]) ** 3, F_FRZ / FPS, .45)
add(thump(42, 1.4, 3), F_FRZ / FPS, .5); add(thump(40, 1.6, 2.6), F_RES / FPS, .6)
add(thump(36, 2.4, 1.8), F_OFF / FPS, .9)
def bell(f, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    return sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in [(1, 1, 1.3), (2.0, .4, 2.2), (2.76, .25, 3.4)])
add(bell(392), F_OFF / FPS + .05, .08)
# room tone so the silence is a real silence, not digital zero
room = sosfilt(butter(2, 400, btype="low", fs=SR, output="sos"), rng.standard_normal(NS)) * .004
L += room; R += room
fi = int(.05 * SR); L[:fi] *= np.linspace(0, 1, fi); R[:fi] *= np.linspace(0, 1, fi)
fo = int(.6 * SR); L[-fo:] *= np.linspace(1, .3, fo); R[-fo:] *= np.linspace(1, .3, fo)
out = np.stack([L, R], 1); pk = np.max(np.abs(out)); out = np.tanh(out / pk * 1.6) / np.tanh(1.6) * .9
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print([round(float(np.sqrt((out[s * SR:(s + 1) * SR] ** 2).mean())), 3) for s in range(int(NS / SR))])
