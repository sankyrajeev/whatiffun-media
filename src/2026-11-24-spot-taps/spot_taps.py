"""SPOT IT v3 (10:00, 2026-11-24): WHICH TAP / BREAKS PHYSICS? 48 identical brass taps on RISER PIPES
(8 copper riser pipes = columns A-H, 6 rows; every tap branches off its pipe, spouts alternate right/left
row by row so the taps zig-zag down each pipe; column letters on top, row numbers on the left). Every tap
runs non-stop on a 1.5 / 2.0 / 2.4 s cycle from a random phase: its cross handle turns open, a burst of
five big drops falls from the spout and splashes into the cream basin below, then the handle turns shut.
ONE tap breaks gravity: its drops jump OUT of the basin and fall UP into the spout.
Rule type: up instead of down (BREAKS PHYSICS, today's one).
Sound: a soft valve tick on open/close, a water plink per landed drop (pentatonic by row, panned by x,
density-normalised); the odd one's drops are reversed plinks (swelling, cut off) - an audio clue.
12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/taps"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 6
PX = float(os.environ.get("PX", "104"))
PY = float(os.environ.get("PY", "156"))
Y0 = float(os.environ.get("Y0", "588"))      # junction y of row 1
PCT = int(os.environ.get("PCT", "4"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))
XOFF = float(os.environ.get("XOFF", "-22"))
colx = [W / 2 + XOFF + (i - (NC - 1) / 2) * PX for i in range(NC)]

SP = 38.0            # spout reach
TIPY = 20.0          # spout tip y (below junction)
BY = 86.0           # basin water surface y
FALL = BY - TIPY
TF = 0.30            # fall time
GACC = 2 * FALL / TF ** 2
ND, DT = 3, 0.12    # drops per burst, spacing
T_OPEN, T_DROP0, T_CLOSE = 0.0, 0.16, 0.62

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        G.append(dict(lab=lab, odd=lab == ODD, cx=colx[i], y=Y0 + r * PY, r=r, i=i,
                      d=1,
                      P=float(rng.choice([1.5, 2.0, 2.4], p=[.3, .4, .3])), ph=rng.uniform(0, 1)))
for g in G:
    if g["odd"]: g["P"] = 2.0
print(len(G), "taps")
assert sum(g["odd"] for g in G) == 1

def cyc(g, t):
    """time u into the current cycle (and the previous cycle's u, for drops still in flight)"""
    P = g["P"]
    return ((t / P + g["ph"]) % 1.0) * P

def handle_angle(u):
    if u < T_OPEN + .2: return 90 * ss((u - T_OPEN) / .2)
    if u < T_CLOSE: return 90
    if u < T_CLOSE + .2: return 90 * (1 - ss((u - T_CLOSE) / .2))
    return 0.0

def drops(g, t):
    """list of (y, vy_sign, age) for drops in flight; plus splash events (age since landing / leaving)"""
    out, spl = [], []
    P = g["P"]
    u = cyc(g, t)
    for back in (0, 1):
        uu = u + back * P
        for k in range(ND):
            tau = uu - (T_DROP0 + k * DT)
            if tau < 0: continue
            if tau < TF:
                if g["odd"]:
                    y = BY - .5 * GACC * tau * tau       # leaves basin slowly, accelerates up
                else:
                    y = TIPY + .5 * GACC * tau * tau
                out.append((y, tau))
            # splash at the basin: at landing (normal) or at leaving (odd)
            sa = tau - (0 if g["odd"] else TF)
            if 0 <= sa < .45: spl.append(sa)
    return out, spl

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BRASS_HI, BRASS, BRASS_LO = (.98, .86, .58), (.84, .64, .32), (.50, .34, .14)
COPPER = [(.42, .24, .13), (.80, .50, .30), (.62, .36, .20), (.36, .20, .11)]
WATER = (.70, .87, .97)
PIPE_PAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-7, 0), (7, 0)],
    [c4(c).toColor() for c in COPPER], [0, .35, .7, 1]))
