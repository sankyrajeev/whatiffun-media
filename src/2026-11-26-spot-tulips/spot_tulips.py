"""SPOT IT v3 (15:00, 2026-11-26): WHICH TULIP / OPENS INSIDE OUT?
49 identical coral tulips planted on seven ROLLING HILL rows (7 columns A-G x 7 rows; every row's soil line is a
gentle wave, alternate rows out of phase; letters on top, numbers on the left).
Every tulip blooms non-stop: its two side petals swing open into a wide cup, hold, and close again, on a
2.0 / 2.4 / 3.0 s cycle from a random phase; a soft breeze sways the stems. ONE tulip (ODD) opens INSIDE OUT:
its petals fold right back past flat and hang DOWN round the stem like a skirt (pale undersides showing).
Rule type: inside out (shape inverts), the No. 49 umbrellas / No. 70 plungers rule on a new object.
Sound: a soft papery 'pop' + rustle per bloom (pitch by row, panned by x, density-normalised); the odd one's
bloom is a hollow lower 'thwup' played reversed (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/tulips"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFG"
NC, NR = 7, 7
PX = float(os.environ.get("PX", "124"))
RP = float(os.environ.get("RP", "138"))
Y0 = float(os.environ.get("Y0", "640"))      # soil line of row 1
STEM = float(os.environ.get("STEM", "54"))
PL = float(os.environ.get("PL", "56"))       # side petal length
PW = float(os.environ.get("PW", "36"))       # side petal width
OPEN = float(os.environ.get("OPEN", "52"))   # normal open angle (deg)
INV = float(os.environ.get("INV", "150"))    # inside-out angle (deg)
HILL = float(os.environ.get("HILL", "10"))
PCT = int(os.environ.get("PCT", "22"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "2611")))
colx = [W / 2 + 22 + (i - (NC - 1) / 2) * PX for i in range(NC)]
def soil(x, r): return Y0 + r * RP + HILL * math.sin(2 * math.pi * (x - 100) / 560 + r * math.pi)

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([2.0, 2.4, 3.0]))
        G.append(dict(lab=lab, odd=lab == ODD, cx=colx[i], y=soil(colx[i], r), r=r, i=i, P=P,
                      ph=rng.uniform(0, P), lean=rng.uniform(-4, 4), sw=rng.uniform(0, 6.28)))
for g in G:
    if g["odd"]: g["P"] = 2.4
print(len(G), "tulips")
assert sum(g["odd"] for g in G) == 1

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                            StrokeJoin=skia.Paint.kRound_Join)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH TULIP", "OPENS INSIDE OUT?"
def fit(s, size, maxw=830):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BRASS = (.86, .66, .34)
PET, PET_HI, PET_LO = (.88, .33, .24), (.98, .55, .40), (.62, .17, .12)
UNDER = (.97, .60, .47)                       # pale underside of a petal
STEMC, LEAF = (.46, .54, .30), (.38, .47, .25)
SOIL, SOIL_HI = (.24, .14, .08), (.36, .22, .12)

def ease(x): return .5 - .5 * math.cos(math.pi * min(1, max(0, x)))
def bloom(g, t):
    """0 = closed bud, 1 = fully open; open 30%, hold 25%, close 30%, rest 15% of the cycle"""
    u = ((t - g["ph"]) % g["P"]) / g["P"]
    if u < .30: return ease(u / .30)
    if u < .55: return 1.0
    if u < .85: return 1 - ease((u - .55) / .30)
    return 0.0

def petal_path(L, Wd):
    """a petal pointing up from its pivot at (0,0)"""
    p = skia.Path()
    p.moveTo(0, 0)
    p.cubicTo(-Wd * .75, -L * .25, -Wd * .55, -L * .85, 0, -L)
    p.cubicTo(Wd * .55, -L * .85, Wd * .75, -L * .25, 0, 0)
    p.close(); return p
PETAL = petal_path(PL, PW)
CENTER = petal_path(PL * .96, PW * 1.15)

def petal_paint(a_deg, side):
    """front (outer) face while < 90 deg, pale underside once folded past flat"""
    if a_deg < 95:
        sh = skia.GradientShader.MakeLinear([(0, 0), (0, -PL)], [c4(PET_LO).toColor(), c4(PET).toColor(), c4(PET_HI).toColor()], [0, .5, 1])
    else:
        sh = skia.GradientShader.MakeLinear([(0, 0), (0, -PL)], [c4(PET).toColor(), c4(UNDER).toColor()], [0, .7])
    return skia.Paint(AntiAlias=True, Shader=sh)

def draw_tulip(c, g, t):
    b = bloom(g, t)
    sway = 3.5 * math.sin(2 * math.pi * t / 6.0 - g["cx"] / 260 + g["r"] * .6) + g["lean"] * .5
    c.save(); c.translate(g["cx"], g["y"])
    # leaves
    for s in (-1, 1):
        lp = skia.Path(); lp.moveTo(0, 0)
        lp.quadTo(s * 30, -14, s * 34, -40); lp.quadTo(s * 14, -18, 0, 0); lp.close()
        c.drawPath(lp, P_(LEAF))
    # stem (curved by sway)
    c.rotate(sway * .5)
    hx, hy = math.sin(math.radians(sway)) * STEM * .4, -STEM
    sp = skia.Path(); sp.moveTo(0, 0); sp.quadTo(0, -STEM * .5, hx, hy)
    c.drawPath(sp, S_(STEMC, 1, 7))
    c.translate(hx, hy); c.rotate(sway)
    A = OPEN * b if not g["odd"] else INV * b
    # stamens visible once open
    if b > .25:
        al = min(1, (b - .25) / .4)
        for k in (-1, 0, 1):
            c.drawLine(0, 0, k * 8, -20, S_(BRASS, al, 2.4))
            c.drawCircle(k * 8, -21, 4, P_((.30, .20, .12), al))
    # center (back) petal: shrinks a little as the cup opens; folds down too for the odd one
    if g["odd"] and A > 60:
        cs = max(.15, 1 - (A - 60) / 75)
    else:
        cs = 1 - .38 * b
    if not (g["odd"] and A > 70):
        c.save(); c.scale(1, cs); c.drawPath(CENTER, P_(PET_LO if (b > .3 and not g["odd"]) else PET)); c.restore()
    if g["odd"] and A > 95:
        # pale underside of the back petal flipping down behind the stem
        c.save(); c.rotate(180); c.scale(.9, (A - 95) / 60 * .8); c.drawPath(CENTER, petal_paint(A, 0)); c.restore()
    for s in (-1, 1):
        c.save(); c.translate(s * 4, 0); c.rotate(s * A)
        c.drawPath(PETAL, petal_paint(A, s))
        c.drawPath(PETAL, S_(PET_LO, .5, 1.2))
        c.restore()
    c.restore()

def draw_hills(c):
    for r in range(NR):
        top = skia.Path(); xs = np.linspace(colx[0] - 95, colx[-1] + 75, 60)
        top.moveTo(xs[0], soil(xs[0], r))
        for x in xs[1:]: top.lineTo(x, soil(x, r))
        band = skia.Path(top)
        for x in xs[::-1]: band.lineTo(x, soil(x, r) + 20)
        band.close()
        y0 = Y0 + r * RP - HILL
        c.drawPath(band, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, y0), (0, y0 + 2 * HILL + 20)], [c4(SOIL_HI).toColor(), c4(SOIL).toColor()])))
        c.drawPath(top, S_(BRASS, .28, 2))

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
        draw_hills(c)
        for r in range(NR):
            text(c, str(r + 1), colx[0] - 82, Y0 + r * RP - 38, F_AX, AMBER, .9)
        for g in G: draw_tulip(c, g, t)
        yb = 1554
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1644, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def pop(seed, f0, odd=False):
    """soft papery bloom: a short airy rustle rising into a muted pluck"""
    rg = np.random.default_rng(seed)
    n = int(.42 * SR); t = np.arange(n) / SR
    x = t / .42
    rustle = bp(rg.standard_normal(n), 900, 5000) * np.sin(np.pi * x) ** 2 * .35
    pt = np.arange(int(.25 * SR)) / SR
    if odd:
        pl = (np.sin(2 * np.pi * f0 * .5 * pt) * .9 + bp(rg.standard_normal(len(pt)), 150, 700) * .7) * np.exp(-pt * 18)
    else:
        pl = (np.sin(2 * np.pi * f0 * pt) * .7 + np.sin(2 * np.pi * f0 * 2 * pt) * .15) * np.exp(-pt * 30)
    s = rustle.copy(); k = int(.24 * SR)
    s[k:k + len(pl)] += pl[:n - k]
    return s[::-1] if odd else s

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        n = int(round(LOOP / g["P"]))
        for j in range(-1, n + 2):
            ts = g["ph"] + j * g["P"]
            if 0 <= ts < LOOP: ev.append((k, ts))
    et = np.array([e[1] for e in ev])
    for k, ts in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .3).sum())) * 1.1
        f0 = note(3 + (6 - g["r"]) + (g["i"] % 2), 196.0)
        s = pop(k * 131 + int(ts * 977), f0, g["odd"])
        if g["odd"]: m.add(s, ts, .55 / max(1, dens * .6), g["cx"])
        else: m.add(s, ts, .30 / dens, g["cx"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_tulips.mp4"))
