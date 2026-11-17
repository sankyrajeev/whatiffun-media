"""SPOT IT v3 (10:00, 2026-11-17): WHICH ONE / BREAKS PHYSICS? — 56 chair-swing carousels, one flings its chairs INWARD.
Rule type: BREAKS PHYSICS (inertia / centrifugal effect). New family: fairground chair-swing carousels. New arrangement:
FAIRGROUND ARCS — 8 rows bowed into gentle smiles (7 columns A–G), each carousel on a brass base plaque "C4".
Every carousel spins up and down (one speed cycle per 4 s, 3 per 12 s loop, 4/3 turn per cycle) from a random phase
(a soft diagonal drift + noise), its six chairs on chains flaring OUT to ~54 deg at full speed (tan a = w^2 r / g, lagging
the speed a little) and dropping back to hanging straight. The odd carousel's chairs swing INWARD under the canopy, meeting
at the pole at full speed — every 4 s, unmistakable once seen.
Sound: a soft wooden clack when each carousel hits full speed (pentatonic by row, panned by x, density-normalised) +
a low fairground hum bed; the odd carousel gives a small music-box ting instead (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/carousels"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 7, 8
LET = "ABCDEFG"
SX, SY = 126, 128
Y0 = 470                               # canopy rim of row 1 (centre column)
BEND = float(os.environ.get("BEND", "26"))
CYC = 4.0                              # speed cycle
TURN = 2 * math.pi * 4 / 3             # rotation per cycle (multiple of 2pi/6 -> seamless)
WMIN_F = .40                           # min speed as a fraction of max
WMAX = TURN / CYC * 2 / (1 + WMIN_F)
AMAX = math.radians(float(os.environ.get("AMAX", "54")))
K = math.tan(AMAX) / WMAX ** 2
RH, CH = 25, 36                        # hang radius on the rim, chain length
KP = .30                               # perspective squash
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "40")))

def omega(u):                          # u in cycles
    return WMAX * (WMIN_F + (1 - WMIN_F) * (.5 - .5 * math.cos(2 * math.pi * u)))
def spin(u):                           # integral of omega dt (u in cycles)
    a = WMAX * CYC
    return a * (WMIN_F * u + (1 - WMIN_F) * (.5 * u - math.sin(2 * math.pi * u) / (4 * math.pi)))
def flare(u):                          # chairs lag the speed by ~0.25 s
    w = omega(u - .25 / CYC)
    return math.atan(K * w * w)

CAR = []                               # (label, x, y, phase, spin0, odd)
for r in range(NR):
    for i in range(NC):
        x = 540 + (i - (NC - 1) / 2) * SX
        y = Y0 + r * SY + BEND * ((x - 540) / 380) ** 2
        lab = (LET[i], r + 1)
        ph = -.07 * (r + i) + rng.normal(0, .16)
        CAR.append((lab, x, y, ph, rng.uniform(0, 2 * math.pi), lab == ODD))

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def mixc(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_PLQ = font(TF_BOLD, 21)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
CREAMC = (.97, .91, .78)
AMB = (.93, .6, .24)
BRASS = [(.98, .86, .6), (.78, .58, .3), (.45, .3, .13)]

def state(car, t):
    lab, x, y, ph, s0, odd = car
    u = t / CYC + ph
    a = flare(u)
    return s0 + spin(u), (-a if odd else a)

def draw_carousel(c, car, phi, a):
    lab, x, y, ph, s0, odd = car
    # base platform + plaque
    by = y + 58
    c.drawOval(skia.Rect(x - 40, by - 9, x + 40, by + 11), skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .5),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    c.drawOval(skia.Rect(x - 38, by - 10, x + 38, by + 8), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, by - 10), (0, by + 8)], [rgb((.62, .44, .22)), rgb((.32, .21, .1))])))
    # chairs: (depth, kind, data)
    items = []
    for k in range(6):
        th = phi + k * math.pi / 3
        rho = RH + CH * math.sin(a)
        hx, hy = x + RH * math.sin(th), y + KP * RH * math.cos(th)
        cx_, cy_ = x + rho * math.sin(th), y + CH * math.cos(a) + KP * rho * math.cos(th)
        items.append((rho * math.cos(th) if abs(rho) > 1 else math.cos(th) * .01, hx, hy, cx_, cy_, th))
    items.sort(key=lambda it: it[0])
    def chair(it):
        d, hx, hy, cx_, cy_, th = it
        lit = .62 + .38 * (.5 + .5 * math.cos(th))
        c.drawLine(hx, hy, cx_, cy_, skia.Paint(AntiAlias=True, StrokeWidth=2.8, Color4f=c4(mixc((.3, .25, .2), CREAMC, lit), .95)))
        col = tuple(v * lit for v in AMB)
        c.drawRoundRect(skia.Rect(cx_ - 10, cy_ - 2, cx_ + 10, cy_ + 10), 3, 3, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .4),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
        c.drawRoundRect(skia.Rect(cx_ - 10, cy_ - 3, cx_ + 10, cy_ + 8), 3, 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, cy_ - 3), (0, cy_ + 8)], [rgb(tuple(min(1, v * 1.25) for v in col)), rgb(col), rgb(tuple(v * .5 for v in col))], [0, .4, 1])))
        c.drawRoundRect(skia.Rect(cx_ - 7, cy_ - 2.5, cx_ + 7, cy_ - .5), 1, 1, skia.Paint(AntiAlias=True, Color4f=c4((1, .95, .8), .45 * lit)))
    for it in items:
        if it[0] < 0: chair(it)
    # pole
    c.drawRoundRect(skia.Rect(x - 4, y - 33, x + 4, by), 3, 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - 4, 0), (x + 4, 0)], [rgb(BRASS[0]), rgb(BRASS[1]), rgb(BRASS[2])], [0, .4, 1])))
    for it in items:
        if it[0] >= 0: chair(it)
    # canopy: a striped cone, 12 segments, drawn back to front
    R, top = 37, y - 37
    segs = []
    for j in range(12):
        t0, t1 = phi + j * math.pi / 6, phi + (j + 1) * math.pi / 6
        segs.append((math.cos((t0 + t1) / 2), j, t0, t1))
    segs.sort()
    for dep, j, t0, t1 in segs:
        p = skia.Path()
        p.moveTo(x, top)
        n = 6
        for q in range(n + 1):
            tt = t0 + (t1 - t0) * q / n
            p.lineTo(x + R * math.sin(tt), y + KP * R * math.cos(tt))
        p.close()
        base = CREAMC if j % 2 == 0 else AMB
        lit = .55 + .45 * (.5 + .5 * math.sin((t0 + t1) / 2 + .6)) * (.6 + .4 * max(0, dep))
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=c4(tuple(v * lit for v in base))))
    # scalloped rim + bulbs (front half)
    c.drawOval(skia.Rect(x - R, y - KP * R - 1.5, x + R, y + KP * R + 1.5), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
               StrokeWidth=2.4, Color4f=c4(BRASS[1], .9)))
    for j in range(12):
        tt = phi + j * math.pi / 6 + math.pi / 12
        if math.cos(tt) > -.2:
            bx, byy = x + R * math.sin(tt), y + KP * R * math.cos(tt) + 1
            c.drawCircle(bx, byy, 3.2, skia.Paint(AntiAlias=True, Color4f=c4((1, .8, .45), .35),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
            c.drawCircle(bx, byy, 1.7, skia.Paint(AntiAlias=True, Color4f=c4((1, .95, .8), .95)))
    # finial
    c.drawCircle(x, top - 3, 4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - 1, top - 5), 6,
                 [rgb(BRASS[0]), rgb(BRASS[2])])))
    # plaque on the base
    pw, ph_ = 40, 22
    c.drawRoundRect(skia.Rect(x - pw / 2, by - 4, x + pw / 2, by - 4 + ph_), 6, 6, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, by - 4), (0, by + ph_ - 4)], [rgb((.99, .93, .78)), rgb((.85, .7, .45)), rgb((.55, .38, .17))], [0, .5, 1])))
    text(c, f"{lab[0]}{lab[1]}", x, by + 13.5, F_PLQ, (.2, .12, .05), .95)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for car in sorted(CAR, key=lambda q: q[2]):
            phi, a = state(car, t)
            draw_carousel(c, car, phi, a)
        yb = 1532
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 46, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 44, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def clack(f0, dur=.12, seed=0):
    t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 45) + .3 * np.sin(2 * np.pi * f0 * 2.4 * t) * np.exp(-t * 80)
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 800) * .35
    return (body + np.diff(n, prepend=0) * .6) * np.minimum(1, t * 5000)
def ting(f0, dur=.6):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 7) + .3 * np.sin(2 * np.pi * f0 * 3.0 * t + 1) * np.exp(-t * 15)
    return s * np.minimum(1, t * 6000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, car in enumerate(CAR):
        ph = car[3]
        for j in range(-3, 6):        # full speed at u = j + .5
            tt = (j + .5 - ph) * CYC
            if 0 <= tt < LOOP: ev.append((tt, k))
    times = np.array([e[0] for e in ev])
    for tt, k in ev:
        lab, x, y, ph, s0, odd = CAR[k]
        r = lab[1] - 1
        dens = (np.abs(times - tt) < .06).sum()
        if odd:
            m.add(ting(note(r + 12, 261.63)), tt, .3, x)
        else:
            m.add(clack(note(NR - 1 - r + 4, 196.0) * (1 + .004 * (x - 540) / 126), seed=k), tt, .5 / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 220) / 200) ** 2)       # soft low hum/air bed
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_carousels.mp4"))
