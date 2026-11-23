"""SPOT IT v3 (13:00, 2026-11-23): WHICH TURBINE / SPINS BACKWARDS? 61 identical cream wind turbines in a
HEXAGON (rows of 5,6,7,8,9,8,7,6,5; every turbine's label, e.g. "F3", on its base: letter = place in the row
from the left, number = row). Every turbine is hit by its own gust every 2.0 / 2.4 / 3.0 s (random phase):
it whips up to ~0.75 rev/s, then coasts down to a slow turn (never stops). One blade of each rotor has an
amber tip so the turn is easy to read. ONE turbine spins the other way (anticlockwise) with every gust.
Rule type: wrong way (rotation direction). Sound: an airy whoosh per gust + a soft tick each time the amber
blade passes the top (pentatonic by row, panned by x, density-normalised); the odd one ticks with a low
wooden tock and its whoosh is reversed. 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/turb"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGHI"
WIDTHS = [5, 6, 7, 8, 9, 8, 7, 6, 5]
PX = float(os.environ.get("PX", "98"))
PY = float(os.environ.get("PY", "109"))
Y0 = float(os.environ.get("Y0", "548"))      # hub y of row 1
R = float(os.environ.get("RAD", "43"))       # blade length
TOWER = 58.0
WLO = float(os.environ.get("WLO", ".14"))    # rev/s coasting
WHI = float(os.environ.get("WHI", ".6"))    # rev/s at gust peak
PCT = int(os.environ.get("PCT", "11"))
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))

def gust(s):
    """speed shape over one gust cycle s in [0,1): fast spin-up, slow coast."""
    if s < .14: return .5 - .5 * math.cos(math.pi * s / .14)
    return math.exp(-(s - .14) / .22)

NS = 2400
G = []
for r, wdt in enumerate(WIDTHS):
    for i in range(wdt):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        cx = W / 2 + (i - (wdt - 1) / 2) * PX
        y = Y0 + r * PY
        P = 2.4 if odd else float(rng.choice([2.0, 2.4, 3.0], p=[.3, .4, .3]))
        ph = float(os.environ.get("OPH", ".35")) if odd else rng.uniform(0, 1)
        ts = np.arange(NS) / NS * LOOP
        w = np.array([WLO + (WHI - WLO) * gust((t / P + ph) % 1) for t in ts])
        rev = w.sum() * LOOP / NS
        k = max(1, round(rev)); w *= k / rev           # whole turns per loop -> seamless
        ang = np.concatenate([[0], np.cumsum(w) * LOOP / NS]) * 360.0   # degrees, at ts and LOOP
        G.append(dict(lab=lab, odd=odd, cx=cx, y=y, r=r, i=i, P=P, ph=ph, ang=ang, w=w,
                      a0=rng.uniform(0, 360), dirn=-1 if odd else 1))
print(len(G), "turbines")
assert sum(g["odd"] for g in G) == 1

def angle(g, t):
    t = t % LOOP
    x = t / LOOP * NS; i = int(x); f = x - i
    a = g["ang"][i] * (1 - f) + g["ang"][min(NS, i + 1)] * f
    return g["a0"] + g["dirn"] * a
def speed(g, t):
    return g["w"][int((t % LOOP) / LOOP * NS) % NS]

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_LAB = font(TF_SB, 21)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

def blade_path():
    p = skia.Path()
    p.moveTo(0, -3); p.cubicTo(7, -10, 7.5, -R * .45, 3.6, -R * .9)
    p.quadTo(1, -R - 1, -.8, -R * .92); p.cubicTo(-3.2, -R * .5, -5, -12, -4, -3); p.close()
    return p
BLADE = blade_path()
def tip_path():
    p = skia.Path()
    p.moveTo(4.6, -R * .70); p.lineTo(3.2, -R * .9); p.quadTo(1, -R - 1, -.8, -R * .92); p.lineTo(-2.4, -R * .70); p.close()
    return p
TIP = tip_path()
BLADE_PAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-5, 0), (5, 0)],
    [c4((.99, .96, .90)).toColor(), c4((.80, .74, .64)).toColor()]))

AMBER_PAINT = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-5, 0), (5, 0)],
    [c4((1.0, .76, .40)).toColor(), c4((.78, .52, .20)).toColor()]))

def draw_rotor(c, x, y, a, alpha=1.0):
    if alpha < 1: c.saveLayerAlpha(None, int(255 * alpha))
    c.save(); c.translate(x, y); c.rotate(a)
    for k in range(3):
        c.save(); c.rotate(120 * k)
        c.drawPath(BLADE, BLADE_PAINT if k else AMBER_PAINT)
        c.restore()
    c.restore()
    if alpha < 1: c.restore()

def draw_turbine(c, g, t):
    x, y = g["cx"], g["y"]
    # tower
    p = skia.Path(); p.moveTo(x - 2.2, y); p.lineTo(x + 2.2, y); p.lineTo(x + 4.2, y + TOWER); p.lineTo(x - 4.2, y + TOWER); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - 4, 0), (x + 4, 0)],
        [c4((.90, .85, .76)).toColor(), c4((.55, .50, .43)).toColor()])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 15, y + TOWER - 1, x + 15, y + TOWER + 4), 2, 2), P_(AMBER, .55))
    text(c, f"{g['lab'][0]}{g['lab'][1]}", x, y + TOWER + 24, F_LAB, AMBER, .78)
    # nacelle
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 6, y - 5, x + 12, y + 5), 4, 4), P_((.78, .72, .62), 1))
    # motion trail: ghosts of the recent past (shows which way it is turning)
    sp = speed(g, t)
    if sp > .22:
        for k, dt in enumerate((.075, .05, .025)):
            draw_rotor(c, x, y, angle(g, t - dt), (.10 + .07 * k) * min(1, (sp - .22) / .3))
    draw_rotor(c, x, y, angle(g, t))
    c.drawCircle(x, y, 6.5, P_(AMBER, 1)); c.drawCircle(x - 1.5, y - 1.5, 2.2, P_((1, .95, .8), .7))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH TURBINE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "SPINS BACKWARDS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for g in G: draw_turbine(c, g, t)
        yb = 1558
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 40, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 38, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def whoosh(seed, rev=False):
    rg = np.random.default_rng(seed)
    t = np.arange(int(1.1 * SR)) / SR
    nz = sosfilt(butter(2, [300, 1800] if not rev else [220, 1200], btype="band", fs=SR, output="sos"),
                 rg.standard_normal(len(t)))
    env = np.where(t < .12, t / .12, np.exp(-(t - .12) / .3))
    if rev: env = env[::-1]
    return nz * env * .25
def tick(f0, seed, odd=False):
    t = np.arange(int(.3 * SR)) / SR
    if odd:
        return (np.sin(2 * np.pi * f0 * .5 * t) * np.exp(-t * 30) + .3 * np.sin(2 * np.pi * f0 * 1.5 * t) * np.exp(-t * 50)) * np.minimum(1, t * 3000)
    return glass_click(f0 * 2, 110, .3, .4) * .7

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for c_ in range(-1, int(LOOP / g["P"]) + 2):
            t0 = (c_ - g["ph"]) * g["P"]
            if 0 <= t0 < LOOP: ev.append((k, "gust", t0))
        # amber blade passes the top: angle ≡ 0 mod 360
        a = np.array([angle(g, t) for t in np.arange(0, LOOP, 1 / 600)])
        crosses = np.where(np.floor(a[1:] / 360) != np.floor(a[:-1] / 360))[0]
        for j in crosses: ev.append((k, "tick", j / 600))
    gt = np.array([e[2] for e in ev if e[1] == "gust"])
    tt_ = np.array([e[2] for e in ev if e[1] == "tick"])
    for k, kind, ts in ev:
        g = G[k]
        f0 = note(3 + (8 - g["r"]) // 2 + (g["i"] % 3), 130.81)
        if kind == "gust":
            dens = math.sqrt(max(1, (np.abs(gt - ts) < .3).sum()))
            m.add(whoosh(k * 7 + int(ts * 90), g["odd"]), ts - (1.0 if g["odd"] else 0), (.5 if not g["odd"] else .8) / dens, g["cx"])
        else:
            dens = math.sqrt(max(1, (np.abs(tt_ - ts) < .15).sum()))
            m.add(tick(f0, k * 11 + int(ts * 40), g["odd"]), ts, (.45 if not g["odd"] else .9) / dens, g["cx"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_turbines.mp4"))
