"""SPOT IT v3 (18:00): 63 clocks, one runs backwards.
New rules after the owner's 2026-11-15 reference ("Who exits the wrong side?"): a big bold QUESTION as the headline,
simple identical objects in one colour scheme (no rainbow), every object in big constant motion, and the odd one is a
CATEGORICAL rule-breaker you can verify once you see it (runs counter-clockwise), not a subtle parameter.
7 x 9 grid (A-G, 1-9). Every hand sweeps 3-5 whole turns per 12 s loop from a random start angle (seamless loop);
the odd clock (E6) sweeps the other way. Sound: a soft wooden tick whenever a hand passes 12 (pentatonic by row,
panned by column); the odd clock's tick is a small brass ting (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/clocks"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 7, 9
LET = "ABCDEFG"
SX, SY = 124, 104
X0 = 540 - 3 * SX
Y0 = 560
RD = 46                                  # dial radius
ODD = (LET.index(os.environ.get("OL", "E")), int(os.environ.get("ON", "6")) - 1)
rng = np.random.default_rng(int(os.environ.get("SEED", "35")))
REVS = rng.choice([3, 4, 5], size=(NC, NR))
PH0 = rng.uniform(0, 2 * math.pi, size=(NC, NR))
REVS[ODD] = 4

def pos(c, r): return X0 + c * SX, Y0 + r * SY
def ang(c, r, t):
    """minute-hand angle, radians clockwise from 12"""
    a = PH0[c, r] + 2 * math.pi * REVS[c, r] * t / LOOP
    return -a if (c, r) == ODD else a

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LBL = font(TF_MONO, 32)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

def dial_sprite():
    sz = RD * 2 + 24
    def fn(c):
        cx = cy = sz / 2
        c.drawCircle(cx, cy + 5, RD + 3, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        # brass bezel
        c.drawCircle(cx, cy, RD + 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(cx - RD, cy - RD), (cx + RD, cy + RD)], [rgb((.98, .82, .5)), rgb((.62, .44, .2)), rgb((.85, .66, .35))], [0, .55, 1])))
        # cream face
        c.drawCircle(cx, cy, RD - 2, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (cx - RD * .3, cy - RD * .35), RD * 1.5, [rgb((1, .98, .93)), rgb((.95, .9, .8)), rgb((.8, .74, .63))], [0, .6, 1])))
        for k in range(12):
            a = k * math.pi / 6
            big = k % 3 == 0
            r0, r1 = RD - (11 if big else 7), RD - 4
            c.drawLine(cx + r0 * math.sin(a), cy - r0 * math.cos(a), cx + r1 * math.sin(a), cy - r1 * math.cos(a),
                       skia.Paint(AntiAlias=True, StrokeWidth=3.2 if big else 1.8, StrokeCap=skia.Paint.kRound_Cap,
                                  Color4f=skia.Color4f(.18, .13, .09, .85 if big else .55)))
    return sprite(fn, sz)
DIAL = dial_sprite()

def hand(cv, x, y, a, L, w, col):
    sx, sy = math.sin(a), -math.cos(a)
    p = skia.Paint(AntiAlias=True, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, Color4f=col)
    cv.drawLine(x - sx * L * .18, y - sy * L * .18, x + sx * L, y + sy * L, p)

def draw_clock(cv, c, r, t):
    x, y = pos(c, r)
    blit(cv, DIAL, x, y)
    a = ang(c, r, t)
    hand(cv, x, y, a / 12 + PH0[(c + 3) % NC, r], RD * .5, 5.5, skia.Color4f(.16, .11, .07, .95))   # hour hand
    hand(cv, x, y, a, RD * .82, 3.6, skia.Color4f(.86, .5, .16, 1))                                   # sweep hand
    cv.drawCircle(x, y, 5, skia.Paint(AntiAlias=True, Color4f=rgb((.86, .5, .16))))
    cv.drawCircle(x - 1.2, y - 1.2, 1.6, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .7)))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH CLOCK", W / 2, 262, F_Q, CREAM, 1.0, spacing=2)
        text(c, "RUNS BACKWARDS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=2)
        for ci in range(NC):
            text(c, LET[ci], X0 + ci * SX, Y0 - RD - 26, F_LBL, CREAM, .7)
        for r in range(NR):
            text(c, str(r + 1), X0 - RD - 44, Y0 + r * SY + 11, F_LBL, CREAM, .62)
            for ci in range(NC):
                draw_clock(c, ci, r, t)
        yb = Y0 + (NR - 1) * SY + RD + 82
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 54, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 52, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def tick(f0, dur=.12):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 60) + .4 * np.sin(2 * np.pi * f0 * 2.4 * t) * np.exp(-t * 90)
    n = np.random.default_rng(int(f0)).standard_normal(len(t)) * np.exp(-t * 1500) * .5
    return (s + np.diff(n, prepend=0) * .6) * np.minimum(1, t * 6000)
def ting(f0, dur=.5):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 8) + .35 * np.sin(2 * np.pi * f0 * 2.76 * t + 1) * np.exp(-t * 14)
    return s * np.minimum(1, t * 6000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for r in range(NR):
        for ci in range(NC):
            n = REVS[ci, r]
            # times the hand passes 12: a(t) = 2*pi*k
            base = PH0[ci, r] / (2 * math.pi)
            for k in range(-2, n + 3):                 # mirrored hand crosses 12 at the same moments
                tt = (k - base) * LOOP / n
                if 0 <= tt < LOOP: ev.append((tt, ci, r))
    times = np.array([e[0] for e in ev])
    for tt, ci, r in sorted(set(ev)):
        x = pos(ci, r)[0]
        dens = ((np.abs(times - tt) < .04)).sum()
        if (ci, r) == ODD:
            m.add(ting(note(r + 10, 261.63)), tt, .22, x)
        else:
            m.add(tick(note(NR - 1 - r + 5, 261.63) * (1 + .003 * ci)), tt, .5 / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 280) / 240) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/C_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_clocks.mp4"))
