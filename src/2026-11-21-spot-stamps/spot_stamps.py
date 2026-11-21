"""SPOT IT v3 (18:00, 2026-11-21): WHICH STAMP / IS BACKWARDS? 64 identical rubber stamps (walnut knob, brass
collar, dark rubber foot) over FOUR SHEETS of cream paper (a 2x2 of 4x4 sheets with a gutter between them;
columns A-H across the top, rows 1-8 on the left, no in-cell labels). Every stamp
slams down on a 2.4 s or 3.0 s cycle from a random phase, lifts high, and leaves a fresh rust-ink "R" that fades
about a second after the stamp lifts (so it only shows briefly every 2.4-3 s). ONE stamp always prints the R MIRRORED. Rule type: mirror (it prints backwards).
Sound: rubber-on-paper thump per hit (pentatonic by row, panned by x, density-normalised) + paper slap;
the odd stamp gives a higher hollow wooden tock (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/stamps"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
CW, CH = 100.0, 116.0      # cell size
GX, GY = 22.0, 26.0        # gutter between sheets
X0 = 540 - (8 * CW + GX) / 2
Y0 = float(os.environ.get("Y0", "540"))
LIFT = float(os.environ.get("LIFT", "50"))
PCT = int(os.environ.get("PCT", "15"))
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))

def cell_xy(i, r):
    x = X0 + i * CW + (GX if i >= 4 else 0) + CW / 2
    y = Y0 + r * CH + (GY if r >= 4 else 0) + CH / 2
    return x, y

ST = []
for r in range(8):
    for i in range(8):
        x, y = cell_xy(i, r)
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = 2.4 if (odd or rng.random() < .55) else 3.0
        ST.append(dict(lab=lab, odd=odd, x=x, y=y, r=r, i=i, P=P, ph=rng.uniform(0, 1),
                       rot=rng.uniform(-6, 6)))
print(len(ST), "stamps")
assert sum(s["odd"] for s in ST) == 1

T_DOWN, T_HOLD, T_UP = .16, .12, .34          # descend, press, rise
def phase(s, t):
    return ((t / s["P"] + s["ph"]) % 1.0) * s["P"]
def height(s, t):
    u = phase(s, t)
    if u < T_DOWN:                         # accelerate down
        k = u / T_DOWN; return LIFT * (1 - k * k)
    if u < T_DOWN + T_HOLD:
        return -1.5 * math.sin(math.pi * (u - T_DOWN) / T_HOLD)    # little squish
    if u < T_DOWN + T_HOLD + T_UP:
        k = (u - T_DOWN - T_HOLD) / T_UP; return LIFT * (1 - (1 - k) ** 3) * 1.06
    k = (u - T_DOWN - T_HOLD - T_UP) / (s["P"] - T_DOWN - T_HOLD - T_UP)
    return LIFT * (1.06 - .06 * ss(k * 3)) + 3 * math.sin(2 * math.pi * k)  # settle + bob, hover
def ink(s, t):
    """alpha of the print: fresh after the hit, fades out before the next one"""
    u = phase(s, t)
    if u < T_DOWN: return 0.0
    age = u - T_DOWN
    fade0, fade1 = float(os.environ.get("F0", "1.0")), float(os.environ.get("F1", "1.5"))
    if age < fade0: return 1.0
    return max(0.0, 1 - (age - fade0) / (fade1 - fade0))
def hits(s, t0=-3.0, t1=LOOP + 3):
    out = []
    for k in range(int(t0 / s["P"]) - 2, int(t1 / s["P"]) + 3):
        tt = (k - s["ph"]) * s["P"] + T_DOWN
        if t0 <= tt <= t1: out.append(tt)
    return out
HITS = [hits(s) for s in ST]

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_LAB = font(TF_SB, 17); F_ROW = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36); F_INK = font(TF_BOLD, 40)
INK = (.74, .27, .12)
PY = 30.0                  # print centre offset below the cell centre
R_W = F_INK.measureText("R")

WOOD = skia.GradientShader.MakeLinear([(-13, 0), (13, 0)],
    [c4((.30, .17, .09)).toColor(), c4((.62, .40, .23)).toColor(), c4((.36, .21, .11)).toColor()], [0, .38, 1])
BRASS = skia.GradientShader.MakeLinear([(-10, 0), (10, 0)],
    [c4((.45, .30, .12)).toColor(), c4((1, .86, .55)).toColor(), c4((.62, .43, .18)).toColor()], [0, .35, 1])

def draw_paper(c):
    for qi in range(2):
        for qr in range(2):
            x0 = X0 + qi * (4 * CW + GX); y0 = Y0 + qr * (4 * CH + GY)
            rc = skia.Rect(x0 - 6, y0 - 4, x0 + 4 * CW + 6, y0 + 4 * CH + 4)
            c.drawRRect(skia.RRect.MakeRectXY(rc.makeOffset(0, 8), 6, 6),
                        P_((0, 0, 0), .55, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
            g = skia.GradientShader.MakeLinear([(rc.left(), rc.top()), (rc.right(), rc.bottom())],
                [c4((.95, .90, .80)).toColor(), c4((.88, .81, .69)).toColor()], [0, 1])
            c.drawRRect(skia.RRect.MakeRectXY(rc, 6, 6), skia.Paint(AntiAlias=True, Shader=g))
            for k in range(1, 4):   # faint cell guides
                c.drawLine(x0 + k * CW, y0 + 6, x0 + k * CW, y0 + 4 * CH - 6, P_((.55, .45, .33), .16, StrokeWidth=1.2))
                c.drawLine(x0 + 6, y0 + k * CH, x0 + 4 * CW - 6, y0 + k * CH, P_((.55, .45, .33), .16, StrokeWidth=1.2))
    for s in ST if os.environ.get("LABELS") else []:
        text(c, f"{s['lab'][0]}{s['lab'][1]}", s["x"] - CW / 2 + 8, s["y"] - CH / 2 + 20, F_LAB, (.42, .32, .22), .75, align="left")

def draw_print(c, s, t):
    a = ink(s, t)
    if a <= .01: return
    c.save(); c.translate(s["x"], s["y"] + PY); c.rotate(s["rot"])
    if s["odd"]: c.scale(-1, 1)
    p = P_(INK, .92 * a)
    c.drawString("R", -R_W / 2, 14.5, F_INK, p)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-23, -22, 23, 22), 5, 5),
                P_(INK, .8 * a, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2))
    c.restore()

def draw_stamp(c, s, t):
    h = height(s, t)
    x, y = s["x"], s["y"] + PY
    hn = max(0, h) / (LIFT * 1.06)
    c.drawOval(skia.Rect(x - 26 - 6 * hn, y - 10 + 3 * hn, x + 26 + 6 * hn, y + 20 + 5 * hn),
               P_((.18, .10, .05), .45 - .25 * hn, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3 + 6 * hn)))
    b = y + 23 - h          # bottom of the rubber foot
    c.save(); c.translate(x, b); c.rotate(s["rot"] * .8 * hn)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-26, -7, 26, 0), 2, 2), P_((.16, .11, .09), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-28, -17, 28, -6), 3, 3), P_((.40, .24, .13), 1))
    c.drawRect(skia.Rect(-28, -17, 28, -14.5), P_((.66, .45, .27), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-10, -24, 10, -16), 2, 2), skia.Paint(AntiAlias=True, Shader=BRASS))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-6, -38, 6, -23), 3, 3), skia.Paint(AntiAlias=True, Shader=WOOD))
    c.drawCircle(0, -47, 13, skia.Paint(AntiAlias=True, Shader=WOOD))
    c.drawCircle(-4, -52, 4.5, P_((1, .85, .6), .3, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2.5)))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH STAMP", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "IS BACKWARDS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(8):
            x, _ = cell_xy(i, 0)
            text(c, LET[i], x, Y0 - 14, F_ROW, AMBER, .9)
        for r in range(8):
            _, y = cell_xy(0, r)
            text(c, str(r + 1), X0 - 24, y + 11, F_ROW, AMBER, .9)
        draw_paper(c)
        for s in ST: draw_print(c, s, t)
        for s in ST: draw_stamp(c, s, t)      # row order: lower rows drawn later (in front)
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
def thump(f0, seed, dur=.32):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    body = np.sin(2 * np.pi * f0 * t * (1 + .25 * np.exp(-t * 60))) * np.exp(-t * 26)
    body += .35 * np.sin(2 * np.pi * f0 * 2.02 * t) * np.exp(-t * 45)
    slap = rg.standard_normal(len(t)) * np.exp(-t * 160) * .55
    return (body + slap) * np.minimum(1, t * 3000)
def tock(f0, seed, dur=.25):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 30) + .5 * np.sin(2 * np.pi * f0 * 1.51 * t) * np.exp(-t * 38)
    return (s + rg.standard_normal(len(t)) * np.exp(-t * 260) * .3) * np.minimum(1, t * 4000)

def audio(path):
    m = Mix(LOOP + 4)
    ev = [(tt, k) for k in range(len(ST)) for tt in HITS[k] if 0 <= tt < LOOP]
    lt = np.array([e[0] for e in ev])
    for tt, k in ev:
        s = ST[k]
        dens = math.sqrt(max(1, (np.abs(lt - tt) < .2).sum()))
        if s["odd"]:
            m.add(tock(520.0, k * 100 + int(tt * 50)), tt, .55 / dens * 2.0, s["x"])
        else:
            m.add(thump(note(7 - s["r"] // 2 + (s["i"] % 3), 65.41), k * 100 + int(tt * 50)), tt, .55 / dens, s["x"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_stamps.mp4"))
