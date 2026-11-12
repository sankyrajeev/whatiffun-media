"""SPOT IT: 63 wooden metronomes (7 cols A-G x 9 rows) ticking in a ripple that rolls out of the centre.
One has its brass weight set a touch higher, so it is a little slower: 11 swings per 12 s loop instead of 12.
It slides out of its ring of the ripple, is fully opposite at 6 s, and is back in step at the loop (frame 0 == frame N)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spotm"
COLS, ROWS = 7, 9
X0, X1, Y0, Y1 = 160, 920, 640, 1520          # base line of each metronome body
LOOP = 12.0
TOTAL = int(LOOP * FPS)
ODD = (5, 3)                                  # column F, row 4
AMP = math.radians(28)
cw, rh = (X1 - X0) / (COLS - 1), (Y1 - Y0) / (ROWS - 1)
LETTERS = "ABCDEFG"
CC, CR = 3, 4                                 # ripple centre: D5
BODY_H, BOT_W, TOP_W = 66, 62, 26
PIV_UP = 14                                   # pivot height above the base
NEEDLE = 92
WFRAC, WFRAC_ODD = .58, .64                   # weight position along the needle (higher = slower)

def ring(c, r): return math.hypot(c - CC, (r - CR) * rh / cw)
def phase0(c, r): return -0.95 * ring(c, r)
def ncyc(c, r): return 11 if (c, r) == ODD else 12
def theta(c, r, t): return AMP * math.sin(2 * math.pi * ncyc(c, r) * t / LOOP + phase0(c, r))

BG = background(1080)
MAXR = max(ring(c, r) for c in range(COLS) for r in range(ROWS))
def wcol(c, r): return hsv(28 + 300 * ring(c, r) / MAXR, .55, 1.0)

def body_sprite():
    w, h = BOT_W + 16, BODY_H + 16
    def fn(c):
        ox, oy = 8, 8
        p = skia.Path(); p.moveTo(ox, oy + BODY_H); p.lineTo(ox + BOT_W, oy + BODY_H)
        p.lineTo(ox + BOT_W / 2 + TOP_W / 2, oy); p.lineTo(ox + BOT_W / 2 - TOP_W / 2, oy); p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(ox, 0), (ox + BOT_W, 0)], [skia.Color(120, 70, 38), skia.Color(84, 46, 24), skia.Color(44, 24, 12)], [0, .45, 1])))
        f = skia.Path(); m = 9
        f.moveTo(ox + m + 4, oy + BODY_H - 9); f.lineTo(ox + BOT_W - m - 4, oy + BODY_H - 9)
        f.lineTo(ox + BOT_W / 2 + TOP_W / 2 - 6, oy + 10); f.lineTo(ox + BOT_W / 2 - TOP_W / 2 + 6, oy + 10); f.close()
        c.drawPath(f, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.07, .045, .03, .92)))
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=skia.Color4f(1, .85, .6, .18)))
        c.drawRect(skia.Rect(ox - 3, oy + BODY_H - 4, ox + BOT_W + 3, oy + BODY_H + 2), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.86, .64, .36, .9)))
    return sprite(fn, max(w, h))
BODY = body_sprite()
PIV = glass_ball((.92, .72, .42), 3.2)
F_LBL = font(TF_MONO, 24)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
TIPC = (.95, .80, .52)

def draw_weight(c, x, y, ang, col):
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang))
    rr = skia.RRect.MakeRectXY(skia.Rect(-8, -6, 8, 6), 2.5, 2.5)
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-8, -6), (8, 6)], [skia.Color4f(*[min(1, v * .5 + .6) for v in col], 1).toColor(), skia.Color4f(*col, 1).toColor(),
                             skia.Color4f(*[v * .5 for v in col], 1).toColor()], [0, .5, 1])))
    c.drawRect(skia.Rect(-6, -4.5, -1, -3), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .7)))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
        text(c, "One metronome is", W / 2, 278, F_Q, CREAM, .97)
        text(c, "a little slower.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
        for i, L in enumerate(LETTERS):
            text(c, L, X0 + i * cw, 500, F_LBL, CREAM, .45)
        for r in range(ROWS):
            text(c, str(r + 1), 92, Y0 + r * rh - 30, F_LBL, CREAM, .45)
        needle = skia.Paint(AntiAlias=True, StrokeWidth=2.6, StrokeCap=skia.Paint.kRound_Cap, Color4f=skia.Color4f(.86, .68, .40, .95))
        sh = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5))
        for r in range(ROWS):
            for col in range(COLS):
                bx, by = X0 + col * cw, Y0 + r * rh
                c.drawOval(skia.Rect(bx - BOT_W / 2 - 4, by - 3, bx + BOT_W / 2 + 8, by + 7), sh)
                blit(c, BODY, bx, by - BODY_H / 2 + 0)
                th = theta(col, r, t)
                px, py = bx, by - PIV_UP
                tx, ty = px + NEEDLE * math.sin(th), py - NEEDLE * math.cos(th)
                c.drawLine(px, py, tx, ty, needle)
                c.drawCircle(tx, ty, 2.2, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*TIPC, 1)))
                wf = WFRAC_ODD if (col, r) == ODD else WFRAC
                draw_weight(c, px + NEEDLE * wf * math.sin(th), py - NEEDLE * wf * math.cos(th), th, wcol(col, r))
                blit(c, PIV, px, py)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

def wood_tick(f0, dec=260, dur=.06):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .35 * np.sin(2 * np.pi * f0 * 2.4 * t)) * np.exp(-t * dec)
    n = np.random.default_rng(int(f0)).standard_normal(len(t)) * np.exp(-t * 2500) * .5
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 8000)

def audio(path):
    m = Mix(LOOP)
    rings = sorted({round(ring(c, r), 2) for c in range(COLS) for r in range(ROWS)})
    dt = 1 / (FPS * 8)
    prev = {}
    for k in range(int(LOOP / dt) + 1):
        t = k * dt
        for r in range(ROWS):
            for col in range(COLS):
                s = math.cos(2 * math.pi * ncyc(col, r) * t / LOOP + phase0(col, r))
                key = (col, r)
                if key in prev and (prev[key] > 0) != (s > 0):
                    x = X0 + col * cw
                    tt = t % LOOP
                    if key == ODD:
                        m.add(wood_tick(470, 170), tt, .6, x)
                    else:
                        i = rings.index(round(ring(col, r), 2))
                        f0 = note(int(i * 5 / len(rings)) + 7, 261.63)   # pentatonic, rising outward
                        n_in_ring = sum(1 for cc in range(COLS) for rr in range(ROWS) if round(ring(cc, rr), 2) == rings[i])
                        m.add(wood_tick(f0), tt + np.random.default_rng(k + col * 31 + r).uniform(0, .003), .32 / math.sqrt(n_in_ring), x)
                prev[key] = s
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/M_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_metronomes.mp4"))
