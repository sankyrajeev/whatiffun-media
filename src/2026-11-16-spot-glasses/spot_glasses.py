"""SPOT IT v3 (10:00) — BREAKS PHYSICS: 56 rocking glasses of tea, one's tea doesn't stay level.
v3 rules (v2 after review: bigger rocks, a rolling diagonal wave, tea dead level): big bold QUESTION headline, simple identical objects in one calm colour scheme (glass + amber tea on walnut
shelves), every object in big constant motion, randomly phased, and the odd one breaks a law you can SEE: in every glass
the tea surface stays level while the round-bottomed tumbler rolls ±26° on its shelf (with a little lagging slosh), but
in the odd glass the tea tilts WITH the glass, as if glued to it (gravity ignores it). Obvious at every rock extreme
(every 1-1.5 s), so once you see it you're sure.
7 columns (A-G) x 8 shelves (1-8). Each glass rocks 4-6 times per 12 s loop (seamless). Sound: a soft glass tink at
each right-hand extreme (pentatonic by shelf, panned by column) + a soft liquid bed; the odd glass gives a dull wooden
plok instead (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/glasses"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 7, 8
LET = "ABCDEFG"
SX, SY = 118, 122
X0 = 540 - 3 * SX
Y0 = 552                                   # first shelf top
RB = 36                                    # radius of the round bottom (rolling)
HB, HT, HH = 29, 34, 84                    # half-width bottom/top, glass height
ZB = math.sqrt(RB * RB - HB * HB)          # bottom corner y (local, below centre C)
WL = -14                                   # tea level on the axis (local y)
A = math.radians(float(os.environ.get("AMP", "34")))
ODD = (LET.index(os.environ.get("OL", "C")), int(os.environ.get("ON", "6")) - 1)
rng = np.random.default_rng(int(os.environ.get("SEED", "5")))
# every shelf rocks at its own tempo (4-6 rocks per loop) so neighbours on a shelf never knock into each other;
# phases = a loose wave along the shelf + noise (found by search_seeds(): no two glasses ever touch)
# v2 (after review): one tempo everywhere and a diagonal wave rolling across the shelves (a pattern to watch), plus
# a little noise so you still have to check each glass. Normal tea stays almost dead level (tiny slosh); bigger rocks.
REVS = np.full((NC, NR), 5)
PH0 = (np.arange(NC)[:, None] * -.38 + np.arange(NR)[None, :] * -.42
       + rng.normal(0, float(os.environ.get("NOISE", ".13")), size=(NC, NR)))
JIT = rng.uniform(-6, 6, size=(NC, NR))

def phase(c, r, t): return PH0[c, r] + 2 * math.pi * REVS[c, r] * t / LOOP
def tilt(c, r, t): return A * math.sin(phase(c, r, t))
def surface(c, r, t):
    """world angle of the tea surface (0 = level)"""
    th = tilt(c, r, t)
    if (c, r) == ODD: return th                          # glued to the glass: tilts with it
    return -.06 * A * math.sin(phase(c, r, t) - .9)     # stays level (tiny lagging slosh)

def base(c, r):
    return X0 + c * SX + (JIT[c, r] if c not in (0, NC - 1) else JIT[c, r] * .4), Y0 + r * SY

def outline(c, r, t, n=40):
    bx, by = base(c, r); th = tilt(c, r, t)
    cx, cy = bx + RB * th, by - RB
    pts = [(-HT, TOP0)] + [(-HB + 2 * HB * k / n, math.sqrt(max(0, RB * RB - (-HB + 2 * HB * k / n) ** 2))) for k in range(n + 1)] + [(HT, TOP0)]
    pts += [(HT - 2 * HT * k / n, TOP0) for k in range(1, n)]
    pts += [(-HT + (HT - HB) * k / n, TOP0 + (ZB - TOP0) * k / n) for k in range(n)] + [(HT - (HT - HB) * k / n, TOP0 + (ZB - TOP0) * k / n) for k in range(n)]
    P = np.array(pts); cs, sn = math.cos(th), math.sin(th)
    return np.c_[cx + P[:, 0] * cs - P[:, 1] * sn, cy + P[:, 0] * sn + P[:, 1] * cs]
TOP0 = -HH + ZB
def min_gap():
    g = 1e9
    for f in range(0, TOTAL, 2):
        t = f / FPS
        for r in range(NR):
            O = [outline(c, r, t) for c in range(NC)]
            for c in range(NC - 1):
                d = O[c + 1][:, None, :] - O[c][None, :, :]
                g = min(g, np.sqrt((d ** 2).sum(-1)).min())
    return g

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LBL = font(TF_MONO, 32)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

def glass_path(inset=0.0):
    p = skia.Path()
    hb, ht = HB - inset, HT - inset
    rb = RB - inset
    zb = math.sqrt(rb * rb - hb * hb)
    top = -HH + ZB + inset * .3
    p.moveTo(-ht, top)
    p.lineTo(-hb, zb)
    a0 = math.degrees(math.atan2(zb, -hb)); a1 = math.degrees(math.atan2(zb, hb))
    p.arcTo(skia.Rect(-rb, -rb, rb, rb), a0, a1 - a0, False)
    p.lineTo(ht, top)
    return p
GP = glass_path(); GPI = glass_path(4.5)
TOP = -HH + ZB

def shelf(cv, r):
    y = Y0 + r * SY
    x0, x1 = X0 - 58, X0 + (NC - 1) * SX + 58
    cv.drawRect(skia.Rect(x0, y + 4, x1, y + 26), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y, x1, y + 15), 3, 3), skia.Paint(AntiAlias=True,
                 Shader=skia.GradientShader.MakeLinear([(0, y), (0, y + 15)],
                 [rgb((.45, .3, .19)), rgb((.3, .19, .11)), rgb((.17, .1, .06))], [0, .35, 1])))
    cv.drawLine(x0 + 3, y + .8, x1 - 3, y + .8, skia.Paint(AntiAlias=True, StrokeWidth=1.4, Color4f=skia.Color4f(.95, .78, .5, .45)))

def draw_glass(cv, c, r, t):
    bx, by = base(c, r)
    th = tilt(c, r, t)
    cx, cy = bx + RB * th, by - RB          # rolling without slipping on the round bottom
    # contact shadow
    cv.drawOval(skia.Rect(cx - 30, by - 4, cx + 30, by + 5), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    cv.save()
    cv.translate(cx, cy); cv.rotate(math.degrees(th))
    # back glass tint
    cv.drawPath(GP, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.9, .85, .75, .07)))
    # tea
    rel = surface(c, r, t) - th
    cv.save(); cv.clipPath(GPI, skia.ClipOp.kIntersect, True)
    cv.save(); cv.translate(0, WL); cv.rotate(math.degrees(rel))
    cv.drawRect(skia.Rect(-120, 0, 120, 160), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (0, 70)], [rgb((.95, .62, .22), .95), rgb((.72, .38, .1), .95), rgb((.45, .2, .05), .95)], [0, .5, 1])))
    cv.drawRect(skia.Rect(-120, 0, 120, 7), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .82, .5, .55)))
    cv.drawLine(-120, 0, 120, 0, skia.Paint(AntiAlias=True, StrokeWidth=2.6, Color4f=skia.Color4f(1, .93, .75, .95)))
    cv.restore(); cv.restore()
    # glass walls
    cv.drawPath(GP, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.4, StrokeJoin=skia.Paint.kRound_Join,
                               Color4f=skia.Color4f(.93, .9, .84, .62)))
    cv.drawLine(-HT, TOP, HT, TOP, skia.Paint(AntiAlias=True, StrokeWidth=3.6, StrokeCap=skia.Paint.kRound_Cap,
                                              Color4f=skia.Color4f(.98, .95, .88, .8)))
    cv.drawLine(-HT + 9, TOP + 10, -HB + 8, ZB - 14, skia.Paint(AntiAlias=True, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap,
                                                              Color4f=skia.Color4f(1, 1, 1, .32)))
    cv.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=2)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=2)
        for ci in range(NC):
            text(c, LET[ci], X0 + ci * SX, Y0 - HH - 40, F_LBL, CREAM, .7)
        for r in range(NR):
            shelf(c, r)
            text(c, str(r + 1), X0 - 78, Y0 + r * SY - 34, F_LBL, CREAM, .62)
            for ci in range(NC):
                draw_glass(c, ci, r, t)
        yb = Y0 + (NR - 1) * SY + 80
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
def tink(f0, dur=.25):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 26) + .45 * np.sin(2 * np.pi * f0 * 2.71 * t + 1) * np.exp(-t * 40)
    n = np.random.default_rng(int(f0)).standard_normal(len(t)) * np.exp(-t * 1800) * .3
    return (s + np.diff(n, prepend=0) * .5) * np.minimum(1, t * 6000)
def plok(f0=180, dur=.3):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * (f0 * t + 40 * (1 - np.exp(-t * 30)) / 30)) * np.exp(-t * 22)
    return (s + .3 * np.sin(2 * np.pi * f0 * 1.5 * t) * np.exp(-t * 35)) * np.minimum(1, t * 5000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for r in range(NR):
        for ci in range(NC):
            n = REVS[ci, r]
            b = (PH0[ci, r] - math.pi / 2) / (2 * math.pi)    # sin(phase) = 1 at phase = pi/2 + 2 pi k
            for k in range(-2, n + 3):
                tt = (k - b) * LOOP / n
                if 0 <= tt < LOOP: ev.append((tt, ci, r))
    times = np.array([e[0] for e in ev])
    for tt, ci, r in ev:
        x = base(ci, r)[0]
        dens = (np.abs(times - tt) < .04).sum()
        if (ci, r) == ODD:
            m.add(plok(), tt, .3, x)
        else:
            m.add(tink(note(NR - 1 - r + 8, 261.63) * (1 + .003 * ci)), tt, .42 / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    # soft liquid bed: band-passed noise with a slow periodic swell (loop-exact)
    rg = np.random.default_rng(3)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 420) / 300) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    tt = np.arange(n) / SR
    sw = .8 + .2 * np.sin(2 * np.pi * 5 * tt / LOOP)
    m.L += bed * .045 * sw; m.R += np.roll(bed, 7000) * .045 * sw
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "gap":
        print(os.environ.get("SEED"), round(min_gap(), 1)); sys.exit()
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/G_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_glasses.mp4"))
