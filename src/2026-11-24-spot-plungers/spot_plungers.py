"""SPOT IT v3 (13:00, 2026-11-24): WHICH PLUNGER / TURNS INSIDE OUT?
52 identical sink plungers (amber rubber cups, cream wooden handles) standing on drains on a ROUND MAT
(PORTHOLE arrangement: an 8 x 8 grid with the corners cut off -> rows of 4, 6, 8, 8, 8, 8, 6, 4; column
letters A-H on top, each row's number at its left end). Every plunger works non-stop on a 1.5 / 2.0 / 2.4 s
cycle from a random phase: it pushes down (cup squashes flat), the cup stretches tall under suction, then
POPS off the drain, hops up and lands with a little bounce.
ONE plunger (D6) turns INSIDE OUT every time it pops: its cup snaps into an upside-down bowl, it lands on
the bowl, then the cup pops back the right way. Rule type: shape inverts (the No. 49 umbrellas rule on a
new everyday object).
Sound: a soft rubber squish on the push, a suction "thwop" on the pop (pentatonic by row, panned by x,
density-normalised); the odd one adds a bright snap when it inverts and again when it pops back.
12 s seamless loop (all periods divide 12)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/plungers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC = NR = 8
PX = float(os.environ.get("PX", "106"))
PY = float(os.environ.get("PY", "110"))
Y0 = float(os.environ.get("Y0", "664"))      # floor y of row 1
PCT = int(os.environ.get("PCT", "24"))
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))
colx = [W / 2 + (i - (NC - 1) / 2) * PX for i in range(NC)]
ROWSPAN = {0: (2, 5), 1: (1, 6), 6: (1, 6), 7: (2, 5)}

W0, H0, HL = 70.0, 32.0, 56.0     # cup width, cup height, handle length
# cycle timing (s)
T_PUSH, T_HOLD, T_YANK, T_POP, T_PEAK, T_LAND = 0.0, 0.20, 0.36, 0.52, 0.68, 0.84
LIFT = 34.0

G = []
for r in range(NR):
    a, b = ROWSPAN.get(r, (0, 7))
    for i in range(a, b + 1):
        lab = (LET[i], r + 1)
        G.append(dict(lab=lab, odd=lab == ODD, cx=colx[i], y=Y0 + r * PY, r=r, i=i,
                      P=float(rng.choice([1.5, 2.0, 2.4], p=[.3, .4, .3])), ph=rng.uniform(0, 1),
                      tilt=rng.choice([-1, 1]) * rng.uniform(.5, 1.0)))
for g in G:
    if g["odd"]: g["P"] = 2.0
print(len(G), "plungers")
assert sum(g["odd"] for g in G) == 1

def cyc(g, t): return ((t / g["P"] + g["ph"]) % 1.0) * g["P"]

def state(g, u):
    """returns lift (px above rest), cup w, cup h, s (1 normal, -1 inside out), tilt deg, base offset"""
    w, h, lift, s = W0, H0, 0.0, 1.0
    if u < T_HOLD:                       # push down: squash
        k = ss(u / T_HOLD); h = H0 * (1 - .48 * k); w = W0 * (1 + .26 * k)
    elif u < T_YANK:                     # hold squashed, tiny wobble
        h = H0 * .52; w = W0 * 1.26
    elif u < T_POP:                      # yank: suction stretch, rim stuck
        k = ss((u - T_YANK) / (T_POP - T_YANK)); h = H0 * (.52 + .98 * k); w = W0 * (1.26 - .42 * k)
    elif u < T_LAND:                     # popped: flight
        k = (u - T_POP) / (T_LAND - T_POP)
        lift = LIFT * 4 * k * (1 - k) + 10 * (1 - k)     # starts slightly lifted (stretched handle)
        e = math.exp(-(u - T_POP) * 9)
        h = H0 * (1 + .5 * e * math.cos((u - T_POP) * 40)); w = W0 * (1 - .18 * e * math.cos((u - T_POP) * 40))
    elif u < T_LAND + .18:               # landing bounce
        k = (u - T_LAND) / .18
        lift = 7 * math.sin(math.pi * k)
        e = math.exp(-(u - T_LAND) * 14)
        h = H0 * (1 - .22 * e * math.cos((u - T_LAND) * 45)); w = W0 * (1 + .12 * e * math.cos((u - T_LAND) * 45))
    tilt = 0.0
    if T_POP <= u < T_LAND + .18:
        tilt = g["tilt"] * 7 * math.sin(math.pi * min(1, (u - T_POP) / (T_LAND + .18 - T_POP)))
    base = 0.0
    if g["odd"]:
        TI0, TI1 = T_POP + .05, T_POP + .11          # snaps inside out just after the pop
        TB0 = T_LAND + .42; TB1 = TB0 + .07           # pops back on the floor
        if TI0 <= u < TB1:
            if u < TI1: s = 1 - 2 * ss((u - TI0) / (TI1 - TI0))
            elif u < TB0: s = -1
            else: s = -1 + 2 * ss((u - TB0) / (TB1 - TB0))
        # where the stick sits: inside out it stands on the bowl's bottom (attachment on the floor)
        if TI0 <= u < TB0:
            base = H0 * ss((u - TI0) / (T_LAND - TI0))
            if u >= T_LAND: base = H0
        elif TB0 <= u < TB1 + .22:
            k = (u - TB0) / (TB1 + .22 - TB0)
            base = H0 * (1 - ss(min(1, (u - TB0) / (TB1 - TB0))))
            lift += 16 * math.sin(math.pi * k)          # the pop-back makes it hop
            h = H0 * (1 + .25 * math.exp(-(u - TB1) * 10) * math.cos((u - TB0) * 40)) if u > TB1 else h
        if T_LAND <= u < TB0:
            h = H0; w = W0 * (1 + .06 * math.sin((u - T_LAND) * 30) * math.exp(-(u - T_LAND) * 8))
            tilt = g["tilt"] * 4 * math.sin((u - T_LAND) * 14) * math.exp(-(u - T_LAND) * 5)
    return lift, w, h, s, tilt, base

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_Q2 = font(TF_BOLD, float(os.environ.get("Q2", "80")))
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

RUB_HI, RUB, RUB_LO, RUB_IN = (.98, .62, .34), (.82, .34, .14), (.44, .15, .06), (.26, .08, .04)
WOOD = [(.62, .50, .34), (.97, .91, .78), (.86, .76, .58), (.55, .43, .28)]

def cup_path(w, h, s, yr):
    """dome from rim (y = yr) to apex; s=1 apex above rim, s=-1 apex below rim"""
    p = skia.Path()
    cy = yr - s * h / .75
    p.moveTo(-w / 2, yr)
    p.cubicTo(-w / 2 + w * .04, cy, w / 2 - w * .04, cy, w / 2, yr)
    p.close()
    return p

def draw_floor(c):
    cx, cy = W / 2, Y0 + 3.5 * PY - 40
    c.drawOval(skia.Rect(cx - 470, cy - 470, cx + 470, cy + 470), P_((.15, .12, .10), .7))
    c.drawOval(skia.Rect(cx - 470, cy - 470, cx + 470, cy + 470),
               P_(AMBER, .16, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
    c.drawOval(skia.Rect(cx - 452, cy - 452, cx + 452, cy + 452),
               P_(AMBER, .07, Style=skia.Paint.kStroke_Style, StrokeWidth=2))
    for g in G:
        x, y = g["cx"], g["y"]
        c.drawOval(skia.Rect(x - 40, y - 9, x + 40, y + 9), P_((.07, .06, .05), .9))
        c.drawOval(skia.Rect(x - 40, y - 9, x + 40, y + 9),
                   P_((.55, .42, .25), .55, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5))
        c.drawOval(skia.Rect(x - 20, y - 4, x + 20, y + 4), P_((.20, .17, .14), .9))

def draw_plunger(c, g, t):
    u = cyc(g, t)
    lift, w, h, s, tilt, base = state(g, u)
    c.save(); c.translate(g["cx"], g["y"])
    # soft contact shadow that shrinks with height
    sh = max(0, 1 - lift / 50)
    c.drawOval(skia.Rect(-w * .55, -5, w * .55, 5), P_((0, 0, 0), .35 * sh))
    c.translate(0, -lift); c.rotate(tilt)
    # rim y: normal -> rim on the floor (0); inside out -> attachment on the floor, rim above
    b = base / H0 if g["odd"] else 0.0
    att = -h * (1 - b)            # where the stick meets the cup
    yr = att + s * h              # rim (below the attachment when normal, above when inside out)
    cupsh = skia.GradientShader.MakeLinear([(-w / 2, 0), (w / 2, 0)],
        [c4(RUB_LO).toColor(), c4(RUB_HI).toColor(), c4(RUB).toColor(), c4(RUB_LO).toColor()], [0, .32, .62, 1])
    cup = cup_path(w, abs(h * s) + 1e-3, 1 if s >= 0 else -1, yr)
    # handle (drawn before an inside-out cup so the bowl wraps it, after a normal cup)
    top = att - HL
    def handle():
        hp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-6, 0), (6, 0)],
             [c4(x).toColor() for x in WOOD], [0, .35, .7, 1]))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-6, top, 6, att + 2), 6, 6), hp)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-8, top - 6, 8, top + 6), 6, 6), P_((.78, .58, .30)))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-5, top - 4, 1, top), 2, 2), P_((1, .92, .7), .7))
    if s < 0:
        # inside out: the inner face (dark) shows as a bowl opening upward
        c.drawPath(cup, skia.Paint(AntiAlias=True, Shader=cupsh))
        c.drawOval(skia.Rect(-w / 2, yr - w * .13, w / 2, yr + w * .13), P_(RUB_IN))
        c.drawOval(skia.Rect(-w / 2, yr - w * .13, w / 2, yr + w * .13),
                   P_(RUB_HI, .9, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        # the stick disappears into the bowl's opening
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-6, top, 6, yr + 3), 6, 6), skia.Paint(AntiAlias=True,
                    Shader=skia.GradientShader.MakeLinear([(-6, 0), (6, 0)], [c4(x).toColor() for x in WOOD], [0, .35, .7, 1])))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-8, top - 6, 8, top + 6), 6, 6), P_((.78, .58, .30)))
    else:
        c.drawPath(cup, skia.Paint(AntiAlias=True, Shader=cupsh))
        # rim lip
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2 - 1, yr - 6, w / 2 + 1, yr + 1), 3, 3), P_(RUB_LO))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2 + 2, yr - 6, w / 2 - 2, yr - 3), 2, 2), P_(RUB, .8))
        # glossy highlight on the dome
        hp = skia.Path(); hp.moveTo(-w * .30, yr - h * .25); hp.quadTo(-w * .26, att + h * .2, -w * .05, att + h * .18)
        c.drawPath(hp, P_((1, .85, .65), .55, Style=skia.Paint.kStroke_Style, StrokeWidth=3.5, StrokeCap=skia.Paint.kRound_Cap))
        handle()
        c.drawOval(skia.Rect(-9, att - 4, 9, att + 3), P_(RUB_LO))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH PLUNGER", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "TURNS INSIDE OUT?", W / 2, 354, F_Q2, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], colx[i], 532, F_AX, AMBER, .9)
        draw_floor(c)
        for r in range(NR):
            a, _ = ROWSPAN.get(r, (0, 7))
            text(c, str(r + 1), colx[a] - 66, Y0 + r * PY - 18, F_AX, AMBER, .9)
        for g in G: draw_plunger(c, g, t)
        yb = 1548
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 46, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 44, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def squish(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.16 * SR)) / SR
    n = bp(rg.standard_normal(len(t)), 300, 1800) * np.exp(-t * 28) * np.minimum(1, t * 120)
    return n * .35 + np.sin(2 * np.pi * 95 * t) * np.exp(-t * 30) * .25
def thwop(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.20 * SR)) / SR
    f = f0 * (1.7 * np.exp(-t * 35) + .55)               # falling pitch: suction pop
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 24) + bp(rg.standard_normal(len(t)), 800, 4000) * np.exp(-t * 260) * .35
    return s * np.minimum(1, t * 4000)
def snap(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.09 * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 55) + bp(rg.standard_normal(len(t)), 3000, 9000) * np.exp(-t * 300) * .5
    return s * np.minimum(1, t * 8000)

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            t0 = (c_ - g["ph"]) * g["P"]
            ev.append((k, "squish", t0 + .03)); ev.append((k, "thwop", t0 + T_POP)); ev.append((k, "tap", t0 + T_LAND))
            if g["odd"]:
                ev.append((k, "snap", t0 + T_POP + .08)); ev.append((k, "snap2", t0 + T_LAND + .45))
    th = np.array([e[2] for e in ev if e[1] == "thwop" and 0 <= e[2] < LOOP])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(th - ts) < .1).sum()))
        f0 = note(3 + (7 - g["r"]) + (g["i"] % 2), 196.0)
        if kind == "thwop":
            m.add(thwop(f0, k * 11 + int(ts * 97)), ts, .42 / dens, g["cx"])
        elif kind == "squish":
            m.add(squish(k * 7 + int(ts * 53)), ts, .20 / dens, g["cx"])
        elif kind == "tap":
            m.add(squish(k * 5 + int(ts * 41))[:int(.05 * SR)], ts, .10 / dens, g["cx"])
        else:
            m.add(snap(f0 * 4 if kind == "snap" else f0 * 3, k + int(ts * 13)), ts, .30, g["cx"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_plungers.mp4"))
