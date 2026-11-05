"""No. 4: stochastic resonance. 1,000 beads, each in its own double well x' = x - x^3 + beat(t) + noise.
The beat (0.30) is below the 0.385 needed to tip a bead. Bead i is shaken with noise sigma_i (log 0.18..1.4).
Seeded Euler-Maruyama. Saves per-frame positions (3 substeps for blur), flip events, group stats."""
import numpy as np
N, A, T = 1000, 0.32, 80.0          # beat amplitude, beat period (sim units) = 1.0 s real
FPS, TOTAL = 30, 750
DT = 0.02; SPF = int(round(T / FPS / DT))   # steps per frame (133)
SIG = np.geomspace(0.08, 3.0, N)
F_N0, F_N1 = 40, 100                  # noise ramps in
F_FRZ, F_RES = 100, 145               # prediction freeze (sim paused)
F_OFF = 560                            # noise switched off
HYS = 0.55
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def knob(f):
    if f >= F_OFF: return float(1 - ss((f - F_OFF) / 5))
    return float(ss((f - F_N0) / (F_N1 - F_N0)))
rng = np.random.default_rng(4)
x = -np.ones(N) + 0.0; st = -np.ones(N, np.int8); t = 0.0
POS = np.zeros((TOTAL, 3, N), np.float32); TS = np.zeros(TOTAL); K = np.zeros(TOTAL)
EV = []        # (frame_float, bead, dir)
for f in range(TOTAL):
    paused = F_FRZ <= f < F_RES
    g = knob(f); K[f] = g
    for k in range(SPF):
        if not paused:
            g = knob(f + k / SPF)
            x += (x - x ** 3 + A * np.tanh(2.5 * np.sin(2 * np.pi * t / T)) / np.tanh(2.5)) * DT + g * SIG * np.sqrt(DT) * rng.standard_normal(N)
            t += DT
            ns = np.where(x > HYS, 1, np.where(x < -HYS, -1, st)).astype(np.int8)
            ch = np.nonzero(ns != st)[0]
            for i in ch: EV.append((f + k / SPF, i, ns[i]))
            st = ns
        if k % 44 == 0 and k // 44 < 3: POS[f, k // 44] = x
    TS[f] = t
EV = np.array(EV)
STATE = None
np.savez_compressed("sr.npz", POS=POS, TS=TS, K=K, EV=EV, SIG=SIG, A=A, T=T)
print("events", len(EV), "sim t", t / T, "s")
# group stats
fr = EV[:, 0]; b = EV[:, 1].astype(int)
for lo, hi, nm in [(0, 333, "A"), (333, 667, "B"), (667, 1000, "C")]:
    m = (b >= lo) & (b < hi); print(nm, "flips", m.sum(), "SIG", SIG[lo].round(2), SIG[hi - 1].round(2))
print("flips before freeze", (fr < F_FRZ).sum(), "after off", (fr > F_OFF + 10).sum())