BASIN_PAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-30, 0), (30, 0)],
    [c4((.70, .64, .56)).toColor(), c4((.98, .95, .89)).toColor(), c4((.86, .80, .70)).toColor(),
     c4((.58, .52, .44)).toColor()], [0, .35, .7, 1]))

def teardrop(up_tail=True):
    # 16 x 26 teardrop centred on its round part; tail pointing up (falling) or down (rising)
    p = skia.Path()
    s = -1 if up_tail else 1
    p.moveTo(0, s * 17)
    p.cubicTo(3, s * 9, 8, s * 3, 8, -s * 1)
    p.cubicTo(8, -s * 6, 4, -s * 9, 0, -s * 9)
    p.cubicTo(-4, -s * 9, -8, -s * 6, -8, -s * 1)
    p.cubicTo(-8, s * 3, -3, s * 9, 0, s * 17)
    p.close()
    return p
DROP_DN, DROP_UP = teardrop(True), teardrop(False)

def draw_pipes(c):
    # a faint tiled wall: one tile per tap, grout lines
    x0, x1 = colx[0] - 30, colx[-1] + PX - 30
    y0, y1 = Y0 - 44, Y0 - 44 + NR * PY
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), 14, 14), P_((.16, .13, .11), .55))
    for i in range(1, NC):
        x = colx[i] - 30
        c.drawLine(x, y0 + 6, x, y1 - 6, P_((.30, .25, .2), .35, StrokeWidth=2))
    for r in range(1, NR):
        y = Y0 - 44 + r * PY
        c.drawLine(x0 + 6, y, x1 - 6, y, P_((.30, .25, .2), .35, StrokeWidth=2))
    for x in colx:
        for r in range(NR):
            y = Y0 + r * PY
            c.drawCircle(x, y, 15, P_((.55, .40, .22)))
            c.drawCircle(x, y, 12, P_(BRASS_LO))

