"""Soundtrack from the simulation itself.
- The string's own voice: partial k = mode k of the chain (frequency ratio OM_k/OM_1, slightly inharmonic like the
  real chain), loudness = sqrt(energy in that mode). Pure tone at the pluck, a buzzing chord as energy spreads,
  pure again at the recurrence.
- One glassy tick per swing, panned to where the string is stretched hardest (the travelling bump).
- Freeze = silence + swell; recurrence = low thump + bell."""
import math, wave
import numpy as np
from scipy.signal import butter, sosfilt
D = np.load("fput.npz"); X, Ef, DT, Ts = D["X"], D["Ef"], float(D["DT"]), float(D["Ts"])
P = np.load("timeline.npy")
from render import F_FRZ, F_RES, F_REC, F_CARD, TOTAL, ROWS, XS
FPS, SR = 30, 48000
NS = int(TOTAL / FPS * SR); ts = np.arange(NS) / SR; ft = np.arange(TOTAL) / FPS
rng = np.random.default_rng(3)
N = X.shape[1]; OM = 2 * np.sin(np.arange(1, N + 1) * np.pi / (2 * (N + 1)))
L = np.zeros(NS); R = np.zeros(NS)
def pan(p): return math.cos((p + 1) * math.pi / 4), math.sin((p + 1) * math.pi / 4)
def add(sig, t0, g, p=0.0):
    i = int(t0 * SR)
    if i >= NS or i < 0: return
    sig = sig[:NS - i]; gl, gr = pan(p)
    L[i:i + len(sig)] += sig * g * gl; R[i:i + len(sig)] += sig * g * gr

# --- string voice ---
idx = np.clip(np.round(P * Ts / DT).astype(int), 0, len(Ef) - 1)
amp = np.sqrt(Ef[idx, :10])                    # (TOTAL, 10)
frz = np.array([1.0 if not (F_FRZ < f <= F_RES) else 0.0 for f in range(TOTAL)])
duck = np.convolve(frz, np.ones(5) / 5, mode="same")
F0 = 98.0
for k in range(10):
    a = np.interp(ts, ft, amp[:, k] * duck) / (1 + .25 * k)
    fr = F0 * OM[k] / OM[0]
    ph = 2 * np.pi * fr * ts + rng.uniform(0, 6.28)
    sig = np.sin(ph) + .12 * np.sin(2 * ph)
    gl, gr = pan((-1) ** k * min(.7, .12 * k))
    L += .16 * a * sig * gl; R += .16 * a * sig * gr

# --- ticks: one per swing ---
def tick(fc):
    t = np.arange(int(.12 * SR)) / SR
    n = sosfilt(butter(2, [2000, 9000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t * 700)
    return (np.sin(2 * np.pi * fc * t) * np.exp(-t * 45) + .4 * np.sin(2 * np.pi * fc * 2.76 * t) * np.exp(-t * 80) + .8 * n) * np.minimum(1, t * 6000)
for f in range(1, TOTAL):
    a, b = P[f - 1], P[f]
    if math.floor(b + 1e-9) > math.floor(a + 1e-9):
        n = int(math.floor(b + 1e-9))
        row = ROWS[min(n, len(ROWS) - 1)]
        xp = XS[np.argmax(row)] if n < len(ROWS) else 540
        e1 = Ef[min(len(Ef) - 1, int(n * Ts / DT)), 0]
        rate = b - a
        g = .5 / (1 + 2.5 * rate)
        add(tick(1500 + 900 * e1 + rng.uniform(-40, 40)), f / FPS, g, (xp - 540) / 500)

# --- thumps ---
def thump(f0=52, dur=1.4, k=3.0):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * (f0 * t + 30 * (1 - np.exp(-t * 16)) / 16)) * np.exp(-t * k)
def bell(f, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    return sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in [(1, 1, 1.3), (2.0, .4, 2.2), (2.76, .25, 3.4), (5.4, .1, 6)])
add(thump(), F_FRZ / FPS, .55)                    # the stop
add(thump(46), F_RES / FPS, .65)                  # the release
add(thump(40, 2.0, 2.2), F_REC / FPS, .9)        # the recurrence
add(bell(F0 * 4), F_REC / FPS, .16); add(bell(F0 * 6), F_REC / FPS + .04, .07, .3)
# swell during freeze
n = int((F_RES - F_FRZ) / FPS * SR); tt = np.arange(n) / SR
sw = sosfilt(butter(2, 900, btype="low", fs=SR, output="sos"), rng.standard_normal(n)) * (tt / tt[-1]) ** 3
add(sw, F_FRZ / FPS, .5)
# end card: everything settles
fade = np.interp(ts, [F_CARD / FPS, TOTAL / FPS], [1, .45]); fade[ts < F_CARD / FPS] = 1
L *= fade; R *= fade
fi = int(.08 * SR); L[:fi] *= np.linspace(0, 1, fi); R[:fi] *= np.linspace(0, 1, fi)
out = np.stack([L, R], 1); out = out / np.sqrt((out ** 2).mean()) * .16
out = np.tanh(out * 1.2) / 1.2; out = out / np.max(np.abs(out)) * .92
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print([round(float(np.sqrt((out[s * SR:(s + 1) * SR] ** 2).mean())), 3) for s in range(int(NS / SR))])
