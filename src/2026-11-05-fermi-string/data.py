"""FPUT-alpha chain: 32 beads, fixed ends, nonlinear springs F = d + ALPHA d^2. Velocity Verlet, deterministic."""
import numpy as np
N, ALPHA, A, DT = 32, 0.5, 1.5, 0.05
j = np.arange(1, N + 1)
S = np.sqrt(2 / (N + 1)) * np.sin(np.outer(j, j) * np.pi / (N + 1))
OM = 2 * np.sin(j * np.pi / (2 * (N + 1)))
def acc(x):
    d = np.diff(np.concatenate([[0], x, [0]])); f = d + ALPHA * d * d
    return f[1:] - f[:-1]
Ts = 65.73833333333334            # measured: 90 swings to the recurrence peak (see strobe.py)
NSW = 94
x = A * np.sin(np.pi * j / (N + 1)); v = np.zeros(N); a = acc(x)
n = int(NSW * Ts / DT) + 2
X = np.zeros((n, N)); V = np.zeros((n, N))
for i in range(n):
    X[i] = x; V[i] = v
    v += .5 * DT * a; x += DT * v; a = acc(x); v += .5 * DT * a
q = X @ S; p = V @ S
E = .5 * (p ** 2 + (OM * q) ** 2); Ef = E / E.sum(1, keepdims=True)
np.savez_compressed("fput.npz", X=X, Ef=Ef, q=q, DT=DT, Ts=Ts)
for s in [0, 10, 20, 45, 80, 89, 90, 91]:
    i = int(round(s * Ts / DT)); print(s, round(Ef[i, 0] * 100, 2), np.round(X[i, [0, 15, 31]], 3))
print("max |x|", np.abs(X).max())