def draw_tap(c, g, t):
    d = g["d"]; u = cyc(g, t)
    c.save(); c.translate(g["cx"], g["y"])
    # basin + bracket
    bx = d * SP
    
    bowl = skia.Path(); bowl.moveTo(bx - 29, BY); bowl.cubicTo(bx - 27, BY + 26, bx + 27, BY + 26, bx + 29, BY); bowl.close()
    c.drawPath(bowl, BASIN_PAINT)
    c.drawOval(skia.Rect(bx - 29, BY - 6, bx + 29, BY + 6), P_((.93, .89, .80)))
    c.drawOval(skia.Rect(bx - 24, BY - 4, bx + 24, BY + 4), P_((.36, .52, .62)))
    c.drawOval(skia.Rect(bx - 20, BY - 3, bx + 12, BY + 1), P_(WATER, .35))
    fl, spl = drops(g, t)
    for sa in spl:
        k = sa / .45
        rx = 8 + 24 * k
        c.drawOval(skia.Rect(bx - rx, BY - rx * .22, bx + rx, BY + rx * .22),
                   P_((.92, .97, 1), .85 * (1 - k), Style=skia.Paint.kStroke_Style, StrokeWidth=2.5))
        if sa < .22:   # two little splash droplets
            h = 70 * sa - 160 * sa * sa
            for sx in (-1, 1):
                c.drawCircle(bx + sx * (4 + 50 * sa), BY - 2 - h * 30 / 7.6, 3.2, P_((.85, .95, 1), 1 - sa / .3))
    # junction collar + spout
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-11, -10, 11, 10), 4, 4), P_(BRASS_LO))
    sp = skia.Path(); sp.moveTo(0, 0); sp.lineTo(d * (SP - 12), 0)
    sp.quadTo(d * SP, 0, d * SP, TIPY - 4)
    c.drawPath(sp, P_(BRASS_LO, 1, Style=skia.Paint.kStroke_Style, StrokeWidth=11, StrokeCap=skia.Paint.kRound_Cap))
    c.drawPath(sp, P_(BRASS, 1, Style=skia.Paint.kStroke_Style, StrokeWidth=8, StrokeCap=skia.Paint.kRound_Cap))
    c.save(); c.translate(0, -2.2)
    c.drawPath(sp, P_(BRASS_HI, .8, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4, StrokeCap=skia.Paint.kRound_Cap))
    c.restore()
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(d * SP - 6, TIPY - 6, d * SP + 6, TIPY + 1), 2, 2), P_(BRASS_LO))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-9, -8, 9, 8), 3, 3), P_(BRASS))
    # stem + cross handle (turns open / shut: a rotating cross seen from the side)
    hx = d * 13
    c.drawRect(skia.Rect(hx - 3, -24, hx + 3, -6), P_(BRASS_LO))
    th = math.radians(handle_angle(u) * 2 + 20)
    arms = []
    for k in range(4):
        a = th + k * math.pi / 2
        arms.append((math.sin(a), 19 * math.cos(a), -27 + 4.5 * math.sin(a)))
    arms.sort(key=lambda z: z[0])
    for depth, ax, ay in arms:
        col = BRASS_HI if depth > 0 else BRASS
        c.drawLine(hx, -27, hx + ax, ay, P_(BRASS_LO, 1, StrokeWidth=6.5, StrokeCap=skia.Paint.kRound_Cap))
        c.drawLine(hx, -27, hx + ax, ay, P_(col, 1, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap))
        c.drawCircle(hx + ax, ay, 4.2, P_((.96, .92, .84) if depth > -.2 else (.8, .76, .68)))
    c.drawCircle(hx, -27, 4.5, P_(BRASS_HI))
    # drops
    for y, tau in fl:
        pth = DROP_UP if g["odd"] else DROP_DN
        c.save(); c.translate(bx, y); c.scale(1.5, 1.5)
        c.drawPath(pth, P_(WATER, .95))
        c.drawCircle(-3, (2 if g["odd"] else -2), 2.2, P_((1, 1, 1), .9))
        c.restore()
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH TAP", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], colx[i] + PX / 2 - 30, 512, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 106, Y0 + r * PY + 52, F_AX, AMBER, .9)
        draw_pipes(c)
        for g in G: draw_tap(c, g, t)
        yb = 1562
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def plink(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.18 * SR)) / SR
    f = f0 * (1 + .9 * (1 - np.exp(-t * 60)))          # rising bubble pitch
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 30) + bp(rg.standard_normal(len(t)), 2500, 8000) * np.exp(-t * 200) * .25
    return s * np.minimum(1, t * 5000)
def tick(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.04 * SR)) / SR
    return bp(rg.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 180) * .35

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            t0 = (c_ - g["ph"]) * g["P"]
            ev.append((k, "tick", t0 + .02)); ev.append((k, "tick", t0 + T_CLOSE + .18))
            for j in range(ND):
                td = t0 + T_DROP0 + j * DT
                ev.append((k, "plink", td if g["odd"] else td + TF))
    pl = np.array([e[2] for e in ev if e[1] == "plink" and 0 <= e[2] < LOOP])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(pl - ts) < .1).sum()))
        if kind == "plink":
            f0 = note(5 + (5 - g["r"]) + (g["i"] % 2) * 2, 261.63)
            s = plink(f0, k * 11 + int(ts * 97))
            if g["odd"]:
                s = s[::-1] * .9                            # reversed drip: swells, then cut off
            m.add(s, ts, (.62 if g["odd"] else .42) / dens, g["cx"])
        else:
            m.add(tick(k * 13 + int(ts * 31)), ts, .16 / dens, g["cx"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    # a faint room tone so it never goes dead
    rg = np.random.default_rng(3)
    m.L += bp(rg.standard_normal(n), 200, 1200) * .006; m.R += bp(rg.standard_normal(n), 200, 1200) * .006
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_taps.mp4"))
