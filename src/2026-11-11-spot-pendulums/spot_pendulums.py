"""SPOT IT: 70 pendulums in a lettered grid; one is a touch longer. Seamless 12 s loop:
69 swing 12 times, the odd one 11 times, so it drifts fully out of phase mid-loop and back in sync at the loop."""
import sys, math
import numpy as np, skia
sys.path.insert(0, "/home/claude/notes")
from kit import *

COLS, ROWS = 7, 10
X0, X1, Y0, Y1 = 150, 930, 600, 1500
LOOP = 12.0
TOTAL = int(LOOP * FPS)
ODD = (4, 6)                          # column E, row 7 (0-based col 4, row 6)
AMP = math.radians(26)
cw, rh = (X1 - X0) / (COLS - 1), (Y1 - Y0) / (ROWS - 1)
ROD = rh * .62
LETTERS = "ABCDEFG"

def phase0(c, r): return 0.42 * (c + r)
def theta(c, r, t):
    n = 11 if (c, r) == ODD else 12
    return AMP * math.sin(2 * math.pi * n * t / LOOP + phase0(c, r))

BG = background(1050)
def bob_col(c, r):
    u = (c + r * COLS) / (COLS * ROWS - 1)
    return hsv(200 + 160 * u, .55, 1.0)
BOBS = {(c, r): glass_ball(bob_col(c, r), 11) for c in range(COLS) for r in range(ROWS)}
PIV = glass_ball((.92, .70, .40), 4.5)
F_LBL = font(TF_MONO, 24)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
        text(c, "One pendulum is", W / 2, 278, F_Q, CREAM, .97)
        text(c, "a little longer.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
        for i, L in enumerate(LETTERS):
            text(c, L, X0 + i * cw, 540, F_LBL, CREAM, .45)
        for r in range(ROWS):
            text(c, str(r + 1), 98, Y0 + r * rh + ROD * .55, F_LBL, CREAM, .45, align="center")
        rod = skia.Paint(AntiAlias=True, StrokeWidth=2.2, StrokeCap=skia.Paint.kRound_Cap)
        sh = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3))
        for r in range(ROWS):
            for col in range(COLS):
                px, py = X0 + col * cw, Y0 + r * rh - rh * .30
                L = ROD * (1.0 if (col, r) != ODD else 1.0)      # identical look; only the period differs
                th = theta(col, r, t)
                bx, by = px + L * math.sin(th), py + L * math.cos(th)
                c.drawCircle(bx + 3, by + 5, 11, sh)
                rod.setColor4f(skia.Color4f(.85, .66, .38, .85))
                c.drawLine(px, py, bx, by, rod)
                blit(c, PIV, px, py)
                blit(c, BOBS[(col, r)], bx, by)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

def audio(path):
    m = Mix(LOOP)
    rng = np.random.default_rng(3)
    tick = glass_click(2600, 120, .06, .25)
    tick_low = glass_click(1700, 90, .07, .25)
    dt = 1 / (FPS * 8)
    prev = {}
    for k in range(int(LOOP / dt)):
        t = k * dt
        for r in range(ROWS):
            for col in range(COLS):
                n = 11 if (col, r) == ODD else 12
                ph = 2 * math.pi * n * t / LOOP + phase0(col, r)
                s = math.cos(ph)                    # turning point when cos crosses 0 (sin = ±1)
                key = (col, r)
                if key in prev and (prev[key] > 0) != (s > 0):
                    x = X0 + col * cw
                    if (col, r) == ODD:
                        m.add(tick_low, t, .3, x)
                    elif rng.random() < .09:        # thin the 69 in-sync ticks into one crisp beat
                        m.add(tick, t + rng.uniform(0, .004), .1, x)
                prev[key] = s
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"/home/claude/spot/S_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("/home/claude/spot/spot_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio("/home/claude/spot/spot.wav"))
        print("mux", mux("/home/claude/spot/spot_silent.mp4", "/home/claude/spot/spot.wav", "/home/claude/spot/spot_pendulums.mp4"))
