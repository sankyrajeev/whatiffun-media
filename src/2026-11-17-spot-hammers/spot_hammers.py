"""SPOT IT v3 (13:00, 2026-11-17): 52 hammers in a DIAMOND, one hits twice.
Rule type: RHYTHM (it double-taps). Arrangement: a diamond of rows 4/5/6/7/8/7/6/5/4 (each anvil carries its own
brass plaque "D5" because the rows are offset). Every hammer lifts high and slams onto its anvil once every 2.4 s
(5 strikes per 12 s loop) from a phase made of a soft diagonal wave + noise, a spark flashing on every strike;
the odd hammer bounces back up and strikes a SECOND time 0.42 s later, every cycle.
Sound: a soft metallic tock per strike (pentatonic by row, panned by x, density-normalised); the odd hammer's tock
is a woodier, lower knock (audio clue) and of course comes in pairs."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/hammers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
WIDTHS = [4, 5, 6, 7, 8, 7, 6, 5, 4]
NR = len(WIDTHS)
LET = "ABCDEFGH"
SX, SY = 108, 110
Y0 = 520                       # strike line of row 1
P = 2.4
UP = math.radians(float(os.environ.get("UP", "74")))
HL = 64                        # handle length (pivot -> head centre)
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "17")))

HAM = []                       # (label, x, y, phase, row)
for r, n in enumerate(WIDTHS):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y0 + r * SY
        ph = (.07 * i + .13 * r + rng.uniform(0, .55)) % 1.0
        HAM.append(((LET[i], r + 1), x, y, ph, r))

def sm(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
U2 = .20                       # odd hammer's second strike (fraction of the cycle)
def angle(t, ph, odd):
    """lift angle (0 = head on the anvil) at time t; strike at u = 0"""
    u = (t / P + ph) % 1.0
    if odd and u < U2:          # big rebound and a second slam
        v = u / U2
        return math.radians(56) * math.sin(math.pi * v) ** 1.3 if v < .55 else math.radians(56) * (1 - ((v - .55) / .45) ** 2) * math.sin(math.pi * .55) ** 1.3
    u0 = U2 if odd else 0.0
    if u < u0 + .10:            # small rebound
        v = (u - u0) / .10
        return math.radians(9) * math.sin(math.pi * v) * (1 - v * .3)
    if u < .30: return 0.0
    if u < .80: return UP * sm((u - .30) / .50)
    if u < .88: return UP * (1 + .03 * math.sin(math.pi * (u - .80) / .08))
    v = (u - .88) / .12          # accelerating slam
    return UP * (1 - v * v)
def strikes(ph, odd):
    out = []
    for k in range(-2, int(LOOP / P) + 3):
        for du in ([0, U2] if odd else [0]):
            tt = (k + du - ph) * P
            if 0 <= tt < LOOP: out.append(tt)
    return out
def since_strike(t, ph, odd):
    best = 9
    for du in ([0, U2] if odd else [0]):
        d = ((t / P + ph - du) % 1.0) * P
        best = min(best, d)
    return best

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_PLQ = font(TF_SB, 25)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

S = 3
HW, HH = 40, 26                 # hammer head
def head_image():
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul((HW + 4) * S, (HH + 4) * S))
    with surf as c:
        c.scale(S, S); c.translate(2, 2)
        c.drawRoundRect(skia.Rect(0, 0, HW, HH), 4, 4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, HH)], [rgb((1, .9, .62)), rgb((.92, .7, .36)), rgb((.6, .4, .17))], [0, .45, 1])))
        c.drawRoundRect(skia.Rect(2, 2, HW - 2, 7), 2, 2, skia.Paint(AntiAlias=True, Color4f=c4((1, .97, .85), .5)))
        for xx in (0, HW - 5):  # darker striking faces
            c.drawRect(skia.Rect(xx, 0, xx + 5, HH), skia.Paint(AntiAlias=True, Color4f=c4((.45, .29, .11), .35)))
    return surf.makeImageSnapshot()
HEAD = head_image()

def anvil(c, lab, x, y):
    # anvil block under the strike point, plaque on its face
    ax = x + 18
    p = skia.Path()
    p.moveTo(ax - 30, y); p.lineTo(ax + 30, y); p.lineTo(ax + 24, y + 12); p.lineTo(ax + 15, y + 15)
    p.lineTo(ax + 18, y + 40); p.lineTo(ax - 18, y + 40); p.lineTo(ax - 15, y + 15); p.lineTo(ax - 24, y + 12); p.close()
    sh = skia.Path(p); sh.offset(3, 5)
    c.drawPath(sh, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y), (0, y + 40)], [rgb((.72, .64, .54)), rgb((.45, .38, .31)), rgb((.26, .21, .16))], [0, .3, 1])))
    c.drawRect(skia.Rect(ax - 30, y, ax + 30, y + 2.5), skia.Paint(AntiAlias=True, Color4f=c4((.85, .76, .62), .8)))

def plaque(c, lab, x, y):
    ax = x + 18
    pw = 48
    c.drawRoundRect(skia.Rect(ax - pw / 2, y + 16, ax + pw / 2, y + 40), 3, 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y + 18), (0, y + 38)], [rgb((.97, .82, .5)), rgb((.68, .48, .22))])))
    text(c, f"{lab[0]}{lab[1]}", ax, y + 37, F_PLQ, (.16, .1, .05), .95)

def post(c, x, y):
    # pivot post
    px = x - 46
    c.drawRoundRect(skia.Rect(px - 5, y - 21, px + 5, y + 40), 3, 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(px - 5, 0), (px + 5, 0)], [rgb((.42, .34, .26)), rgb((.22, .17, .12))])))

def hammer(c, x, y, th, flash):
    px, py = x - 46, y - 20     # pivot; head centre sits at (x+18, y-20) when down
    hx, hy = px + (HL - 6) * math.cos(th), py - (HL - 6) * math.sin(th)
    # spark / glow on impact
    if flash > 0:
        g = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Color4f=c4((1, .6, .2), .75 * flash),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10 + 8 * (1 - flash)))
        c.drawOval(skia.Rect(x + 18 - 30, y - 10, x + 18 + 30, y + 8), g)
        rr = 10 + 26 * (1 - flash)
        sp = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, StrokeWidth=2.2, StrokeCap=skia.Paint.kRound_Cap,
                        Color4f=c4((1, .82, .45), .95 * flash))
        for k in range(7):
            a = math.pi * (.08 + .84 * k / 6)
            c.drawLine(x + 18 + math.cos(a) * rr * .45, y - math.sin(a) * rr * .3,
                       x + 18 + math.cos(a) * rr, y - math.sin(a) * rr * .75, sp)
    # handle
    c.drawLine(px, py, hx, hy, skia.Paint(AntiAlias=True, StrokeWidth=8, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.25, .17, .1), .9)))
    c.drawLine(px, py, hx, hy, skia.Paint(AntiAlias=True, StrokeWidth=6, StrokeCap=skia.Paint.kRound_Cap, Shader=skia.GradientShader.MakeLinear(
        [(px, py - 3), (px, py + 3)], [rgb((.97, .9, .76)), rgb((.78, .66, .5))])))
    # head (perpendicular to the handle)
    c.save()
    c.translate(px + HL * math.cos(th), py - HL * math.sin(th))
    c.rotate(-math.degrees(th) + 90)
    c.drawImageRect(HEAD, skia.Rect(-HW / 2 - 2, -HH / 2 - 2, HW / 2 + 2, HH / 2 + 2), SAMP)
    c.restore()
    # pivot pin
    c.drawCircle(px, py, 5, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((px - 1.5, py - 1.5), 6,
                 [rgb((1, .9, .6)), rgb((.55, .38, .16))])))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH HAMMER", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "HITS TWICE?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for lab, x, y, ph, r in HAM:
            anvil(c, lab, x, y); post(c, x, y)
        for lab, x, y, ph, r in HAM:
            odd = lab == ODD
            d = since_strike(t, ph, odd)
            fl = max(0.0, 1 - d / .22) if d < .22 else 0.0
            hammer(c, x, y, angle(t, ph, odd), fl)
        for lab, x, y, ph, r in HAM:
            plaque(c, lab, x, y)
        yb = Y0 + (NR - 1) * SY + 112
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
def tock(f0, dur=.22, seed=0, wood=False):
    t = np.arange(int(dur * SR)) / SR
    if wood:
        body = np.sin(2 * np.pi * f0 * .7 * t) * np.exp(-t * 60) + .3 * np.sin(2 * np.pi * f0 * 1.6 * t) * np.exp(-t * 90)
    else:
        body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 28) + .3 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 45)
    low = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 35) * .5
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 1100) * .45
    return (body + low + np.diff(n, prepend=0) * .6) * np.minimum(1, t * 6000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, r) in enumerate(HAM):
        for tt in strikes(ph, lab == ODD): ev.append((tt, k))
    times = np.array([e[0] for e in ev])
    for tt, k in ev:
        lab, x, y, ph, r = HAM[k]
        dens = (np.abs(times - tt) < .05).sum()
        odd = lab == ODD
        m.add(tock(note(NR - 1 - r + 4, 196.0) * (1 + .004 * (x - 540) / 108), seed=k, wood=odd), tt,
              (.62 if odd else .5) / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 240) / 200) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/H_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_hammers.mp4"))
