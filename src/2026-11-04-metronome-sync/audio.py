"""Soundtrack from the simulation: every escapement tick is a real event (wooden 'tock' + brass click),
stereo-panned by the metronome's x on the moving shelf; rollers rumble with the shelf's speed."""
import pickle, math, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from render import TOTAL, CARD_AT, XS, COLS, PXM, ALL

d = pickle.load(open("sim.pkl", "rb"))
FPS, SR = 30, 48000
N = int(TOTAL / FPS * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(5)
ts = np.arange(N) / SR
NM = d["N"]

def pan_gains(x):
    p = np.clip((np.asarray(x) - 540) / 460, -.9, .9)
    return np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)

def tock(f_body, f_click):
    t = np.arange(int(.09 * SR)) / SR
    n = sosfilt(butter(2, [1500, 7000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t * 900)
    s = (.9 * np.sin(2 * np.pi * f_click * t) * np.exp(-t * 160) + .35 * np.sin(2 * np.pi * f_click * 2.31 * t) * np.exp(-t * 260)
         + .7 * np.sin(2 * np.pi * f_body * t) * np.exp(-t * 70))
    return (s + 1.4 * n) * np.minimum(1, t * 8000)
# each metronome has its own little voice (slightly different wood), two flavours for left/right swing
VOICE = [(tock(rng.uniform(330, 420), rng.uniform(2000, 2600)), tock(rng.uniform(330, 420), rng.uniform(2300, 2900))) for _ in range(NM)]

tk = np.array(d["ticks"]); tt, ti, sp = tk[:, 0], tk[:, 1].astype(int), tk[:, 2]
thd = d["thetad"]
# local density (ticks within +-15 ms) -> per-tick gain so 48 in unison sum to a big but clean 'TOCK'
srt = np.sort(tt)
dens = np.searchsorted(srt, tt + .015) - np.searchsorted(srt, tt - .015)
for t0, i, s_, dn in zip(tt, ti, sp, dens):
    if t0 >= N / SR: continue
    f = min(len(thd) - 1, int(t0 * FPS))
    v = VOICE[i][0 if thd[f, i] > 0 else 1]
    x = XS[i % COLS] + d["x"][f] * PXM
    g = .5 * (s_ / 7.0) ** .5 / dn ** .4
    j = int(t0 * SR); seg = v[:N - j]; gl, gr = pan_gains(x)
    L[j:j + len(seg)] += seg * g * gl; R[j:j + len(seg)] += seg * g * gr

# rollers: low rumble following shelf speed
ft = (np.arange(len(d["xd"])) + 1) / FPS
v = np.abs(np.interp(ts, ft, d["xd"])); v = v / (np.percentile(v, 99) + 1e-9)
rum = sosfilt(butter(2, [40, 220], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, N)), axis=1)
L += rum[0] * v * .22; R += rum[1] * v * .22

def add(sig, t0, g, x=540):
    j = int(t0 * SR)
    if j >= N: return
    s = sig[:N - j]; gl, gr = pan_gains(x)
    L[j:j + len(s)] += s * g * gl; R[j:j + len(s)] += s * g * gr
# all in step: a soft brass bell under the unison
t = np.arange(int(3.0 * SR)) / SR
ring = sum(a * np.sin(2 * np.pi * f0 * t) * np.exp(-t * dd) for f0, a, dd in [(440, 1, 1.3), (1061, .45, 2), (1717, .25, 3)])
add(ring * np.minimum(1, t * 2000), ALL / FPS, .07)
add(ring * np.minimum(1, t * 2000), (CARD_AT + 3) / FPS, .09)

ir_n = int(.5 * SR); ti_ = np.arange(ir_n) / SR
irs = [sosfilt(butter(1, 4000, fs=SR, output="sos"), rng.standard_normal(ir_n) * np.exp(-ti_ * 9)) for _ in range(2)]
irs = [x / np.sqrt((x ** 2).sum()) for x in irs]
L = L + .18 * fftconvolve(L, irs[0])[:N]; R = R + .18 * fftconvolve(R, irs[1])[:N]

out = np.stack([L, R], 1)
fo = int(.6 * SR); out[-fo:] *= np.linspace(1, .25, fo)[:, None]
fi = int(.02 * SR); out[:fi] *= np.linspace(0, 1, fi)[:, None]
out = np.tanh(out / np.percentile(np.abs(out), 99.9) * 1.0)
out = out / np.max(np.abs(out)) * .89
with wave.open("audio.wav", "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((out * 32767).astype(np.int16).tobytes())
for s in range(int(N / SR)):
    seg = out[s * SR:(s + 1) * SR]; print(s, round(float(np.sqrt((seg ** 2).mean())), 3), end=" | ")
print()
