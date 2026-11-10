"""Soundtrack from the machine's own motion: brass ticks of the arms, the nib's fine scratch, a brass clunk + chord at
each new arm count, a bright ring when the line closes, a low brass slide as the knight rises, a resolving chord."""
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
def X(z): return 540 + float(np.real(z)) * 230
def tsec(f): return f / 30

def tick(f0, dur=.05, dec=260):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .6 * np.sin(2 * np.pi * f0 * 2.41 * t) + .35 * np.sin(2 * np.pi * f0 * 5.13 * t)) * np.exp(-t * dec)
    n = rng.standard_normal(len(t)) * np.exp(-t * 2500) * .4
    return (s + n) * np.minimum(1, t * 8000)
def clunk(f0=150):
    t = np.arange(int(1.1 * SR)) / SR
    p = sum(a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t * d) for m, a, d in [(1, 1, 7), (2.71, .55, 11), (5.2, .3, 18), (8.6, .18, 30)])
    th = np.zeros(len(t)); d = thud(58, .6); th[:len(d)] = d
    return (p * .6 + th) * np.minimum(1, t * 3000)
def noise_band(dur, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), rng.standard_normal(int(dur * SR)))

# tip positions per frame (for panning + nib speed)
tips = []
for f in range(NFR):
    st = state(f); cs, _ = chain(st); tips.append(cs[-1])
tips = np.array(tips)

# ---- arm ticks: arm 0 clicks 12 times a turn, arms 1-3 four times a turn (higher, softer) ----
def drawing_segments():
    segs = [(0, FLASH, .52 * 2 * np.pi, .72 * 2 * np.pi, 1024)]
    for i, N in enumerate(STAGES):
        a = STARTS[i] + UNF; b = STARTS[i] + SFR[i]
        segs.append((a - 1, b, 0.0, 2 * np.pi, N))
    return segs
for (fa, fb, ta, tb, N) in drawing_segments():
    for j, (teeth, f0, g) in enumerate([(12, 1900, .16), (4, 2600, .07), (4, 3100, .05), (4, 3500, .04)]):
        if j >= N: break
        k = abs(K[j]); step = 2 * np.pi / (teeth * k)
        for n in range(int(np.ceil(ta / step)), int(tb / step) + 1):
            tv = n * step; f = fa + (tv - ta) / (tb - ta) * (fb - fa)
            if f >= fb: continue
            mx.add(tick(f0 * (1 + .03 * rng.standard_normal())), tsec(f), g * (.8 + .4 * rng.random()), X(tips[min(int(f), NFR - 1)]))

# ---- nib scratch: fine high noise following the nib speed; whirr of many small arms ----
scr = noise_band(T, 3500, 9000); whir = noise_band(T, 900, 2400)
env = np.zeros(len(scr)); wenv = np.zeros(len(scr))
for f in range(1, NFR):
    st = state(f)
    drawing = st["frac"] > 0 and f < DRAW_END and not (FLASH <= f < S0)
    sp = abs(tips[f] - tips[f - 1]) * 30
    a, b = int(tsec(f - 1) * SR), int(tsec(f) * SR)
    env[a:b] = np.linspace(env[a - 1] if a else 0, min(1, sp / 3.0) * drawing, b - a)
    wenv[a:b] = (np.log2(st["n"]) / 10) * drawing * (1 - st["retract"])
sm = butter(1, 30, fs=SR, output="sos")
L = sosfilt(sm, env) * scr * .09; Wb = sosfilt(sm, wenv) * whir * .06
mx.L += L + Wb; mx.R += L * .9 + Wb * 1.05

# ---- flash-forward shimmer at frame 0, rewind whoosh, stage clunks + chords ----
for i, nn in enumerate([7, 9, 11]): mx.add(mallet(note(nn, 261.63), 1.6, .7), .0 + .04 * i, .18, 540)
w = noise_band(.4, 600, 5000) * np.linspace(0, 1, int(.4 * SR)) ** 2 * np.linspace(1, 0, int(.4 * SR)) ** .3
mx.add(w, tsec(FLASH), .25, 540)
CH = [[0, 2, 4], [1, 3, 5], [2, 4, 6], [3, 5, 7], [4, 6, 8], [5, 7, 9]]
for i, N in enumerate(STAGES):
    f = STARTS[i]
    mx.add(clunk(130 + 12 * i), tsec(f), .55, X(C0))
    for j, nn in enumerate(CH[i]): mx.add(mallet(note(nn + 2, 196), 1.8, .8), tsec(f) + .03 * j, .16, 400 + 140 * j)
# line closes: bright ring
for j, nn in enumerate([5, 7, 9, 12]): mx.add(mallet(note(nn, 261.63), 2.4, 1.0), tsec(DRAW_END) + .05 * j, .2, 380 + 100 * j)
# knight rises: low brass slide swell, then a soft landing thump
n = int(1.8 * SR); s = noise_band(1.8, 120, 900) * np.sin(np.linspace(0, np.pi, n)) ** 2
tt_ = np.arange(n) / SR; s += .5 * np.sin(2 * np.pi * (55 * tt_ + 20 * tt_ ** 2)) * np.sin(np.linspace(0, np.pi, n))
mx.add(s, tsec(DRAW_END + 12), .3, 540)
mx.add(clunk(98), tsec(DRAW_END + 64), .5, 540)
# end card: gentle resolving chord
for j, nn in enumerate([0, 4, 7, 9]): mx.add(mallet(note(nn, 130.81), 3.0, .6), tsec(NFR + HOLD) + .08 * j, .22, 440 + 70 * j)
n = int(3.6 * SR); tp = np.arange(n) / SR; pad = np.zeros(n)
for nn in [0, 4, 7, 12]: pad += np.sin(2 * np.pi * note(nn, 130.81) * tp) * (1 + .3 * np.sin(2 * np.pi * 3.1 * tp))
pad *= np.minimum(1, tp / .6) * np.exp(-tp * .55)
mx.add(pad, tsec(NFR + HOLD) - .2, .07, 540)
print(mx.save("/home/claude/eq/eq.wav"))
