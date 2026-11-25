"""SPOT IT v3 (13:00, 2026-11-25): WHICH CUCKOO / POPS OUT TWICE?
49 identical walnut cuckoo clocks (cream roof trim, cream face, brass pendulum + pine-cone weights) hung on a
wall in ZIGZAG ROWS (7 columns A-G x 7 rows; alternate columns hang a little higher/lower; letters on top,
numbers on the left). Every pendulum swings non-stop (1.2 / 1.5 / 2.0 s, random phase); every clock's little
doors fly open and a big cream cuckoo pops out ONCE every 2.4 / 3.0 / 4.0 s (random phase).
ONE clock (ODD) pops out TWICE in a row every 2.4 s. Rule type: twice (double vs single).
Sound: a soft two-note whistle per pop (pentatonic by row, panned by x, density-normalised) over quiet
pendulum ticks; the odd one's call is a hollow wooden tock-tock instead (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/cuckoos"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFG"
NC, NR = 7, 7
PX = float(os.environ.get("PX", "124"))
PY = float(os.environ.get("PY", "132"))
Y0 = float(os.environ.get("Y0", "562"))      # body top of row 1
ZZ = float(os.environ.get("ZZ", "12"))       # zigzag offset
SC = float(os.environ.get("SC", "1.0"))      # clock scale
BS = float(os.environ.get("BS", "2.05"))     # bird scale at full pop
PCT = int(os.environ.get("PCT", "12"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "1125")))
colx = [W / 2 + 22 + (i - (NC - 1) / 2) * PX for i in range(NC)]

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([3.0, 4.0, 6.0]))
        G.append(dict(lab=lab, odd=lab == ODD, cx=colx[i], y=Y0 + r * PY + (ZZ if i % 2 else -ZZ), r=r, i=i,
                      P=P, ph=rng.uniform(0, P), PP=float(rng.choice([1.2, 1.5, 2.0])), pph=rng.uniform(0, 1),
                      hand=rng.uniform(0, 2 * math.pi)))
for g in G:
    if g["odd"]: g["P"] = 2.4
print(len(G), "clocks")
assert sum(g["odd"] for g in G) == 1

RISE, HOLD, FALL, GAP = .10, .20, .12, .16
def pop1(u):
    if u < 0: return 0.0
    if u < RISE:
        x = u / RISE; c1 = 2.2
        return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2   # ease-out-back
    if u < RISE + HOLD: return 1.0
    if u < RISE + HOLD + FALL:
        x = (u - RISE - HOLD) / FALL; return 1 - x * x
    return 0.0
D1 = RISE + HOLD + FALL
def popstarts(g):
    """pop start times inside one period (relative)"""
    return [0.0, D1 + GAP] if g["odd"] else [0.0]
def pop(g, t):
    u = (t - g["ph"]) % g["P"]
    return max(pop1(u - s) for s in popstarts(g))
def swing(g, t):
    return math.radians(24) * math.sin(2 * math.pi * (t / g["PP"] + g["pph"]))

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                            StrokeJoin=skia.Paint.kRound_Join)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH CUCKOO", "POPS OUT TWICE?"
def fit(s, size, maxw=830):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BRASS = (.86, .66, .34); BRASS_LO = (.50, .37, .19)
WOOD, WOOD_HI, WOOD_LO = (.42, .24, .12), (.60, .36, .18), (.24, .13, .06)
DARK = (.07, .045, .03)

def lin(x0, x1, cols, pos):
    return skia.GradientShader.MakeLinear([(x0, 0), (x1, 0)], [c4(c).toColor() for c in cols], pos)

def draw_bird(c, p):
    s = BS * (0.25 + 0.75 * min(1.2, p))
    c.save(); c.translate(0, -18 + 8 * p); c.scale(s, s)
    # perch
    c.drawLine(-4, 9, 10, 9, S_(BRASS, 1, 2.2))
    # tail
    tail = skia.Path(); tail.moveTo(-10, 0); tail.lineTo(-24, -6); tail.lineTo(-22, 4); tail.close()
    c.drawPath(tail, P_(AMBER))
    # body
    c.drawOval(skia.Rect(-15, -9, 11, 9), P_(CREAM))
    c.drawOval(skia.Rect(-12, -7, 4, 3), P_((1, 1, .95), .5))
    # wing
    wing = skia.Path(); wing.moveTo(-10, -2); wing.quadTo(-2, -8, 6, -1); wing.quadTo(-2, 5, -10, -2); wing.close()
    c.drawPath(wing, P_(AMBER, .95))
    # head
    c.drawCircle(9, -9, 7.5, P_(CREAM))
    # beak (open while popped out)
    ob = 3.5 * min(1, p)
    bk = skia.Path(); bk.moveTo(15, -11); bk.lineTo(24, -9 - ob * .3); bk.lineTo(15, -8); bk.close()
    bk2 = skia.Path(); bk2.moveTo(15, -8); bk2.lineTo(23, -7 + ob); bk2.lineTo(15, -6); bk2.close()
    c.drawPath(bk, P_(AMBER)); c.drawPath(bk2, P_((.85, .45, .15)))
    c.drawCircle(10.5, -10.5, 1.7, P_(DARK))
    c.restore()

def draw_clock(c, g, t):
    p = pop(g, t)
    sw = swing(g, t)
    c.save(); c.translate(g["cx"], g["y"] - 2.5 * min(1, p)); c.scale(SC, SC)
    # chains + pine-cone weights (sway a touch with the pendulum)
    for sx, h in ((-20, 86), (20, 74)):
        c.drawLine(sx, 60, sx, h, S_(BRASS_LO, 1, 1.6))
        cone = skia.RRect.MakeRectXY(skia.Rect(sx - 5, h, sx + 5, h + 20), 5, 5)
        c.drawRRect(cone, skia.Paint(AntiAlias=True, Shader=lin(sx - 5, sx + 5, [BRASS_LO, BRASS, BRASS_LO], [0, .45, 1])))
    # pendulum
    c.save(); c.translate(0, 60); c.rotate(math.degrees(sw))
    c.drawLine(0, 0, 0, 30, S_(BRASS_LO, 1, 3))
    c.drawCircle(0, 32, 9.5, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (-3, 29), 12, [c4((1, .9, .6)).toColor(), c4(BRASS).toColor(), c4(BRASS_LO).toColor()], [0, .5, 1])))
    c.restore()
    # body
    c.drawRect(skia.Rect(-38, 0, 38, 62), skia.Paint(AntiAlias=True, Shader=lin(-38, 38, [WOOD_LO, WOOD_HI, WOOD, WOOD_LO], [0, .3, .7, 1])))
    c.drawRect(skia.Rect(-38, 58, 38, 64), P_(CREAM, .9))
    # gable
    gable = skia.Path(); gable.moveTo(-38, 0); gable.lineTo(0, -30); gable.lineTo(38, 0); gable.close()
    c.drawPath(gable, P_(WOOD))
    roof = skia.Path(); roof.moveTo(-50, 6); roof.lineTo(0, -34); roof.lineTo(50, 6)
    c.drawPath(roof, S_(CREAM, .97, 6.5))
    # face
    c.drawCircle(0, 30, 21, P_(CREAM)); c.drawCircle(0, 30, 21, S_(BRASS, 1, 2.2))
    for k in range(12):
        a = k * math.pi / 6
        c.drawLine(17 * math.sin(a), 30 - 17 * math.cos(a), 19.5 * math.sin(a), 30 - 19.5 * math.cos(a), S_(DARK, .7, 1.4))
    am = g["hand"] + 2 * math.pi * t / LOOP; ah = g["hand"] * .5 + 2 * math.pi * t / LOOP / 12 * 0
    c.drawLine(0, 30, 15 * math.sin(am), 30 - 15 * math.cos(am), S_(DARK, .95, 2.2))
    c.drawLine(0, 30, 10 * math.sin(ah), 30 - 10 * math.cos(ah), S_(DARK, .95, 3))
    c.drawCircle(0, 30, 2.2, P_(BRASS))
    # door (in the gable): opening + two leaves that swing outward
    o = min(1.0, p * 1.6)
    dx0, dx1, dy0, dy1 = -9, 9, -22, -4
    c.drawRect(skia.Rect(dx0, dy0, dx1, dy1), P_(DARK))
    e = 9 * math.cos(math.pi * o)
    for hx, sg in ((dx0, 1), (dx1, -1)):
        xa, xb = hx, hx + sg * e
        lo, hi = min(xa, xb), max(xa, xb)
        if hi - lo > .4:
            c.drawRect(skia.Rect(lo, dy0, hi, dy1), P_(AMBER if o < .5 else (.75, .45, .2)))
    c.drawRect(skia.Rect(dx0 - 1.5, dy0 - 1.5, dx1 + 1.5, dy1 + 1.5), S_(CREAM, .8, 1.5))
    if p > .02: draw_bird(c, p)
    c.restore()

def draw_wall(c):
    for r in range(NR):
        y = Y0 + r * PY - 46
        for i in range(NC):
            yy = y + (ZZ if i % 2 else -ZZ)
            c.drawCircle(colx[i], yy + 6, 2.2, P_(BRASS, .5))

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
            text(c, LET[i], colx[i], 508, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), colx[0] - 80, Y0 + r * PY + 40, F_AX, AMBER, .9)
        for g in G: draw_clock(c, g, t)
        yb = 1552
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 38, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 36, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def whistle(f0):
    out = []
    for k, (fr, d) in enumerate(((f0 * 1.19, .085), (f0, .11))):
        t = np.arange(int(d * SR)) / SR
        env = np.minimum(1, t * 300) * np.exp(-t * 18)
        out.append(np.sin(2 * np.pi * fr * t + .3 * np.sin(2 * np.pi * 6 * t)) * env)
        out.append(np.zeros(int(.03 * SR)))
    return np.concatenate(out) * .8
def tocktock(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.11 * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * .5 * t) * .7 + np.sin(2 * np.pi * f0 * 1.31 * t) * .3) * np.exp(-t * 45) \
        + bp(rg.standard_normal(len(t)), 600, 2200) * np.exp(-t * 160) * .3
    s *= np.minimum(1, t * 5000)
    return np.concatenate([s, np.zeros(int(.02 * SR)), s * .8])
def tick(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.03 * SR)) / SR
    return bp(rg.standard_normal(len(t)), 2500, 7000) * np.exp(-t * 400)

def audio(path):
    m = Mix(LOOP + 4)
    pops = []
    for k, g in enumerate(G):
        n = int(round(LOOP / g["P"]))
        for j in range(-1, n + 1):
            for s in popstarts(g):
                ts = g["ph"] + j * g["P"] + s
                if 0 <= ts < LOOP: pops.append((k, ts))
        npp = int(round(LOOP / g["PP"]))
        for j in range(2 * npp + 2):   # tick at each extreme of the swing
            ts = (0.25 - g["pph"]) * g["PP"] + j * g["PP"] / 2
            ts %= LOOP
            m.add(tick(k * 31 + j), ts, .035, g["cx"])
    pt = np.array([p[1] for p in pops])
    for k, ts in pops:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(pt - ts) < .15).sum()))
        f0 = note(7 + (6 - g["r"]) + (g["i"] % 3), 261.63)
        if g["odd"]: m.add(tocktock(f0, k * 11 + int(ts * 97)), ts, .5, g["cx"])
        else: m.add(whistle(f0), ts, .30 / dens, g["cx"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_cuckoos.mp4"))
