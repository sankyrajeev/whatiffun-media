"""SPOT IT (13:00, normal field + COUNTDOWN arm): 36 glowing paper lanterns hang from 6 DRAPED GARLANDS
(catenary cords strung across the frame, rows 1-6; lanterns in columns A-F). Every lantern swings in a
circle (its size swelling as a slow wave rolls diagonally across the garlands twice per loop) (a conical pendulum), seen slightly from above: sideways sway + nearer/brighter at the front. The
circling phase rolls along each garland and down the rows, so the field is a travelling rainbow snake.
The odd one (E4) hangs on a shorter cord: a conical pendulum's period goes as sqrt(L), so it circles 9 times
per 12 s loop instead of 8 (cord (12/13)^2 as long, so it honestly hangs a few px higher). It drifts ahead of
its wave, is fully opposite at 6 s and back in step at the loop (all motion = whole cycles per loop: seamless).
Sound: a soft bamboo/glass tinkle per lantern as it swings through the front of its circle (pentatonic by
row, panned by x, density-normalised) over a faint night-air bed; the odd one's is a low hollow wooden tock."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spotl"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 6, 6
LET = "ABCDEF"
XS = [210 + c * 132 for c in range(NC)]
ROW0, RS = 640, 158
SAG = 34
ODD = (LET.index(os.environ.get("OL", "E")), int(os.environ.get("ON", "4")) - 1)
N_NORM, N_ODD = 8, 9
CORD = 36.0
AMP = float(os.environ.get('AMP', '38'))                       # radius of the swing circle (px)
DEPTH_Y = 15.0                    # back of the circle sits a little higher (camera slightly above)

def cord_y(x, r):                # draped garland (parabolic catenary)
    u = (x - 540) / 440
    return ROW0 + r * RS + SAG * (1 - u * u)
def phase0(c, r):
    return 2 * math.pi * (c / NC * 1.0 + r * 0.14)
PMAX = 2 * math.pi * ((NC - 1) / NC + (NR - 1) * 0.14)
def theta(c, r, t):
    n = N_ODD if (c, r) == ODD else N_NORM
    return 2 * math.pi * n * t / LOOP - phase0(c, r)
def amp(c, r, t):                # a slow swell rolls diagonally across the garlands twice per loop
    u = 2 * math.pi * (2 * t / LOOP - XS[c] / 1100 - r * 0.11)
    return AMP * (.55 + .45 * (.5 + .5 * math.cos(u)))
def cord(c, r):
    return CORD * ((N_NORM / N_ODD) ** 2 if (c, r) == ODD else 1)

BG = background(1080)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
F_LBL = font(TF_MONO, 34); F_NUM = font(TF_MONO, 34)
F_CD = font(TF_SERIF, 34)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
PLUS = skia.Paint(BlendMode=skia.BlendMode.kPlus)
def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()

def colour(c, r):
    u = (phase0(c, r) / PMAX)
    return hsv((14 - 290 * u) % 360, .68, 1.0)   # red -> magenta -> violet -> blue -> teal along the wave

COLS = {(c, r): colour(c, r) for c in range(NC) for r in range(NR)}
GLOWS = {k: glow(tuple(min(1, v * .9 + .1) for v in col), 52, .55) for k, col in COLS.items()}
SEED = {(c, r): (c * 7.3 + r * 3.1) for c in range(NC) for r in range(NR)}

def flicker(c, r, t):
    s = SEED[(c, r)]
    return 1 + .05 * math.sin(2 * math.pi * 5 * t / LOOP + s) + .035 * math.sin(2 * math.pi * 11 * t / LOOP + 2.1 * s)

def draw_garland(c, r):
    p = skia.Path(); p.moveTo(110, cord_y(110, r))
    for x in range(120, 981, 20): p.lineTo(x, cord_y(x, r))
    c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
               Color4f=skia.Color4f(0, 0, 0, .4), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
               Color4f=skia.Color4f(.55, .42, .28, 1)))
    for xe in (110, 970):
        c.drawCircle(xe, cord_y(xe, r), 5, skia.Paint(AntiAlias=True, Color4f=rgb((.72, .52, .26))))

def draw_lantern(cv, ci, r, t):
    hx = XS[ci]; hy = cord_y(hx, r)
    th = theta(ci, r, t)
    A = amp(ci, r, t)
    dx = A * math.sin(th)                 # sideways
    dz = math.cos(th)                       # +1 = front (nearest the viewer)
    L = cord(ci, r)
    x = hx + dx; ytop = hy + L + DEPTH_Y * dz * A / AMP
    sc = 1 + .06 * dz * A / AMP
    col = COLS[(ci, r)]
    br = flicker(ci, r, t) * (.9 + .12 * dz * A / AMP)
    # cord
    cv.drawLine(hx, hy, x, ytop, skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color4f=skia.Color4f(.62, .5, .36, .9)))
    rx, ry = 30 * sc, 34 * sc
    cy = ytop + 7 * sc + ry
    # glow halo (additive)
    gp = skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=min(1, .75 * br))
    blit(cv, GLOWS[(ci, r)], x, cy, 1.0 + .06 * dz, gp)
    # body
    hot = tuple(min(1, v * .35 + .72 * br) for v in col)
    mid = tuple(min(1, v * .95 * br) for v in col)
    dk = tuple(v * .42 for v in col)
    body = skia.Rect(x - rx, cy - ry, x + rx, cy + ry)
    cv.drawOval(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - 4 * dx / AMP, cy + 3), rx * 1.12, [rgb(hot), rgb(mid), rgb(dk)], [0, .55, 1])))
    # paper ribs (rotate with the swing)
    cv.save(); clip = skia.Path(); clip.addOval(body); cv.clipPath(clip, doAntiAlias=True)
    for k in range(8):
        a = th * .5 + k * math.pi / 4
        if math.cos(a) <= 0: continue
        s = math.sin(a)
        p = skia.Path(); p.addOval(skia.Rect(x - abs(s) * rx, cy - ry, x + abs(s) * rx, cy + ry))
        cv.save(); cv.clipRect(skia.Rect(x, cy - ry - 1, x + rx + 2, cy + ry + 1) if s > 0 else
                               skia.Rect(x - rx - 2, cy - ry - 1, x, cy + ry + 1))
        cv.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3,
                    Color4f=skia.Color4f(*[v * .35 for v in col], .55 * math.cos(a))))
        cv.restore()
    # horizontal paper ring lines
    for yy in (-.5, 0, .5):
        w = rx * math.sqrt(1 - yy * yy)
        cv.drawOval(skia.Rect(x - w, cy + yy * ry - 2.2, x + w, cy + yy * ry + 2.2), skia.Paint(
            AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1, Color4f=skia.Color4f(*[v * .4 for v in col], .35)))
    cv.restore()
    # caps (lacquered wood) top + bottom
    for yc, w in ((cy - ry + 1, 17 * sc), (cy + ry - 1, 15 * sc)):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - w, yc - 4.5 * sc, x + w, yc + 4.5 * sc), 2.5, 2.5),
                     skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                         [(x - w, 0), (x + w, 0)], [rgb((.16, .08, .05)), rgb((.5, .22, .12)), rgb((.14, .07, .04))], [0, .4, 1])))
    cv.drawLine(x, ytop, x, cy - ry - 3, skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color4f=skia.Color4f(.62, .5, .36, .9)))
    # tassel (lags the swing slightly)
    tx = x - 4 * math.sin(th - .5)
    yb = cy + ry + 4 * sc
    for k in (-2, 0, 2):
        cv.drawLine(x + k * .6, yb, tx + k, yb + 13, skia.Paint(AntiAlias=True, StrokeWidth=1.4,
                    Color4f=rgb(tuple(v * .7 for v in col), .85)))
    cv.drawCircle(x, yb, 2.6, skia.Paint(AntiAlias=True, Color4f=rgb((.7, .55, .25))))

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
        text(c, "One lantern hangs", W / 2, 278, F_Q, CREAM, .97)
        text(c, "on a shorter cord.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 40), CREAM, .72)
        fi = font(TF_SERIF_I, 35); fe = font(TF_EMOJI, 28)
        s1 = "Like it if you found it "
        w1 = fi.measureText(s1); w2 = fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, 466, fi, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))
        countdown(c, t)
        for ci in range(NC):
            text(c, LET[ci], XS[ci], 612, F_LBL, CREAM, .66)
        for r in range(NR):
            draw_garland(c, r)
            text(c, str(r + 1), 124, cord_y(124, r) + 66, F_NUM, CREAM, .62)
            order = sorted(range(NC), key=lambda ci: math.cos(theta(ci, r, t)))
            for ci in order:
                draw_lantern(c, ci, r, t)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def tinkle(f0, dur=.35):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 11) + .35 * np.sin(2 * np.pi * f0 * 2.71 * t + .6) * np.exp(-t * 20)
         + .15 * np.sin(2 * np.pi * f0 * 5.2 * t) * np.exp(-t * 34))
    n = np.random.default_rng(int(f0)).standard_normal(len(t)) * np.exp(-t * 2200) * .2
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 4000)
def tock(f0, dur=.4):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t * (1 + .02 * np.exp(-t * 40))) * np.exp(-t * 16) + .4 * np.sin(2 * np.pi * f0 * 1.58 * t) * np.exp(-t * 24)
    n = np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t * 900) * .3
    return (s + n) * np.minimum(1, t * 3000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for r in range(NR):
        for ci in range(NC):
            n = N_ODD if (ci, r) == ODD else N_NORM
            # front of the circle: theta = 2*pi*k
            for k in range(-2, n + 3):
                tt = (phase0(ci, r) + 2 * math.pi * k) * LOOP / (2 * math.pi * n)
                if 0 <= tt < LOOP: ev.append((tt, ci, r))
    times = np.array([e[0] for e in ev])
    for tt, ci, r in ev:
        x = XS[ci]
        dens = ((np.abs(times - tt) < .06) | (np.abs(times - tt) > LOOP - .06)).sum()
        g = .5 / math.sqrt(dens)
        if (ci, r) == ODD:
            m.add(tock(note(r, 261.63) * .5), tt, .34, x)
        else:
            m.add(tinkle(note(NR - 1 - r + 7, 261.63) * (1 + .003 * ci)), tt, g, x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 350) / 300) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/L_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_lanterns.mp4"))
