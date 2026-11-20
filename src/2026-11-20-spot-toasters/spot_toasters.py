"""SPOT IT v3 (13:00, 2026-11-20): 56 retro toasters on a kitchen counter seen in PERSPECTIVE; one pops just ONE slice.
Rule type: COUNT (new: every toaster pops two slices, the odd one pops only one; its second slice never comes up).
Family: toasters (new). Arrangement: PERSPECTIVE ROWS (7 columns A-G x 8 rows; back rows smaller and narrower,
front rows bigger, like rows of a counter receding; letters on top, numbers beside each row, label on each toaster).
Every toaster runs a 3 s cycle from a random phase (4 per 12 s loop): lever down, slices sink, slots glow amber,
then POP: both slices fly up ~1.5 toaster heights (each its own height) and drop back to rest half out, hold, repeat.
Sound: a soft lever click, a springy pop + small bell 'ding' (pentatonic by row, panned by x, density-normalised);
the odd toaster's pop is a single hollow clack without the bright ding."""
import sys, os, math
import numpy as np, skia
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/toasters"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 7, 8
LET = "ABCDEFG"
P = 3.0
NT = int(round(LOOP / P))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))

YROW = [575 + 108 * r + 4.5 * r * r / 2 for r in range(NR)]      # rows a touch further apart toward the front
def sc(r): return .86 + .14 * r / (NR - 1)
def pitch(r): return 104 + 22 * r / (NR - 1)
def pos(i, r): return 540 + (i - (NC - 1) / 2) * pitch(r), YROW[r]

BW, BH = 104, 64            # body at scale 1 (front face)
TOPH = 14                   # top face depth
SLW, SLH = 40, 58           # slice size
RISE = 38                   # slice top above the slot when resting popped
SINK = -6                   # slice top below slot when down (hidden)
POPH = 78                  # extra flight height

T = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        x, y = pos(i, r)
        T.append(dict(lab=lab, odd=lab == ODD, x=x, y=y, r=r, s=sc(r), ph=rng.uniform(0, 1),
                      hj=[(rng.uniform(.75, 1.15), rng.uniform(.75, 1.15), rng.uniform(-.04, .04)) for _ in range(NT)]))

# cycle (s): 0-.35 sink, .35-1.55 toasting, 1.55 POP, flight to ~2.15, hold to 3.0
TSINK, TPOP, TFL = .32, 1.1, .62
def cyc(tg, t):
    v = t / P + tg["ph"]; n = math.floor(v); return (v - n) * P, n % NT

def slice_h(tg, t, k):
    """height of slice k's top above the slot line (scale-1 px); also returns glow, lever"""
    w, j = cyc(tg, t)
    if tg["odd"] and k == 1:                    # the second slice never comes up
        return SINK, 1.0, None
    if w < TSINK:
        u = ss(w / TSINK); return RISE + (SINK - RISE) * u, u, 1 - u
    if w < TPOP:
        return SINK, 1.0, 0.0
    a = w - TPOP - tg["hj"][j][2] * k
    a = max(0, a)
    if a < TFL:
        hmax = POPH * tg["hj"][j][k]
        # ballistic: rise from SINK to RISE+hmax and fall to RISE, then a small bounce
        T1 = TFL * .45
        if a < T1:
            u = a / T1; return SINK + (RISE + hmax - SINK) * (1 - (1 - u) ** 2), max(0, 1 - a * 6), min(1, a * 8)
        u = (a - T1) / (TFL - T1)
        return RISE + hmax * (1 - u * u), 0.0, 1.0
    b = a - TFL
    return RISE + 7 * math.exp(-b * 9) * abs(math.sin(b * 22)), 0.0, 1.0

def lever(tg, t):
    w, j = cyc(tg, t)
    if w < TSINK: return ss(w / TSINK)
    if w < TPOP: return 1.0
    return max(0, 1 - (w - TPOP) * 12)

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 34)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
F_MARK = font(TF_SERIF_I, 34)
CR = (.95, .9, .8)
AM = (.9, .62, .26)
BREAD = (.93, .74, .42)
CRUST = (.6, .36, .16)
CHROME = (.72, .66, .58)

