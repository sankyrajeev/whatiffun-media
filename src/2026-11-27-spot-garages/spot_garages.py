"""SPOT IT v3 (10:00, 2026-11-27): WHICH GARAGE / OPENS THE WRONG WAY?
72 identical lock-up garages in LOCK-UP TERRACES (9 terraces of 8, each terrace split 4 | 4 by an alley;
letters A-H on top, numbers 1-9 on the left). Every amber roller door opens UP into its lintel and comes back down,
non-stop, on a 1.5 / 1.71 / 2.0 / 2.4 s cycle from a random phase (+-23% speed jitter), showing a lit garage with a
cream car inside. Now and then a door does a legal 'safety reverse' (it opens halfway and drops back).
ONE door (ODD) twice per loop opens DOWNWARDS instead: it slides down through the floor, over the driveway, for
~0.56 s, then pops back and carries on as normal. At each of those moments 5 decoys do a quick safety reverse.
Rule type: passes through the floor (wrong way). Sound: a soft roller-door rattle per opening + a muted thunk per
close (pitch by row, panned by x, density-normalised); the odd one's rattle is a touch lower (subtle).
12 s seamless loop.  Reproduce: python3 spot_garages.py render x <outdir>"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/garages"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 9
CW = float(os.environ.get("CW", "98"))      # column pitch
RP = float(os.environ.get("RP", "106"))     # row pitch
ALLEY = 22.0
X0 = 168.0
Y0 = 640.0                                   # bottom (threshold) of row 1 doors
DW, DH = 80.0, 64.0                          # door opening
OPEN = .93
PCT = int(os.environ.get("PCT", "4"))
ODD = (os.environ.get("OL", "G"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "2711")))

def col_x(i): return X0 + i * CW + (ALLEY if i >= 4 else 0)
def row_y(r): return Y0 + r * RP
def ease(x): x = min(1, max(0, x)); return .5 - .5 * math.cos(math.pi * x)

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([12 / 8, 12 / 7, 12 / 6, 12 / 5]))
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i), y=row_y(r), r=r, i=i, P=P,
                      ph=rng.uniform(0, P), ev={}))
ODDG = [g for g in G if g["odd"]][0]
ODDG["P"] = 2.0

# cycle shape (fractions of P): opening .00-.30, open .30-.50, closing .50-.80, closed .80-1.0
def opens(g):
    n = int(round(LOOP / g["P"]))
    return [g["ph"] + j * g["P"] for j in range(-1, n + 1)]

BREAK = .56
def pick(g, want):
    c = [(abs(t - want), t) for t in opens(g) if .6 < t < LOOP - 1.0]
    return min(c)[1]
BREAKS = [pick(ODDG, 4.1), pick(ODDG, 9.5)]
for tb in BREAKS:
    ODDG["ev"][round(tb % LOOP, 4)] = "down"
    cand = []
    for g in G:
        if g["odd"] or (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1): continue
        for t2 in opens(g):
            if abs(t2 - tb) < .3: cand.append((abs(t2 - tb) + rng.uniform(0, .2), id(g), g, t2))
    cand.sort(key=lambda x: x[0]); used = set()
    for _, gid, g, t2 in cand:
        if gid in used or len(used) >= 5: continue
        used.add(gid); g["ev"][round(t2 % LOOP, 4)] = "rev"
for g in G:
    if g["odd"]: continue
    for t2 in opens(g):
        if 0 <= t2 < LOOP and rng.random() < .07: g["ev"].setdefault(round(t2 % LOOP, 4), "rev")

def kind(g, t0):
    return g["ev"].get(round(t0 % LOOP, 4))

def door(g, t):
    """door offset in door heights: + = up into the lintel (normal), - = down through the floor"""
    P = g["P"]
    j = math.floor((t - g["ph"]) / P); t0 = g["ph"] + j * P
    u = (t - t0) / P; dt = t - t0
    k = kind(g, t0)
    if k == "down":
        if dt < .2: return -OPEN * ease(dt / .2)
        if dt < .36: return -OPEN
        if dt < BREAK: return -OPEN * (1 - ease((dt - .36) / .2))
        return 0.0
    if k == "rev":
        if dt < .26: return .5 * ease(dt / .26)
        if dt < BREAK: return .5 * (1 - ease((dt - .26) / .3))
        return 0.0
    if u < .30: return OPEN * ease(u / .30)
    if u < .50: return OPEN
    if u < .80: return OPEN * (1 - ease((u - .50) / .30))
    return 0.0

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def lin(y0, y1, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y0), (0, y1)], [c4(cc).toColor() for cc in cols], pos))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH GARAGE", "OPENS THE WRONG WAY?"
def fit(s, size, maxw=850):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_Q = F_Q2 if F_Q2.getSize() < F_Q.getSize() else F_Q
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

WALL_T, WALL_B = (.93, .88, .78), (.80, .74, .63)
ROOF = (.55, .42, .26)
DOOR_T, DOOR_B = (.95, .70, .34), (.80, .52, .20)
SLAT = (.62, .38, .13)
IN_T, IN_B = (.30, .22, .13), (.08, .065, .05)
CAR = (.93, .90, .82)

def draw_terraces(c):
    for r in range(NR):
        y = row_y(r)
        for blk in (0, 1):
            xl = col_x(blk * 4) - CW / 2 + 2; xr = col_x(blk * 4 + 3) + CW / 2 - 2
            c.drawRect(skia.Rect(xl - 4, y + 2, xr + 4, y + 20), lin(y + 2, y + 20, [(.20, .18, .16), (.12, .11, .10)]))  # driveway
            c.drawRect(skia.Rect(xl, y - DH - 18, xr, y + 2), lin(y - DH - 18, y, [WALL_T, WALL_B]))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xl - 5, y - DH - 27, xr + 5, y - DH - 16), 3, 3),
                        lin(y - DH - 27, y - DH - 16, [(.70, .55, .34), ROOF]))
            for k in range(1, 4):   # piers between doors
                xp = col_x(blk * 4 + k) - CW / 2
                c.drawLine(xp, y - DH - 16, xp, y + 1, S_((.70, .64, .54), .7, 1.5))

def draw_inside(c, g, t):
    x, y = g["x"], g["y"]
    R = skia.Rect(x - DW / 2, y - DH, x + DW / 2, y)
    c.drawRect(R, lin(y - DH, y, [IN_T, IN_B]))
    c.save(); c.clipRect(R, doAntiAlias=True)
    c.drawCircle(x, y - DH + 6, 26, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x, y - DH + 6), 26, [c4((1, .85, .55), .55).toColor(), c4((1, .85, .55), 0).toColor()])))
    c.drawCircle(x, y - DH + 5, 3.2, P_((1, .93, .75)))
    # cream car, front view
    cb = skia.Path(); cb.addRRect(skia.RRect.MakeRectXY(skia.Rect(x - 28, y - 30, x + 28, y - 9), 7, 7))
    c.drawPath(cb, P_(CAR))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 20, y - 44, x + 20, y - 27), 7, 7), P_(CAR))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 16, y - 41, x + 16, y - 30), 4, 4), P_((.25, .24, .24)))
    for s in (-1, 1):
        c.drawCircle(x + s * 19, y - 20, 4, P_((1, .88, .55)))
        c.drawRect(skia.Rect(x + s * 22 - 5, y - 10, x + s * 22 + 5, y - 1), P_((.12, .11, .10)))
    c.restore()
    c.drawRect(R, S_((.55, .46, .34), .9, 2))

def draw_door(c, g, t):
    x, y = g["x"], g["y"]
    d = door(g, t)
    top = y - DH - d * DH
    c.save(); c.clipRect(skia.Rect(x - DW / 2 - 1, y - DH, x + DW / 2 + 1, 4000), doAntiAlias=True)
    R = skia.Rect(x - DW / 2 + 1, top, x + DW / 2 - 1, top + DH)
    c.drawRect(R, lin(top, top + DH, [DOOR_T, DOOR_B]))
    for k in range(1, 6):
        yy = top + k * DH / 6
        c.drawLine(x - DW / 2 + 3, yy, x + DW / 2 - 3, yy, S_(SLAT, .55, 1.6))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 8, top + DH - 9, x + 8, top + DH - 5), 2, 2), P_(CAR, .95))
    c.drawLine(x - DW / 2 + 1, top + DH - 1, x + DW / 2 - 1, top + DH - 1, S_(SLAT, .9, 2))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, L1, W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, L2, W / 2, 354, F_Q2, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], col_x(i), 528, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), X0 - CW / 2 - 24, row_y(r) - DH / 2 + 2, F_AX, AMBER, .9)
        draw_terraces(c)
        for g in G: draw_inside(c, g, t)
        for g in G: draw_door(c, g, t)
        yb = 1560
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 40, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 38, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def rattle(seed, f0, dur, odd=False):
    rg = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR; x = t / dur
    am = .55 + .45 * np.sign(np.sin(2 * np.pi * (34 if odd else 40) * t))
    s = bp(rg.standard_normal(n), 700 * (.85 if odd else 1), 2600 * (.85 if odd else 1)) * am * np.sin(np.pi * x) ** 1.5 * .16
    tk_t = np.arange(int(.1 * SR)) / SR
    tk = np.sin(2 * np.pi * f0 * (.9 if odd else 1) * tk_t) * np.exp(-tk_t * 40) * .5
    k = max(0, n - len(tk)); s[k:k + len(tk)] += tk[:n - k]
    return s
def thunk(f0):
    tt = np.arange(int(.16 * SR)) / SR
    return (np.sin(2 * np.pi * f0 * .5 * tt) * .7 + np.sin(2 * np.pi * f0 * tt) * .2) * np.exp(-tt * 30) * .6

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for t0 in opens(g):
            if not (0 <= t0 < LOOP): continue
            kd = kind(g, t0)
            if kd == "down": ev.append((k, t0, "odd", .2))
            elif kd == "rev": ev.append((k, t0, "open", .26)); ev.append((k, t0 + BREAK - .02, "close", 0))
            else: ev.append((k, t0, "open", .3 * g["P"])); ev.append((k, t0 + .8 * g["P"] - .03, "close", 0))
    et = np.array([e[1] for e in ev])
    for k, ts, typ, dur in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .25).sum())) * 1.1
        f0 = note(2 + (8 - g["r"]) // 2 + (g["i"] % 3), 220.0)
        if typ == "close": s = thunk(f0); a = .30
        else: s = rattle(k * 131 + int(ts * 977), f0, dur, typ == "odd"); a = .34
        m.add(s, ts % LOOP, a / dens, g["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 200, 900) * .006
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "garages; odd", ODD, "breaks at", [round(b, 2) for b in BREAKS])
    print("decoys:", sorted([(g["lab"], t) for g in G if not g["odd"] for t, k in g["ev"].items()
                             if any(abs(t - b % LOOP) < .4 for b in BREAKS)]))
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print(audio(f"{OUT}/spot.wav"))
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_garages.mp4"))
