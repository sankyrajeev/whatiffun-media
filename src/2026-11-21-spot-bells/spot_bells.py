"""SPOT IT v3 (15:00, 2026-11-21): WHICH BELL / NEVER RINGS? 52 identical brass bells hung from walnut
headstocks in a DIAMOND (rows of 4-5-6-7-8-7-6-5-4, rows 1-9 top to bottom, letters A.. from the left of each
row, label engraved on each bell's waist band "C6"). Every bell swings big (+-30 deg) on a 2.4 s swing, phased by
a soft diagonal wave plus noise; at each end of the swing its clapper (which hangs near-vertical while the bell
tilts) strikes the rim: a flash at the lip and cream sound-rings ripple out. The odd bell's clapper is stuck to
the bell: it tilts WITH the bell, never touches the rim, no flash, no ripples. Rule type: cause without effect
(it swings but never rings). Sound: soft inharmonic bell dings per strike (pentatonic by row, panned by x,
density-normalised) + faint creak at each turn; the odd bell gives a dull wooden clonk at each end of its swing
(audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/bells"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
ROWS = [4, 5, 6, 7, 8, 7, 6, 5, 4]
LET = "ABCDEFGH"
SX = float(os.environ.get("SX", "104"))
SY = float(os.environ.get("SY", "107"))
Y0 = float(os.environ.get("Y0", "528"))       # pivot y of row 1
S = float(os.environ.get("BS", ".92"))        # bell scale
AMP = float(os.environ.get("AMP", "27"))      # swing amplitude, deg
P = 2.4                                       # full swing period (5 per loop)
PCT = int(os.environ.get("PCT", "11"))
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "5")))

B = []
for r, n in enumerate(ROWS):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y0 + r * SY
        lab = (LET[i], r + 1)
        ph = .18 * (x - 540) / SX * .5 + .12 * r + rng.uniform(-.16, .16)
        B.append(dict(lab=lab, odd=lab == ODD, x=x, y=y, r=r, i=i, ph=ph))
print(len(B), "bells")
assert sum(b["odd"] for b in B) == 1

PSI = 19.0            # clapper-to-bell max relative angle (rim contact)
def ang(b, t):
    return AMP * math.sin(2 * math.pi * (t / P + b["ph"]))
def clap_rel(b, th):
    if b["odd"]: return 0.0
    return -max(-PSI, min(PSI, .78 * th))
def strikes(b, t0=-3.0, t1=LOOP + 3):
    """times + side (+1 bell tilted right) when the clapper reaches the rim"""
    out = []
    th_c = math.degrees(math.asin(min(1, PSI / .78 / AMP)))   # bell angle where contact starts
    u = math.asin(PSI / .78 / AMP) / (2 * math.pi)           # fraction of period
    for k in range(int(t0 / P) - 2, int(t1 / P) + 3):
        base = (k - b["ph"]) * P
        out.append((base + u * P, 1))                         # rising toward +AMP
        out.append((base + (.5 + u) * P, -1))                 # rising toward -AMP (sin negative half)
    return [(t, s) for t, s in out if t0 <= t <= t1]
STR = [strikes(b) for b in B]

# ---------- bell geometry (local, pivot at 0,0, y down) ----------
def bell_path():
    p = skia.Path()
    top, mouth = 10 * S, 92 * S
    p.moveTo(-17 * S, top)
    p.cubicTo(-24 * S, top + 2 * S, -23 * S, 34 * S, -25 * S, 52 * S)
    p.cubicTo(-27 * S, 70 * S, -36 * S, 82 * S, -45 * S, mouth)
    p.quadTo(-47 * S, mouth + 6 * S, -40 * S, mouth + 6 * S)
    p.quadTo(0, mouth + 13 * S, 40 * S, mouth + 6 * S)
    p.quadTo(47 * S, mouth + 6 * S, 45 * S, mouth)
    p.cubicTo(36 * S, 82 * S, 27 * S, 70 * S, 25 * S, 52 * S)
    p.cubicTo(23 * S, 34 * S, 24 * S, top + 2 * S, 17 * S, top)
    p.quadTo(0, top - 6 * S, -17 * S, top)
    p.close(); return p
BELL = bell_path()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
BRASS = skia.GradientShader.MakeLinear([(-46 * S, 0), (46 * S, 0)],
    [c4((.42, .28, .11)).toColor(), c4((.80, .58, .26)).toColor(), c4((1, .88, .58)).toColor(),
     c4((.78, .55, .24)).toColor(), c4((.36, .23, .09)).toColor()], [0, .28, .42, .7, 1])
WOOD = skia.GradientShader.MakeLinear([(0, -16), (0, 0)],
    [c4((.42, .26, .15)).toColor(), c4((.24, .14, .08)).toColor()], [0, 1])
MOUTH = skia.Rect(-41 * S, 89 * S, 41 * S, 103 * S)
BAND_Y = 50 * S

TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_LAB = font(TF_BOLD, 22); F_ROW = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

def draw_bell(c, b, t):
    th = ang(b, t)
    rel = clap_rel(b, th)
    x, y = b["x"], b["y"]
    # headstock beam (fixed) + pivot
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 30, y - 16, x + 30, y - 2), 4, 4),
                skia.Paint(AntiAlias=True, Shader=WOOD) if False else P_((.34, .21, .12), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 30, y - 16, x + 30, y - 12), 2, 2), P_((.55, .37, .22), 1))
    c.save(); c.translate(x, y); c.rotate(th)
    # crown loop
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-7 * S, -3, 7 * S, 12 * S), 5, 5),
                P_((.72, .52, .24), 1, Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    # body
    c.drawPath(BELL, skia.Paint(AntiAlias=True, Shader=BRASS))
    c.drawPath(BELL, P_((.30, .18, .06), .7, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4))
    # dark mouth + clapper hanging in it (clapper rotated by rel about the pivot)
    c.drawOval(skia.Rect(-41 * S, 91 * S, 41 * S, 103 * S), P_((.10, .06, .03), 1))
    c.save(); c.rotate(rel)
    c.save(); c.clipRect(skia.Rect(-60, 94 * S, 60, 140)); 
    c.drawRect(skia.Rect(-2.4 * S, 60 * S, 2.4 * S, 100 * S), P_((.22, .16, .10), 1))
    c.restore()
    c.drawOval(skia.Rect(-8 * S, 96 * S, 8 * S, 114 * S), P_((.30, .22, .14), 1))
    c.drawOval(skia.Rect(-4.5 * S, 99 * S, 0 * S, 106 * S), P_((.7, .55, .35), .55))
    c.restore()
    # lip ring + waist band
    c.drawOval(skia.Rect(-45 * S, 88 * S, 45 * S, 100 * S), P_((1, .86, .55), .55, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2))
    c.drawRect(skia.Rect(-26.5 * S, BAND_Y - 13 * S, 26.5 * S, BAND_Y + 13 * S), P_((.24, .15, .06), .78))
    c.drawRect(skia.Rect(-26.5 * S, BAND_Y - 13 * S, 26.5 * S, BAND_Y - 11.5 * S), P_((1, .86, .55), .5))
    c.drawRect(skia.Rect(-26.5 * S, BAND_Y + 11.5 * S, 26.5 * S, BAND_Y + 13 * S), P_((1, .86, .55), .5))
    text(c, f"{b['lab'][0]}{b['lab'][1]}", 0, BAND_Y + 8 * S, F_LAB, CREAM, .97)
    c.restore()

def ripples(c, b, t):
    """strike flash at the lip + expanding sound rings (world space, drawn above the bells)"""
    if b["odd"]: return
    for ts, side in STR[B.index(b)]:
        a = t - ts
        if a < -.01 or a > .75: continue
        th = ang(b, ts)
        rr = math.radians(th)
        # contact point: the lip on the side the clapper hits (opposite to tilt)
        lx, ly = -side * 41 * S, 90 * S
        px = b["x"] + lx * math.cos(rr) - ly * math.sin(rr)
        py = b["y"] + lx * math.sin(rr) + ly * math.cos(rr)
        if a < .16:
            g = 1 - a / .16
            c.drawCircle(b["x"] - side * 10, b["y"] + 55 * S, 62 * S * (1 + a * 1.5), P_((1, .85, .5), .30 * g, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
            c.drawCircle(px, py, 20 * S * (1 + a * 3), P_((1, .93, .7), .95 * g, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
        out_ang = math.degrees(math.atan2(py - (b["y"] + 60 * S), px - b["x"]))
        for k in range(3):
            aa = a - k * .1
            if aa < 0 or aa > .45: continue
            rad = 14 + aa * 210
            al = .95 * (1 - aa / .45) ** 1.2
            ob = skia.Rect(px - rad, py - rad, px + rad, py + rad)
            c.drawArc(ob, out_ang - 50, 100, False,
                      P_((1, .92, .7), al, Style=skia.Paint.kStroke_Style, StrokeWidth=4.6, StrokeCap=skia.Paint.kRound_Cap))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH BELL", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER RINGS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s) + 2 * (len(s) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for b in B: draw_bell(c, b, t)
        c.save(); c.clipRect(skia.Rect(100, 470, 980, 1515))
        for b in B: ripples(c, b, t)
        c.restore()
        yb = 1566
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1648, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def ding(f0, seed, dur=1.1):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    parts = ((.5, 2.6, .35), (1, 3.4, .8), (1.19, 5, .35), (1.5, 6, .3), (2, 7, .28), (2.51, 10, .16), (3.0, 13, .1))
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + rg.uniform(0, 6)) * np.exp(-t * d) for m, d, a in parts)
    nz = rg.standard_normal(len(t)) * np.exp(-t * 500) * .25
    return (s + nz) * np.minimum(1, t * 5000)
def clonk(f0, seed, dur=.28):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 22) + .3 * np.sin(2 * np.pi * f0 * 2.3 * t) * np.exp(-t * 40)
    return (s + rg.standard_normal(len(t)) * np.exp(-t * 300) * .3) * np.minimum(1, t * 4000)

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, b in enumerate(B):
        for ts, side in STR[k]:
            if 0 <= ts < LOOP: ev.append((ts, k))
    lt = np.array([e[0] for e in ev])
    for tt, k in ev:
        b = B[k]
        dens = math.sqrt(max(1, (np.abs(lt - tt) < .25).sum()))
        if b["odd"]:
            m.add(clonk(150.0, k * 100 + int(tt * 50)), tt + .05, .55 / dens * 2.2, b["x"])
        else:
            m.add(ding(note(8 - b["r"] // 2 + (b["i"] % 2) * 2, 261.63), k * 100 + int(tt * 50)), tt, .42 / dens, b["x"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_bells.mp4"))
