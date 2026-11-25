"""SPOT IT v3 (10:00, 2026-11-25): WHICH WHEEL / TURNS THE OTHER WAY?
56 identical Ferris wheels (cream rims, brass spokes, amber gondolas, little warm bulbs) on 8 lit BOARDWALK
ROWS (7 columns A-G x 8 rows; each row stands on its own boardwalk rail with bulbs; letters on top, numbers on
the left). Every wheel turns CLOCKWISE in big eased pulses (a quarter turn per pulse, on a 1.5 / 2.0 / 3.0 s
cycle from a random phase) and its gondolas swing with real pendulum lag when it starts and stops.
ONE wheel (E6) turns ANTI-CLOCKWISE. Rule type: wrong way (rotation direction).
Sound: a soft ratchet tick each time a gondola passes the top (pentatonic by row, panned by x, density-
normalised) and a padded clunk when the wheel stops; E6's ticks are a hollow wood tock instead (audio clue).
12 s seamless loop (all periods divide 12; a quarter turn maps the 8-gondola wheel onto itself; the gondola
swing is integrated over three loops so the last one is periodic)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/wheels"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEF"
NC, NR = 6, 8
PX = float(os.environ.get("PX", "148"))
PY = float(os.environ.get("PY", "124"))
Y0 = float(os.environ.get("Y0", "580"))      # hub y of row 1
PCT = int(os.environ.get("PCT", "22"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "25")))
colx = [W / 2 + 24 + (i - (NC - 1) / 2) * PX for i in range(NC)]

R = float(os.environ.get("RR", "48"))   # rim radius
NG = 8                                   # gondolas (one of them red, so the direction reads at a glance)
LG = 10.0                                # gondola hanger length
LEG = 70.0                               # hub -> boardwalk
SURGE = float(os.environ.get("SURGE", "0.7"))   # rad: each wheel surges and eases, never stops

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        G.append(dict(lab=lab, odd=lab == ODD, cx=colx[i], y=Y0 + r * PY, r=r, i=i,
                      n=3, m=int(rng.choice([3, 4, 6])),
                      ph=rng.uniform(0, 2 * math.pi), a0=rng.uniform(0, 2 * math.pi)))
for g in G:
    if g["odd"]: g["n"], g["m"] = 3, 4
    g["dir"] = -1.0 if g["odd"] else 1.0      # +1 = clockwise on screen (y down)
print(len(G), "wheels")
assert sum(g["odd"] for g in G) == 1

def theta(g, t):
    """wheel angle (rad, screen coords: + is clockwise)"""
    w = 2 * math.pi * t / LOOP
    # n whole turns per loop + a surge m times per loop (speed varies 0.3x..1.7x, never zero)
    A = min(SURGE, 0.7 * g["n"] / g["m"])
    return g["a0"] + g["dir"] * (g["n"] * w + A * math.sin(g["m"] * w + g["ph"]))

# ---- gondola swing: driven pendulums, integrated over 3 loops (last loop periodic) ----
SUB = 6
DT = 1.0 / (FPS * SUB)
GRAV = float(os.environ.get("GRAV", "620"))   # px/s^2 (sets the natural period with LG)
GAM = 3.2
NS = int(3 * LOOP / DT)
SW = np.zeros((len(G), NG, TOTAL))
for k, g in enumerate(G):
    ts = np.arange(NS + 2) * DT
    th = np.array([theta(g, t) for t in ts])
    a = th[:, None] + np.arange(NG)[None, :] * (2 * math.pi / NG)
    hx = R * np.cos(a); hy = R * np.sin(a)
    ax = np.gradient(np.gradient(hx, DT, axis=0), DT, axis=0); ay = np.gradient(np.gradient(hy, DT, axis=0), DT, axis=0)
    phi = np.zeros(NG); om = np.zeros(NG)
    for s in range(NS):
        # pendulum hanging down (+y), angle phi from vertical; support accel (ax, ay)
        acc = (-(GRAV + ay[s]) * np.sin(phi) - ax[s] * np.cos(phi)) / LG - GAM * om
        om += acc * DT; phi += om * DT
        f = s - 2 * int(LOOP / DT)
        if f >= 0 and f % SUB == 0 and f // SUB < TOTAL:
            SW[k, :, f // SUB] = phi
print("swing max deg", float(np.degrees(np.abs(SW).max())))

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH WHEEL", "TURNS THE OTHER WAY?"
def fit(s, size, maxw=830):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BRASS = (.80, .62, .34); BRASS_LO = (.48, .36, .20)
GON, GON_HI, GON_LO = (.88, .52, .22), (1.0, .78, .45), (.55, .28, .10)
BULB = (1.0, .86, .55)
RED, RED_HI, RED_LO = (.80, .22, .15), (1.0, .45, .35), (.45, .10, .07)

def draw_ground(c):
    for r in range(NR):
        y = Y0 + r * PY + LEG
        c.drawRect(skia.Rect(colx[0] - 76, y, colx[-1] + 76, y + 7), P_((.22, .17, .12), .95))
        c.drawRect(skia.Rect(colx[0] - 70, y, colx[-1] + 70, y + 2), P_(BRASS, .45))
        for j in range(25):
            x = colx[0] - 64 + j * ((colx[-1] - colx[0] + 128) / 24)
            c.drawCircle(x, y + 3.5, 1.8, P_(BULB, .35))

def draw_wheel(c, g, t, f):
    th = theta(g, t)
    x0, y0 = g["cx"], g["y"]
    c.save(); c.translate(x0, y0)
    # A-frame legs (behind the wheel)
    for sx in (-1, 1):
        c.drawLine(0, 0, sx * 36, LEG, S_(BRASS_LO, 1, 6))
        c.drawLine(0, 0, sx * 36, LEG, S_(BRASS, .9, 3.2))
    c.drawLine(-25, LEG * .7, 25, LEG * .7, S_(BRASS_LO, .9, 2.5))
    # spokes
    for j in range(NG):
        a = th + j * 2 * math.pi / NG
        c.drawLine(0, 0, R * math.cos(a), R * math.sin(a), S_(BRASS, .9, 3.0))
        b = a + math.pi / NG
        c.drawLine(R * .45 * math.cos(a), R * .45 * math.sin(a), R * .45 * math.cos(b + math.pi / NG),
                   R * .45 * math.sin(b + math.pi / NG), S_(BRASS_LO, .8, 1.6))
    # rims
    c.drawCircle(0, 0, R, S_(CREAM, .97, 5.5))
    c.drawCircle(0, 0, R * .45, S_(CREAM, .6, 2.6))
    # bulbs on the rim between gondolas (they ride with the wheel, so they show the turning too)
    for j in range(NG):
        b = th + (j + .5) * 2 * math.pi / NG
        c.drawCircle(R * math.cos(b), R * math.sin(b), 3.0, P_(BULB, .95))
    # hub
    c.drawCircle(0, 0, 6.5, P_(BRASS)); c.drawCircle(-1.5, -1.5, 2.5, P_((1, .92, .7), .8))
    # gondolas
    k = G.index(g)
    for j in range(NG):
        a = th + j * 2 * math.pi / NG
        hx, hy = R * math.cos(a), R * math.sin(a)
        phi = SW[k, j, f]
        c.save(); c.translate(hx, hy); c.rotate(math.degrees(phi))
        c.drawLine(0, 0, 0, LG - 3, S_(CREAM, .8, 1.6))
        body = skia.RRect.MakeRectXY(skia.Rect(-10.5, LG - 4, 10.5, LG + 11), 5, 5)
        cl = (RED_LO, RED_HI, RED) if j == 0 else (GON_LO, GON_HI, GON)
        sh = skia.GradientShader.MakeLinear([(-10.5, 0), (10.5, 0)],
             [c4(cl[0]).toColor(), c4(cl[1]).toColor(), c4(cl[2]).toColor(), c4(cl[0]).toColor()], [0, .3, .65, 1])
        c.drawRRect(body, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-12, LG - 6, 12, LG - 2), 2, 2), P_(CREAM, .9))
        c.restore()
    c.restore()

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
            text(c, LET[i], colx[i], 504, F_AX, AMBER, .9)
        draw_ground(c)
        for r in range(NR):
            text(c, str(r + 1), colx[0] - 92, Y0 + r * PY + 11, F_AX, AMBER, .9)
        for g in G: draw_wheel(c, g, t, f)
        yb = 1566
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
def tick(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.08 * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 70) * .6 + bp(rg.standard_normal(len(t)), 2500, 7000) * np.exp(-t * 320) * .4
    return s * np.minimum(1, t * 6000)
def tock(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.12 * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * .5 * t) * .7 + np.sin(2 * np.pi * f0 * 1.31 * t) * .3) * np.exp(-t * 40) \
        + bp(rg.standard_normal(len(t)), 600, 2200) * np.exp(-t * 150) * .3
    return s * np.minimum(1, t * 5000)
def clunk(seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.18 * SR)) / SR
    return np.sin(2 * np.pi * 82 * t) * np.exp(-t * 26) * .6 + bp(rg.standard_normal(len(t)), 150, 900) * np.exp(-t * 60) * .25

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        tt = np.arange(0, LOOP, 1 / 2000)
        th = np.array([theta(g, x) for x in tt]) * g["dir"]
        q = np.floor(th / (2 * math.pi / NG))
        for idx in np.nonzero(np.diff(q))[0]:
            ev.append((k, "tick", float(tt[idx + 1])))
        for c_ in range(g["m"]):       # a soft clunk at each surge (fastest point)
            w0 = ((-g["ph"]) / g["m"] + c_ * 2 * math.pi / g["m"]) % (2 * math.pi)
            ev.append((k, "clunk", w0 * LOOP / (2 * math.pi)))
    ticks = np.array([e[2] for e in ev if e[1] == "tick" and 0 <= e[2] < LOOP])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(ticks - ts) < .1).sum()))
        f0 = note(5 + (7 - g["r"]) + (g["i"] % 3), 261.63)
        if kind == "tick":
            if g["odd"]: m.add(tock(f0, k * 11 + int(ts * 97)), ts, .55, g["cx"])
            else: m.add(tick(f0, k * 11 + int(ts * 97)), ts, .36 / dens, g["cx"])
        else:
            m.add(clunk(k * 7 + int(ts * 53)), ts, .22 / dens, g["cx"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_wheels.mp4"))
