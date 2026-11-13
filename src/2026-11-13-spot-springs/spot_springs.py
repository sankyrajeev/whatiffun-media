"""SPOT IT (13:00): 56 hanging springs in STAGGERED rows (8 brass rails, 7 springs each, even rows shifted
half a step), each holding a lacquered slotted weight. They bob in a chevron wave that rolls down and out
from the centre line, weights coloured by their place in the wave. One weight (C5) is a little heavier:
it bobs 11 times per 12 s loop instead of 12 (omega ~ 1/sqrt(m)) and, honestly, sags a hair lower
(static stretch g/omega^2). It drifts out of its wave, is fully opposite at 6 s and back in step at the loop.
Sound: a soft springy 'boing' tick per spring at the bottom of each bob (pentatonic by row, panned by x);
C5's is a lower, ringier metal boing (audio clue). 13:00 = A/B countdown variant: slim 12 -> 0 ring above.
All motion uses integer cycles per loop, so frame 0 == frame N (seamless)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spots"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 7, 8
LETTERS = "ABCDEFG"
DX, RAIL0, RP = 112, 652, 118
X0 = 540 - (DX * (NC - 1) + DX / 2) / 2
ODD = (2, 4)                     # column C, row 5 (an unshifted row, so the top letters line up)
NAT, STRETCH, AMP = 34.0, 14.0, 24.0
N_NORM, N_ODD = 12, 11

def pos(c, r):
    return X0 + c * DX + (DX / 2 if r % 2 else 0), RAIL0 + r * RP
def phase0(c, r):
    x, y = pos(c, r)
    return 2 * math.pi * (abs(x - 540) / 1500 + (y - RAIL0) / 640)
PMAX = 2 * math.pi * ((DX * 3 + DX / 2) / 1500 + 7 * RP / 640)
def disp(c, r, t):
    n = N_ODD if (c, r) == ODD else N_NORM
    return AMP * math.sin(2 * math.pi * n * t / LOOP - phase0(c, r))
def rest(c, r):
    return NAT + STRETCH * ((N_NORM / N_ODD) ** 2 if (c, r) == ODD else 1)

BG = background(1080)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
F_LBL = font(TF_MONO, 26); F_NUM = font(TF_MONO, 24); F_TINY = font(TF_MONO, 13)
F_CD = font(TF_SERIF, 34)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
PLUS = skia.Paint(BlendMode=skia.BlendMode.kPlus)
def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()

def colour(c, r):
    u = phase0(c, r) / PMAX
    return hsv(38 - 160 * u, .58, 1.0)   # amber -> coral -> magenta -> violet -> blue along the wave

def draw_rail(c, y):
    c.drawRect(skia.Rect(150, y - 9, 930, y + 3), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(150, y - 6, 930, y), 3, 3), skia.Paint(AntiAlias=True,
        Shader=skia.GradientShader.MakeLinear([(0, y - 6), (0, y)], [rgb((1, .88, .6)), rgb((.78, .55, .27)), rgb((.38, .24, .1))], [0, .45, 1])))
    for xe in (150, 930):
        c.drawCircle(xe, y - 3, 6, skia.Paint(AntiAlias=True, Color4f=rgb((.6, .42, .2))))

def draw_spring(c, x, ytop, ybot, tint):
    turns = 9; n = turns * 14
    L = ybot - ytop
    hook = 5
    y0, y1 = ytop + hook, ybot - 4
    pts = [(x + 9.5 * math.sin(2 * math.pi * turns * k / n), y0 + (y1 - y0) * k / n, math.cos(2 * math.pi * turns * k / n)) for k in range(n + 1)]
    back = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0, StrokeCap=skia.Paint.kRound_Cap,
                      Color4f=skia.Color4f(.42, .43, .46, 1))
    front = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.3, StrokeCap=skia.Paint.kRound_Cap)
    for k in range(n):
        (xa, ya, za), (xb, yb, zb) = pts[k], pts[k + 1]
        if za + zb < 0: c.drawLine(xa, ya, xb, yb, back)
    c.drawLine(x, ytop, x, y0, skia.Paint(AntiAlias=True, StrokeWidth=2.2, Color4f=skia.Color4f(.75, .76, .8, 1)))
    for k in range(n):
        (xa, ya, za), (xb, yb, zb) = pts[k], pts[k + 1]
        if za + zb >= 0:
            sh = .62 + .38 * (za + zb) / 2
            front.setColor(rgb((.86 * sh + .1 * tint[0], .88 * sh + .08 * tint[1], .93 * sh + .08 * tint[2])))
            c.drawLine(xa, ya, xb, yb, front)
    c.drawLine(x, y1, x, ybot + 2, skia.Paint(AntiAlias=True, StrokeWidth=2.2, Color4f=skia.Color4f(.75, .76, .8, 1)))

def draw_weight(c, x, y, col):
    # y = top of weight (hook). Slotted lacquered cylinder, side view with a hint of top face
    rx, h, ry = 15, 26, 4.2
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - rx + 3, y + 6, x + rx + 5, y + h + 8), 5, 5),
                skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    body = skia.Path(); body.addRect(skia.Rect(x - rx, y + ry, x + rx, y + h)); body.addOval(skia.Rect(x - rx, y + h - ry, x + rx, y + h + ry))
    dk = [v * .38 for v in col]; md = [v * .8 for v in col]; hi = [min(1, v * .55 + .5) for v in col]
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - rx, 0), (x + rx, 0)], [rgb(dk), rgb(md), rgb(hi), rgb(md), rgb(dk)], [0, .22, .38, .7, 1])))
    for yy in (y + 11, y + 18):   # stacked slotted plates
        c.drawLine(x - rx, yy, x + rx, yy, skia.Paint(AntiAlias=True, StrokeWidth=1.1, Color4f=skia.Color4f(0, 0, 0, .35)))
        c.drawLine(x - rx, yy + 1.2, x + rx, yy + 1.2, skia.Paint(AntiAlias=True, StrokeWidth=.8, Color4f=skia.Color4f(1, 1, 1, .12)))
    c.drawOval(skia.Rect(x - rx, y, x + rx, y + 2 * ry), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - rx, 0), (x + rx, 0)], [rgb(md), rgb(hi), rgb(md)], [0, .4, 1])))
    c.drawRect(skia.Rect(x - 1.5, y - 3, x + 1.5, y + ry), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.85, .85, .88, 1)))
    c.drawRect(skia.Rect(x - rx + 4, y + ry + 2, x - rx + 7, y + h - 2), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .22)))

def countdown(c, t):
    cx, cy, R = 540, 538, 30
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
        text(c, "One weight is", W / 2, 278, F_Q, CREAM, .97)
        text(c, "a little heavier.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
        fi = font(TF_SERIF_I, 32); fe = font(TF_EMOJI, 26)
        s1 = "Like it if you found it "
        w1 = fi.measureText(s1); w2 = fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, 466, fi, CREAM, .5, align="left")
        c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))
        countdown(c, t)
        for ci in range(NC):
            x, _ = pos(ci, 0)
            text(c, LETTERS[ci], x, 616, F_LBL, CREAM, .5)
        for r in range(NR):
            _, y = pos(0, r)
            draw_rail(c, y)
            text(c, str(r + 1), 118, y + 40, F_NUM, CREAM, .42)
            for ci in range(NC):
                x, y = pos(ci, r)
                if r > 0: text(c, LETTERS[ci], x + 21, y + 18, F_TINY, CREAM, .3)
                yb = y + rest(ci, r) + disp(ci, r, t)
                col = colour(ci, r)
                draw_spring(c, x, y, yb, col)
                draw_weight(c, x, yb, col)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def boing(f0, dur=.22, ring=False):
    t = np.arange(int(dur * SR)) / SR
    fm = f0 * (1 + .05 * np.exp(-t * 30) * np.sin(2 * np.pi * 26 * t))
    ph = 2 * np.pi * np.cumsum(fm) / SR
    s = np.sin(ph) * np.exp(-t * (14 if not ring else 6))
    if ring:
        s += .5 * np.sin(2.76 * ph) * np.exp(-t * 9) + .25 * np.sin(5.4 * ph) * np.exp(-t * 14)
    n = np.random.default_rng(int(f0 * 7)).standard_normal(len(t)) * np.exp(-t * 1500) * .25
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 3000)

def audio(path):
    m = Mix(LOOP + 1.0)
    # count simultaneous events per frame to normalise density
    ev = []
    for r in range(NR):
        for ci in range(NC):
            n = N_ODD if (ci, r) == ODD else N_NORM
            # bottom of bob: sin(...) = 1  ->  2*pi*n*t/LOOP - p0 = pi/2 + 2*pi*k
            for k in range(-2, n + 2):
                tt = (math.pi / 2 + phase0(ci, r) + 2 * math.pi * k) * LOOP / (2 * math.pi * n)
                if 0 <= tt < LOOP: ev.append((tt, ci, r))
    times = np.array([e[0] for e in ev])
    for tt, ci, r in ev:
        x, _ = pos(ci, r)
        dens = ((np.abs(times - tt) < .06) | (np.abs(times - tt) > LOOP - .06)).sum()
        g = .5 / math.sqrt(dens)
        if (ci, r) == ODD:
            m.add(boing(note(r, 261.63) * .5, .5, ring=True), tt, .3, x)
        else:
            m.add(boing(note(r + 4, 261.63) * (1 + .004 * ci)), tt, g, x)
    # fold the tail past the loop end back onto its start (seamless)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    # soft periodic air bed
    n = m.N; rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 400) / 350) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/S_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_springs.mp4"))
