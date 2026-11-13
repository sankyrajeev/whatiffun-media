"""Brachistochrone race: frictionless sleds released from rest on three tracks with the same start + finish.
Energy conservation: v = sqrt(2 g (y - y0)), y down. Integrate ds/v along each track (exact quadrature on a dense polyline),
then invert to get arc position s(t) and the point (x, y)."""
import numpy as np
from scipy.optimize import brentq
L, HD = 740.0, 150.0          # px: horizontal span and drop (start -> finish)
G = 196.0 * (3.77128215 / 8.0) ** 2   # px/s^2: sets the on-screen pace (cycloid = 8.0 s)

def cycloid():
    th_e = brentq(lambda th: (1 - np.cos(th)) / (th - np.sin(th)) - HD / L, 1e-3, 2 * np.pi - 1e-3)
    r = L / (th_e - np.sin(th_e)); th = np.linspace(0, th_e, 20001)
    return r * (th - np.sin(th)), r * (1 - np.cos(th))
def straight():
    u = np.linspace(0, 1, 20001); return L * u, HD * u
Q, DEPTH = 0.6, 140.0
def steep():
    """front-loaded drop: y = HD u + DEPTH sin(pi u^Q) — falls steeply first, then a shallow bowl (searched headless:
    it leads for ~64% of the race and loses by ~0.2 s)"""
    u = np.linspace(0, 1, 20001)
    return L * u, HD * u + DEPTH * np.sin(np.pi * u ** Q)

def times(x, y):
    ds = np.hypot(np.diff(x), np.diff(y)); ym = (y[1:] + y[:-1]) / 2
    # exact for a straight segment under constant accel: dt = 2 ds/(v0+v1)
    v = np.sqrt(2 * G * np.maximum(y, 0)); dt = 2 * ds / np.maximum(v[1:] + v[:-1], 1e-9)
    return np.concatenate([[0], np.cumsum(dt)]), np.concatenate([[0], np.cumsum(ds)])

def lane(kind):
    x, y = {"straight": straight, "cycloid": cycloid, "steep": steep}[kind]()
    t, s = times(x, y); return dict(x=x, y=y, t=t, s=s, T=t[-1])

if __name__ == "__main__":
    for k in ("straight", "steep", "cycloid"):
        d = lane(k); print(k, round(d["T"], 3), "max depth", round(d["y"].max(), 1), "length", round(d["s"][-1], 1))
