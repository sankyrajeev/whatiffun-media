"""SPOT IT v3 (13:00, 2026-11-22): WHICH GATE / OPENS DOWNWARD? 56 identical amber/cream striped BOOM GATES
(toll barriers) in a TOLL PLAZA: 8 columns x 7 rows split into two MIRRORED banks either side of a central road
(A-D posts on the left with arms pointing right, E-H posts on the right with arms pointing left).
Every gate opens on a 2.4 s or 3.0 s cycle from a random phase: its lamp blinks, the arm swings UP to ~80 deg,
holds, comes back down and settles with a small bounce. ONE gate opens DOWNWARD: its arm dips into the road
(and its counterweight rises) every 2.4 s. Rule type: up/down (goes down instead of up).
Sound: a soft relay click + short motor whirr on every opening (pentatonic by row, panned by x, density-
normalised) and a soft thunk when the arm lands; the odd gate's whirr is lower with a hollow clunk. 12 s loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/gates"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 7
CH = float(os.environ.get("CH", "140"))
GY0 = float(os.environ.get("GY0", "662"))    # ground y of row 1
POST = 56.0
ARM = float(os.environ.get("ARM", "70"))
UP, DN = 80.0, float(os.environ.get("DN", "56"))
PCT = int(os.environ.get("PCT", "35"))
ODD = (os.environ.get("OL", "B"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "13")))
XS = [140, 240, 340, 440, 640, 740, 840, 940]

T_UP, T_HOLD, T_DN = .42, .62, .48
G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = 2.4 if (odd or rng.random() < .6) else 3.0
        G.append(dict(lab=lab, odd=odd, x=XS[i], gy=GY0 + r * CH, dir=1 if i < 4 else -1, r=r, i=i,
                      P=P, ph=(float(os.environ.get("OPH", ".5")) if odd else rng.uniform(0, 1)) + 0 * rng.uniform(0, 1), w=rng.uniform(0, 6.28)))
print(len(G), "gates")
assert sum(g["odd"] for g in G) == 1

def cyc(g, t): return ((t / g["P"] + g["ph"]) % 1.0) * g["P"]
def lift(g, t):
    """0..1 open amount, with an overshoot on opening and a bounce on landing"""
    u = cyc(g, t)
    if u < T_UP:
        k = u / T_UP; return 1 - (1 - k) ** 3 * math.cos(k * 2.2) if k < 1 else 1
    if u < T_UP + T_HOLD:
        v = u - T_UP; return 1 + .05 * math.exp(-v * 7) * math.sin(v * 22)
    if u < T_UP + T_HOLD + T_DN:
        k = (u - T_UP - T_HOLD) / T_DN; return 1 - k * k
    v = u - T_UP - T_HOLD - T_DN
    return .10 * math.exp(-v * 7) * abs(math.sin(v * 15))
def angle(g, t):
    a = lift(g, t)
    return -(DN * a) if g["odd"] else UP * a      # degrees above horizontal
def events(g):
    out = []
    for k in range(-3, int(LOOP / g["P"]) + 4):
        t0 = (k - g["ph"]) * g["P"]
        out.append(("open", t0)); out.append(("land", t0 + T_UP + T_HOLD + T_DN))
    return [(e, tt % LOOP) for e, tt in out if -1 <= tt < LOOP + 1]
EV = [events(g) for g in G]

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_LAB = font(TF_SB, 17); F_PCT = font(TF_BOLD, 38); F_ROW = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
ORANGE = (.93, .50, .17); CRM = (.96, .91, .81)

def draw_gate(c, g, t):
    x, gy, d = g["x"], g["gy"], g["dir"]
    py = gy - POST + 8                  # pivot
    ang = angle(g, t)
    moving = 0 < cyc(g, t) < T_UP + T_HOLD + T_DN
    # ground shadow + base
    c.drawOval(skia.Rect(x - 20, gy - 3, x + 20, gy + 5), P_((0, 0, 0), .5, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    # arm
    c.save(); c.translate(x, py); c.scale(d, 1); c.rotate(-ang)
    # shadow
    c.save(); c.translate(2, 6)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-20, -8, ARM, 8), 8, 8), P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    c.restore()
    # counterweight
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-24, -9, -6, 9), 3, 3), P_((.42, .30, .15), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-24, -9, -6, 9), 3, 3), P_((.9, .72, .42), .8, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2))
    arm = skia.RRect.MakeRectXY(skia.Rect(0, -7.5, ARM, 7.5), 7.5, 7.5)
    c.save(); c.clipRRect(arm, doAntiAlias=True)
    n = 6; sw = ARM / n
    for k in range(n):
        c.drawRect(skia.Rect(k * sw, -7.5, (k + 1) * sw + .5, 7.5), P_(ORANGE if k % 2 == 0 else CRM, 1))
    c.drawRect(skia.Rect(0, -7.5, ARM, -3.5), P_((1, .98, .92), .35))
    c.drawRect(skia.Rect(0, 3.5, ARM, 7.5), P_((.15, .06, .02), .25))
    c.restore()
    c.restore()
    # post body (cream cabinet with brass edge), label engraved on it
    body = skia.RRect.MakeRectXY(skia.Rect(x - 17, gy - POST, x + 17, gy), 4, 4)
    sh = skia.GradientShader.MakeLinear([(x - 17, 0), (x + 17, 0)],
        [c4((.62, .55, .45)).toColor(), c4((.97, .93, .84)).toColor(), c4((.70, .62, .50)).toColor()], [0, .45, 1])
    c.drawRRect(body, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawRRect(body, P_((.85, .66, .36), .9, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 15, gy - 24, x + 15, gy - 4), 3, 3), P_((.30, .21, .11), 1))
    text(c, f"{g['lab'][0]}{g['lab'][1]}", x, gy - 8, F_LAB, (1, .88, .62), .95)
    # lamp on top
    lamp = .25 + .75 * (moving and (int(t * 4) % 2 == 0))
    if lamp > .5:
        c.drawCircle(x, gy - POST - 3, 13, P_(AMBER, .35, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
    c.drawCircle(x, gy - POST - 3, 5, P_(tuple(v * (.45 + .55 * lamp) for v in (1, .72, .25)), 1))
    # brass hub
    c.drawCircle(x, py, 6, P_((.95, .78, .45), 1)); c.drawCircle(x, py, 2.4, P_((.35, .24, .1), 1))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH GATE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "OPENS DOWNWARD?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], XS[i], 512, F_ROW, AMBER, .9)
        # central road: a faint tarmac band with a dashed centre line
        c.drawRect(skia.Rect(506, 528, 574, GY0 + (NR - 1) * CH + 8), P_((.5, .42, .32), .10))
        for yy in np.arange(540, GY0 + (NR - 1) * CH + 10, 34):
            c.drawLine(540, yy, 540, yy + 16, P_(CREAM, .13, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))
        for r in range(NR):
            yb = GY0 + r * CH
            c.drawLine(112, yb + 1, 968, yb + 1, P_(AMBER, .15, StrokeWidth=1.5))
        for g in G: draw_gate(c, g, t)
        yb = 1560
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1650, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def whirr(f0, seed, odd=False):
    dur = .5
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    click = rg.standard_normal(len(t)) * np.exp(-t * 500) * .5
    ph = 2 * np.pi * np.cumsum(f0 * (1 + .25 * np.sin(np.pi * np.minimum(t / T_UP, 1))) ) / SR
    motor = (np.sin(ph) + .3 * np.sin(2 * ph)) * np.sin(np.pi * np.minimum(t / (T_UP + .05), 1)) ** 2 * .35
    body = np.sin(2 * np.pi * f0 * 2 * t) * np.exp(-t * 30) * .6
    if odd:
        body += .7 * np.sin(2 * np.pi * f0 * 1.5 * t) * np.exp(-t * 12)
    return click + motor + body
def thunk(f0, seed, odd=False):
    t = np.arange(int(.3 * SR)) / SR
    rg = np.random.default_rng(seed)
    nz = sosfilt(butter(2, [200, 1800], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t))) * np.exp(-t * 60)
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * (25 if not odd else 12))
    return nz * .5 + body * .8

def audio(path):
    m = Mix(LOOP + 4)
    allt = np.array([tt for k in range(len(G)) for e, tt in EV[k] if e == "open"])
    for k, g in enumerate(G):
        for e, tt in EV[k]:
            if not (0 <= tt < LOOP): continue
            dens = math.sqrt(max(1, (np.abs(allt - tt) < .2).sum()))
            f0 = note(5 + (6 - g["r"]) // 2 + (g["i"] % 3), 65.41)
            if e == "open":
                if g["odd"]: m.add(whirr(73.4, k * 100 + int(tt * 50), True), tt, .5 / dens * 2.2, g["x"])
                else: m.add(whirr(f0, k * 100 + int(tt * 50)), tt, .5 / dens, g["x"])
            else:
                m.add(thunk(110 if not g["odd"] else 70, k * 77 + int(tt * 40), g["odd"]), tt, .35 / dens * (1.8 if g["odd"] else 1), g["x"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_gates.mp4"))
