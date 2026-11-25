"""SPOT IT v3 (15:00, 2026-11-25): WHICH CHAIR / NEVER STOPS? 56 identical cream rocking chairs (walnut
rockers, amber cushion) in an AMPHITHEATRE: 7 columns A-G x 8 rows, every row a gentle smile-shaped arc of
floorboards and alternate rows nudged left / right (staggered); column letters on top, row numbers on the left.
Every chair gets a push from a random phase on a 3.0 / 4.0 s cycle: it rocks in big rolling swings (it really
rolls on its curved rockers), dies down over two swings and then STANDS DEAD STILL. ONE chair never stops: it
rocks at full swing the whole time.
Rule type: never stops (the No. 43 fans rule on a new everyday object).
Sound: a soft wooden knock at each push, a hushed creak at each turn of the swing, a little settle tap when it
stops (pentatonic by row, panned by x, density-normalised); the odd one's creak is a higher, thinner squeak.
12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/rockers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFG"
NC, NR = 7, 7
PX = 124.0                       # column pitch
PY = float(os.environ.get("PY", "134"))
Y0 = float(os.environ.get("Y0", "668"))     # floor y of row 1 (ends of the arc)
SMILE = 16.0                     # how much lower the middle of each row sits
STAG = 0.0                      # alternate rows nudged +/- this much
PCT = int(os.environ.get("PCT", "18"))
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))
colx = [W / 2 + 14 + (i - (NC - 1) / 2) * PX for i in range(NC)]

SC = 1.17
R = 70.0                         # rocker radius (rolling)
AMP = 25.0                       # degrees, full swing
TSW = 1.0                        # swing period (s)
ROCK = 2.0                       # rocking time per cycle (two swings), then still

def rock_angle(u):
    """degrees at time u into a normal chair's cycle"""
    if u <= 0 or u >= ROCK: return 0.0
    env = min(1.0, u / .12)
    if u > 1.5: env *= .5 + .5 * math.cos(math.pi * (u - 1.5) / .5)
    return AMP * env * math.sin(2 * math.pi * u / TSW)

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = float(rng.choice([4.0, 6.0], p=[.75, .25]))
        xn = (i - (NC - 1) / 2) / ((NC - 1) / 2)
        st = STAG if r % 2 else -STAG
        G.append(dict(lab=lab, odd=odd, cx=colx[i] + st, fy=Y0 + r * PY + SMILE * (1 - xn * xn), r=r, i=i, P=P,
                      ph=rng.uniform(0, 1), sh=rng.uniform(0, 6.283)))
print(len(G), "chairs")
assert sum(g["odd"] for g in G) == 1

def angle(g, t):
    if g["odd"]:
        return AMP * math.sin(2 * math.pi * t / TSW + g["sh"])
    P = g["P"]; tc = ((t / P + g["ph"]) % 1.0) * P
    return rock_angle(tc)

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

WALNUT = (.42, .27, .15); WAL_D = (.26, .16, .09)
CR = (.95, .90, .80); CR_D = (.74, .67, .56)
STROKE = dict(Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)

# chair geometry, origin = rocker circle centre, floor contact at (0, R); chair faces right
def chair_picture():
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(-120, -120, 120, 120))
    fl = R
    # rockers: an arc of the rolling circle, thick walnut band
    arc = skia.Path()
    a0, a1 = 90 + 33, 90 - 33          # degrees in skia coords (90 = straight down)
    arc.addArc(skia.Rect(-R, -R, R, R), a0, a1 - a0)
    c.drawPath(arc, P_(WAL_D, 1, StrokeWidth=11, **STROKE))
    c.drawPath(arc, P_(WALNUT, 1, StrokeWidth=7, **STROKE))
    def rk(xx): return math.sqrt(R * R - xx * xx)   # rocker y at x
    sy = fl - 44                      # seat height
    # legs (back pair slightly left), front pair
    for x0, x1 in [(-24, -26), (22, 24)]:
        c.drawLine(x1, rk(x1) - 3, x0, sy, P_(CR_D, 1, StrokeWidth=6.5, **STROKE))
        c.drawLine(x1, rk(x1) - 3, x0, sy, P_(CR, 1, StrokeWidth=4, **STROKE))
    # back: leans back from the rear of the seat
    bx0, by0, bx1, by1 = -27, sy, -42, sy - 70
    bp_ = skia.Path(); bp_.moveTo(bx0, by0 - 2); bp_.lineTo(bx1, by1 + 2); bp_.lineTo(bx1 + 22, by1 + 5); bp_.lineTo(bx0 + 20, by0 - 3); bp_.close()
    c.drawPath(bp_, P_(CR_D, 1))
    c.drawPath(bp_, P_((.84, .78, .68), 1))
    for off in [6.5, 13]:
        c.drawLine(bx0 + off, by0 - 8, bx1 + off + 1, by1 + 12, P_(WAL_D, .75, StrokeWidth=2.2, **STROKE))
    for k, off in enumerate([]):
        c.drawLine(bx0 + off, by0 - 4, bx1 + off, by1 + 10, P_(CR, .85, StrokeWidth=2.6, **STROKE))
    c.drawLine(bx0, by0, bx1, by1, P_(CR_D, 1, StrokeWidth=7, **STROKE))
    c.drawLine(bx0, by0, bx1, by1, P_(CR, 1, StrokeWidth=4.5, **STROKE))
    c.drawLine(bx0 + 19, by0 - 2, bx1 + 19, by1 + 6, P_(CR, 1, StrokeWidth=3.4, **STROKE))
    # top rail
    c.drawLine(bx1 - 3, by1, bx1 + 23, by1 + 4, P_(CR_D, 1, StrokeWidth=8, **STROKE))
    c.drawLine(bx1 - 3, by1, bx1 + 23, by1 + 4, P_(CR, 1, StrokeWidth=5.5, **STROKE))
    # arm rest
    c.drawLine(-33, sy - 32, 26, sy - 26, P_(CR_D, 1, StrokeWidth=6.5, **STROKE))
    c.drawLine(-33, sy - 32, 26, sy - 26, P_(CR, 1, StrokeWidth=4, **STROKE))
    c.drawLine(22, sy, 25, sy - 26, P_(CR, 1, StrokeWidth=3.6, **STROKE))
    # seat
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-32, sy - 3, 32, sy + 5), 3, 3), P_(CR_D, 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-31, sy - 3, 31, sy + 3), 3, 3), P_(CR, 1))
    # amber cushion
    cu = skia.Path(); cu.moveTo(-28, sy - 3); cu.cubicTo(-26, sy - 15, 24, sy - 15, 28, sy - 3); cu.close()
    c.drawPath(cu, P_(AMBER, 1))
    c.drawPath(cu, P_((1, .85, .55), .35, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5))
    return rec.finishRecordingAsPicture()
