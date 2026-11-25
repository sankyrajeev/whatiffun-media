"""SPOT IT v3 (18:00, 2026-11-25): WHICH BOTTLE / LANDS ON ITS CAP? 56 identical clear bottles, half full of
amber juice, with cream caps, on STAIRCASE SHELVES: 7 shelves, the top one 11 bottles wide (A-K) and each shelf
below one bottle shorter (row 7 = A-E), all left-aligned so the column letters line up; letters on top, row
numbers on the left. Every bottle does a bottle flip on a 2.0 / 3.0 s cycle from a random phase: it hops up,
turns a full 360 and lands upright with a wobble. ONE bottle only turns 180 every flip, so every other landing
it lands on its CAP and stands upside down (juice at the cap end) until its next flip.
Rule type: flips vs doesn't (lands upside down; the No. 45 pancakes / No. 65 toast family on a new object).
Sound: a soft whoosh at each toss, a hollow plastic thunk + liquid slosh at each landing (pentatonic by row,
panned by x, density-normalised); the odd one lands with a higher, harder cap 'tock'.
12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/bottles"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGHIJK"
NR = 7
TOPW = 11
PX = 78.0
PY = float(os.environ.get("PY", "128"))
Y0 = float(os.environ.get("Y0", "684"))      # shelf y of row 1
PCT = int(os.environ.get("PCT", "9"))
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))
X0 = float(os.environ.get("X0", "168"))
colx = [X0 + i * PX for i in range(TOPW)]

BL, BW = 108.0, 40.0              # bottle length / body width
HALF = BL / 2
HOP = float(os.environ.get("HOP", "40"))   # flight height of the centre
TF = 0.86                        # flight time

G = []
for r in range(NR):
    for i in range(TOPW - r):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = 2.0 if odd else float(rng.choice([2.0, 3.0], p=[.5, .5]))
        G.append(dict(lab=lab, odd=odd, cx=colx[i], fy=Y0 + r * PY, r=r, i=i, P=P, ph=rng.uniform(0, 1)))
print(len(G), "bottles")
assert sum(g["odd"] for g in G) == 1

def ease(u): return .55 * u + .45 * (u * u * (3 - 2 * u))
def state(g, t):
    """(dx, dy, angle_deg) of the bottle centre relative to its resting centre"""
    P = g["P"]; x = t / P + g["ph"]; k = math.floor(x); tc = (x - k) * P
    turn = 180.0 if g["odd"] else 360.0
    base = (k % 2) * 180.0 if g["odd"] else 0.0
    if tc < TF:
        u = tc / TF
        dy = -4 * HOP * u * (1 - u)
        a = base + turn * ease(u)
        return 0.0, dy, a
    # landed: damped wobble + tiny squash bounce
    s = tc - TF
    a = base + turn + 7.0 * math.exp(-s * 5.5) * math.sin(2 * math.pi * 2.6 * s)
    return 0.0, 0.0, a

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
QS = int(os.environ.get("QS", "84"))
F_Q = font(TF_BOLD, QS); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
CR = (.95, .90, .80); CR_D = (.74, .67, .56); JUICE = (.93, .58, .20); JUICE_D = (.70, .38, .10)
STROKE = dict(Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)

def bottle_path():
    """upright bottle, origin at the centre, base at y=+HALF, cap at y=-HALF"""
    w = BW / 2; nw = 9.5
    p = skia.Path()
    yb, ys, yn, yt = HALF, -7, -34, -HALF + 13   # base, shoulder start, neck start, neck top (cap below this)
    p.moveTo(-w + 5, yb); p.lineTo(w - 5, yb)
    p.quadTo(w, yb, w, yb - 6)
    p.lineTo(w, ys)
    p.cubicTo(w, ys - 14, nw, yn + 6, nw, yn)
    p.lineTo(nw, yt); p.lineTo(-nw, yt); p.lineTo(-nw, yn)
    p.cubicTo(-nw, yn + 6, -w, ys - 14, -w, ys)
    p.lineTo(-w, yb - 6); p.quadTo(-w, yb, -w + 5, yb)
    p.close()
    return p
BPATH = bottle_path()

def draw_bottle(c, g, t):
    dx, dy, a = state(g, t)
    cx, cy = g["cx"] + dx, g["fy"] - HALF + dy
    # contact shadow (shrinks in flight)
    lift = -dy / max(1, HOP)
    sw = 26 * (1 - .45 * lift)
    c.drawOval(skia.Rect(g["cx"] - sw, g["fy"] - 4, g["cx"] + sw, g["fy"] + 5),
               P_((0, 0, 0), .5 * (1 - .5 * lift), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    c.save(); c.translate(cx, cy); c.rotate(a)
    # glass body
    c.drawPath(BPATH, P_(CR, .10))
    # juice: everything below a world-horizontal line through the centre (+3 px)
    c.save(); c.clipPath(BPATH, doAntiAlias=True)
    c.rotate(-a)
    c.drawRect(skia.Rect(-80, 4, 80, 80), P_(JUICE, .92))
    c.drawRect(skia.Rect(-80, 4, 80, 8), P_((1, .82, .5), .55))       # bright surface line
    c.rotate(a)
    # label band
    c.drawRect(skia.Rect(-BW, 10, BW, 27), P_(CR, .88))
    c.drawRect(skia.Rect(-BW, 16.5, BW, 19.5), P_(AMBER, .9))
    c.restore()
    # highlight + outline
    c.drawLine(-BW / 2 + 6, -4, -BW / 2 + 6, HALF - 10, P_((1, 1, 1), .35, StrokeWidth=3, **STROKE))
    c.drawPath(BPATH, P_(CR, .95, StrokeWidth=2.6, **STROKE))
    # cap (solid cream, ridged)
    cap = skia.RRect.MakeRectXY(skia.Rect(-11.5, -HALF, 11.5, -HALF + 14), 3, 3)
    c.drawRRect(cap, P_(CR, 1))
    for xx in (-6, -2, 2, 6):
        c.drawLine(xx, -HALF + 2, xx, -HALF + 11, P_(CR_D, .9, StrokeWidth=1.6))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH BOTTLE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "LANDS ON ITS CAP?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(TOPW):
            text(c, LET[i], colx[i], 502, F_AX, AMBER, .9)
        for r in range(NR):
            y = Y0 + r * PY
            text(c, str(r + 1), X0 - 58, y - 36, F_AX, AMBER, .9)
            x1 = colx[TOPW - r - 1] + PX / 2
            c.drawLine(X0 - PX / 2 + 4, y + 2, x1, y + 2, P_(AMBER, .35, StrokeWidth=4, **STROKE))
        for g in G: draw_bottle(c, g, t)
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
def thunk(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.45 * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 22) * .8 + np.sin(2 * np.pi * f0 * 1.5 * t) * np.exp(-t * 40) * .25
    s += bp(rg.standard_normal(len(t)), 300, 2500) * np.exp(-t * 70) * .3
    # liquid slosh: a few gliding bubbly blips
    for j in range(3):
        t0 = .03 + .045 * j + rg.uniform(0, .02)
        tt = np.clip(t - t0, 0, None)
        fr = (700 + 300 * j) * (1 + 2.5 * tt)
        s += np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * 60) * (t > t0) * .12
    return s * np.minimum(1, t * 3000)
def tock(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.35 * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 35) * .7 + np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 50) * .35
    s += bp(rg.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 120) * .4
    return s * np.minimum(1, t * 4000)
def whoosh(seed, dur=.3):
    rg = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    return bp(rg.standard_normal(len(t)), 500, 2500) * np.sin(np.pi * t / dur) ** 2 * .5

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            base = (c_ - g["ph"]) * g["P"]
            ev.append((k, "whoosh", base + .05, c_))
            ev.append((k, "land", base + TF, c_))
    allt = np.array([e[2] % LOOP for e in ev if e[1] == "land"])
    for k, kind, ts, c_ in ev:
        ts = ts % LOOP
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(allt - ts) < .15).sum() / 3))
        f0 = note(2 + (6 - g["r"]) // 2 + (g["i"] % 3), 110.0)
        sd = k * 13 + int(ts * 97)
        if kind == "whoosh":
            m.add(whoosh(sd), ts, .10 / dens, g["cx"])
        elif g["odd"]:
            # every flip counter c_: landing upside down when the flip index parity says so
            m.add(tock(f0 * 2.5, sd), ts, .40 / dens, g["cx"])
        else:
            m.add(thunk(f0, sd), ts, .42 / dens, g["cx"])
    n = int(LOOP * SR)
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_bottles.mp4"))
