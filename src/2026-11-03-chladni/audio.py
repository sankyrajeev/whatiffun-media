"""Chladni soundtrack: the driving tone (its exact on-screen frequency) + granular sand sizzle whose
density follows how much the sand is actually moving in the simulation, panned to where it moves."""
import numpy as np, math, wave
from scipy.signal import butter, sosfilt, fftconvolve

FPS, SR = 30, 48000
TL = np.load("timeline.npy")          # j, env, hz, tamp, pass_env
EN, PANX = np.load("energy.npy")
T = len(TL)
N = int(T / FPS * SR)
rng = np.random.default_rng(9)
ft = (np.arange(T) + 0.5) / FPS
ts = np.arange(N) / SR

# ---------- tone ----------
hz = TL[:, 2].copy()
hz[hz <= 0] = TL[TL[:, 2] > 0][0, 2]               # hold first pitch through the intro (silent anyway)
lf = np.interp(ts, ft, np.log(hz))
f_s = np.exp(lf)
ph = 2 * np.pi * np.cumsum(f_s) / SR
ph2 = 2 * np.pi * np.cumsum(f_s * 1.0025) / SR
tamp = np.interp(ts, ft, TL[:, 3])
tamp = sosfilt(butter(1, 6, fs=SR, output="sos"), tamp)       # smooth steps
eq = np.clip((260 / f_s) ** 0.42, 0.45, 1.0)
tone = (np.sin(ph) * 0.8 + np.sin(ph2) * 0.35 + 0.12 * np.sin(2 * ph)) * tamp * eq
L = tone * 0.20; R = tone * 0.20

# ---------- sand sizzle ----------
e = np.zeros(T)
SEG = 104
for j in range(6):
    a0, a1 = 36 + j * SEG, 36 + (j + 1) * SEG
    seg = EN[a0:a1]
    e[a0:a1] = seg / (seg.max() + 1e-12)
e = np.clip(e, 0, 1.0)
kern = []
for k in range(3):
    n = int(rng.uniform(0.0012, 0.0024) * SR)
    t = np.arange(n) / SR
    g = rng.standard_normal(n) * np.exp(-t * rng.uniform(2200, 3600))
    kern.append(np.diff(g, prepend=0))
imp_l = [np.zeros(N) for _ in kern]; imp_r = [np.zeros(N) for _ in kern]
for f in range(T):
    if e[f] <= 0.002: continue
    rate = int(900 * e[f] ** 0.8)
    if rate == 0: continue
    t0 = int(f / FPS * SR)
    pos = rng.integers(0, SR // FPS, rate) + t0
    pos = pos[pos < N]
    amp = rng.exponential(1.0, len(pos)) * (0.35 + 0.65 * e[f] ** 0.5)
    pan = np.clip((PANX[f] - 0.5) * 1.4 + rng.normal(0, 0.45, len(pos)), -1, 1)
    which = rng.integers(0, len(kern), len(pos))
    gl = np.cos((pan + 1) * np.pi / 4); gr = np.sin((pan + 1) * np.pi / 4)
    for k in range(len(kern)):
        s = which == k
        np.add.at(imp_l[k], pos[s], amp[s] * gl[s])
        np.add.at(imp_r[k], pos[s], amp[s] * gr[s])
sz_l = sum(fftconvolve(imp_l[k], kern[k])[:N] for k in range(len(kern)))
sz_r = sum(fftconvolve(imp_r[k], kern[k])[:N] for k in range(len(kern)))
hp = butter(2, 1800, btype="highpass", fs=SR, output="sos")
sz_l = sosfilt(hp, sz_l); sz_r = sosfilt(hp, sz_r)
# soft continuous hiss under the grains
env_s = np.interp(ts, ft, e) ** 0.7
bed = sosfilt(butter(2, [2500, 9000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, N)), axis=1) * env_s
sz_l = sz_l + bed[0] * 0.5; sz_r = sz_r + bed[1] * 0.5
norm = np.percentile(np.abs(np.concatenate([sz_l, sz_r])), 99.7) + 1e-9
L += sz_l / norm * 0.32; R += sz_r / norm * 0.32

def add(sig, t0, g, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    s = sig[:N - i]
    L[i:i + len(s)] += s * g * math.cos((pan + 1) * math.pi / 4)
    R[i:i + len(s)] += s * g * math.sin((pan + 1) * math.pi / 4)

# struck-plate ring as the card arrives (inharmonic partials, long decay)
T_MODES = int(np.argmax((TL[:, 3] < 1) & (np.arange(T) > 600))) if T > 600 else T - 96
t_card = (T - 96 + 4) / FPS
tt = np.arange(int(3.2 * SR)) / SR
ring = sum(a * np.sin(2 * np.pi * f0 * tt + p) * np.exp(-tt * d)
           for f0, a, d, p in [(311, 1, 1.1, 0), (622 * 1.012, .5, 1.6, 1), (874, .35, 2.2, 2), (1388, .2, 3, .5)])
ring *= np.minimum(1, tt * 2000)
add(ring, t_card, 0.10)

# loop: a pour of sand rustling back onto the plate
t_l = (T - 18) / FPS; n = int(18 / FPS * SR) + SR // 4
pour = sosfilt(butter(2, [1500, 7000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, n)), axis=1)
pour *= np.sin(np.pi * np.arange(n) / n) ** 1.5 * 0.08
i0 = int(t_l * SR); m = min(n, N - i0)
L[i0:i0 + m] += pour[0, :m]; R[i0:i0 + m] += pour[1, :m]

# small warm room
ir_n = int(0.45 * SR); ti = np.arange(ir_n) / SR
irs = [sosfilt(butter(1, 4500, fs=SR, output="sos"), rng.standard_normal(ir_n) * np.exp(-ti * 11)) for _ in range(2)]
irs = [x / np.sqrt((x ** 2).sum()) for x in irs]
L = L + 0.14 * fftconvolve(L, irs[0])[:N]; R = R + 0.14 * fftconvolve(R, irs[1])[:N]

out = np.stack([L, R], 1)
fi = int(0.05 * SR); out[:fi] *= np.linspace(0, 1, fi)[:, None]
out = np.tanh(out / np.percentile(np.abs(out), 99.95) * 0.95)
out = out / np.max(np.abs(out)) * 0.89
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
for s in range(int(N / SR)):
    seg = out[s * SR:(s + 1) * SR]; print(s, round(float(np.sqrt((seg ** 2).mean())), 3), end=" | ")
print()
