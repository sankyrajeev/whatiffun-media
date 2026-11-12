"""SPOT IT: 63 lacquered spinning tops (7 cols A-G x 9 rows), each leaning 20 deg and precessing,
their lean phases set by angle around the centre (D5) so the whole grid swirls like a pinwheel.
One top (B6) spins the other way, so it also precesses the other way: its left-right lean matches its
place in the swirl exactly, but it leans toward you when its neighbours lean away. 12 s seamless loop
(4 precessions, 9 spins per loop, all integers -> frame 0 == frame N)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spott"
COLS, ROWS = 7, 9
X0, X1, Y0, Y1 = 178, 902, 640, 1530          # tip (ground contact) of each top
LOOP = 12.0
TOTAL = int(LOOP * FPS)
ODD = (1, 5)                                  # column B, row 6
cw, rh = (X1 - X0) / (COLS - 1), (Y1 - Y0) / (ROWS - 1)
LETTERS = "ABCDEFG"
CC, CR = 3, 4                                 # swirl centre D5
P_CYC, S_CYC = 4, 9                           # precessions / spins per loop
ALPHA = math.radians(20)                      # lean
ELEV = math.radians(32)                       # camera looks down
R, H_DISC, H_STEM = 37, 30, 30
NSEG = 48
SECT = 6

def ang(c, r): return math.atan2((r - CR) * rh, (c - CC) * cw)
def rad(c, r): return math.hypot((c - CC) * cw, (r - CR) * rh) / cw
def phase0(c, r): return ang(c, r) + 0.55 * rad(c, r)         # pinwheel with a slight spiral twist
DELTA = -phase0(*ODD)                                          # start where the odd one looks just like its slot
def phase(c, r): return phase0(c, r) + DELTA
def sign(c, r): return -1 if (c, r) == ODD else 1
def phi(c, r, t):
    th = 2 * math.pi * P_CYC * t / LOOP + phase(c, r)
    return th if sign(c, r) > 0 else -th                      # odd: same cos (left-right), flipped depth

BG = background(1080)
F_LBL = font(TF_MONO, 24)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
KNOB = glass_ball((.95, .76, .44), 5.0)
CE, SE = math.cos(ELEV), math.sin(ELEV)
TH = np.linspace(0, 2 * math.pi, NSEG, endpoint=False)

def col_of(c, r):
    return hsv(math.degrees(ang(c, r)) + 200 + 40 * rad(c, r), .52, .95)

def proj(bx, by, P):  # P: (...,3) x right, y up, z toward viewer
    return np.stack([bx + P[..., 0], by - P[..., 1] * CE + P[..., 2] * SE], -1)

def hull(pts):
    pts = sorted(map(tuple, pts))
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0: h.pop()
            h.append(p)
        return h
    lo, up = half(pts), half(pts[::-1])
    return lo[:-1] + up[:-1]

def poly(pts):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close(); return p

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)

def draw_top(c, bx, by, ph, psi, col):
    u = np.array([math.sin(ALPHA) * math.cos(ph), math.cos(ALPHA), math.sin(ALPHA) * math.sin(ph)])
    a = np.cross(u, [0, 0, 1.0]); a /= np.linalg.norm(a)
    b = np.cross(u, a)
    C = u * H_DISC
    rim = C + R * (np.cos(TH)[:, None] * a + np.sin(TH)[:, None] * b)
    rim_lo = rim - u * 7
    s_rim, s_lo, s_tip = proj(bx, by, rim), proj(bx, by, rim_lo), proj(bx, by, np.zeros(3))
    s_c = proj(bx, by, C)
    # ground shadow (light from upper left)
    c.drawOval(skia.Rect(bx - R * .95 + 10, by - 9, bx + R * .95 + 16, by + 11),
               skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    # body: cone from tip + rim thickness
    body = hull(np.vstack([s_lo, s_rim, s_tip[None]]))
    xs = [p[0] for p in body]
    dark = tuple(v * .32 for v in col); mid = tuple(v * .62 for v in col)
    c.drawPath(poly(body), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(min(xs), 0), (max(xs), 0)], [rgb(mid).toColor(), rgb(tuple(v * .8 for v in col)).toColor(), rgb(dark).toColor()], [0, .35, 1])))
    # top face, sectors spinning with psi
    face = poly(s_rim)
    for k in range(SECT):
        a0 = psi + k * 2 * math.pi / SECT
        ts = np.linspace(a0, a0 + 2 * math.pi / SECT, 9)
        P = C + R * (np.cos(ts)[:, None] * a + np.sin(ts)[:, None] * b)
        pts = [tuple(s_c)] + [tuple(q) for q in proj(bx, by, P)]
        shade = col if k % 2 == 0 else tuple(v * .80 for v in col)
        c.drawPath(poly(pts), skia.Paint(AntiAlias=True, Color4f=rgb(shade)))
    # inner ring + gloss
    inner = C + R * .42 * (np.cos(TH)[:, None] * a + np.sin(TH)[:, None] * b)
    c.drawPath(poly([tuple(q) for q in proj(bx, by, inner)]), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
               StrokeWidth=1.4, Color4f=skia.Color4f(1, .9, .7, .35)))
    xs = s_rim[:, 0]; ys = s_rim[:, 1]
    c.drawPath(face, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(xs.min(), ys.min()), (xs.max(), ys.max())], [skia.Color4f(1, 1, 1, .32).toColor(), skia.Color4f(1, 1, 1, 0).toColor(),
         skia.Color4f(0, 0, 0, .25).toColor()], [0, .5, 1])))
    c.drawPath(face, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6, Color4f=skia.Color4f(.95, .78, .48, .75)))
    # brass stem + knob
    st = proj(bx, by, C + u * H_STEM)
    c.drawLine(s_c[0], s_c[1], st[0], st[1], skia.Paint(AntiAlias=True, StrokeWidth=4.2, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=skia.Color4f(.80, .60, .32, 1)))
    c.drawLine(s_c[0] - 1, s_c[1], st[0] - 1, st[1], skia.Paint(AntiAlias=True, StrokeWidth=1.2, Color4f=skia.Color4f(1, .92, .7, .6)))
    blit(c, KNOB, st[0], st[1])

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
        text(c, "One top is spinning", W / 2, 278, F_Q, CREAM, .97)
        text(c, "the other way.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
        for i, L in enumerate(LETTERS):
            text(c, L, X0 + i * cw, 520, F_LBL, CREAM, .45)
        for r in range(ROWS):
            text(c, str(r + 1), 88, Y0 + r * rh - 22, F_LBL, CREAM, .45)
        for r in range(ROWS):
            for col in range(COLS):
                psi = sign(col, r) * 2 * math.pi * S_CYC * t / LOOP + col * .7 + r * 1.3
                draw_top(c, X0 + col * cw, Y0 + r * rh, phi(col, r, t), psi, col_of(col, r))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

def tick(f0, dec=300, dur=.07, bright=.3):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + bright * np.sin(2 * np.pi * f0 * 2.76 * t)) * np.exp(-t * dec)
    n = np.random.default_rng(int(f0 * 7)).standard_normal(len(t)) * np.exp(-t * 3000) * .35
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 8000)

def audio(path):
    m = Mix(LOOP)
    # tick when each top leans fully toward the viewer (phi = pi/2 mod 2pi) - the pinwheel sweeps the ticks round
    radii = sorted({round(rad(c, r), 2) for c in range(COLS) for r in range(ROWS)})
    for r in range(ROWS):
        for col in range(COLS):
            x = X0 + col * cw
            for k in range(P_CYC + 1):
                if (col, r) == ODD:
                    # phi = -(w t + p) = pi/2  ->  w t = -pi/2 - p
                    th = -math.pi / 2 - phase(col, r)
                else:
                    th = math.pi / 2 - phase(col, r)
                tt = ((th / (2 * math.pi) * LOOP / P_CYC) % (LOOP / P_CYC)) + k * LOOP / P_CYC
                if tt >= LOOP: continue
                if (col, r) == ODD:
                    m.add(tick(1568, 120, .25, 1.1), tt, .30, x)      # brighter, ringing metal tick
                else:
                    i = radii.index(round(rad(col, r), 2))
                    f0 = note(int(i * 7 / len(radii)) + 5, 261.63)   # pentatonic, rising outward
                    m.add(tick(f0), tt + np.random.default_rng(k * 97 + col * 31 + r).uniform(0, .004), .22, x)
    # soft spinning hum, integer cycles per loop so it loops seamlessly
    n = m.N; t = np.arange(n) / SR
    hum = sum(a * np.sin(2 * np.pi * (round(fq * LOOP) / LOOP) * t) for fq, a in ((110, 1), (165, .5), (220, .3)))
    hum *= 1 + .25 * np.sin(2 * np.pi * (S_CYC * 6 / LOOP) * t)
    m.L += hum * .012; m.R += hum * .012
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/T_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_tops.mp4"))
