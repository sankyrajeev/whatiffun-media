"""SPOT IT v3 (13:00, 2026-11-19): 56 umbrellas in WAVE ROWS, one turns inside out.
Rule type: INSIDE OUT (shape inversion: every canopy pops open as a dome; one pops into a cup every time).
Arrangement: WAVE ROWS (7 columns A-G x 8 rows, each row a soft sine wave; letters on top, numbers on the left).
Every umbrella opens and closes once every 3 s (4 cycles per 12 s loop, random phase) and sways all the time in a
diagonal wave. While open, every canopy gets a gust that flattens it for a moment (decoy); the odd one's gust blows it
INSIDE OUT (ribs up, canopy a cup) for ~1 s, then it pops back before closing.
Sound: a soft fabric 'fwump' on every opening (pentatonic by row, panned by x, density-normalised), a swish + click on
every close, a light rain bed; the odd umbrella adds a twangy flap when it flips (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/umbrellas"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 7, 8
LET = "ABCDEFG"
SX, SY = 118, 124
X0 = 540 + 14 - (NC - 1) / 2 * SX       # leave room for row numbers on the left
Y0 = 512                                 # canopy apex of row 1
P = 3.0
PS = 2.4                                 # sway period (5 per loop)
HW, DOME, SHAFT = 53, 34, 80
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "19")))

U = []   # (label, x, y, phase, gust_u, sway_phase, row)
for r in range(NR):
    for i in range(NC):
        x = X0 + i * SX
        y = Y0 + r * SY + 15 * math.sin(2 * math.pi * i / 6.5 + r * .9)
        ph = rng.uniform(0, 1)
        gu = rng.uniform(.24, .44)
        sp = (.11 * i + .07 * r + rng.uniform(0, .12)) % 1
        U.append(((LET[i], r + 1), x, y, ph, gu, sp, r))
for k, u in enumerate(U):
    if u[0] == ODD: U[k] = (u[0], u[1], u[2], u[3], .22, u[5], u[6])

O0, O1, C0, C1 = .0, .11, .66, .78       # opening / closing windows (fraction of cycle)
INV0, INV1 = .22, .55                    # odd one inside out

def bump(u, c, w): return math.exp(-((u - c) / w) ** 2)
def state(t, ph, gu, odd):
    """openness o, curvature c (1 dome, -1 cup), extra tilt"""
    u = (t / P + ph) % 1.0
    if u < O1:
        v = u / O1; o = ss(v) + .10 * math.sin(math.pi * v) * (v > .6)
    elif u < C0: o = 1.0
    elif u < C1: o = 1 - ss((u - C0) / (C1 - C0))
    else: o = 0.0
    o = max(0, min(1.06, o))
    if odd:
        if u < INV0: c = 1.0
        elif u < INV0 + .035: c = 1 - 2.25 * ss((u - INV0) / .035)
        elif u < INV1: c = -1 - .1 * math.cos(2 * math.pi * (u - INV0) / .09) * math.exp(-(u - INV0) * 9)
        elif u < INV1 + .04: c = -1 + 2.2 * ss((u - INV1) / .04)
        else: c = 1.0 + .12 * bump(u, INV1 + .06, .02)
        c += .05 * math.sin(2 * math.pi * u * 9) * (INV0 < u < INV1)
    else:
        c = 1 - .62 * bump(u, gu, .04) + .1 * bump(u, gu + .07, .02)   # gust flattens it, then it springs back
    # a little shake on opening / gust
    tilt = 7 * math.sin(math.pi * min(1, u / .14)) * (u < .14) * math.sin(u * 60)
    return o, c, tilt, u

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
CREAMC = (.97, .92, .82)
AMB = (.90, .60, .26)

def canopy_pts(o, c):
    hw = 8 + (HW - 8) * min(1, o)
    hw *= 1 + .06 * max(0, -c)                      # an inverted canopy flares a little wider
    ty = DOME * c * min(1, o) + (1 - min(1, o)) * 64   # closed: the cloth hangs down the shaft
    n = 24
    top = []
    for j in range(n + 1):
        uu = -1 + 2 * j / n
        top.append((uu * hw, ty * (1 - math.sqrt(max(0, 1 - uu * uu)))))
    return hw, ty, top

def umbrella(c, x, y, o, cc, tilt, sway):
    c.save(); c.translate(x, y + SHAFT * .55); c.rotate(sway + tilt); c.translate(0, -SHAFT * .55)
    hw, ty, top = canopy_pts(o, cc)
    # soft shadow behind
    c.drawOval(skia.Rect(-hw * .9, ty * .2 + 4, hw * .9, ty * .2 + 30), skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .35),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
    # shaft + J handle
    sh = skia.Paint(AntiAlias=True, StrokeWidth=4.2, StrokeCap=skia.Paint.kRound_Cap, Style=skia.Paint.kStroke_Style,
                    Color4f=c4((.55, .44, .3)))
    c.drawLine(0, -12, 0, SHAFT, sh)
    hp = skia.Path(); hp.moveTo(0, SHAFT - 4); hp.cubicTo(0, SHAFT + 17, 22, SHAFT + 17, 22, SHAFT + 3)
    c.drawPath(hp, skia.Paint(AntiAlias=True, StrokeWidth=8, StrokeCap=skia.Paint.kRound_Cap, Style=skia.Paint.kStroke_Style,
               Color4f=c4((.62, .36, .16))))
    c.drawPath(hp, skia.Paint(AntiAlias=True, StrokeWidth=2.5, StrokeCap=skia.Paint.kRound_Cap, Style=skia.Paint.kStroke_Style,
               Color4f=c4((.95, .7, .42), .5)))
    # canopy path: top profile + scalloped edge
    nsc = 4
    path = skia.Path(); path.moveTo(*top[0])
    for p in top[1:]: path.lineTo(*p)
    dep = 7 * min(1, o) * (1 if cc >= 0 else -.4)
    for k in range(nsc, 0, -1):
        xa, xb = -hw + 2 * hw * k / nsc, -hw + 2 * hw * (k - 1) / nsc
        path.quadTo((xa + xb) / 2, ty - dep * 2, xb, ty)
    path.close()
    inside = cc < 0
    dark = .84 if inside else 1.0
    c.save(); c.clipPath(path, doAntiAlias=True)
    c.drawRect(skia.Rect(-hw - 4, min(0, ty) - 80, hw + 4, max(0, ty) + 80), skia.Paint(Color4f=c4([v * dark for v in CREAMC])))
    for k in range(nsc):                       # amber panels (alternate)
        if k % 2: continue
        xa, xb = -hw + 2 * hw * k / nsc, -hw + 2 * hw * (k + 1) / nsc
        q = skia.Path(); q.moveTo(0, 0); q.lineTo(xa * 1.25, ty * 1.6 + (8 if ty >= 0 else -8)); q.lineTo(xb * 1.25, ty * 1.6 + (8 if ty >= 0 else -8)); q.close()
        c.drawPath(q, skia.Paint(AntiAlias=True, Color4f=c4([v * dark for v in AMB])))
    # shading: light from the top left
    c.drawRect(skia.Rect(-hw - 4, min(0, ty) - 80, hw + 4, max(0, ty) + 80), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(-hw, min(0, ty)), (hw, max(0, ty) + 10)], [skia.Color4f(1, 1, 1, .22).toColor(), skia.Color4f(0, 0, 0, 0).toColor(),
                                                     skia.Color4f(0, 0, 0, .35).toColor()], [0, .45, 1])))
    c.restore()
    # ribs
    rp = skia.Paint(AntiAlias=True, StrokeWidth=1.6, Style=skia.Paint.kStroke_Style, Color4f=c4((.35, .22, .1), .55))
    for k in range(1, nsc):
        xk = -hw + 2 * hw * k / nsc
        uu = xk / hw
        c.drawLine(0, 0, xk, ty * (1 - math.sqrt(max(0, 1 - uu * uu))) + (ty - ty * (1 - math.sqrt(max(0, 1 - uu * uu)))) * .0, rp) if False else None
        c.drawLine(0, 0, xk, ty, rp)
    c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8, Color4f=c4((.3, .18, .08), .6)))
    # ferrule on top
    c.drawLine(0, 0, 0, -13, skia.Paint(AntiAlias=True, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.86, .7, .45))))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH UMBRELLA", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "TURNS INSIDE OUT?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for i in range(NC):
            text(c, LET[i], X0 + i * SX, 436, F_LAB, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 96, Y0 + r * SY + 46, F_LAB, AMBER, .9)
        for lab, x, y, ph, gu, sp, r in U:
            o, cc, tl, u = state(t, ph, gu, lab == ODD)
            sway = 10 * math.sin(2 * math.pi * (t / PS + sp)) * (1.0 if o > .5 else 1.25)
            umbrella(c, x, y, o, cc, tl, sway)
        yb = 1532
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 52, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 50, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def band(n, f0, bw, seed):
    x = np.random.default_rng(seed).standard_normal(n)
    sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    sp *= np.exp(-((fr - f0) / bw) ** 2)
    y = np.fft.irfft(sp, n); return y / (np.abs(y).max() + 1e-9)
def fwump(f0, seed, dur=.35):
    t = np.arange(int(dur * SR)) / SR
    cloth = band(len(t), 700, 500, seed) * np.exp(-t * 18) * np.minimum(1, t * 300) * .5
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 26) * .55 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 22) * .5
    return (cloth + body) * np.minimum(1, t * 3000)
def swish(seed, dur=.3):
    t = np.arange(int(dur * SR)) / SR
    s = band(len(t), 1800, 900, seed + 7) * np.sin(np.pi * t / dur) ** 2 * .35
    clk = np.zeros(len(t)); k = int(.22 * SR); tt = t[:len(t) - k]
    clk[k:] = (np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 300)) * .35
    return s + clk
def flap(seed, dur=.45):
    t = np.arange(int(dur * SR)) / SR
    cloth = band(len(t), 450, 350, seed + 11) * np.exp(-t * 10) * np.minimum(1, t * 200) * .8
    twang = np.sin(2 * np.pi * (620 * t - 120 * t * t)) * np.exp(-t * 9) * .4
    return cloth + twang
def events(ph, gu, odd):
    ev = []
    for k in range(-2, int(LOOP / P) + 3):
        for du, kind in ((O1 * .8, "open"), (C0 + .02, "close")) + (((INV0 + .01, "flip"),) if odd else ()):
            tt = (k + du - ph) * P
            if 0 <= tt < LOOP: ev.append((tt, kind))
    return ev

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, gu, sp, r) in enumerate(U):
        for tt, kind in events(ph, gu, lab == ODD): ev.append((tt, k, kind))
    ot = np.array([e[0] for e in ev if e[2] == "open"])
    for tt, k, kind in ev:
        lab, x, y, ph, gu, sp, r = U[k]
        odd = lab == ODD
        if kind == "close": m.add(swish(k), tt, .16, x); continue
        if kind == "flip": m.add(flap(k), tt, .55, x); continue
        dens = (np.abs(ot - tt) < .06).sum()
        m.add(fwump(note(NR - 1 - r + 2, 196.0), k), tt, .55 / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)          # light rain bed (seamless: generated at loop length)
    for ch, seed in ((m.L, 3), (m.R, 4)):
        x = np.random.default_rng(seed).standard_normal(n)
        sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
        sp *= np.exp(-((fr - 5000) / 3500) ** 2) + .25 * np.exp(-((fr - 400) / 300) ** 2)
        bed = np.fft.irfft(sp, n); bed /= np.abs(bed).max()
        ch += bed * .06
        # sparse rain ticks
        for tt in rg.uniform(0, LOOP, 260):
            i = int(tt * SR); L_ = 400; tt2 = np.arange(L_) / SR
            tick = np.sin(2 * np.pi * rg.uniform(2500, 4200) * tt2) * np.exp(-tt2 * 900) * .05
            j = min(L_, n - i); ch[i:i + j] += tick[:j]
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_umbrellas.mp4"))
