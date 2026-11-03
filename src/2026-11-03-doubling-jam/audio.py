"""Soundtrack from the simulation: motor hum/whine following real rotor speed, a glass 'pop' for every
doubling, stereo glass/brass collision clicks, and the jam."""
import pickle, math, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

d = pickle.load(open("sim.pkl", "rb"))
FPS, SR = 30, 48000
JAM = d["jam"]; OM = d["omegas"]; NF = len(OM)
TOTAL = JAM + 40 + 70 + 18
N = int(TOTAL / FPS * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(17)
ts = np.arange(N) / SR
ft = (np.arange(TOTAL) + .5) / FPS

def pan_gains(x):
    p = np.clip((np.asarray(x) - 540) / 440, -.95, .95)
    return np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)

# ---------- motor ----------
w = np.abs(np.concatenate([OM[:, 0], np.zeros(TOTAL - NF)]))[:TOTAL]
w[JAM:] = 0
r = w / w[5:60].max()
r_s = np.interp(ts, ft, r)
r_s = sosfilt(butter(1, 4, fs=SR, output="sos"), r_s)
f_body = 26 + 54 * r_s
f_gear = 140 + 520 * r_s
ph_b = 2 * np.pi * np.cumsum(f_body) / SR
ph_g = 2 * np.pi * np.cumsum(f_gear) / SR
body = sum(np.sin(k * ph_b) / k for k in range(1, 7))
gear = np.sin(ph_g) + .35 * np.sin(2 * ph_g) + .15 * np.sin(3.01 * ph_g)
strain = 1 + .35 * (1 - r_s) * np.sin(2 * np.pi * 7.5 * ts) * (r_s > .03)
on = np.clip(r_s * 6, 0, 1)
motor = (body * .16 + gear * .045 * np.clip(r_s, 0, 1)) * strain * on
motor = sosfilt(butter(2, 1800, fs=SR, output="sos"), motor)
L += motor; R += motor

# ---------- glass pops for every doubling ----------
PENTA = [0, 3, 5, 7, 10]
def pop(f0, dur=.05):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * (1 + 1.6 * np.minimum(t / .018, 1))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 85)
    s += .3 * np.sin(2 * np.pi * np.cumsum(f * 2.71) / SR) * np.exp(-t * 160)
    return s * np.minimum(1, t * 4000)
