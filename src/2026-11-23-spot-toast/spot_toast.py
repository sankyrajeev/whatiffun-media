"""SPOT IT v3 (10:00, 2026-11-23): WHICH TOAST / DOES A FLIP? 48 identical cream pop-up toasters on WAVY
SHELVES (8 columns A-H x 6 rows = 48; each row's shelf is the same gentle wave;
column letters on top, row numbers on the left). Every toaster runs its cycle non-stop (1.5 / 2.0 / 2.4 s,
random phase): the lever goes down, the slot glows, the toast POPS ~80 px into the air with a little wobble
and drops back in. ONE toaster flings its toast into a full somersault every time.
Rule type: flips vs doesn't (the 11-22 review's "toasters that flip, not pop").
Sound: spring clack + soft ding per pop, bread thup on landing, lever click (pentatonic by row, panned by x,
density-normalised); the odd one's pop is a lower hollow tock with an airy whoosh. 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/toast"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 6
PX = float(os.environ.get("PX", "104"))
PY = float(os.environ.get("PY", "160"))
Y0 = float(os.environ.get("Y0", "622"))      # top of row-1 toaster bodies
WAVE = float(os.environ.get("WAVE", "14"))
TW, TH = 86.0, 52.0                          # toaster body
BW, BH = 48.0, 50.0                          # toast slice
HMAX = float(os.environ.get("HMAX", "76"))
AIR = float(os.environ.get("AIR", ".80"))
PCT = int(os.environ.get("PCT", "25"))
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "23")))

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        cx = W / 2 + (i - (NC - 1) / 2) * PX
        y = Y0 + r * PY + WAVE * math.sin(2 * math.pi * i / 6 + r * .0)
        P = 2.0 if odd else float(rng.choice([1.5, 2.0, 2.4], p=[.3, .4, .3]))
        G.append(dict(lab=lab, odd=odd, cx=cx, y=y, r=r, i=i, P=P,
                      ph=float(os.environ.get("OPH", ".62")) if odd else rng.uniform(0, 1),
                      sgn=1 if rng.random() < .5 else -1))
print(len(G), "toasters")
assert sum(g["odd"] for g in G) == 1

def ease(u): u = min(1, max(0, u)); return .5 - .5 * math.cos(math.pi * u)
SINK = 17.0
def state(g, t):
    """returns (lift d [px, + = up], tilt deg, lever 0 up..1 down, heat 0..1, airborne)"""
    P = g["P"]; tc = ((t / P + g["ph"]) % 1.0) * P
    push0, push1 = AIR + .30, AIR + .48
    if tc < AIR:
        s = tc / AIR
        d = -SINK * (1 - s) + HMAX * 4 * s * (1 - s)
        if g["odd"]:
            tilt = -360 * ease((s - .04) / .88)
        else:
            tilt = g["sgn"] * 7 * math.sin(2 * math.pi * s)
        lev = max(0, 1 - tc / .07)
        return d, tilt, lev, 0.0, True
    tl = tc - AIR
    if tl < .22:                                    # landing bounce
        d = 7 * math.sin(math.pi * tl / .22) * (1 - tl / .22)
        return d, 0.0, 0.0, 0.0, False
    if tc < push0: return 0.0, 0.0, 0.0, 0.0, False
    if tc < push1:                                  # lever pushed down, toast sinks
        k = ease((tc - push0) / (push1 - push0))
        return -SINK * k, 0.0, k, 0.0, False
    heat = min(1, (tc - push1) / max(.2, P - push1))
    return -SINK, 0.0, 1.0, heat, False

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
CRM = (.96, .91, .81)

def toast_path():
    p = skia.Path()
    w, h = BW, BH
    x0, x1, y0, y1 = -w / 2, w / 2, -h / 2, h / 2
    p.moveTo(x0 + 3, y1); p.lineTo(x0 + 2, y0 + 16)
    p.cubicTo(x0 - 6, y0 + 2, x0 + 10, y0 - 7, 0, y0 - 1)
    p.cubicTo(x1 - 10, y0 - 7, x1 + 6, y0 + 2, x1 - 2, y0 + 16)
    p.lineTo(x1 - 3, y1); p.close()
    return p
TOAST = toast_path()
def toast_inner():
    m = skia.Matrix(); m.setScale(.78, .8); p = skia.Path(); TOAST.transform(m, p); return p
TOAST_IN = toast_inner()
CRUST = (.58, .34, .14); CRUMB = (.95, .79, .50)

def draw_toast(c, x, y, tilt, odd):
    c.save(); c.translate(x, y); c.rotate(tilt)
    c.drawPath(TOAST, P_(CRUST, 1))
    c.save(); c.translate(0, 2)
    c.drawPath(TOAST_IN, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (0, 0), 30, [c4((.98, .84, .56)).toColor(), c4((.86, .62, .32)).toColor()])))
    c.restore()
    c.restore()

def body_paint(y):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y), (0, y + TH)],
        [c4((.97, .93, .85)).toColor(), c4((.86, .80, .70)).toColor(), c4((.62, .55, .46)).toColor()], [0, .55, 1]))

def draw_toaster(c, g, t):
    cx, y = g["cx"], g["y"]
    d, tilt, lev, heat, air = state(g, t)
    x0, x1 = cx - TW / 2, cx + TW / 2
    # shadow + slot back lip
    c.drawOval(skia.Rect(x0 - 2, y + TH - 5, x1 + 2, y + TH + 7), P_((0, 0, 0), .45))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 30, y - 5, cx + 30, y + 5), 4, 4), P_((.12, .09, .07), 1))
    if heat > 0:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 28, y - 3, cx + 28, y + 3), 3, 3), P_((1, .45, .15), .55 * heat))
    # toast (behind the body front); motion ghosts while flying
    ty = y + 8 - d
    if air:
        for k, dt in enumerate((.05, .025)):
            d2, t2, *_ = state(g, t - dt)
            if g["odd"] or abs(d2 - d) > 4:
                c.saveLayerAlpha(None, int(255 * (.16 + .12 * k)))
                draw_toast(c, cx, y + 8 - d2, t2, g["odd"]); c.restore()
    draw_toast(c, cx, ty, tilt, g["odd"])
    # body front
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y, x1, y + TH), 15, 15), body_paint(y))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y + 30, x1, y + 37), 2, 2), P_(AMBER, .9))
    c.drawLine(x0 + 12, y + 6, x1 - 12, y + 6, P_((1, 1, 1), .55, StrokeWidth=2.5, StrokeCap=skia.Paint.kRound_Cap))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 30, y - 1, cx + 30, y + 4), 3, 3), P_((.30, .25, .2), .9))
    # lever on the right side
    ly = y + 11 + lev * 20
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x1 - 3, ly - 4, x1 + 9, ly + 4), 3, 3), P_((.30, .20, .10), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x1 + 2, ly - 5, x1 + 12, ly + 5), 4, 4), P_(AMBER, 1))
    # glow on the body when hot
    if heat > 0:
        c.drawCircle(cx, y + 18, 4.5, P_((1, .5, .2), .35 + .6 * heat))

def shelf(c, r):
    p = skia.Path()
    for k in range(0, 81):
        x = 130 + k * (840 / 80)
        ii = (x - (W / 2 - (NC - 1) / 2 * PX)) / PX
        y = Y0 + r * PY + WAVE * math.sin(2 * math.pi * ii / 6 + r * .0) + TH + 2
        p.moveTo(x, y) if k == 0 else p.lineTo(x, y)
    c.drawPath(p, P_(AMBER, .28, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH TOAST", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "DOES A FLIP?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], W / 2 + (i - (NC - 1) / 2) * PX, 506, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 112, Y0 + r * PY + 38, F_AX, AMBER, .9)
            shelf(c, r)
        for g in G: draw_toaster(c, g, t)
        yb = 1540
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def clack(f0, seed, odd=False):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.5 * SR)) / SR
    if odd:   # lower hollow tock + airy whoosh as it flips
        s = np.sin(2 * np.pi * f0 * .5 * t) * np.exp(-t * 26) * .9
        nz = sosfilt(butter(2, [400, 2500], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t)))
        s += nz * np.sin(np.pi * np.clip(t / .45, 0, 1)) ** 2 * .35
    else:     # spring clack + a soft little ding
        s = glass_click(f0 * 2, 90, .5, .5) * .5
        s = s + np.sin(2 * np.pi * f0 * 4 * t) * np.exp(-t * 9) * .22
    return s * np.minimum(1, t * 4000)
def thup(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.12 * SR)) / SR
    nz = sosfilt(butter(2, [150, 900], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t)))
    return nz * np.exp(-t * 45) * .7
def click(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.05 * SR)) / SR
    return sosfilt(butter(2, [1500, 6000], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t))) * np.exp(-t * 160) * .4

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            t0 = (c_ - g["ph"]) * g["P"]
            ev += [(k, "pop", t0), (k, "land", t0 + AIR), (k, "lev", t0 + AIR + .30)]
    pops = np.array([e[2] % LOOP for e in ev if e[1] == "pop"])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        tt = ts % LOOP
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(pops - tt) < .2).sum()))
        f0 = note(3 + (7 - g["r"]) // 2 + (g["i"] % 3), 130.81)
        if kind == "pop":
            m.add(clack(f0, k * 7 + int(tt * 90), g["odd"]), tt, (.5 if not g["odd"] else 1.1) / dens, g["cx"])
        elif kind == "land":
            m.add(thup(k * 13 + int(tt * 50)), tt, .45 / dens, g["cx"])
        else:
            m.add(click(k * 17 + int(tt * 30)), tt, .25 / dens, g["cx"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_toast.mp4"))
