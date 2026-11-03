"""ASMR soundtrack for the Galton board: every collision becomes a synthesized glass/brass/wood click,
placed in stereo by where it happened (with a small inter-aural delay)."""
import pickle, math, wave
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

d = pickle.load(open("sim.pkl", "rb"))
G = d["geom"]; EV = d["events"]
FPS, SR = 30, 48000
NF = len(d["frames"])
CURVE, HOLD, CARD, XF = 45, 30, 84, 18
TOTAL = NF + CURVE + HOLD + CARD + XF
N = int(TOTAL / FPS * SR) + SR // 2
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(21)

def env_t(dur): return np.arange(int(dur * SR)) / SR

def glass(f0, decay, dur=0.09, noise=0.25):
    t = env_t(dur)
    s = (np.sin(2 * np.pi * f0 * t) + 0.55 * np.sin(2 * np.pi * f0 * 2.76 * t + 1.1) * np.exp(-t * decay * 0.6)
         + 0.28 * np.sin(2 * np.pi * f0 * 5.40 * t + 0.3) * np.exp(-t * decay * 1.3))
    s *= np.exp(-t * decay)
    n = rng.standard_normal(len(t)) * np.exp(-t * 1800) * noise
    s += np.diff(n, prepend=0)          # crisp, high-passed transient
    s *= np.minimum(1, t * 6000)
    return s

def wood(f0, dur=0.07):
    t = env_t(dur)
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 90) + 0.5 * np.sin(2 * np.pi * f0 * 1.58 * t) * np.exp(-t * 140)
    s += 0.6 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 60)
    n = rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.4
    s += n
    return s * np.minimum(1, t * 5000)

BANK = {
    "pin":   [glass(rng.uniform(2500, 3500), rng.uniform(55, 80), noise=0.2) for _ in range(48)],
    "ball":  [glass(rng.uniform(3600, 5200), rng.uniform(85, 130), dur=0.06, noise=0.35) for _ in range(48)],
    "wall":  [glass(rng.uniform(1800, 2400), rng.uniform(70, 100), dur=0.07, noise=0.3) for _ in range(24)],
    "wood":  [wood(rng.uniform(750, 1100)) for _ in range(24)],
    "floor": [wood(rng.uniform(420, 600), dur=0.09) for _ in range(24)],
}
GAIN = {"pin": 0.55, "ball": 0.32, "wall": 0.35, "wood": 0.6, "floor": 0.75}
REF = {"pin": 60.0, "ball": 60.0, "wall": 60.0, "wood": 50.0, "floor": 60.0}

def place(sig, t0, gain, x):
    pan = max(-0.92, min(0.92, (x - 540) / 430))
    gl = math.cos((pan + 1) * math.pi / 4); gr = math.sin((pan + 1) * math.pi / 4)
    itd = int(abs(pan) * 0.00045 * SR)          # inter-aural delay, far ear later
    i = int(t0 * SR)
    il, ir = (i + itd, i) if pan > 0 else (i, i + itd)
    for buf, j, g in ((L, il, gl), (R, ir, gr)):
        if j >= N: continue
        s = sig[: N - j]
        buf[j:j + len(s)] += s * gain * g

# thin events per frame so the density stays crisp, not mushy
by_frame = {}
for e in EV:
    by_frame.setdefault(int(e[0] * FPS), []).append(e)
CAP = 26
for f, es in by_frame.items():
    es.sort(key=lambda e: -e[3])
    keep = es[:CAP]
    density = len(es)
    dg = 1.0 / (1 + 0.035 * max(0, density - 8))
    for (t, x, y, imp, kind) in keep:
        g = GAIN[kind] * min(1.6, (imp / REF[kind]) ** 0.6) * dg
        place(BANK[kind][rng.integers(len(BANK[kind]))], t + rng.uniform(0, 0.004), g, x)

# gate opening: a soft wooden latch
place(wood(320, 0.15) * 0.9, 12 / FPS - 0.03, 0.9, 540); place(wood(980, 0.08) * 0.5, 12 / FPS - 0.03, 0.9, 540)

# pencil drawing the bell curve: grainy band-passed noise sweeping left -> right
t0 = NF / FPS; dur = CURVE / FPS
n = int(dur * SR)
noise = rng.standard_normal(n)
sos = butter(2, [1800, 6500], btype="bandpass", fs=SR, output="sos")
pen = sosfilt(sos, noise)
grain = np.repeat(rng.uniform(0.3, 1.0, n // 240 + 1), 240)[:n]
tt = np.arange(n) / n
u = tt * tt * (3 - 2 * tt)
penv = np.sin(np.pi * np.clip(tt, 0, 1)) ** 0.6
xs = G["BX0"] + u * (G["BX1"] - G["BX0"])
for a in range(0, n, 2400):
    seg = pen[a:a + 2400] * grain[a:a + 2400] * penv[a:a + 2400] * 0.55
    place(seg, t0 + a / SR, 1.0, float(xs[min(a, n - 1)]))

# card arriving: soft paper whoosh + tap
tc = (NF + CURVE + HOLD) / FPS
n = int(0.5 * SR); tt = np.arange(n) / SR
wh = sosfilt(butter(2, [300, 2500], btype="bandpass", fs=SR, output="sos"), rng.standard_normal(n))
wh *= np.sin(np.pi * tt / 0.5) ** 2 * 0.5
place(wh, tc - 0.15, 1.0, 540)
place(wood(260, 0.12), tc + 0.33, 0.35, 540)

# loop: hopper refills -> a gentle shimmer of tiny clicks rising under the crossfade
tl = (TOTAL - XF) / FPS
for k in range(70):
    tt_ = tl + (k / 70) ** 0.7 * (XF / FPS)
    place(BANK["ball"][rng.integers(48)], tt_, 0.08 + 0.12 * k / 70, rng.uniform(330, 750))

# faint room tone so it never drops to digital silence
room = sosfilt(butter(1, 900, fs=SR, output="sos"), rng.standard_normal(N)) * 0.004
L += room; R += room * 0.97

# small-room reverb for warmth
ir_n = int(0.38 * SR); ti = np.arange(ir_n) / SR
ir = rng.standard_normal(ir_n) * np.exp(-ti * 16)
ir = sosfilt(butter(1, 5000, fs=SR, output="sos"), ir); ir /= np.sqrt((ir ** 2).sum())
L = L + 0.18 * fftconvolve(L, ir)[:N]
R = R + 0.18 * fftconvolve(R, ir)[:N]

out = np.stack([L, R], 1)[: int(TOTAL / FPS * SR)]
fo = int(0.25 * SR); out[-fo:] *= np.linspace(1, 0.4, fo)[:, None]
out = np.tanh(out / np.percentile(np.abs(out), 99.9) * 0.9)
out = out / np.max(np.abs(out)) * 0.89
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
for s in range(0, int(len(out) / SR)):
    seg = out[s * SR:(s + 1) * SR]
    print(s, round(float(np.sqrt((seg ** 2).mean())), 3), end=" | ")
print()
