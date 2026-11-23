"""SPOT IT v3 (15:00, 2026-11-23): WHICH BIN / OPENS TWICE? 54 identical cream pedal bins with amber flip
lids on SLOPED ROWS (9 columns A-I x 6 rows; every row runs gently downhill to the right like bins along a
sloping street; column letters on top, row numbers on the left). Every bin's pedal is stepped on non-stop
(2.4 / 3.0 / 4.0 s, random phase): the lid FLIPS up ~108 deg, hangs open, then SLAMS shut with a
little bounce. ONE bin flips open, slams... and flips straight open again every time (it opens twice).
Rule type: twice vs once (the No. 41 hammers rule on a new everyday object).
Sound: pedal click + lid clonk per slam (pentatonic by row, panned by x, density-normalised); the odd one's
slams are a lower hollow tock. 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/bins"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGHI"
NC, NR = 9, 6
PX = float(os.environ.get("PX", "92"))
PY = float(os.environ.get("PY", "157"))
Y0 = float(os.environ.get("Y0", "590"))      # top rim of row-1 bins (column A)
SLOPE = float(os.environ.get("SLOPE", "5"))  # px down per column
BW, BB, BH = 66.0, 54.0, 70.0                # body top width, bottom width, height
LW = 74.0                                    # lid width
SC = float(os.environ.get("SC", "1.17"))
OPEN = float(os.environ.get("OPEN", "106"))
PCT = int(os.environ.get("PCT", "12"))
ODD = (os.environ.get("OL", "G"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))

X0 = W / 2 - (NC - 1) / 2 * PX + 2
G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        cx = X0 + i * PX
        y = Y0 + r * PY + SLOPE * i
        P = 2.4 if odd else float(rng.choice([2.4, 3.0, 4.0], p=[.35, .35, .3]))
        G.append(dict(lab=lab, odd=odd, cx=cx, y=y, r=r, i=i, P=P,
                      ph=float(os.environ.get("OPH", ".37")) if odd else rng.uniform(0, 1)))
print(len(G), "bins")
assert sum(g["odd"] for g in G) == 1

def eo(u): u = min(1, max(0, u)); return 1 - (1 - u) ** 3
# one flap: 0..D seconds -> angle (deg)
RISE, HOLD, FALL = .16, .26, .11
D1 = RISE + HOLD + FALL                       # slam moment
def flap(u, hold=HOLD):
    if u < 0: return 0.0
    if u < RISE:
        k = u / RISE
        return OPEN * eo(k) + 10 * math.sin(math.pi * k)       # snappy with overshoot
    if u < RISE + hold:
        k = (u - RISE) / hold
        return OPEN + 4 * math.sin(2 * math.pi * k) * (1 - k)
    if u < RISE + hold + FALL:
        k = (u - RISE - hold) / FALL
        return OPEN * (1 - k * k)                               # accelerates into the slam
    v = u - RISE - hold - FALL
    if v < .2: return 9 * math.sin(math.pi * v / .2) * (1 - v / .2)   # bounce
    return 0.0
GAP2 = .22                                    # odd: re-opens right after the slam
HOLD2 = .26
def slams(g):
    """slam times within one cycle (relative to cycle start)"""
    if g["odd"]:
        return [D1, D1 + GAP2 + RISE + HOLD2 + FALL]
    return [D1]
def state(g, t):
    P = g["P"]; tc = ((t / P + g["ph"]) % 1.0) * P
    a = flap(tc)
    if g["odd"]:
        t2 = tc - (D1 + GAP2)
        if t2 >= 0:
            a = flap(t2, HOLD2)
    ped = 1.0 if tc < D1 - .05 else 0.0
    if g["odd"] and D1 + GAP2 <= tc < D1 + GAP2 + RISE + HOLD2 - .05: ped = 1.0
    return a, ped

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

def body_path():
    p = skia.Path()
    p.moveTo(-BW / 2, 0); p.lineTo(BW / 2, 0)
    p.lineTo(BB / 2, BH - 6); p.quadTo(BB / 2, BH, BB / 2 - 6, BH)
    p.lineTo(-BB / 2 + 6, BH); p.quadTo(-BB / 2, BH, -BB / 2, BH - 6)
    p.close(); return p
BODY = body_path()
def lid_path():
    # lid in hinge coordinates: hinge at (0,0) on the right, lid extends to the left
    p = skia.Path()
    p.moveTo(2, 1); p.lineTo(-LW + 2, 1)
    p.cubicTo(-LW + 2, -10, -LW + 12, -17, -LW / 2, -17)
    p.cubicTo(-12, -17, 2, -10, 2, 1); p.close(); return p
LID = lid_path()

def body_paint(y):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-BW / 2, 0), (BW / 2, 0)],
        [c4((.70, .64, .55)).toColor(), c4((.97, .93, .85)).toColor(), c4((.88, .82, .72)).toColor(),
         c4((.58, .52, .44)).toColor()], [0, .35, .7, 1]))
LIDPAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, -17), (0, 2)],
    [c4((1.0, .80, .45)).toColor(), c4(AMBER).toColor(), c4((.62, .40, .16)).toColor()], [0, .5, 1]))

def draw_bin(c, g, t):
    cx, y = g["cx"], g["y"]
    a, ped = state(g, t)
    c.save(); c.translate(cx, y); c.scale(SC, SC)
    c.drawOval(skia.Rect(-BB / 2 - 6, BH - 5, BB / 2 + 10, BH + 7), P_((0, 0, 0), .45))
    # mouth (dark opening) visible when the lid lifts
    if a > 2:
        k = min(1, a / 40)
        c.drawOval(skia.Rect(-BW / 2 + 2, -5 * k, BW / 2 - 2, 5 * k + 1), P_((.07, .05, .04), 1))
    # lid behind? draw body first, lid on top
    c.drawPath(BODY, body_paint(y))
    c.drawRect(skia.Rect(-BW / 2 + 3, 10, BW / 2 - 3, 15), P_(AMBER, .85))
    c.drawLine(-BW / 2 + 9, 22, -BB / 2 + 7, BH - 10, P_((1, 1, 1), .35, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))
    # pedal (front-left foot), dips when stepped on
    py_ = BH - 10 + 6 * ped
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-BB / 2 - 16, py_ - 4, -BB / 2 + 4, py_ + 4), 3, 3), P_((.30, .22, .14), 1))
    # lid hinged at the back-right of the rim
    c.save(); c.translate(BW / 2 + 3, 0); c.rotate(a)
    if a > 25:   # motion ghosts on the way up/down
        pass
    c.drawPath(LID, LIDPAINT)
    c.drawLine(-LW + 10, -11, -16, -14, P_((1, .95, .8), .55, StrokeWidth=2.5, StrokeCap=skia.Paint.kRound_Cap))
    c.restore()
    c.drawCircle(BW / 2 + 3, 0, 4, P_((.35, .25, .15), 1))
    c.restore()

def ground(c, r):
    y0 = Y0 + r * PY + BH * SC + 2
    c.drawLine(X0 - 50, y0 - SLOPE * 50 / PX, X0 + (NC - 1) * PX + 50, y0 + SLOPE * (NC - 1 + 50 / PX),
               P_(AMBER, .25, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH BIN", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "OPENS TWICE?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], X0 + i * PX, 516, F_AX, AMBER, .9)
        c.save(); c.clipRect(skia.Rect(100, 480, 980, 1500))
        for r in range(NR): ground(c, r)
        c.restore()
        for r in range(NR):
            text(c, str(r + 1), 112, Y0 + r * PY + 52, F_AX, AMBER, .9)
        for g in G: draw_bin(c, g, t)
        yb = 1548
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
def clonk(f0, seed, odd=False):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.45 * SR)) / SR
    nz = sosfilt(butter(2, [200, 1800], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t)))
    if odd:   # lower hollow tock
        s = np.sin(2 * np.pi * f0 * .5 * t) * np.exp(-t * 22) * .9 + nz * np.exp(-t * 70) * .4
    else:     # plastic lid clonk + a soft tonal ring
        s = nz * np.exp(-t * 60) * .55 + np.sin(2 * np.pi * f0 * 2 * t) * np.exp(-t * 14) * .3
    return s * np.minimum(1, t * 4000)
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
            ev.append((k, "ped", t0))
            for s in slams(g): ev.append((k, "slam", t0 + s))
            if g["odd"]: ev.append((k, "ped", t0 + D1 + GAP2))
    sl = np.array([e[2] % LOOP for e in ev if e[1] == "slam"])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        tt = ts
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(sl - tt) < .2).sum()))
        f0 = note(3 + (7 - g["r"]) // 2 + (g["i"] % 3), 130.81)
        if kind == "slam":
            m.add(clonk(f0, k * 7 + int(tt * 90), g["odd"]), tt, (.6 if not g["odd"] else 1.1) / dens, g["cx"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_bins.mp4"))