def rrect(c, l, t, r, b, rad, paint): c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(l, t, r, b), rad, rad), paint)

def toast(c, cx, top, s, toasted):
    w, h = SLW * s, SLH * s
    col = tuple(BREAD[q] * (1 - .25 * toasted) + CRUST[q] * .25 * toasted for q in range(3))
    p = skia.Path()
    l, r = cx - w / 2, cx + w / 2
    p.moveTo(l, top + h); p.lineTo(l, top + 9 * s)
    p.cubicTo(l - 4 * s, top - 2 * s, cx - 2 * s, top - 7 * s, cx, top + 1 * s)
    p.cubicTo(cx + 2 * s, top - 7 * s, r + 4 * s, top - 2 * s, r, top + 9 * s)
    p.lineTo(r, top + h); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=c4(col)))
    c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2 * s, Color4f=c4(CRUST)))
    c.drawLine(l + 6 * s, top + 12 * s, l + 6 * s, top + h, skia.Paint(AntiAlias=True, Color4f=c4((1, 1, 1), .18), StrokeWidth=3 * s))

def toaster(c, tg, t):
    x, y, s = tg["x"], tg["y"], tg["s"]
    bw, bh, th = BW * s, BH * s, TOPH * s
    top = y - bh / 2                       # top edge of front face = slot line
    # shadow
    c.drawOval(skia.Rect(x - bw * .6, y + bh / 2 - 6 * s, x + bw * .6, y + bh / 2 + 12 * s),
               skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    # top face
    rrect(c, x - bw / 2 + 3 * s, top - th, x + bw / 2 - 3 * s, top + 8 * s, 12 * s, skia.Paint(AntiAlias=True, Color4f=c4((.82, .77, .68))))
    hs = [slice_h(tg, t, k) for k in (0, 1)]
    for k in (0, 1):
        sx = x + (k - .5) * 42 * s
        g = hs[k][1]
        rrect(c, sx - 20 * s, top - th * .72, sx + 20 * s, top - th * .22, 3 * s, skia.Paint(AntiAlias=True, Color4f=c4((.16, .1, .06))))
        if g > 0:
            rrect(c, sx - 19 * s, top - th * .7, sx + 19 * s, top - th * .24, 3 * s,
                  skia.Paint(AntiAlias=True, Color4f=c4((1, .55, .2), .75 * g)))
            c.drawCircle(sx, top - th * .5, 22 * s, skia.Paint(AntiAlias=True, Color4f=c4((1, .55, .2), .25 * g),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9)))
    # slices (behind the front face, clipped at the slot so they come out of it)
    c.save(); c.clipRect(skia.Rect(0, 0, W, top - th * .47))
    for k in (0, 1):
        sx = x + (k - .5) * 42 * s
        hh = hs[k][0]
        toast(c, sx, top - th * .47 - hh * s, s, 1.0 if not (tg["odd"] and k == 1) else .3)
    c.restore()
    # front face
    g = skia.GradientShader.MakeLinear([(x, top), (x, top + bh)], [c4((.98, .94, .85)).toColor(), c4((.82, .75, .64)).toColor()], [0, 1])
    rrect(c, x - bw / 2, top - 2 * s, x + bw / 2, top + bh, 16 * s, skia.Paint(AntiAlias=True, Shader=g))
    hl = skia.GradientShader.MakeLinear([(x - bw / 2, 0), (x + bw / 2, 0)], [c4((1, 1, 1), 0).toColor(), c4((1, 1, 1), .35).toColor(),
                                         c4((1, 1, 1), 0).toColor()], [.1, .3, .5])
    rrect(c, x - bw / 2, top - 2 * s, x + bw / 2, top + bh, 16 * s, skia.Paint(AntiAlias=True, Shader=hl))
    # chrome band + label
    c.drawRect(skia.Rect(x - bw / 2 + 2 * s, top + bh * .55, x + bw / 2 - 2 * s, top + bh * .55 + 5 * s), skia.Paint(AntiAlias=True, Color4f=c4(AM, .9)))
    text(c, f"{tg['lab'][0]}{tg['lab'][1]}", x - 8 * s, top + bh * .43, font(TF_SB, 19 * s), (.45, .3, .18), .95)
    # lever slot + lever on the right
    lx = x + bw / 2 - 16 * s
    c.drawLine(lx, top + 9 * s, lx, top + bh * .48, skia.Paint(AntiAlias=True, Color4f=c4((.35, .25, .17), .8), StrokeWidth=3 * s, StrokeCap=skia.Paint.kRound_Cap))
    ly = top + 9 * s + (bh * .39) * lever(tg, t)
    rrect(c, lx - 9 * s, ly - 4 * s, lx + 9 * s, ly + 4 * s, 3 * s, skia.Paint(AntiAlias=True, Color4f=c4(AM)))
    # feet
    for d in (-1, 1):
        rrect(c, x + d * bw * .33 - 7 * s, top + bh - 1, x + d * bw * .33 + 7 * s, top + bh + 5 * s, 2 * s, skia.Paint(AntiAlias=True, Color4f=c4(CHROME)))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH TOASTER", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "POPS JUST ONE?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for i in range(NC):
            text(c, LET[i], pos(i, 0)[0], 432, F_LAB, AMBER, .9)
        for r in range(NR):
            x0, y = pos(0, r)
            text(c, str(r + 1), x0 - 70 * sc(r) - 12, y + 12, F_LAB, AMBER, .9)
        for r in range(NR):   # faint counter edges
            yy = YROW[r] + BH * sc(r) / 2 + 6
            c.drawLine(pos(0, r)[0] - 58, yy, pos(NC - 1, r)[0] + 58, yy, skia.Paint(AntiAlias=True, Color4f=c4((.5, .38, .26), .25), StrokeWidth=1.5))
        for tg in T:
            toaster(c, tg, t)
        yb = 1556
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 48, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 46, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1644, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def env(t, a, d): return np.minimum(1, t * a) * np.exp(-t * d)
def click(seed, dur=.08):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = sosfilt(butter(2, [900, 3500], btype="band", fs=SR, output="sos"), n)
    return n * env(t, 4000, 90) * 1.2
