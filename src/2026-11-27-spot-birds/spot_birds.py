"""SPOT IT v3 (15:00, 2026-11-27): WHICH BIRD / STOPS MID-AIR?
64 identical drinking birds (amber glass head + bulb, cream top hat, brass legs, a glass of water in front) on a
SHELF WALL: 8 walnut wall shelves (rows 1-8) with brass brackets, 8 birds per shelf (columns A-H); letters on top,
numbers on the left.
Every bird rocks back and dips its beak into its glass non-stop, on a 1.5 / 1.71 / 2.0 / 2.4 s cycle from a random
phase (+-23% speed jitter). Now and then a bird legally 'drinks': it rests with its beak in the water for 0.5 s.
ONE bird (ODD) twice per loop STOPS MID-AIR: on its way down it freezes, tilted halfway, beak in empty air, for
0.5 s (impossible: nothing holds it), then carries on. At each of those moments 5 decoys pause legally in the water.
Rule type: STOPS (freezes mid-motion). Sound: a soft glass tink + water plip at each dip, a tiny wooden creak at the
back of each rock (pitch by row, panned by x, density-normalised); the odd bird's tink is a touch lower (subtle).
12 s seamless loop.  Reproduce: python3 spot_birds.py render x <outdir>"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/birds"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 8
CW = float(os.environ.get("CW", "104"))
RP = float(os.environ.get("RP", "120"))
SC = float(os.environ.get("SC", "0.86"))
Y0 = 606.0                                   # pivot of row 1
PCT = int(os.environ.get("PCT", "4"))
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "7")))
NDEC = int(os.environ.get("NDEC", "5"))
HOLD = float(os.environ.get("HOLD", "0.5"))
FREEZE = float(os.environ.get("FREEZE", "42"))   # degrees the odd bird hangs at
rng = np.random.default_rng(int(os.environ.get("SEED", "2715")))

BACK, DIP = -24.0, 96.0
def col_x(i): return 540 + (i - 3.5) * CW - 14 * SC
def row_y(r): return Y0 + r * RP
def s_of(u):
    b = .5 - .5 * math.cos(2 * math.pi * u)
    return 1 - (1 - b) ** 1.6
def u_for(theta):              # phase on the way DOWN where the angle equals theta
    lo, hi = 0.0, .5
    for _ in range(40):
        m = (lo + hi) / 2
        if BACK + (DIP - BACK) * s_of(m) < theta: lo = m
        else: hi = m
    return lo
UF = u_for(FREEZE)

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([12 / 8, 12 / 7, 12 / 6, 12 / 5]))
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i), y=row_y(r), r=r, i=i, P=P,
                      ph=rng.uniform(0, P), ev={}))
ODDG = [g for g in G if g["odd"]][0]
ODDG["P"] = 2.4
ODDG["ph"] = (float(os.environ.get("B1", "5.2")) - UF * (2.4 - HOLD)) % 2.4

def cycles(g):
    n = int(round(LOOP / g["P"]))
    return [g["ph"] + j * g["P"] for j in range(-1, n + 2)]
def hold_at(g, t0, uh): return t0 + uh * (g["P"] - HOLD)

def pick(g, want):
    c = [(abs(hold_at(g, t0, UF) - want), t0) for t0 in cycles(g) if 1.0 < hold_at(g, t0, UF) < LOOP - 1.2]
    return min(c)[1]
BREAKS = [pick(ODDG, float(os.environ.get("B1", "4.8"))), pick(ODDG, float(os.environ.get("B2", "10.0")))]
BTIMES = [hold_at(ODDG, t0, UF) for t0 in BREAKS]
for t0b, tb in zip(BREAKS, BTIMES):
    ODDG["ev"][round(t0b % LOOP, 4)] = "freeze"
    cand = []
    for g in G:
        if g["odd"] or g["P"] < 1.7 or (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1): continue
        for t0 in cycles(g):
            d = abs(hold_at(g, t0, .5) - tb)
            if d < .3: cand.append((d + rng.uniform(0, .15), id(g), g, t0))
    cand.sort(key=lambda x: x[0]); used = set()
    for _, gid, g, t0 in cand:
        if gid in used or len(used) >= NDEC: continue
        used.add(gid); g["ev"][round(t0 % LOOP, 4)] = "drink"
for g in G:
    if g["odd"] or g["P"] < 1.9: continue
    for t0 in cycles(g):
        if 0 <= t0 < LOOP and rng.random() < .08: g["ev"].setdefault(round(t0 % LOOP, 4), "drink")

def kind(g, t0): return g["ev"].get(round(t0 % LOOP, 4))

def angle(g, t):
    """returns (angle deg, splash 0..1). t0 = back extreme of the cycle."""
    P = g["P"]
    j = math.floor((t - g["ph"]) / P); t0 = g["ph"] + j * P
    dt = t - t0
    k = kind(g, t0)
    if k in ("freeze", "drink"):
        uh = UF if k == "freeze" else .5
        m = P - HOLD
        if dt < uh * m: u = dt / m
        elif dt < uh * m + HOLD: u = uh
        else: u = (dt - HOLD) / m
    else:
        u = dt / P
    th = BACK + (DIP - BACK) * s_of(u)
    sp = max(0.0, (th - 86) / 10)          # beak in the water
    return th, sp

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def rad(cx, cy, r, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (cx, cy), r, [c4(*cc).toColor() if isinstance(cc[0], tuple) else c4(cc).toColor() for cc in cols], pos))
def lin(y0, y1, cols):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y0), (0, y1)], [c4(cc).toColor() for cc in cols]))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH BIRD", "STOPS MID-AIR?"
def fit(s, size, maxw=850):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_Q = F_Q2 if F_Q2.getSize() < F_Q.getSize() else F_Q
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

AMB_HI, AMB, AMB_LO = (1.0, .82, .48), (.90, .58, .20), (.55, .30, .08)
HAT = (.95, .91, .83)
BRASS = (.86, .70, .40)
DARK = (.14, .12, .10)
SHELF_Y = 58 * SC                          # shelf top relative to the pivot

def draw_shelves(c):
    for r in range(NR):
        y = row_y(r) + SHELF_Y
        c.drawRect(skia.Rect(120, y + 14, 960, y + 22), P_((0, 0, 0), .28))           # shadow on the wall
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(118, y, 962, y + 13), 3, 3),
                    lin(y, y + 13, [(.42, .29, .18), (.24, .16, .10)]))
        c.drawLine(122, y + 1.2, 958, y + 1.2, S_((.62, .46, .30), .55, 1.4))
        for bx in (170, 540, 910):
            c.drawRect(skia.Rect(bx - 4, y + 13, bx + 4, y + 30), P_(BRASS, .75))

def draw_glass(c, g, sp, front):
    s = SC
    x0, x1, y0, y1 = 30 * s, 62 * s, 8 * s, SHELF_Y
    if not front:
        c.drawRect(skia.Rect(x0, 22 * s, x1, y1), P_((.80, .86, .90), .16))            # water
        c.drawLine(x0 + 1, 22 * s, x1 - 1, 22 * s, S_((.92, .95, 1.0), .45, 1.4))
    else:
        c.drawLine(x0, y0, x0 + 1, y1, S_((.95, .95, .92), .55, 1.6))
        c.drawLine(x1, y0, x1 - 1, y1, S_((.95, .95, .92), .55, 1.6))
        c.drawLine(x0 + 1, y1 - 1, x1 - 1, y1 - 1, S_((.95, .95, .92), .5, 2.0))
        c.drawLine(x0 + 5, y0 + 6, x0 + 5, y1 - 8, S_((1, 1, 1), .22, 2.4))
        if sp > 0:
            cx = 45 * s
            for k in range(5):
                a = math.radians(-150 + k * 30)
                rr = 6 + 12 * sp
                c.drawCircle(cx + rr * math.cos(a), 20 * s + rr * math.sin(a) * .8, 1.8, P_((.9, .95, 1), .7 * sp))

def draw_bird(c, g, t):
    s = SC
    th, sp = angle(g, t)
    c.save(); c.translate(g["x"], g["y"])
    # shadow on the shelf
    c.drawOval(skia.Rect(-30 * s, SHELF_Y - 4, 66 * s, SHELF_Y + 4), P_((0, 0, 0), .33))
    draw_glass(c, g, sp, False)
    # legs
    for dx in (-17, 17):
        c.drawLine(0, 0, dx * s, SHELF_Y - 1, S_(BRASS, .95, 3.2))
        c.drawLine(dx * s - 6, SHELF_Y - 1, dx * s + 6, SHELF_Y - 1, S_(BRASS, .95, 3.2))
    c.save(); c.rotate(th)
    # tube
    c.drawLine(0, 34 * s, 0, -44 * s, S_((.96, .93, .86), .55, 7 * s))
    c.drawLine(0, 34 * s, 0, -6 * s, S_(AMB, .9, 3.6 * s))
    # bottom bulb
    c.drawCircle(0, 38 * s, 17 * s, rad(-5 * s, 32 * s, 24 * s, [AMB_HI, AMB, AMB_LO], [0, .45, 1]))
    c.drawCircle(-6 * s, 32 * s, 4 * s, P_((1, .97, .9), .55))
    # head
    c.drawCircle(0, -46 * s, 13 * s, rad(-4 * s, -50 * s, 18 * s, [AMB_HI, AMB, AMB_LO], [0, .45, 1]))
    c.drawCircle(-4 * s, -50 * s, 3 * s, P_((1, .97, .9), .55))
    # beak
    bk = skia.Path(); bk.moveTo(9 * s, -51 * s); bk.lineTo(28 * s, -45 * s); bk.lineTo(9 * s, -40 * s); bk.close()
    c.drawPath(bk, P_(BRASS))
    c.drawCircle(4 * s, -49 * s, 2.2 * s, P_(DARK))
    # top hat
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-15 * s, -60 * s, 15 * s, -56 * s), 2, 2), P_(HAT))
    c.drawRect(skia.Rect(-9 * s, -76 * s, 9 * s, -59 * s), lin(-76 * s, -59 * s, [HAT, (.80, .74, .64)]))
    c.drawRect(skia.Rect(-9 * s, -63 * s, 9 * s, -60 * s), P_(AMB_LO, .9))
    c.restore()
    c.drawCircle(0, 0, 4.2 * s, P_(BRASS)); c.drawCircle(0, 0, 1.8 * s, P_(AMB_LO))
    draw_glass(c, g, sp, True)
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
            text(c, LET[i], col_x(i) + 14 * SC, 528, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 104, row_y(r) + 22, F_AX, AMBER, .9)
        draw_shelves(c)
        for g in G: draw_bird(c, g, t)
        yb = 1562
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 38, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 36, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1644, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def tink(seed, f0, low=False):
    rg = np.random.default_rng(seed)
    n = int(.25 * SR); t = np.arange(n) / SR
    k = .93 if low else 1.0
    s = np.sin(2 * np.pi * f0 * 4 * k * t) * np.exp(-t * 28) * .30
    s += np.sin(2 * np.pi * f0 * 6.1 * k * t) * np.exp(-t * 40) * .10
    s += bp(rg.standard_normal(n), 900, 3200) * np.exp(-t * 60) * .18          # plip
    return s
def creak(seed, f0):
    rg = np.random.default_rng(seed)
    n = int(.09 * SR); t = np.arange(n) / SR
    return bp(rg.standard_normal(n), 300, 900) * np.exp(-t * 45) * .12 + np.sin(2 * np.pi * f0 * t) * np.exp(-t * 40) * .06

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        P = g["P"]
        for t0 in cycles(g):
            if not (0 <= t0 < LOOP): continue
            kd = kind(g, t0)
            m_ = P - HOLD if kd in ("freeze", "drink") else P
            td = t0 + .43 * m_ + (HOLD if kd == "freeze" else 0)     # beak reaches the water
            ev.append((k, td, "tink"))
            ev.append((k, t0, "creak"))
    et = np.array([e[1] for e in ev if e[2] == "tink"])
    for k, ts, typ in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .25).sum())) * 1.1
        f0 = note(2 + (7 - g["r"]) // 2 + (g["i"] % 3), 220.0)
        sd = k * 131 + int(ts * 977)
        if typ == "creak": s = creak(sd, f0 * .5); a = .35
        else: s = tink(sd, f0, g["odd"]); a = .5
        m.add(s, ts % LOOP, a / dens, g["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 200, 900) * .004
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "birds; odd", ODD, "freezes at", [round(b, 2) for b in BTIMES], "UF", round(UF, 3))
    print("decoys:", sorted([(g["lab"], round(hold_at(g, t, .5), 2)) for g in G if not g["odd"] for t, k in g["ev"].items()
                             if any(abs(hold_at(g, t, .5) - b) < .4 for b in BTIMES)]))
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_birds.mp4"))
