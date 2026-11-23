"""SPOT IT v3 (18:00, 2026-11-23): WHICH WASHER / NEVER STOPS? 56 identical cream front-loading washing
machines in a LAUNDROMAT WALL (8 columns A-H x 7 rows, stacked in four double towers with aisles between;
column letters on top, row numbers on the left). Every machine runs a short spin non-stop on a 3.0 / 4.0 s
cycle from a random phase: the drum whips the amber laundry round the glass door, the whole machine shakes
and its lamp glows, then it winds down and STOPS DEAD, the laundry slumping to the bottom. ONE machine
never stops: it spins the whole time.
Rule type: never stops (the No. 43 fans rule on a new everyday object).
Sound: a soft dial click at each spin start, a hushed drum whoosh while spinning, a padded thump + clothes
flop when each stops (pentatonic by row, panned by x, density-normalised); the odd one has no thumps but a
little hollow coin-rattle tock every 2 s. 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/washers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 7
MW, MH = 92.0, 120.0          # machine size
PIN = 96.0                    # pitch inside a tower pair
AISLE = 30.0                  # extra gap between pairs
PY = float(os.environ.get("PY", "128"))
Y0 = float(os.environ.get("Y0", "560"))      # top of row-1 machines
PCT = int(os.environ.get("PCT", "8"))
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))

colx = []
for i in range(NC):
    colx.append(i * PIN + (i // 2) * AISLE)
span = colx[-1]
XOFF = float(os.environ.get("XOFF", "12"))
colx = [W / 2 + XOFF - span / 2 + x for x in colx]

# spin profile within a cycle: up, full, down, then dead still
UP, FULL, DOWN = .35, .75, .55
SPIN = UP + FULL + DOWN
REVS = 2.0                     # drum revolutions per cycle (integer -> seamless + rests at the bottom)
def _raw_w(u):
    if u < 0: return 0.0
    if u < UP: return (u / UP) ** 1.5
    if u < UP + FULL: return 1.0
    if u < SPIN: k = (u - UP - FULL) / DOWN; return (1 - k) ** 2
    return 0.0
_us = np.linspace(0, SPIN, 4001)
_ws = np.array([_raw_w(u) for u in _us])
_cum = np.concatenate([[0], np.cumsum((_ws[1:] + _ws[:-1]) / 2 * np.diff(_us))])
WMAX = REVS / _cum[-1]         # rev/s at full speed
_cum *= WMAX
def drum(u):
    """(angle in revs, speed 0..1) at time u into the cycle"""
    if u >= SPIN: return REVS, 0.0
    if u <= 0: return 0.0, 0.0
    return float(np.interp(u, _us, _cum)), _raw_w(u)
ODD_W = 24.0 / LOOP            # odd: 2 rev/s constant-ish -> 24 revs per loop
print("full speed rev/s", round(WMAX, 2), "odd", ODD_W)

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = float(rng.choice([3.0, 4.0], p=[.55, .45]))
        G.append(dict(lab=lab, odd=odd, cx=colx[i], y=Y0 + r * PY, r=r, i=i, P=P, ph=rng.uniform(0, 1),
                      sh=rng.uniform(0, 6.283)))
print(len(G), "machines")
assert sum(g["odd"] for g in G) == 1

def state(g, t):
    if g["odd"]:
        # never stops; tiny speed wobble so it doesn't look mechanical (integrates to whole revs per loop)
        a = ODD_W * t + .06 * math.sin(2 * math.pi * t / 3.0) + g["sh"] / 6.283
        return a, .9 + .1 * math.cos(2 * math.pi * t / 3.0)
    P = g["P"]; tc = ((t / P + g["ph"]) % 1.0) * P
    a, s = drum(tc)
    return a, s

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BODYPAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-MW / 2, 0), (MW / 2, 0)],
    [c4((.72, .66, .57)).toColor(), c4((.97, .93, .85)).toColor(), c4((.90, .84, .74)).toColor(),
     c4((.60, .54, .46)).toColor()], [0, .35, .7, 1]))
DCY, DR = 74.0, 37.0           # door centre y, door outer radius
GR = 29.5                      # glass radius
RIMPAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, DCY - DR), (0, DCY + DR)],
    [c4((.86, .80, .70)).toColor(), c4((.55, .48, .40)).toColor()], [0, 1]))
AMB_D = (.62, .40, .16)

def laundry_path():
    # a lumpy amber towel bundle, in drum coordinates, sitting against the wall at angle 0 (pointing +x)
    p = skia.Path()
    p.moveTo(GR - 2, -12); p.cubicTo(GR - 12, -15, GR - 19, -6, GR - 17, 2)
    p.cubicTo(GR - 16, 9, GR - 8, 15, GR - 2, 12); p.close()
    return p
LAUNDRY = laundry_path()
def sock_path():
    p = skia.Path()
    p.moveTo(GR - 2, -6); p.cubicTo(GR - 9, -8, GR - 12, -2, GR - 11, 3)
    p.cubicTo(GR - 9, 7, GR - 4, 7, GR - 2, 5); p.close(); return p
SOCK = sock_path()

def draw_machine(c, g, t):
    a, s = state(g, t)
    ang = a * 360.0
    # shake: whole machine buzzes while spinning (big enough to catch the eye)
    jx = 3.4 * s * math.sin(2 * math.pi * a * 1.0 + g["sh"]) + 1.2 * s * math.sin(t * 2 * math.pi * 117 / 12 + g["sh"])
    jy = 1.4 * s * math.sin(t * 2 * math.pi * 90 / 12 + g["sh"] * 2)
    rot = 2.2 * s * math.sin(2 * math.pi * a + g["sh"])
    c.save(); c.translate(g["cx"] + jx, g["y"] + jy); c.rotate(rot)
    r = skia.Rect(-MW / 2, 0, MW / 2, MH)
    c.drawRRect(skia.RRect.MakeRectXY(r, 9, 9), BODYPAINT)
    c.drawRRect(skia.RRect.MakeRectXY(r, 9, 9), P_((.35, .28, .2), .6, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5))
    # control panel
    c.drawLine(-MW / 2 + 4, 24, MW / 2 - 4, 24, P_((.45, .38, .3), .55, StrokeWidth=1.5))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-MW / 2 + 9, 8, -MW / 2 + 33, 17), 2, 2), P_((.42, .34, .26), .7))
    c.drawCircle(MW / 2 - 16, 12.5, 7, P_((.70, .62, .52), 1))
    c.drawLine(MW / 2 - 16, 12.5, MW / 2 - 16 + 6 * math.cos(ang / 40), 12.5 - 6 * abs(math.sin(ang / 40)) - 0,
               P_((.3, .22, .15), .9, StrokeWidth=2, StrokeCap=skia.Paint.kRound_Cap))
    lamp = min(1, s * 1.6)
    if lamp > .02:
        c.drawCircle(MW / 2 - 32, 12.5, 7, P_(AMBER, .45 * lamp, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    c.drawCircle(MW / 2 - 32, 12.5, 3.3, P_((1, .78, .4) if lamp > .02 else (.36, .3, .24), .4 + .6 * lamp))
    # door
    c.drawCircle(0, DCY, DR, RIMPAINT)
    c.drawCircle(0, DCY, GR + 2, P_((.30, .25, .2), 1))
    c.drawCircle(0, DCY, GR, P_((.06, .05, .05), 1))
    # laundry: flung to the wall at the drum angle while spinning, slumps to the bottom when slow
    c.save(); c.clipPath(skia.Path().addCircle(0, DCY, GR - .5), doAntiAlias=True)
    c.translate(0, DCY)
    # spinning -> rides the wall at drum angle; slow -> drops towards the bottom (90 deg in skia coords)
    base = 90.0 + ang
    for k, (pth, col, off) in enumerate([(LAUNDRY, AMBER, 0.0), (SOCK, (.95, .9, .8), 42.0), (LAUNDRY, (.80, .55, .25), -40.0)]):
        th = base + off
        # motion smear while fast
        if s > .35:
            for j in range(1, 4):
                c.save(); c.rotate(th - j * 14 * s); c.drawPath(pth, P_(col, .16 * s)); c.restore()
        c.save(); c.rotate(th); c.drawPath(pth, P_(col, 1.0)); c.restore()
    # drum holes ring rotating (visible texture)
    for k in range(10):
        th = math.radians(ang + k * 36)
        c.drawCircle((GR - 4) * math.cos(th), (GR - 4) * math.sin(th), 1.3, P_((.4, .36, .32), .5))
    c.restore()
    # glass highlight
    c.drawArc(skia.Rect(-GR + 4, DCY - GR + 4, GR - 4, DCY + GR - 4), 200, 60, False,
              P_((1, 1, 1), .35, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(DR - 6, DCY - 7, DR + 1, DCY + 7), 2, 2), P_((.5, .43, .35), 1))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH WASHER", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER STOPS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], colx[i], 530, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 118, Y0 + r * PY + 70, F_AX, AMBER, .9)
        # floor line under each tower
        yb_ = Y0 + NR * PY - (PY - MH) + 4
        for p in range(4):
            x0, x1 = colx[2 * p] - MW / 2 - 6, colx[2 * p + 1] + MW / 2 + 6
            c.drawLine(x0, yb_, x1, yb_, P_(AMBER, .3, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))
        for g in G: draw_machine(c, g, t)
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
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def thump(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.5 * SR)) / SR
    nz = bp(rg.standard_normal(len(t)), 120, 900)
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 18) * .7 + nz * np.exp(-t * 40) * .45
    flop = np.zeros_like(t); k = int(.07 * SR)
    flop[k:] = bp(rg.standard_normal(len(t) - k), 300, 2500)[: len(t) - k] * np.exp(-np.arange(len(t) - k) / SR * 30) * .25
    return (s + flop) * np.minimum(1, t * 3000)
def click(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.05 * SR)) / SR
    return bp(rg.standard_normal(len(t)), 1800, 7000) * np.exp(-t * 170) * .4
def tock(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.35 * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 26) + np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 40) * .35
    return (s + bp(rg.standard_normal(len(t)), 2000, 6000) * np.exp(-t * 90) * .2) * np.minimum(1, t * 4000)

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        if g["odd"]:
            for j in range(-1, 8): ev.append((k, "tock", 2.0 * j + .3))
            continue
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            t0 = (c_ - g["ph"]) * g["P"]
            ev.append((k, "click", t0))
            ev.append((k, "thump", t0 + SPIN - .05))
    th = np.array([e[2] % LOOP for e in ev if e[1] == "thump"])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(th - ts) < .2).sum()))
        f0 = note(2 + (6 - g["r"]) // 2 + (g["i"] % 3), 110.0)
        if kind == "thump":
            m.add(thump(f0, k * 7 + int(ts * 90)), ts, .55 / dens, g["cx"])
        elif kind == "click":
            m.add(click(k * 17 + int(ts * 30)), ts, .2 / dens, g["cx"])
        else:
            m.add(tock(note(6, 261.63), k * 3 + int(ts * 10)), ts, .42, g["cx"])
    # drum whoosh bed: filtered noise following how many machines spin, panned by their x
    n = int(LOOP * SR)
    tt = np.arange(n) / SR
    rg = np.random.default_rng(5)
    nzL = bp(rg.standard_normal(n), 180, 1400); nzR = bp(rg.standard_normal(n), 180, 1400)
    ts = np.arange(0, LOOP, 1 / 120)
    envL = np.zeros_like(ts); envR = np.zeros_like(ts)
    for g in G:
        sp = np.array([state(g, x)[1] for x in ts])
        pan = (g["cx"] - 100) / 880
        envL += sp * (1 - pan); envR += sp * pan
    envL = np.interp(tt, ts, envL) / 30; envR = np.interp(tt, ts, envR) / 30
    hum = np.sin(2 * np.pi * 55 * tt) * .25
    m.L[:n] += .10 * (nzL + hum) * envL; m.R[:n] += .10 * (nzR + hum) * envR
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_washers.mp4"))