def pop(f0, seed, dur=.9):
    t = np.arange(int(dur * SR)) / SR
    spring = np.sin(2 * np.pi * (300 + 500 * np.exp(-t * 25)) * t) * env(t, 3000, 30) * .35
    knock = np.sin(2 * np.pi * 95 * t) * env(t, 3000, 28) * .6
    ding = (np.sin(2 * np.pi * f0 * t) + .35 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 4)) * env(t, 800, 4.5) * .45
    return (spring + knock + ding + click(seed, dur) * .4)
def clack(seed, dur=.5):
    t = np.arange(int(dur * SR)) / SR
    hollow = np.sin(2 * np.pi * 210 * t) * env(t, 3000, 14) * .7 + np.sin(2 * np.pi * 523 * t) * env(t, 3000, 40) * .3
    return hollow + click(seed, dur) * .6

def audio(path):
    m = Mix(LOOP + 1.5)
    ev = []
    for k, tg in enumerate(T):
        for n in range(-2, NT + 3):
            t0 = (n - tg["ph"]) * P
            for tt, kind in ((t0 + .02, "lev"), (t0 + TPOP, "pop")):
                if 0 <= tt < LOOP: ev.append((tt, k, kind))
    pt = np.array([e[0] for e in ev if e[2] == "pop"])
    for tt, k, kind in ev:
        tg = T[k]
        if kind == "lev": m.add(click(k * 17 + int(tt * 10)), tt, .05, tg["x"]); continue
        dens = max(1, (np.abs(pt - tt) < .08).sum())
        if tg["odd"]: m.add(clack(k + int(tt * 100)), tt, .55, tg["x"]); continue
        m.add(pop(note(NR - 1 - tg["r"] + 5, 261.63), k + int(tt * 100)), tt, .42 / math.sqrt(dens), tg["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    for ch, seed in ((m.L, 3), (m.R, 4)):
        x = np.random.default_rng(seed).standard_normal(n)
        sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
        sp *= np.exp(-((fr - 300) / 400) ** 2)
        bed = np.fft.irfft(sp, n); bed /= np.abs(bed).max(); ch += bed * .03
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_toasters.mp4"))
