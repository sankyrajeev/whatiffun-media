"""1,000 double pendulums, each released 0.000001 deg apart. RK4, float64."""
import numpy as np, sys, pickle

N = 1000
G = float(sys.argv[1]) if len(sys.argv) > 1 else 14.0
TH1 = float(sys.argv[2]) if len(sys.argv) > 2 else 2.1
TH2 = float(sys.argv[3]) if len(sys.argv) > 3 else 2.6
EPS_DEG = 1e-6
SECONDS = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
FPS, SUB = 30, 40
dt = 1.0 / (FPS * SUB)

th1 = np.full(N, TH1)
th2 = TH2 + np.radians(EPS_DEG) * np.arange(N)
w1 = np.zeros(N); w2 = np.zeros(N)

def acc(t1, t2, a1, a2):
    d = t1 - t2
    den = 3.0 - np.cos(2 * d)          # 2m1+m2-m2cos(2d), m=1
    a1dd = (-3 * G * np.sin(t1) - G * np.sin(t1 - 2 * t2)
            - 2 * np.sin(d) * (a2 * a2 + a1 * a1 * np.cos(d))) / den
    a2dd = (2 * np.sin(d) * (a1 * a1 * 2 + 2 * G * np.cos(t1) + a2 * a2 * np.cos(d))) / den
    return a1dd, a2dd

def step(s):
    t1, t2, a1, a2 = s
    def f(t1, t2, a1, a2):
        b1, b2 = acc(t1, t2, a1, a2)
        return a1, a2, b1, b2
    k1 = f(t1, t2, a1, a2)
    k2 = f(*(x + 0.5 * dt * k for x, k in zip(s, k1)))
    k3 = f(*(x + 0.5 * dt * k for x, k in zip(s, k2)))
    k4 = f(*(x + dt * k for x, k in zip(s, k3)))
    return tuple(x + dt / 6 * (a + 2 * b + 2 * c + d) for x, a, b, c, d in zip(s, k1, k2, k3, k4))

s = (th1, th2, w1, w2)
frames = []
nf = int(SECONDS * FPS)
for f in range(nf):
    frames.append(np.stack([s[0], s[1]]).astype(np.float64))
    for _ in range(SUB):
        s = step(s)

frames = np.array(frames)   # (nf, 2, N)
# divergence: angular spread of the tip direction vs pendulum 0, in degrees
def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi
spread = np.degrees(np.max(np.abs(wrap(frames[:, 1, :] - frames[:, 1, :1])), axis=1))
np.save("frames.npy", frames)
np.save("spread.npy", spread)
for t in range(0, int(SECONDS) + 1, 1):
    i = min(nf - 1, t * FPS)
    print(t, "%.3g" % spread[i])