CHAIR = chair_picture()

def draw_chair(c, g, t):
    th = angle(g, t)
    # rolling without slipping: centre moves by R*theta (rocking back = rotating ccw = negative skia angle)
    dx = .55 * SC * R * math.radians(th)
    c.save(); c.translate(g["cx"] + dx, g["fy"] - SC * R)
    # contact shadow
    c.drawOval(skia.Rect(-44, SC * R - 4, 44, SC * R + 6), P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    c.rotate(th); c.scale(SC, SC)
    c.drawPicture(CHAIR)
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH CHAIR", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER STOPS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], colx[i], 504, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 104, Y0 + r * PY - 50, F_AX, AMBER, .9)
        # smile-arc floorboards per row
        for r in range(NR):
            st = STAG if r % 2 else -STAG
            p = skia.Path(); x0, x1 = colx[0] - 58 + st, colx[-1] + 58 + st
            for k in range(41):
                x = x0 + (x1 - x0) * k / 40
                xn = (x - st - W / 2) / ((NC - 1) / 2 * PX)
                y = Y0 + r * PY + SMILE * (1 - xn * xn) + 4
                (p.moveTo if k == 0 else p.lineTo)(x, y)
            c.drawPath(p, P_(AMBER, .28, StrokeWidth=3, **STROKE))
        for g in G: draw_chair(c, g, t)
        yb = 1546
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 42, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 40, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def knock(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.4 * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 30) * .8 + np.sin(2 * np.pi * f0 * 2.3 * t) * np.exp(-t * 55) * .3
    s += bp(rg.standard_normal(len(t)), 400, 3000) * np.exp(-t * 80) * .35
    return s * np.minimum(1, t * 3000)
def creak(f0, seed, dur=.22, hi=False):
    rg = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    # stick-slip creak: a train of tiny clicks at a gliding rate, band-passed like wood
    rate = f0 * (1 + .25 * np.sin(np.pi * t / dur))
    ph = np.cumsum(rate) / SR
    pulses = np.maximum(0, np.sin(2 * np.pi * ph)) ** 12
    nz = rg.standard_normal(len(t)) * .25
    lo, hh = (1400, 5200) if hi else (500, 2200)
    s = bp(pulses + nz * pulses, lo, hh)
    env = np.sin(np.pi * t / dur) ** 1.5
    return s * env * (1.6 if hi else 1.0)
def tap(f0, seed):
    t = np.arange(int(.25 * SR)) / SR
    return np.sin(2 * np.pi * f0 * t) * np.exp(-t * 40) * np.minimum(1, t * 4000) * .6

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        if g["odd"]:
            # turn points of its swing: every half period
            t0 = (math.pi / 2 - g["sh"]) / (2 * math.pi) * TSW
            for j in range(-2, 28): ev.append((k, "squeak", t0 + j * TSW / 2))
            continue
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            base = (c_ - g["ph"]) * g["P"]
            ev.append((k, "knock", base + .01))
            for j in range(4):
                ev.append((k, "creak%d" % j, base + (j + .5) * TSW / 2))
            ev.append((k, "tap", base + ROCK - .05))
    allt = np.array([e[2] % LOOP for e in ev])
    for k, kind, ts in ev:
        if not (0 <= ts < LOOP): continue
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(allt - ts) < .15).sum() / 3))
        f0 = note(2 + (7 - g["r"]) // 2 + (g["i"] % 3), 110.0)
        sd = k * 13 + int(ts * 97)
        if kind == "knock":
            m.add(knock(f0, sd), ts, .42 / dens, g["cx"])
        elif kind.startswith("creak"):
            j = int(kind[-1]); amp = math.exp(-(j + .5) * TSW / 2 * 1.1)
            m.add(creak(38 + g["r"] * 3, sd), ts, .30 * amp / dens, g["cx"])
        elif kind == "tap":
            m.add(tap(f0 * 2, sd), ts, .14 / dens, g["cx"])
        else:
            m.add(creak(62, sd, dur=.2, hi=True), ts, .30, g["cx"])
    n = int(LOOP * SR)
    # gentle room tone so there are no dead stretches
    rg = np.random.default_rng(3)
    room = bp(rg.standard_normal(n), 150, 900) * .006
    m.L[:n] += room; m.R[:n] += room
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_rockers.mp4"))
