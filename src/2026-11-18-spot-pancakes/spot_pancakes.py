"""SPOT IT v3 (13:00, 2026-11-18): 47 pancakes tossed from pans in a BOWTIE, one never flips.
Rule type: TURN-OVER (it goes up and comes down the same side). Arrangement: a bowtie of rows 8/7/6/5/6/7/8
(each pan carries its own brass plaque "D6" because the rows are offset). Every pan tosses its pancake high once
every 3 s (4 tosses per 12 s loop, so the faces come back to where they started), from a phase made of a soft
diagonal wave + noise; in mid-air every pancake turns over (golden side <-> pale side) and lands the other way up,
except the odd one, which rises and falls flat and always lands golden side up.
Sound: a soft pat + sizzle on every landing (pentatonic by row, panned by x, density-normalised) and a faint
whoosh on every toss; the odd pancake lands with a higher, hollow tock (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/pancakes"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
WIDTHS = [8, 7, 6, 5, 6, 7, 8]
NR = len(WIDTHS)
LET = "ABCDEFGH"
SX, SY = 112, 140
Y0 = 585                       # rim line of row 1
P = 3.0
U0, U1 = .03, .40              # launch / landing (fraction of the cycle)
HT = float(os.environ.get("HT", "88"))   # toss height
EL = math.radians(22)          # viewing elevation
PR, PT = 33, 8                 # pancake radius, thickness
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "18")))

PAN = []                       # (label, x, y, phase, row)
for r, n in enumerate(WIDTHS):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * SX - 10
        y = Y0 + r * SY
        ph = (.09 * i + .17 * r + rng.uniform(0, .6)) % 1.0
        PAN.append(((LET[i], r + 1), x, y, ph, r))
PAR = {lab: int(rng.integers(0, 2)) for lab, *_ in PAN}   # which face is up at the start (random, so nothing pops out)
PAR[ODD] = 0

def sm(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def state(t, ph, odd, lab):
    """(pancake dy (up = negative), flip angle, pan dy, pan tilt deg)"""
    tt = t / P + ph
    k, u = int(math.floor(tt)), tt % 1.0
    base = math.pi * (k * (0 if odd else 1) + PAR[lab])          # turned over once per toss
    pan_dy, tilt = 0.0, 0.0
    if u < .10:                                      # flick of the pan
        s = math.sin(math.pi * u / .10)
        pan_dy, tilt = -12 * s, -9 * s
    if U0 <= u < U1:
        v = (u - U0) / (U1 - U0)
        dy = -HT * 4 * v * (1 - v)
        if odd: fl = .10 * math.sin(2 * math.pi * v)
        else:   fl = math.pi * (v - math.sin(2 * math.pi * v) / (2 * math.pi) * .55)
        return dy + pan_dy * (1 - v) * (v < .1), base + fl, pan_dy, tilt
    if u >= U1:
        v = (u - U1) / (1 - U1)
        dy = -7 * math.sin(math.pi * min(1, v / .06)) * (v < .06)  # little bounce
        wob = .05 * math.sin(math.pi * min(1, v / .12)) * math.exp(-v * 8)
        return dy + .8 * math.sin(2 * math.pi * (t * 1.3 + ph)), base + math.pi * (0 if odd else 1) + wob, 0.0, 0.0
    return pan_dy, base, pan_dy, tilt
def landings(ph):
    out = []
    for k in range(-2, int(LOOP / P) + 3):
        for du, kind in ((U1, "land"), (U0, "toss")):
            tt = (k + du - ph) * P
            if 0 <= tt < LOOP: out.append((tt, kind))
    return out
def since_land(t, ph):
    return ((t / P + ph - U1) % 1.0) * P

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_PLQ = font(TF_SB, 24)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

S = 3
def face_image(golden):
    R = PR
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul((2 * R + 4) * S, (2 * R + 4) * S))
    rg = np.random.default_rng(3 if golden else 4)
    with surf as c:
        c.scale(S, S); c.translate(R + 2, R + 2)
        if golden:
            cols = [rgb((.98, .74, .36)), rgb((.86, .55, .22)), rgb((.62, .36, .13))]
        else:
            cols = [rgb((.99, .93, .78)), rgb((.95, .85, .64)), rgb((.82, .66, .42))]
        c.drawCircle(0, 0, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((-4, -4), R * 1.1, cols, [0, .6, 1])))
        for _ in range(26 if golden else 14):          # browned spots / freckles
            a, d = rg.uniform(0, 2 * math.pi), R * math.sqrt(rg.uniform(0, .8))
            sp = skia.Paint(AntiAlias=True, Color4f=c4((.45, .24, .08) if golden else (.85, .62, .3), .35 if golden else .4),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.2))
            c.drawCircle(d * math.cos(a), d * math.sin(a), rg.uniform(1.5, 3.4), sp)
        if golden:   # a soft butter shine
            c.drawOval(skia.Rect(-14, -18, 6, -8), skia.Paint(AntiAlias=True, Color4f=c4((1, .95, .75), .35),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    return surf.makeImageSnapshot()
GOLD, PALE = face_image(True), face_image(False)

BURN_T = [0.0]
def pan_back(c, x, y, dy, tilt):
    c.save(); c.translate(x, y + dy); c.rotate(tilt)
    # shadow
    c.drawOval(skia.Rect(-44, 18, 48, 40), skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .55),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    # burner glow under the pan
    fl = .75 + .25 * math.sin(7.3 * x + 11 * BURN_T[0])
    c.drawOval(skia.Rect(-40, 20, 40, 42), skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
               Color4f=c4((1, .45, .12), .55 * fl), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
    # handle (brass) to the right
    c.drawLine(34, 6, 64, -6, skia.Paint(AntiAlias=True, StrokeWidth=9, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.2, .14, .08), .9)))
    c.drawLine(34, 6, 64, -6, skia.Paint(AntiAlias=True, StrokeWidth=7, StrokeCap=skia.Paint.kRound_Cap, Shader=skia.GradientShader.MakeLinear(
        [(0, -8), (0, 8)], [rgb((1, .88, .58)), rgb((.62, .42, .17))])))
    # body
    p = skia.Path(); p.moveTo(-42, 0); p.lineTo(42, 0); p.lineTo(35, 24); p.quadTo(0, 30, -35, 24); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-42, 0), (42, 0)], [rgb((.17, .15, .14)), rgb((.33, .3, .27)), rgb((.12, .1, .09))], [0, .4, 1])))
    # inside of the pan (rim ellipse)
    c.drawOval(skia.Rect(-42, -11, 42, 11), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, -11), (0, 11)], [rgb((.05, .045, .04)), rgb((.2, .18, .16))])))
    c.drawOval(skia.Rect(-42, -11, 42, 11), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4,
               Color4f=c4((.86, .7, .45), .75)))
    c.restore()

def plaque(c, lab, x, y, dy, tilt):
    c.save(); c.translate(x, y + dy); c.rotate(tilt)
    pw = 46
    c.drawRoundRect(skia.Rect(-pw / 2, 9, pw / 2, 30), 3, 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, 9), (0, 30)], [rgb((.97, .82, .5)), rgb((.68, .48, .22))])))
    text(c, f"{lab[0]}{lab[1]}", 0, 27.5, F_PLQ, (.16, .1, .05), .95)
    c.restore()

def pancake(c, x, y, phi):
    s = math.sin(phi + EL)
    k = math.cos(phi + EL)
    b = max(1.2, PR * abs(s))
    top_vis = s > 0
    # face centres (screen y down): top face at -PT/2*k, bottom face at +PT/2*k
    yt, yb_ = y - PT / 2 * k, y + PT / 2 * k
    yv, yh = (yt, yb_) if top_vis else (yb_, yt)
    # which physical face is visible: the golden face is the "top" one at phi = 0
    golden_vis = top_vis
    edge = skia.Paint(AntiAlias=True, Color4f=c4((.72, .5, .25)))
    c.drawOval(skia.Rect(x - PR, yh - b, x + PR, yh + b), edge)
    lo, hi = min(yv, yh), max(yv, yh)
    c.drawRect(skia.Rect(x - PR, lo, x + PR, hi), edge)
    c.save(); c.translate(x, yv); c.scale(1, b / PR)
    c.drawImageRect(GOLD if golden_vis else PALE, skia.Rect(-PR - 2, -PR - 2, PR + 2, PR + 2), SAMP)
    c.restore()

def frame(f):
    t = f / FPS
    BURN_T[0] = 2 * math.pi * t / LOOP * 6
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH PANCAKE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER FLIPS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        st = []
        for lab, x, y, ph, r in PAN:
            st.append(state(t, ph, lab == ODD, lab))
        for (lab, x, y, ph, r), (dy, phi, pdy, tl) in zip(PAN, st):
            pan_back(c, x, y, pdy, tl)
            # sizzle glow under a freshly landed pancake
            d = since_land(t, ph)
            if d < .35:
                g = 1 - d / .35
                c.drawOval(skia.Rect(x - 38, y - 9 + pdy, x + 38, y + 9 + pdy), skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus,
                           Color4f=c4((1, .62, .25), .35 * g), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
        air = [st[i][0] < -14 for i in range(len(PAN))]
        for i in range(len(PAN)):              # resting pancakes, then plaques, then the airborne ones on top
            if not air[i]: pancake(c, PAN[i][1], PAN[i][2] - 4 + st[i][0], st[i][1])
        for (lab, x, y, ph, r), (dy, phi, pdy, tl) in zip(PAN, st):
            plaque(c, lab, x, y, pdy, tl)
        for i in range(len(PAN)):
            if air[i]: pancake(c, PAN[i][1], PAN[i][2] - 4 + st[i][0], st[i][1])
        yb = Y0 + (NR - 1) * SY + 100
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
def pat(f0, dur=.32, seed=0, hollow=False):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    if hollow:   # higher wooden tock
        body = np.sin(2 * np.pi * f0 * 2 * t) * np.exp(-t * 40) + .35 * np.sin(2 * np.pi * f0 * 5.1 * t) * np.exp(-t * 70)
    else:        # soft padded pat
        body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 34) + .2 * np.sin(2 * np.pi * f0 * 2.3 * t) * np.exp(-t * 60)
    low = np.sin(2 * np.pi * 85 * t) * np.exp(-t * 30) * .55
    n = rg.standard_normal(len(t))
    sizzle = np.diff(np.diff(n, prepend=0), prepend=0) * .06 * np.exp(-t * 9) * np.minimum(1, t * 40)
    return (body + low + sizzle) * np.minimum(1, t * 4000)
def whoosh(seed=0, dur=.3):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(seed + 99).standard_normal(len(t))
    spec = np.fft.rfft(n); fr = np.fft.rfftfreq(len(n), 1 / SR)
    spec *= np.exp(-((fr - 900) / 500) ** 2)
    return np.fft.irfft(spec, len(n)) / 8 * np.sin(np.pi * t / dur) ** 2

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, r) in enumerate(PAN):
        for tt, kind in landings(ph): ev.append((tt, k, kind))
    lt = np.array([e[0] for e in ev if e[2] == "land"])
    for tt, k, kind in ev:
        lab, x, y, ph, r = PAN[k]
        odd = lab == ODD
        if kind == "toss":
            m.add(whoosh(k), tt, .12, x); continue
        dens = (np.abs(lt - tt) < .06).sum()
        m.add(pat(note(NR - 1 - r + 3, 196.0) * (1 + .004 * (x - 540) / 112), seed=k, hollow=odd), tt,
              (.62 if odd else .5) / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)          # soft sizzle bed
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 3500) / 2500) ** 2) * .5 + np.exp(-((fr - 240) / 200) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_pancakes.mp4"))
