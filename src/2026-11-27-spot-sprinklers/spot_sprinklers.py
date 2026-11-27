"""SPOT IT v3 (18:00, 2026-11-27): WHICH SPRINKLER / BREAKS PHYSICS?
70 identical oscillating lawn sprinklers (cream sled base, brass tube, five water jets) on BRICK-PATTERN LAWN PLOTS:
7 columns (A-G) x 10 rows, odd rows shifted half a plot to the right like brickwork; letters on top, numbers on the left.
Every sprinkler sweeps its fan of water from side to side non-stop (+-30..40 deg, dwelling at each end) on a
1.5 / 1.71 / 2.0 / 2.4 s cycle from a random phase; the water arcs up and falls back onto its own lawn.
Now and then a sprinkler gets a legal pressure SURGE: its arcs shoot ~70% higher for ~0.55 s, but still fall down.
ONE sprinkler (ODD) twice per loop, for ~0.55 s, has its water FALL UP: the jets bend upwards and stream off into
the sky (gravity reversed). At each of those moments 5 decoys surge. Rule type: BREAKS PHYSICS (falls up, not down).
Sound: soft plastic tick at each end of a sweep (pitch by row, panned by x, density-normalised) over a light water
hiss; the odd sprinkler's ticks are a touch lower (subtle).  12 s seamless loop.
Reproduce: python3 spot_sprinklers.py render x <outdir>"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spr"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFG"
NC, NR = 7, 10
CW = float(os.environ.get("CW", "110"))
RH = float(os.environ.get("RH", "94"))
Y0 = float(os.environ.get("Y0", "648"))          # ground line of row 1
PCT = int(os.environ.get("PCT", "5"))
ODD = (os.environ.get("OL", "B"), int(os.environ.get("ON", "8")))
NDEC = int(os.environ.get("NDEC", "5"))
WIN = float(os.environ.get("WIN", "0.55"))       # length of a break / surge
H0 = float(os.environ.get("H0", "54"))           # jet height at alpha = 0
KX = float(os.environ.get("KX", "0.46"))         # horizontal squash of the arcs
SURGE = float(os.environ.get("SURGE", "1.26"))   # speed factor of a surge
rng = np.random.default_rng(int(os.environ.get("SEED", "2718")))
SPREAD = [-20, -10, 0, 10, 20]

def col_x(i, r): return 540 + (i - 3) * CW + ((r % 2) - .5) * CW / 4
def row_y(r): return Y0 + r * RH

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([12 / 8, 12 / 7, 12 / 6, 12 / 5]))
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i, r), y=row_y(r), r=r, i=i, P=P,
                      ph=rng.uniform(0, P), A=rng.uniform(30, 40), wob=rng.uniform(0, 2 * math.pi),
                      win=[]))                     # list of (t_center, kind)
ODDG = [g for g in G if g["odd"]][0]
BTIMES = [float(os.environ.get("B1", "4.6")), float(os.environ.get("B2", "10.3"))]
for tb in BTIMES:
    ODDG["win"].append((tb, "up"))
    cand = [g for g in G if not g["odd"] and not (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1)]
    idx = rng.choice(len(cand), NDEC, replace=False)
    for k in idx: cand[k]["win"].append((tb + rng.uniform(-.12, .12), "surge"))
# random legal surges all through the loop (about one every ~9 s per sprinkler)
for g in G:
    if g["odd"]: continue
    for j in range(int(rng.poisson(1.3))):
        tc = rng.uniform(.6, LOOP - .6)
        if all(abs(tc - b) > .9 for b in BTIMES) and all(abs(tc - w[0]) > 1.2 for w in g["win"]):
            g["win"].append((tc, "surge"))

def env(t, tc):
    """0..1 window around tc, ~WIN long with 0.12 s ramps; wraps around the loop."""
    d = abs(((t - tc + LOOP / 2) % LOOP) - LOOP / 2)
    half = WIN / 2
    if d >= half: return 0.0
    return ss(min(1.0, (half - d) / .12))

def state(g, t):
    u = ((t - g["ph"]) / g["P"]) % 1.0
    th = g["A"] * max(-1, min(1, 1.3 * math.cos(2 * math.pi * u)))
    vf, gf = 1.0 + .03 * math.sin(2 * math.pi * t / 1.5 + g["wob"]), 1.0
    for tc, k in g["win"]:
        e = env(t, tc)
        if e <= 0: continue
        if k == "surge": vf *= 1 + (SURGE - 1) * e
        else: gf = 1 - 2 * e                       # +1 -> -1: gravity reversed
    return th, vf, gf

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def lin(y0, y1, cols):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y0), (0, y1)], [c4(cc).toColor() for cc in cols]))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH SPRINKLER", "BREAKS PHYSICS?"
def fit(s, size, maxw=850):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_Q = F_Q2 = F_Q2 if F_Q2.getSize() < F_Q.getSize() else F_Q
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

AMB_HI, AMB, AMB_LO = (1.0, .82, .48), (.90, .58, .20), (.55, .30, .08)
CRM = (.95, .91, .83)
BRASS = (.86, .70, .40)
WATER = (.90, .97, 1.0)
LAWN_HI, LAWN_LO = (.15, .20, .10), (.07, .10, .05)

def draw_plots(c):
    for i in range(NC + 1):
        px = 540 + (i - 3.5) * CW
        c.drawLine(px, row_y(0) - 84, px, row_y(NR - 1) + 22, S_((.55, .45, .32), .16, 6))
    for g in G:
        x, y = g["x"], g["y"]
        rr = skia.RRect.MakeRectXY(skia.Rect(x - 50, y - 72, x + 50, y + 16), 12, 12)
        c.drawRRect(rr, lin(y - 72, y + 16, [LAWN_LO, LAWN_HI]))
        c.drawRRect(rr, S_((.42, .50, .28), .35, 1.4))
        # a few grass blades along the ground line
        for k in range(9):
            bx = x - 42 + k * 10.5 + (k * 37 % 5)
            c.drawLine(bx, y + 6, bx + 1.5, y - 1 - (k * 13 % 4), S_((.38, .48, .22), .7, 1.6))

DASH_SPD = 70.0       # px/s along the jets; 70 * 12 / 14 = 60 -> seamless
def jet_path(x, y, alpha, vf, gf):
    a = math.radians(alpha)
    H = H0 * vf * vf                              # v^2 / 2g with g = 1 scale
    p = skia.Path(); p.moveTo(x, y)
    # parametric in normalised time s (s = 1 is the normal landing time for gf = 1)
    end = None
    n = 24
    e = (1 - gf) / 2                              # 0 normal .. 1 falls up
    smax = 1.0 + .25 * e
    tip = None
    for k in range(1, n + 1):
        s = k / n * smax
        X = (1 + .35 * e) * KX * 4 * H * math.sin(a) * math.cos(a) * s
        c2 = math.cos(a) ** 2
        Yn = -4 * H * c2 * (s - s * s)
        Ym = Yn if s <= .5 else 2 * (-H * c2) - Yn   # past the top it keeps rising: a mirrored fall
        Y = Yn * (1 - e) + Ym * e
        if e < .5 and Y > 0: Y = 0
        p.lineTo(x + X, y + Y); tip = (x + X, y + Y)
    return p, tip

def draw_sprinkler(c, g, t):
    x, y = g["x"], g["y"] - 6
    th, vf, gf = state(g, t)
    # water first (behind the tube)
    ph = -(t * DASH_SPD) % 14.0
    dash = skia.DashPathEffect.Make([8.0, 6.0], ph)
    for sp in SPREAD:
        al = th + sp
        path, tip = jet_path(x, y - 6, al, vf, gf)
        c.drawPath(path, S_(WATER, .28, 5.0))
        pd = S_(WATER, .95, 3.0); pd.setPathEffect(dash)
        c.drawPath(path, pd)
        if tip and gf > .5:                       # splash where it lands
            for k in (-1, 0, 1):
                c.drawLine(tip[0] + k * 3, tip[1] - 1, tip[0] + k * 6, tip[1] - 5 - (k == 0) * 2, S_(WATER, .55, 1.4))
        elif tip and gf < 0:                      # spray leaving upwards
            for k in (-1, 0, 1):
                c.drawLine(tip[0] + k * 4, tip[1] + 2, tip[0] + k * 6, tip[1] - 6, S_(WATER, .5, 1.4))
    # base sled
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 24, y + 2, x + 24, y + 9), 3, 3), P_(CRM, .95))
    c.drawRect(skia.Rect(x - 22, y + 8, x + 22, y + 10), P_((0, 0, 0), .35))
    # end posts
    for dx in (-18, 18):
        c.drawLine(x + dx, y + 3, x + dx * .8, y - 8, S_(BRASS, .95, 3.0))
    # tube (seen end-on: a ring that rotates, with a nozzle marker)
    c.drawCircle(x, y - 7, 9, P_(BRASS))
    c.drawCircle(x, y - 7, 9, S_(AMB_LO, .8, 1.5))
    a = math.radians(th)
    c.drawCircle(x + 6.5 * math.sin(a), y - 7 - 6.5 * math.cos(a), 2.6, P_(AMB_LO))
    c.drawCircle(x - 3, y - 10, 2.2, P_((1, .97, .9), .5))

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
            text(c, LET[i], 540 + (i - 3) * CW, 524, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 106, row_y(r) - 20, F_AX, AMBER, .9)
        draw_plots(c)
        for g in sorted(G, key=lambda g: -g["r"]): draw_sprinkler(c, g, t)   # upper rows' jets drawn last
        yb = 1574
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
def tick(seed, f0, low=False):
    rg = np.random.default_rng(seed)
    n = int(.12 * SR); t = np.arange(n) / SR
    k = .92 if low else 1.0
    s = np.sin(2 * np.pi * f0 * 3 * k * t) * np.exp(-t * 55) * .28
    s += bp(rg.standard_normal(n), 1500 * k, 4200 * k) * np.exp(-t * 90) * .22
    return s

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        P = g["P"]
        n = int(round(LOOP / P))
        for j in range(2 * n):
            ev.append((k, (g["ph"] + j * P / 2) % LOOP))
    et = np.array([e[1] for e in ev])
    for k, ts in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .2).sum())) * 1.1
        f0 = note(2 + (9 - g["r"]) // 2 + (g["i"] % 3), 220.0)
        m.add(tick(k * 131 + int(ts * 977), f0, g["odd"]), ts, .5 / dens, g["x"])
    nn = int(LOOP * SR)
    m.L[:m.N - nn] += m.L[nn:]; m.R[:m.N - nn] += m.R[nn:]
    m.L, m.R, m.N = m.L[:nn], m.R[:nn], nn
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):                         # soft water hiss bed, loop-continuous noise
        buf += bp(rg.standard_normal(nn), 2500, 7000) * .018 + bp(rg.standard_normal(nn), 400, 1200) * .008
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "sprinklers; odd", ODD, "falls up at", BTIMES)
    print("decoys at breaks:", sorted([(g["lab"], round(w[0], 2)) for g in G if not g["odd"] for w in g["win"]
                                       if any(abs(w[0] - b) < .4 for b in BTIMES)]))
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_sprinklers.mp4"))