POPS = [pop(880 * 2 ** ((PENTA[i % 5] + 12 * (i // 5)) / 12)) for i in range(10)]
cl = np.array([(c[0], c[1], c[3]) for c in d["clones"]])
cf = (cl[:, 0] * FPS).astype(int)
cnt_f = np.bincount(cf, minlength=TOTAL)
for f in np.unique(cf):
    idx = np.nonzero(cf == f)[0]
    if len(idx) > 10: idx = rng.choice(idx, 10, replace=False)
    g = .5 / math.sqrt(max(1, cnt_f[f]) ** .8)
    for i in idx:
        t0, x, gen = cl[i]
        sig = POPS[int(gen) % 10]
        j = int((t0 + rng.uniform(0, 1 / FPS)) * SR)
        if j >= N: continue
        s = sig[:N - j]; gl, gr = pan_gains(x)
        L[j:j + len(s)] += s * g * gl; R[j:j + len(s)] += s * g * gr

# ---------- collisions ----------
ev = d["events"]
et = np.fromiter((e[0] for e in ev), float, len(ev))
ex = np.fromiter((e[1] for e in ev), float, len(ev))
ei = np.fromiter((e[3] for e in ev), float, len(ev))
ek = np.fromiter(({"ball": 0, "wall": 1, "arm": 2}[e[4]] for e in ev), int, len(ev))
del ev
efr = (et * FPS).astype(int)
order = np.lexsort((-ei, efr))
efr_o = efr[order]
starts = np.r_[0, np.nonzero(np.diff(efr_o))[0] + 1]
rank = np.arange(len(order)) - np.repeat(starts, np.diff(np.r_[starts, len(order)]))
K = 22
keep = order[rank < K]
dens = np.bincount(efr, minlength=TOTAL).astype(float)

def glass(f0, dec, dur=.07, noise=.3):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .5 * np.sin(2 * np.pi * f0 * 2.76 * t + 1) * np.exp(-t * dec * .6)) * np.exp(-t * dec)
    n = rng.standard_normal(len(t)) * np.exp(-t * 1800) * noise
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 6000)
def tink(f0):
    t = np.arange(int(.18 * SR)) / SR
    return sum(a * np.sin(2 * np.pi * f0 * m * t) * np.exp(-t * dd) for m, a, dd in
               [(1, 1, 22), (2.41, .5, 30), (4.1, .3, 45)]) * np.minimum(1, t * 6000)
BANK = [[glass(rng.uniform(3600, 5200), rng.uniform(90, 140), .05, .35) for _ in range(32)],
        [glass(rng.uniform(1700, 2300), rng.uniform(60, 90), .08, .25) for _ in range(16)],
        [tink(rng.uniform(1900, 2500)) for _ in range(16)]]
GK = [.22, .3, .34]; REF = [80., 80., 120.]
for i in keep:
    k = ek[i]; f = efr[i]
    if f >= TOTAL: continue
    g = GK[k] * min(1.5, (ei[i] / REF[k]) ** .55) / (1 + .02 * max(0, dens[f] - 30) ** .6)
    sig = BANK[k][rng.integers(len(BANK[k]))]
    j = int(et[i] * SR)
    if j >= N: continue
    s = sig[:N - j]; gl, gr = pan_gains(ex[i])
    L[j:j + len(s)] += s * g * gl; R[j:j + len(s)] += s * g * gr

# dense-swarm texture: soft glassy hiss following collision density
dn = np.clip(np.interp(ts, ft, dens / (np.percentile(dens[:JAM], 99) + 1)), 0, 1.2)
dn = sosfilt(butter(1, 3, fs=SR, output="sos"), dn)
hiss = sosfilt(butter(2, [3000, 9000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, N)), axis=1)
L += hiss[0] * dn * .05; R += hiss[1] * dn * .05

def add(sig, t0, g, x=540):
    j = int(t0 * SR)
    if j >= N: return
    s = sig[:N - j]; gl, gr = pan_gains(x)
    L[j:j + len(s)] += s * g * gl; R[j:j + len(s)] += s * g * gr

# ---------- the jam ----------
tj = JAM / FPS
t = np.arange(int(1.6 * SR)) / SR
thud = np.sin(2 * np.pi * (38 * t + 30 * (1 - np.exp(-t * 10)) / 10)) * np.exp(-t * 3.2)
crunch = sosfilt(butter(2, [900, 5000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t * 14)
add(thud * .9 + crunch * .5, tj, 1.0)
for k in range(40):                      # marbles settling after the stop
    add(BANK[0][rng.integers(32)], tj + .05 + rng.exponential(.25), .12 * math.exp(-k / 18), rng.uniform(150, 930))

# card: soft brass ring
tc = (JAM + 40 + 3) / FPS
t = np.arange(int(2.8 * SR)) / SR
ring = sum(a * np.sin(2 * np.pi * f0 * t) * np.exp(-t * dd) for f0, a, dd in [(440, 1, 1.3), (1061, .45, 2), (1717, .25, 3)])
add(ring * np.minimum(1, t * 2000), tc, .12)

# room
ir_n = int(.4 * SR); ti = np.arange(ir_n) / SR
irs = [sosfilt(butter(1, 4500, fs=SR, output="sos"), rng.standard_normal(ir_n) * np.exp(-ti * 12)) for _ in range(2)]
irs = [x / np.sqrt((x ** 2).sum()) for x in irs]
L = L + .15 * fftconvolve(L, irs[0])[:N]; R = R + .15 * fftconvolve(R, irs[1])[:N]

out = np.stack([L, R], 1)
fo = int(.5 * SR); out[-fo:] *= np.linspace(1, .2, fo)[:, None]
fi = int(.03 * SR); out[:fi] *= np.linspace(0, 1, fi)[:, None]
out = np.tanh(out / np.percentile(np.abs(out), 99.95) * .95)
out = out / np.max(np.abs(out)) * .89
with wave.open("audio.wav", "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((out * 32767).astype(np.int16).tobytes())
for s in range(int(N / SR)):
    seg = out[s * SR:(s + 1) * SR]; print(s, round(float(np.sqrt((seg ** 2).mean())), 3), end=" | ")
print()
