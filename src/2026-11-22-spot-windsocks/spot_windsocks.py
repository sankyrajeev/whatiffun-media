"""SPOT IT v3 (10:00, 2026-11-22): WHICH ONE / BREAKS PHYSICS? 56 identical amber/cream striped WINDSOCKS on
brass poles, 8 columns A-H x 7 rows, poles alternately tall and short along each row (BATTLEMENT ROWS).
A steady wind blows left -> right (soft streaks drift across the whole frame). Every sock catches a gust on a
2.4 s or 3.0 s cycle from a random phase: it snaps full and streams downwind (to the RIGHT) with a flutter,
then collapses and swings down past the pole. ONE sock streams INTO the wind (to the LEFT) every 2.4 s.
Rule type: breaks physics (a windsock pointing upwind).
Sound: soft looping wind bed + a fabric flump each time a sock fills (pentatonic by row, panned by x,
density-normalised); the odd sock's flump is lower and hollow (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/socks"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 7
CW = 104.0
CH = float(os.environ.get("CH", "132"))
X0 = 152.0                       # pole x of column A
Y0 = float(os.environ.get("Y0", "580"))   # pole-top y of row 1 (tall poles)
POLE = 96.0
L = float(os.environ.get("L", "84"))       # sock length
PCT = int(os.environ.get("PCT", "5"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "22")))

T_RISE, T_HOLD, T_FALL = .28, .95, .55
SK = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        dy = 0 if i % 2 == 0 else 16          # battlement: alternate tall / short poles
        P = 2.4 if (odd or rng.random() < .6) else 3.0
        SK.append(dict(lab=lab, odd=odd, x=X0 + i * CW, y=Y0 + r * CH + dy, base=Y0 + r * CH + POLE, r=r, i=i,
                       P=P, H=(float(os.environ.get("OH", "0.6")) if odd else T_HOLD), ph=rng.uniform(0, 1), fl=rng.uniform(0, 6.28), sw=rng.uniform(0, 6.28)))
print(len(SK), "socks")
assert sum(s["odd"] for s in SK) == 1

def cyc(s, t): return ((t / s["P"] + s["ph"]) % 1.0) * s["P"]
def infl(s, t):
    u = cyc(s, t)
    if u < T_RISE: k = u / T_RISE; return 1 - (1 - k) ** 3
    H = s["H"]
    if u < T_RISE + H: return 1.0
    if u < T_RISE + H + T_FALL: return 1 - ss((u - T_RISE - H) / T_FALL)
    return 0.0
def swing(s, t):
    """degrees from straight down while limp: falls past the pole (upwind side) and settles"""
    u = cyc(s, t)
    tau = (u - (T_RISE + s["H"] + T_FALL * .55)) % s["P"]
    return -float(os.environ.get("SWA", "52")) * math.exp(-tau / .55) * math.sin(2 * math.pi * tau / 1.05 + .6) + 4 * math.sin(2 * math.pi * t / 2.0 + s["sw"])
def fills(s, t0=-3.0, t1=LOOP + 3):
    out = []
    for k in range(int(t0 / s["P"]) - 2, int(t1 / s["P"]) + 3):
        tt = (k - s["ph"]) * s["P"] + T_RISE * .55
        if t0 <= tt <= t1: out.append(tt)
    return out
FILLS = [fills(s) for s in SK]

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_LAB = font(TF_SB, 16); F_PCT = font(TF_BOLD, 38); F_ROW = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
ORANGE = (.93, .47, .17); CRM = (.96, .91, .81)
BRASS = skia.GradientShader.MakeLinear([(-4, 0), (4, 0)],
    [c4((.45, .30, .12)).toColor(), c4((1, .86, .55)).toColor(), c4((.58, .40, .16)).toColor()], [0, .4, 1])

NSEG = 10
def spine(s, t):
    a = infl(s, t); sw = swing(s, t)
    pts = [(0.0, 0.0)]; rad = []
    seg = L * (.86 + .14 * a) / NSEG
    x = y = 0.0
    for k in range(NSEG + 1):
        u = k / NSEG
        e = a ** (1 + 1.6 * u)                          # the tail fills last, empties first
        fl = (2.5 + 7 * u) * e * math.sin(2 * math.pi * 4.25 * t - 3.0 * u + s["fl"])
        phi = e * (84 - 7 * u) + (1 - e) * (sw * (1 + .35 * u)) + fl
        rad.append((1 - e) * (9.5 - 5.5 * u) + e * (17.5 - 7.5 * u) + 1.2 * e * math.sin(2 * math.pi * 6 * t + 5 * u + s["fl"]))
        if k < NSEG:
            pr = math.radians(phi)
            x += seg * math.sin(pr); y += seg * math.cos(pr); pts.append((x, y))
    return pts, rad, a

def draw_sock(c, s, t):
    pts, rad, a = spine(s, t)
    c.save(); c.translate(s["x"], s["y"] + 6)
    if s["odd"]: c.scale(-1, 1)
    # outline edges
    Ls, Rs = [], []
    for k, (x, y) in enumerate(pts):
        if k == 0: dx, dy = pts[1][0] - x, pts[1][1] - y
        elif k == NSEG: dx, dy = x - pts[k - 1][0], y - pts[k - 1][1]
        else: dx, dy = pts[k + 1][0] - pts[k - 1][0], pts[k + 1][1] - pts[k - 1][1]
        n = math.hypot(dx, dy) + 1e-9; nx, ny = -dy / n, dx / n
        Ls.append((x + nx * rad[k], y + ny * rad[k])); Rs.append((x - nx * rad[k], y - ny * rad[k]))
    # soft shadow body
    sh = skia.Path(); sh.moveTo(*Ls[0])
    for p in Ls[1:]: sh.lineTo(*p)
    for p in reversed(Rs): sh.lineTo(*p)
    sh.close()
    c.save(); c.translate(3, 7)
    c.drawPath(sh, P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.restore()
    for b in range(5):                                  # 5 stripes, 2 segments each
        k0, k1 = 2 * b, 2 * b + 2
        p = skia.Path(); p.moveTo(*Ls[k0])
        for k in range(k0 + 1, k1 + 1): p.lineTo(*Ls[k])
        for k in range(k1, k0 - 1, -1): p.lineTo(*Rs[k])
        p.close()
        col = ORANGE if b % 2 == 0 else CRM
        shade = .80 + .2 * a
        c.drawPath(p, P_(tuple(v * shade for v in col), 1))
    # lower-side shading + top highlight for volume
    lo = skia.Path(); lo.moveTo(*Rs[0])
    for k in range(1, NSEG + 1): lo.lineTo(*Rs[k])
    for k in range(NSEG, -1, -1):
        x, y = pts[k]; lo.lineTo(x * .5 + Rs[k][0] * .5, y * .5 + Rs[k][1] * .5)
    lo.close(); c.drawPath(lo, P_((.12, .05, .02), .28))
    hl = skia.Path(); hl.moveTo(*[(Ls[0][0] * .7 + pts[0][0] * .3), (Ls[0][1] * .7 + pts[0][1] * .3)][0:2])
    for k in range(1, NSEG):
        hl.lineTo(Ls[k][0] * .7 + pts[k][0] * .3, Ls[k][1] * .7 + pts[k][1] * .3)
    c.drawPath(hl, P_((1, .97, .9), .35 * a + .1, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, StrokeCap=skia.Paint.kRound_Cap))
    # mouth ring (brass hoop at the pole)
    dx, dy = pts[1][0], pts[1][1]
    ang = math.degrees(math.atan2(dy, dx))
    c.save(); c.rotate(ang)
    ro = rad[0] + 1
    c.drawOval(skia.Rect(-3.5 - 2 * a, -ro, 3.5 + 2 * a, ro), P_((.25, .12, .05), .9 * a))
    c.drawOval(skia.Rect(-3.5 - 2 * a, -ro, 3.5 + 2 * a, ro), P_((.95, .78, .45), 1, Style=skia.Paint.kStroke_Style, StrokeWidth=2.6))
    c.restore()
    c.restore()

def draw_pole(c, s):
    x, y0, y1 = s["x"], s["y"], s["base"]
    c.drawRect(skia.Rect(x - 3, y0 + 2, x + 3, y1), skia.Paint(AntiAlias=True, Shader=BRASS.makeWithLocalMatrix(skia.Matrix.Translate(x, 0))))
    c.drawCircle(x, y0, 5.5, P_((1, .86, .55), 1))
    c.drawOval(skia.Rect(x - 14, y1 - 3, x + 14, y1 + 4), P_((0, 0, 0), .5, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 9, y1 - 5, x + 9, y1 + 1), 2, 2), P_((.55, .40, .2), 1))
    # engraved brass plaque with the cell name, so a sock pointing into a neighbour's cell can't be misread
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 19, y1 + 3, x + 19, y1 + 24), 4, 4), P_((.30, .21, .11), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 19, y1 + 3, x + 19, y1 + 24), 4, 4), P_((.85, .66, .36), .8, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4))
    text(c, f"{s['lab'][0]}{s['lab'][1]}", x, y1 + 20, F_LAB, (1, .88, .62), .95)

STREAKS = []
for k in range(46):
    STREAKS.append(dict(x0=rng.uniform(0, 1300), y=rng.uniform(500, 1500), len=rng.uniform(50, 150),
                        v=1300 * rng.choice([5, 6, 7]) / LOOP, a=rng.uniform(.05, .13), w=rng.uniform(1.2, 2.4)))
def draw_wind(c, t):
    for st in STREAKS:
        x = (st["x0"] + st["v"] * t) % 1300 - 150
        g = skia.GradientShader.MakeLinear([(x - st["len"], 0), (x, 0)],
            [c4(CREAM, 0).toColor(), c4(CREAM, st["a"]).toColor()], [0, 1])
        c.drawLine(x - st["len"], st["y"], x, st["y"], skia.Paint(AntiAlias=True, Shader=g, StrokeWidth=st["w"], StrokeCap=skia.Paint.kRound_Cap))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], X0 + i * CW, Y0 - 34, F_ROW, AMBER, .9)
        # row numbers live on each pole's plaque (a left-hanging column-A sock would hit a margin number)
        draw_wind(c, t)
        for r in range(NR):        # faint ground line per row
            yb = Y0 + r * CH + POLE
            c.drawLine(X0 - 30, yb + 1, X0 + (NC - 1) * CW + 60, yb + 1, P_(AMBER, .16, StrokeWidth=1.5))
        for s in SK: draw_pole(c, s)
        for s in SK: draw_sock(c, s, t)
        yb = 1558
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
def flump(f0, seed, dur=.36, hollow=False):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    nz = sosfilt(butter(2, [300, 2600] if not hollow else [150, 900], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t)))
    env = np.minimum(1, t * 220) * np.exp(-t * (16 if not hollow else 11))
    body = np.sin(2 * np.pi * f0 * t * (1 + .3 * np.exp(-t * 40))) * np.exp(-t * 20)
    if hollow: body += .6 * np.sin(2 * np.pi * f0 * 1.5 * t) * np.exp(-t * 14)
    snap = rg.standard_normal(len(t)) * np.exp(-t * 300) * .25
    return nz * env * .9 + body * .7 + snap
def wind_bed(n, seed=3):
    rg = np.random.default_rng(seed)
    out = []
    for ch in range(2):
        X = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
        X *= 1 / (1 + (fr / 420) ** 2) * (fr > 60)          # circular filtering = seamless loop
        x = np.fft.irfft(X, n)
        tt = np.arange(n) / SR
        x *= 1 + .35 * np.sin(2 * np.pi * tt / 3.0 + ch) + .2 * np.sin(2 * np.pi * tt / 2.0)
        out.append(x / np.sqrt((x ** 2).mean()))
    return out

def audio(path):
    m = Mix(LOOP + 4)
    ev = [(tt, k) for k in range(len(SK)) for tt in FILLS[k] if 0 <= tt < LOOP]
    lt = np.array([e[0] for e in ev])
    for tt, k in ev:
        s = SK[k]
        dens = math.sqrt(max(1, (np.abs(lt - tt) < .2).sum()))
        if s["odd"]:
            m.add(flump(98.0, k * 100 + int(tt * 50), .5, True), tt, .55 / dens * 2.2, s["x"])
        else:
            m.add(flump(note(5 + (6 - s["r"]) // 2 + (s["i"] % 3), 65.41), k * 100 + int(tt * 50)), tt, .55 / dens, s["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    bl, br = wind_bed(n)
    pk = np.sqrt((m.L ** 2).mean()) + 1e-9
    m.L += bl * pk * .55; m.R += br * pk * .55
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_windsocks.mp4"))
