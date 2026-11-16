"""SPOT IT v3 (13:00, 2026-11-16): 52 doors in a brick-bond facade, one opens the wrong way.
Rule type: SIDE (which way it swings). Arrangement: staggered brick-bond rows 7/8/7/8/7/8/7 (each door has its own
lintel plaque "C4" because the rows are offset). Rows alternate hinges: odd rows open from the left, even rows from
the right (a zig-zag pattern). Every door swings wide open and slams shut every 3 or 4 s from a random phase, so
light flickers across the whole facade; the odd door (G4) opens from the LEFT in a right-hinged row.
Sound: a soft wooden clack when each door shuts (pentatonic by row, panned by x); the odd door's clack has a small
brass latch ting on top (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/doors"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
WIDTHS = [7, 8, 7, 8, 7, 8, 7]
NR = len(WIDTHS)
LET = "ABCDEFGH"
SX, SY = 110, 136
Y0 = 528
DW, DH = 78, 104                       # door leaf
TMAX = math.radians(80)
ODD = (os.environ.get("OL", "G"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "16")))

DOORS = []                             # (label, x, y, side, period, phase)
for r, n in enumerate(WIDTHS):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y0 + r * SY
        side = 1 if r % 2 == 0 else -1          # +1: hinge on the left
        lab = (LET[i], r + 1)
        if lab == ODD: side = -side
        P = float(rng.choice([3.0, 4.0]))
        DOORS.append((lab, x, y, side, P, rng.uniform(0, 1)))

def ease_out(u): return 1 - (1 - u) ** 3
def theta(P, ph, t):
    """door angle (0 shut .. TMAX wide open) and whether it just shut"""
    u = (t / P + ph) % 1.0
    if u < .30: return TMAX * ease_out(u / .30)
    if u < .50: return TMAX * (1 - .05 * math.sin(math.pi * (u - .30) / .20))
    if u < .76: v = (u - .50) / .26; return TMAX * (1 - v * v)
    if u < .86: v = (u - .76) / .10; return math.radians(7) * math.sin(math.pi * v) * (1 - v)
    return 0.0
def shut_times(P, ph):
    out = []
    for k in range(-2, int(LOOP / P) + 3):
        tt = (k + .76 - ph) * P
        if 0 <= tt < LOOP: out.append(tt)
    return out

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
def leaf_image():
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(DW * S, DH * S))
    with surf as c:
        c.scale(S, S)
        c.drawRect(skia.Rect(0, 0, DW, DH), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (DW, DH)], [rgb((.97, .91, .8)), rgb((.88, .8, .66)), rgb((.78, .69, .55))], [0, .55, 1])))
        def inset(x0, y0, x1, y1):
            c.drawRect(skia.Rect(x0, y0, x1, y1), skia.Paint(AntiAlias=True, Color4f=c4((.72, .62, .48), .55)))
            c.drawRect(skia.Rect(x0 + 2.2, y0 + 2.2, x1 - 1, y1 - 1), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                [(x0, y0), (x1, y1)], [rgb((.99, .95, .86)), rgb((.86, .78, .64))])))
        inset(11, 10, DW - 11, 40)
        inset(11, 50, DW - 11, DH - 10)
        # centred brass push plate (symmetric: a closed door never shows its hinge side)
        c.drawRoundRect(skia.Rect(DW / 2 - 4, 41, DW / 2 + 4, 49), 2, 2, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, 41), (0, 49)], [rgb((1, .86, .55)), rgb((.66, .46, .2))])))
        c.drawRect(skia.Rect(0, 0, DW, DH), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                                                       Color4f=c4((.45, .35, .24), .7)))
    return surf.makeImageSnapshot()
LEAF = leaf_image()

def room_image():
    """the lit room behind each door"""
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(DW * S, DH * S))
    with surf as c:
        c.scale(S, S)
        c.drawRect(skia.Rect(0, 0, DW, DH), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (DW / 2, DH * .38), DH * .8, [rgb((1, .9, .62)), rgb((.98, .66, .28)), rgb((.55, .27, .08))], [0, .45, 1])))
        c.drawRect(skia.Rect(0, DH * .78, DW, DH), skia.Paint(Color4f=c4((.45, .2, .06), .45)))
    return surf.makeImageSnapshot()
ROOM = room_image()
SRC = [skia.Point(0, 0), skia.Point(DW * S, 0), skia.Point(DW * S, DH * S), skia.Point(0, DH * S)]

def door_static(c, lab, x, y):
    L, T = x - DW / 2, y - DH / 2
    # shadowed recess + cream trim (architrave)
    c.drawRect(skia.Rect(L - 7, T - 7, L + DW + 7, T + DH + 3), skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .55),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.drawRect(skia.Rect(L - 6, T - 6, L + DW + 6, T + DH), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(L, T), (L + DW, T + DH)], [rgb((.62, .48, .3)), rgb((.4, .29, .17))])))
    # sill
    c.drawRect(skia.Rect(L - 10, T + DH, L + DW + 10, T + DH + 6), skia.Paint(AntiAlias=True, Color4f=c4((.55, .42, .27))))
    # plaque
    pw = 48
    c.drawRoundRect(skia.Rect(x - pw / 2, T - 37, x + pw / 2, T - 10), 4, 4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, T - 37), (0, T - 10)], [rgb((.95, .78, .45)), rgb((.66, .47, .22))])))
    text(c, f"{lab[0]}{lab[1]}", x, T - 15, F_PLQ, (.16, .1, .05), .92)

def door_dynamic(c, x, y, side, th):
    L, T = x - DW / 2, y - DH / 2
    o = math.sin(th)
    # room behind
    c.drawImageRect(ROOM, skia.Rect(L, T, L + DW, T + DH), SAMP)
    # light spill (additive) when open
    if o > .02:
        hx = L + DW - DW * (1 - math.cos(th)) / 2 if side > 0 else L + DW * (1 - math.cos(th)) / 2
        p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Color4f=c4((.9, .52, .18), .30 * o),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        c.drawOval(skia.Rect(hx - 34, T + DH - 6, hx + 34, T + DH + 22), p)
        p2 = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Color4f=c4((.8, .45, .15), .16 * o),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
        c.drawRect(skia.Rect(hx - 30, T - 4, hx + 30, T + DH), p2)
    # the leaf, hinged at the left (side=+1) or right (side=-1), its free edge swinging toward us
    xh = L if side > 0 else L + DW
    xf = xh + side * DW * math.cos(th)
    grow = .17 * o
    dst = [skia.Point(xh, T), skia.Point(xf, T - DH * grow / 2), skia.Point(xf, T + DH * (1 + grow / 2)), skia.Point(xh, T + DH)]
    if side < 0: dst = [dst[1], dst[0], dst[3], dst[2]]
    m = skia.Matrix()
    m.setPolyToPoly(SRC, dst)
    # soft shadow the open leaf casts on the facade
    if o > .02:
        sh = skia.Path(); sh.addPoly([dst[0], dst[1], dst[2], dst[3]], True)
        sh.offset(-side * 4 * o + 2, 5)
        c.drawPath(sh, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .45 * o), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.save(); c.concat(m)
    c.drawImage(LEAF, 0, 0, SAMP)
    c.restore()
    if o > .02:
        q = skia.Path(); q.addPoly(dst, True)
        c.drawPath(q, skia.Paint(AntiAlias=True, Color4f=c4((.12, .07, .03), .42 * o)))
        # the leaf's thick edge
        c.drawLine(xf, T - DH * grow / 2, xf, T + DH * (1 + grow / 2),
                   skia.Paint(AntiAlias=True, StrokeWidth=1 + 5 * o, Color4f=c4((.55, .42, .28), .95)))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        # facade wall behind the doors
        c.drawRoundRect(skia.Rect(102, Y0 - 104, 978, Y0 + (NR - 1) * SY + 82), 18, 18, skia.Paint(AntiAlias=True,
                        Shader=skia.GradientShader.MakeLinear([(0, Y0 - 108), (0, Y0 + NR * SY)],
                        [rgb((.17, .12, .085)), rgb((.11, .08, .055))])))
        for r in range(NR):
            yy = Y0 + r * SY + DH / 2 + 3
            c.drawRect(skia.Rect(104, yy, 976, yy + 3), skia.Paint(Color4f=c4((.3, .22, .14), .8)))
        text(c, "WHICH DOOR OPENS", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "THE WRONG WAY?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for lab, x, y, side, P, ph in DOORS:
            door_static(c, lab, x, y)
        for lab, x, y, side, P, ph in DOORS:
            door_dynamic(c, x, y, side, theta(P, ph, t))
        yb = Y0 + (NR - 1) * SY + DH / 2 + 104
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
def clack(f0, dur=.16, seed=0):
    t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 45) + .35 * np.sin(2 * np.pi * f0 * 2.3 * t) * np.exp(-t * 80)
    low = np.sin(2 * np.pi * 85 * t) * np.exp(-t * 30) * .6
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 900) * .5
    return (body + low + np.diff(n, prepend=0) * .7) * np.minimum(1, t * 6000)
def ting(f0, dur=.45):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 9) + .35 * np.sin(2 * np.pi * f0 * 2.76 * t + 1) * np.exp(-t * 15)
    return s * np.minimum(1, t * 6000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, side, P, ph) in enumerate(DOORS):
        for tt in shut_times(P, ph): ev.append((tt, k))
    times = np.array([e[0] for e in ev])
    for tt, k in ev:
        lab, x, y, side, P, ph = DOORS[k]
        r = lab[1] - 1
        dens = (np.abs(times - tt) < .05).sum()
        m.add(clack(note(NR - 1 - r + 3, 196.0) * (1 + .004 * (x - 540) / 110), seed=k), tt, .5 / math.sqrt(dens), x)
        if lab == ODD:
            m.add(ting(note(r + 11, 261.63)), tt + .012, .2, x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 260) / 220) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/D_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_doors.mp4"))
