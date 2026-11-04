"""'48 metronomes start at random. The only rule: the rack they sit on can slide.'
Pantaleone (2002) model: each metronome is a pendulum with a van der Pol escapement; all sit on one rack
that rolls freely. Every swing shoves the rack, the rack shoves every pendulum -> they phase-lock.
Integrated with RK4, seeded and deterministic. Ticks = zero crossings (escapement events)."""
import numpy as np, pickle, os
ENV = lambda k, d: float(os.environ.get(k, d))
N = int(ENV("N", 48)); SEED = int(ENV("SEED", 23))
FPS, SUB = 30, 40
DT = 1 / (FPS * SUB)
SECS = ENV("SECS", 22)
F0 = ENV("F0", 1.15)                 # Hz pendulum frequency (2.3 ticks/s)
SPREAD = ENV("SPREAD", 0.004)        # relative frequency spread
TH0 = ENV("TH0", 0.5)               # escapement target amplitude (rad)
MU = ENV("MU", 0.8)                  # escapement strength
MR = ENV("MR", 0.014)                # bob mass / total rack mass, per metronome
GAM = ENV("GAM", 0.10)               # rack rolling friction (1/s)
L = 0.25                             # effective length (m)
rng = np.random.default_rng(SEED)
w = 2 * np.pi * F0 * (1 + SPREAD * rng.standard_normal(N))
ph = rng.uniform(0, 2 * np.pi, N)
A0 = 2 * TH0                        # van der Pol limit amplitude
th = A0 * np.cos(ph); thd = -A0 * w * np.sin(ph)
m = MR; M = 1.0 + N * m                  # rack + all bobs
x = 0.0; xd = -m * L * np.sum(np.cos(th) * thd) / M   # zero net momentum

def acc(th, thd, x, xd):
    D = MU * ((th / TH0) ** 2 - 1) * thd
    c, s = np.cos(th), np.sin(th)
    num = -GAM * M * xd + m * L * np.sum(c * (w ** 2 * s + D) + s * thd ** 2)
    xdd = num / (M - m * np.sum(c * c))
    thdd = -w ** 2 * s - D - c * xdd / L
    return thdd, xdd

steps = int(SECS * FPS * SUB)
TH = np.zeros((int(SECS * FPS), N), np.float32); THD = np.zeros_like(TH); X = np.zeros(int(SECS * FPS)); XD = np.zeros(int(SECS * FPS))
ticks = []   # (t, i, speed)
for k in range(steps):
    a1, b1 = acc(th, thd, x, xd)
    a2, b2 = acc(th + .5 * DT * thd, thd + .5 * DT * a1, x + .5 * DT * xd, xd + .5 * DT * b1)
    a3, b3 = acc(th + .5 * DT * (thd + .5 * DT * a1), thd + .5 * DT * a2, x + .5 * DT * (xd + .5 * DT * b1), xd + .5 * DT * b2)
    a4, b4 = acc(th + DT * (thd + .5 * DT * a2), thd + DT * a3, x + DT * (xd + .5 * DT * b2), xd + DT * b3)
    nth = th + DT * (thd + DT / 6 * (a1 + a2 + a3))
    nthd = thd + DT / 6 * (a1 + 2 * a2 + 2 * a3 + a4)
    x = x + DT * (xd + DT / 6 * (b1 + b2 + b3)); xd = xd + DT / 6 * (b1 + 2 * b2 + 2 * b3 + b4)
    cr = np.nonzero(np.sign(nth) != np.sign(th))[0]
    for i in cr:
        ticks.append(((k + th[i] / (th[i] - nth[i])) * DT, int(i), float(abs(nthd[i]))))
    th, thd = nth, nthd
    if (k + 1) % SUB == 0:
        f = (k + 1) // SUB - 1
        TH[f] = th; THD[f] = thd; X[f] = x; XD[f] = xd
        if f % 30 == 0:
            phase = np.arctan2(-thd / w, th)
            z = np.exp(1j * phase).mean()
            insync = np.sum(np.abs(np.angle(np.exp(1j * (phase - np.angle(z))))) < np.radians(30))
            print(f"t={f/FPS:5.1f} r={abs(z):.3f} r2={abs(np.exp(2j*phase).mean()):.2f} insync={insync:2d} rack={x*1000:+6.2f}mm amp={np.abs(th).max():.2f}", flush=True)
if not os.environ.get("NOSAVE"): pickle.dump(dict(theta=TH, thetad=THD, x=X, xd=XD, ticks=ticks, w=w, N=N, TH0=TH0), open("sim.pkl", "wb"))
print("ticks", len(ticks))
