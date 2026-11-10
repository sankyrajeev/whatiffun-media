"""One equation draws a chess knight: deterministic per-frame state for the 3D render, sound and composite.
Fourier series of the knight glyph's outline; the arm count ladders 1 -> 4 -> 16 -> 64 -> 256 -> 1,024."""
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fourier import outline, coeffs

SCALE = 3.0                       # knight height in scene units
STAGES = [1, 4, 16, 64, 256, 1024]
SFR = [39, 48, 54, 60, 69, 84]    # frames per stage (first UNF frames: new arms unfold, t held at 0)
UNF = 7
FLASH, REW = 28, 10               # flash-forward of the 1,024-arm stage, then a quick rewind
S0 = FLASH + REW                  # first stage starts here
STARTS = list(np.cumsum([S0] + SFR[:-1]))
DRAW_END = STARTS[-1] + SFR[-1]   # 392: the line closes
NFR = 480                         # rendered frames
TS = 2048                         # trail samples per loop

z = outline("♞")
C0, C, K = coeffs(z)
C0 = C0 * SCALE; C = C * SCALE
R = np.abs(C)
tt = np.linspace(0, 2 * np.pi, TS + 1)
CURVES = {N: C0 + (C[:N, None] * np.exp(1j * K[:N, None] * tt)).sum(0) for N in STAGES}
TARGET = z * SCALE                # the exact outline (for the solid knight)

def ss(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)

def state(f):
    """returns dict: n (arms shown), grow (per-arm scale array len n), t (phase), N (curve stage), frac (trail drawn),
    ghostN, ghost (ghost line strength), label (arm count shown), glow, retract, extrude, stand, cam (0..1 glide)"""
    st = dict(ghostN=None, ghost=0.0, glow=0.0, retract=0.0, extrude=0.0, stand=0.0, cam=0.0, event=None)
    if f < FLASH:                                   # flash-forward: dense stage mid-drawing
        frac = .52 + .2 * f / FLASH
        st.update(N=1024, n=1024, grow=np.ones(1024), frac=frac, label=1024)
    elif f < S0:                                    # rewind the line back to its start
        u = ss((f - FLASH + 1) / REW)
        st.update(N=1024, n=1024, grow=np.ones(1024), frac=.72 * (1 - u), label=1024)
    elif f < DRAW_END:
        i = max(j for j in range(len(STAGES)) if STARTS[j] <= f)
        N = STAGES[i]; prev = STAGES[i - 1] if i else 0; lf = f - STARTS[i]
        g = np.ones(N)
        if lf < UNF:
            u = ss((lf + 1) / UNF); g[prev:] = u
            frac = 0.0
            if i: st.update(ghostN=STAGES[i - 1], ghost=1 - u)
            elif f == S0: pass
        else:
            frac = (lf - UNF + 1) / (SFR[i] - UNF)
        if lf == 0: st["event"] = ("stage", N)
        st.update(N=N, n=N, grow=g, frac=frac, label=N)
        if i == 0 and lf < UNF:                     # the 1,024 arms fold back into one
            st.update(n=1024, grow=np.r_[1.0, np.full(1023, 1 - ss((lf + 1) / UNF))])
    else:                                           # closed: glow, arms fold away, the knight rises
        e = f - DRAW_END
        st.update(N=1024, n=1024, grow=np.ones(1024), frac=1.0, label=1024)
        st["glow"] = np.exp(-((e - 6) / 7.0) ** 2)
        st["retract"] = ss((e - 6) / 22)
        st["extrude"] = ss((e - 14) / 16)
        st["stand"] = ss((e - 26) / 40)
        st["cam"] = ss((e - 12) / 70)
        if e == 0: st["event"] = ("close", 1024)
    st["t"] = 2 * np.pi * st["frac"]
    return st

def chain(st):
    """joint centres (n+1 complex) for the state; arm j has radius R[j]*grow[j]"""
    n = st["n"]; g = st["grow"] * (1 - st["retract"])
    v = C[:n] * g * np.exp(1j * K[:n] * st["t"])
    return np.r_[C0, C0 + np.cumsum(v)], R[:n] * g

def trail(st):
    N = st["N"]; m = int(np.floor(st["frac"] * TS))
    if st["frac"] <= 0: return None
    pts = CURVES[N][:m + 1]
    tip = C0 + (C[:N] * np.exp(1j * K[:N] * st["t"])).sum()
    return np.r_[pts, tip]

if __name__ == "__main__":
    print("stages start", STARTS, "draw end", DRAW_END, "frames", NFR)
    print("arms with r > 0.004:", (R[:1024] > .004).sum(), "r1", R[0])
