"""SPOT IT (18:00, BREAKS PHYSICS + normal field + COUNTDOWN): 54 walnut seesaws in STAGGERED ROWS (brickwork:
columns A-F zig-zag a quarter-step left/right, rows 1-9). A diagonal wave rolls down from the top-left corner and rocks
every seesaw +-20 deg (4 rocks per 12 s loop), and a glossy coloured block on each plank slides DOWNHILL to the low
end each time it tips (real sliding: gravity along the plank, static + kinetic friction, a soft end-stop bounce),
landing with a wooden tock. The odd one (D6) breaks physics: its block slides UPHILL and parks at the raised end.
All seesaws share one steady-state sim shifted by their ripple phase (whole cycles per loop: seamless).
Sound: a wooden tock per block landing (pentatonic by row, panned, density-normalised) over a soft room bed;
the odd one's landing is a small glassy ping (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spots"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 5, 9
LET = "ABCDE"
S = 168
X0 = 540 - 2 * S
STAG = 28
ROW0, RS = 694, 108
ODD = (LET.index(os.environ.get("OL", "D")), int(os.environ.get("ON", "6")) - 1)
NCYC = 5
P = LOOP / NCYC
TH0 = math.radians(float(os.environ.get("TILT", "27")))
LB = 76.0                       # plank half-length
BW, BH = 44.0, 34.0             # block
TRAV = LB - 8 - BW / 2           # block centre travel
SRC = (40.0, 470.0)              # ripple source (top-left, off the grid)
LAM = 1000.0

def pos(c, r):
    return X0 + c * S + (STAG if r % 2 else -STAG), ROW0 + r * RS
def phase(c, r):
    return 2 * math.pi * (0.10 * r + 0.08 * c)     # a clean diagonal wave rolling down from the top-left
def tilt(c, r, t):
    return TH0 * math.sin(2 * math.pi * t / P - phase(c, r))

# ---- one steady-state sliding sim (phase 0), reused with time shifts ----
def sim():
    g, mus, muk, e = 8000.0, math.tan(math.radians(5)), .14, .22
    dt = 1 / 2400
    n = int(round(P / dt))
    s, v = -TRAV, 0.0
    for lap in range(6):
        ss_, hits = np.zeros(n), []
        for i in range(n):
            t = i * dt
            th = TH0 * math.sin(2 * math.pi * t / P)
            gs, gn = g * math.sin(th), g * math.cos(th)
            if v == 0 and abs(gs) <= mus * gn:
                a = 0.0
            else:
                dirn = np.sign(v) if v != 0 else np.sign(gs)
                a = gs - muk * gn * dirn
                if v != 0 and np.sign(v + a * dt) != np.sign(v) and abs(gs) <= mus * gn:
                    v, a = 0.0, 0.0
            v += a * dt; s += v * dt
            if abs(s) > TRAV:
                hv = abs(v); s = math.copysign(TRAV, s)
                v = -e * v if hv > 60 else 0.0
                if hv > 25: hits.append((t, math.copysign(1, s), hv))
            ss_[i] = s
    return np.arange(n) * dt, ss_, hits

ST, SS, HITS = sim()
def slide(c, r, t):
    tt = (t - phase(c, r) * P / (2 * math.pi)) % P
    s = float(np.interp(tt, ST, SS, period=P))
    return -s if (c, r) == ODD else s

BG = background(1060)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
F_LBL = font(TF_MONO, 34)
F_CD = font(TF_SERIF, 34)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
PH = [phase(c, r) for c in range(NC) for r in range(NR)]
PMIN, PMAX = min(PH), max(PH)
def colour(c, r):
    u = (phase(c, r) - PMIN) / (PMAX - PMIN)
    return hsv((38 - 300 * u) % 360, .78, 1.0)     # amber -> coral -> magenta -> violet -> blue -> teal
COLS = {(c, r): colour(c, r) for c in range(NC) for r in range(NR)}

WOOD = [rgb((.36, .22, .12)), rgb((.62, .42, .24)), rgb((.44, .28, .15)), rgb((.25, .15, .08))]
def draw_seesaw(cv, c, r, t):
    x, y = pos(c, r)
    th = tilt(c, r, t)
    col = COLS[(c, r)]
    # ground shadow + base
    cv.drawOval(skia.Rect(x - 60, y + 31, x + 60, y + 41), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    # fulcrum (brass triangle)
    p = skia.Path(); p.moveTo(x, y + 2); p.lineTo(x - 20, y + 35); p.lineTo(x + 20, y + 35); p.close()
    cv.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - 20, 0), (x + 20, 0)], [rgb((.45, .32, .14)), rgb((.95, .78, .45)), rgb((.55, .38, .16))], [0, .45, 1])))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 30, y + 33, x + 30, y + 39), 2, 2),
                 skia.Paint(AntiAlias=True, Color4f=rgb((.3, .2, .1))))
    cv.save(); cv.translate(x, y); cv.rotate(math.degrees(th))
    # plank
    pc = [rgb(tuple(v * k for v in col)) for k in (.55, .95, .7, .35)]
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-LB, -5, LB, 9), 5, 5), skia.Paint(AntiAlias=True,
                 Shader=skia.GradientShader.MakeLinear([(0, -5), (0, 9)], pc, [0, .3, .7, 1])))
    cv.drawLine(-LB + 3, -3.2, LB - 3, -3.2, skia.Paint(AntiAlias=True, StrokeWidth=1, Color4f=skia.Color4f(1, .9, .7, .25)))
    # brass end stops
    for sx in (-LB + 3, LB - 8):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx, -16, sx + 5, -4), 1.5, 1.5),
                     skia.Paint(AntiAlias=True, Color4f=rgb((.9, .72, .4))))
    cv.drawCircle(0, 1, 3, skia.Paint(AntiAlias=True, Color4f=rgb((.95, .8, .5))))
    # block
    s = slide(c, r, t)
    cv.drawOval(skia.Rect(s - 38, -32, s + 38, 8), skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                Color4f=skia.Color4f(*col, .22), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
    hot = tuple(min(1, v * .45 + .6) for v in col); dk = tuple(v * .5 for v in col)
    br = skia.Rect(s - BW / 2, -4 - BH, s + BW / 2, -4)
    cv.drawRRect(skia.RRect.MakeRectXY(br, 5, 5), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, -4 - BH), (0, -4)], [rgb(hot), rgb(col), rgb(dk)], [0, .45, 1])))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(s - BW / 2 + 5, -4 - BH + 4, s + BW / 2 - 5, -4 - BH + 11), 4, 4),
                 skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .45)))
    cv.restore()

def countdown(c, t):
    cx, cy, R = 540, 536, 30
    left = LOOP - t
    c.drawCircle(cx, cy, R, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(*CREAM, .12)))
    c.drawArc(skia.Rect(cx - R, cy - R, cx + R, cy + R), -90, -360 * left / LOOP, False,
              skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap,
                         Color4f=skia.Color4f(*AMBER, .75)))
    text(c, str(int(math.ceil(left - 1e-6)) if left > 1e-6 else 0), cx, cy + 12, F_CD, CREAM, .8)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
        text(c, "One of these", W / 2, 278, F_Q, CREAM, .97)
        text(c, "breaks physics.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 40), CREAM, .72)
        fi = font(TF_SERIF_I, 35); fe = font(TF_EMOJI, 28)
        s1 = "Like it if you found it "
        w1 = fi.measureText(s1); w2 = fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, 466, fi, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))
        countdown(c, t)
        for ci in range(NC):
            text(c, LET[ci], X0 + ci * S, 624, F_LBL, CREAM, .66)
        for r in range(NR):
            text(c, str(r + 1), 74, ROW0 + r * RS + 22, F_LBL, CREAM, .6)
            for ci in range(NC):
                draw_seesaw(c, ci, r, t)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def tock(f0, dur=.3, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t * (1 + .03 * np.exp(-t * 50))) * np.exp(-t * 26)
         + .35 * bright * np.sin(2 * np.pi * f0 * 2.32 * t) * np.exp(-t * 40))
    n = np.random.default_rng(int(f0)).standard_normal(len(t)) * np.exp(-t * 1400) * .35
    return (s + np.diff(n, prepend=0) * .5) * np.minimum(1, t * 5000)
def ping(f0, dur=.45):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 9) + .4 * np.sin(2 * np.pi * f0 * 2.76 * t + 1) * np.exp(-t * 16)
    return s * np.minimum(1, t * 6000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for r in range(NR):
        for ci in range(NC):
            sh = phase(ci, r) * P / (2 * math.pi)
            for k in range(-1, NCYC + 2):
                for (ht, side, hv) in HITS:
                    tt = ht + sh + k * P
                    if 0 <= tt < LOOP: ev.append((tt, ci, r, hv))
    times = np.array([e[0] for e in ev])
    vmax = max(h[2] for h in HITS)
    for tt, ci, r, hv in ev:
        x = pos(ci, r)[0]
        dens = ((np.abs(times - tt) < .05) | (np.abs(times - tt) > LOOP - .05)).sum()
        g = .55 / math.sqrt(dens) * (.35 + .65 * hv / vmax)
        if (ci, r) == ODD:
            m.add(ping(note(r + 9, 261.63)), tt, .30 * (.35 + .65 * hv / vmax), x)
        else:
            m.add(tock(note(NR - 1 - r + 2, 261.63) * (1 + .004 * ci)), tt, g, x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 300) / 260) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .04; m.R += np.roll(bed, 5000) * .04
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/S_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "sim":
        print("hits", [(round(a, 3), b, round(c)) for a, b, c in HITS])
        i = np.linspace(0, len(SS) - 1, 25).astype(int); print([round(SS[j]) for j in i])
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_seesaws.mp4"))
