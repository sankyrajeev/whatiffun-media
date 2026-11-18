"""SPOT IT v3 (10:00, 2026-11-18): 48 swinging lamps, one shadow breaks physics.
Rule type: BREAKS PHYSICS (light travels in straight lines): every lamp swings in a big arc in front of a little cream
pawn on its own wall card, and the pawn's shadow, cast from its foot, leans across the wall AWAY from the bulb. On the
odd one (B6) the shadow leans TOWARD the bulb. Arrangement: a plain 6 x 8 grid (A-F across, 1-8 down, labels outside).
v1 was 52 small cells in an hourglass silhouette with a straight post; the blind review (5 vs anchor 7) said the
cells did not read at phone size, so v2 uses 48 bigger cards, a pawn and a foot-anchored leaning shadow.
Sound: a soft glass tink at each lamp's right-hand extreme (pentatonic by row, panned by x, density-normalised) over
a faint warm hum; the odd lamp's tink is a hollow wooden plok (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/lamps"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 6, 8
LET = "ABCDEF"
SX, SY = 136, 130
X0 = 540 - (NC - 1) / 2 * SX
Y0 = 438                       # pivot line of row 1
P = 2.4                        # swing period (5 per loop)
AMP = math.radians(float(os.environ.get("AMP", "55")))
CL = 46                        # cord length
PH_H = 44                      # pawn height
ODD = (os.environ.get("OL", "B"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "18")))

LAMPS = []                     # (label, x, y, phase, row)
for r in range(NR):
    for i in range(NC):
        x = X0 + i * SX
        y = Y0 + r * SY
        ph = (.08 * i + .10 * r + rng.uniform(0, .22)) % 1.0
        LAMPS.append(((LET[i], r + 1), x, y, ph, r))

def angle(t, ph): return AMP * math.sin(2 * math.pi * (t / P + ph))
def extremes(ph):
    out = []
    for k in range(-2, int(LOOP / P) + 3):
        tt = (k + .25 - ph) * P
        if 0 <= tt < LOOP: out.append(tt)
    return out

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 34)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
BLUR = lambda s: skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, s)

CW, CH = 126, 120               # wall card
PLH = 14                       # floor strip at the bottom of the card
WALL = (.13, .1, .08)
def geom(x, y, th):
    bx, by = x + CL * math.sin(th), y + CL * math.cos(th)
    return bx, by, y + CH - 8 - PLH

def pawn_path():
    p = skia.Path()           # base at (0,0), up is negative y
    p.moveTo(-14, 0); p.lineTo(14, 0); p.lineTo(13, -6); p.lineTo(8, -9)
    p.quadTo(4, -22, 5, -30); p.lineTo(8, -32); p.lineTo(8, -35); p.lineTo(-8, -35); p.lineTo(-8, -32); p.lineTo(-5, -30)
    p.quadTo(-4, -22, -8, -9); p.lineTo(-13, -6); p.close()
    p.addCircle(0, -PH_H + 9, 9)
    return p
PAWN = pawn_path()

def card(c, x, y):
    r = skia.Rect(x - CW / 2, y - 8, x + CW / 2, y + CH - 8)
    c.drawRoundRect(r.makeOffset(3, 6), 9, 9, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .6), MaskFilter=BLUR(6)))
    c.drawRoundRect(r, 9, 9, skia.Paint(AntiAlias=True, Color4f=c4(WALL)))

def wall_light(c, x, y, bx, by, fy, odd):
    r = skia.Rect(x - CW / 2, y - 8, x + CW / 2, y + CH - 8)
    c.save(); c.clipRRect(skia.RRect.MakeRectXY(r, 9, 9), True)
    c.drawCircle(bx, by, 120, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((bx, by), 120,
                 [c4((1, .9, .7), .95).toColor(), c4((.95, .7, .4), .55).toColor(), c4((.6, .35, .15), 0).toColor()], [0, .5, 1])))
    # the pawn's shadow, cast on the wall from its foot and leaning AWAY from the bulb (toward it on the odd one)
    k = (bx - x) / CL * 1.25
    if odd: k = -k
    c.save(); c.translate(x, fy)
    c.concat(skia.Matrix.MakeAll(1, k, 0, 0, 1.35, 0, 0, 0, 1))
    c.drawPath(PAWN, skia.Paint(AntiAlias=True, Color4f=c4((.06, .04, .03), .92), MaskFilter=BLUR(1.2)))
    c.restore()
    c.restore()

def plinth(c, x, fy):
    c.drawRect(skia.Rect(x - CW / 2, fy, x + CW / 2, fy + PLH), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, fy), (0, fy + PLH)], [rgb((.5, .35, .22)), rgb((.22, .14, .08))])))

def post(c, x, fy, bx):
    lit = (1, .96, .86); dark = (.55, .46, .36)
    cols = [rgb(dark), rgb(lit)] if bx > x else [rgb(lit), rgb(dark)]
    c.save(); c.translate(x, fy)
    c.drawPath(PAWN, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-12, 0), (12, 0)], cols)))
    c.restore()

def lamp(c, x, y, bx, by, th):
    c.drawCircle(x, y - 2, 4.5, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - 1, y - 3), 5,
                 [rgb((1, .9, .6)), rgb((.55, .38, .16))])))
    cx, cy = x + (CL - 13) * math.sin(th), y + (CL - 13) * math.cos(th)
    c.drawLine(x, y, cx, cy, skia.Paint(AntiAlias=True, StrokeWidth=2.4, Color4f=c4((.3, .22, .15), .95)))
    c.drawCircle(bx, by, 34, skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Color4f=c4((1, .62, .22), .35), MaskFilter=BLUR(14)))
    c.save(); c.translate(cx, cy); c.rotate(-math.degrees(th))
    c.drawRoundRect(skia.Rect(-7, -2, 7, 9), 2, 2, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-7, 0), (7, 0)], [rgb((.98, .84, .52)), rgb((.45, .3, .12))])))
    c.restore()
    c.drawCircle(bx, by, 13, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((bx - 3, by - 3), 15,
                 [rgb((1, 1, .94)), rgb((1, .9, .58)), rgb((1, .66, .25))], [0, .45, 1])))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for i in range(NC):
            text(c, LET[i], X0 + i * SX, Y0 - 22, F_LAB, CREAM, .85)
        for r in range(NR):
            text(c, str(r + 1), X0 - SX / 2 - 12, Y0 + r * SY + 58, F_LAB, CREAM, .85, align="right")
        G = []
        for lab, x, y, ph, r in LAMPS:
            th = angle(t, ph)
            G.append((lab, x, y, th) + geom(x, y, th))
        for lab, x, y, th, bx, by, fy in G:
            card(c, x, y)
        for lab, x, y, th, bx, by, fy in G:
            wall_light(c, x, y, bx, by, fy, lab == ODD)
            plinth(c, x, fy); post(c, x, fy, bx)
            lamp(c, x, y, bx, by, th)
        yb = Y0 + (NR - 1) * SY + CH + 64
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 50, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 48, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def tink(f0, dur=.35, seed=0, wood=False):
    t = np.arange(int(dur * SR)) / SR
    if wood:
        body = np.sin(2 * np.pi * f0 * .5 * t) * np.exp(-t * 45) + .35 * np.sin(2 * np.pi * f0 * 1.1 * t) * np.exp(-t * 70)
    else:
        body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 14) + .25 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 30)
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 1500) * .3
    return (body + np.diff(n, prepend=0) * .5) * np.minimum(1, t * 4000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, r) in enumerate(LAMPS):
        for tt in extremes(ph): ev.append((tt, k))
    times = np.array([e[0] for e in ev])
    for tt, k in ev:
        lab, x, y, ph, r = LAMPS[k]
        dens = (np.abs(times - tt) < .06).sum()
        odd = lab == ODD
        m.add(tink(note(NR - 1 - r + 5, 261.63) * (1 + .004 * (x - 540) / 108), seed=k, wood=odd), tt,
              (.55 if odd else .32) / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 110 * tt) + .4 * np.sin(2 * np.pi * 220 * tt)) * .018
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 300) / 250) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .04 + hum; m.R += np.roll(bed, 5000) * .04 + hum
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_lamps.mp4"))
