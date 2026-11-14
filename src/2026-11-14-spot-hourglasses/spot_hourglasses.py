"""SPOT IT (13:00) — BREAKS PHYSICS: 48 walnut-and-glass hourglasses on 6 walnut shelves (8 per shelf, A–H × 1–6).
Each one drains for 6 s, then tumbles end over end toward you (a 0.5 s flip about its horizontal axis) and drains
again. The flips roll across the cabinet in a diagonal wave (one diagonal every 6/13 s), so the sand levels form a
sliding rainbow gradient. E3 breaks physics: its sand trickles UP — it piles against the top cap and empties the
bottom bulb, flipping (in step with its diagonal) when its TOP is full. At frame 0 it is half/half like its
diagonal, so it looks the same until the streams are spotted.
Sound: a soft wooden knock + glass tink per hourglass as it lands its flip (pentatonic by shelf, panned by x,
density-normalised) over a faint periodic sand hiss; E3's landing is a hollow rising glass swell (audio clue).
13:00 = A/B countdown variant: slim 12 -> 0 ring above. Every motion is periodic in 6 s, so frame 0 == frame N."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spoth"
LOOP = 12.0
P = 6.0                         # drain + flip period
FD = 0.5 / P                    # flip fraction of the cycle
TOTAL = int(LOOP * FPS)
NC, NR = 8, 6
LETTERS = "ABCDEFGH"
DX, Y0, RP = 104, 712, 164
X0 = 540 - DX * (NC - 1) / 2
ODD = (4, 2)                    # E3 (diagonal 6 -> half/half at t = 0)
H, WN, WB, CAP = 50.0, 2.6, 30.0, 10.0   # bulb height, neck half-width, bulb half-width, cap thickness

def pos(c, r): return X0 + c * DX, Y0 + r * RP
def offset(c, r): return P * (c + r) / 13.0
def cycle(c, r, t):
    u = ((t - offset(c, r)) / P) % 1.0
    if u < FD: return True, u / FD, 0.0          # flipping: progress, sand all in local bottom
    return False, 0.0, 1 - (u - FD) / (1 - FD)  # draining: top fraction (local frame)

# bulb profile: half-width at distance s from the neck (0..H)
SS = np.linspace(0, H, 400)
def wid(s):
    x = np.clip(s / H, 0, 1)
    w = WN + (WB - WN) * np.sin(np.pi / 2 * np.clip(x / .72, 0, 1)) ** .9
    tail = x > .72
    w = np.where(tail, WB * np.sqrt(np.clip(1 - ((x - .72) / .36) ** 2 * .55, 0, 1)), w)
    return w
WS = wid(SS)
VOL = np.concatenate([[0], np.cumsum((WS[1:] ** 2 + WS[:-1] ** 2) / 2 * np.diff(SS))])
VOL /= VOL[-1]
def h_from_neck(f): return float(np.interp(f, VOL, SS))            # sand against the neck, fraction f
def h_from_cap(f): return float(np.interp(1 - f, VOL, SS))     # sand against the cap: fills s in [this, H]

def bulb_path():
    p = skia.Path()
    s = np.linspace(0, H, 80); w = wid(s)
    p.moveTo(-w[-1], -H)
    for si, wi in zip(s[::-1], w[::-1]): p.lineTo(-wi, -si)
    for si, wi in zip(s, w): p.lineTo(-wi, si)
    for si, wi in zip(s[::-1], w[::-1]): p.lineTo(wi, si)
    for si, wi in zip(s, w): p.lineTo(wi, -si)
    p.close(); return p
BULB = bulb_path()

BG = background(1080)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
F_LBL = font(TF_MONO, 26); F_NUM = font(TF_MONO, 24)
F_CD = font(TF_SERIF, 34)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def P_(col, a=1.0): return skia.Paint(AntiAlias=True, Color=rgb(col, a))

def sand_colour(c, r):
    u = (c + r) / 12.0
    return hsv(40 - 150 * u, .62, 1.0)    # amber -> coral -> magenta -> violet along the flip wave

RNG = np.random.default_rng(7)
SPECK = [(RNG.uniform(-WB, WB), RNG.uniform(-H, H), RNG.uniform(.6, 1.3), RNG.uniform(-1, 1)) for _ in range(140)]

def draw_sand(c, top, col, t, flowing, seed, rev=False):
    """Local frame, gravity +y. Neck at (0,0); top bulb y<0, bottom bulb y>0."""
    dk = [v * .62 for v in col]; hi = [min(1, v * .7 + .38) for v in col]
    fill = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-WB, 0), (WB, 0)], [rgb(dk), rgb(col), rgb(hi), rgb(col), rgb(dk)], [0, .25, .45, .7, 1]))
    c.save(); c.clipPath(BULB, doAntiAlias=True)
    sand = skia.Path()
    if top > .002:                                     # top bulb: against the neck, a funnel dip while draining
        ht = h_from_neck(top); wt = float(wid(ht)); dip = min(ht * .5, 8.0) if flowing else 0
        if rev: dip = -min(ht * .5, 7.0) if flowing else 0      # a mound growing UP instead of a funnel
        sand.moveTo(-WB - 2, 1)
        n = 24
        for k in range(n + 1):
            x = -wt + 2 * wt * k / n
            sand.lineTo(x, -ht + dip * max(0, 1 - abs(x) / (wt * .75)) ** 1.6)
        sand.lineTo(WB + 2, 1); sand.close()
    bot = 1 - top
    if bot > .002:                                     # bottom bulb: against the cap, a cone where it lands
        hb = h_from_cap(bot); wb = float(wid(hb)); cone = min((H - hb) * .6, 10.0) if flowing else 3.0
        if rev and flowing: cone = -min((H - hb) * .5, 8.0)      # a dip where it is sucked away
        sand.moveTo(-WB - 2, H + 2)
        n = 24
        for k in range(n + 1):
            x = -wb + 2 * wb * k / n
            sand.lineTo(x, hb - cone * max(0, 1 - abs(x) / wb) ** 1.3)
        sand.lineTo(WB + 2, H + 2); sand.close()
    c.save(); c.clipPath(sand, doAntiAlias=True)
    c.drawPaint(fill)
    for (sx, sy, sr, sh) in SPECK:
        c.drawCircle(sx, sy, sr, P_([min(1, v * (1 + .35 * sh)) for v in col], .55))
    c.restore()
    if flowing and top > .002 and bot < .998:          # the falling stream + grains
        hb = h_from_cap(bot)
        land = hb + (min((H - hb) * .5, 8.0) if rev else -min((H - hb) * .6, 10.0))
        c.drawLine(0, -1, 0, land, skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color=rgb(hi, .8)))
        for k in range(7):
            v = ((t * 2.4 + k / 7 + seed) % 1.0)
            if rev: v = 1 - v                          # grains rise
            c.drawCircle(.6 * math.sin(k * 2.1), v * land, 1.25, P_(hi, .95))
    c.restore()

def draw_frame_parts(c, cosv, front):
    """Glass + walnut caps + posts in the hourglass's frame, scaled vertically by cosv (tumble)."""
    pass

def draw_hourglass(c, x, y, c_, r, t):
    flipping, prog, top = cycle(c_, r, t)
    col = sand_colour(c_, r)
    odd = (c_, r) == ODD
    if flipping:
        e = ss(prog); e = e + .06 * math.sin(math.pi * e) * (1 - e)   # tiny overshoot feel
        th = math.pi * e
        lift = 10 * math.sin(math.pi * e)
        top_l = 0.0 if not odd else 1.0          # normal: all sand in bottom as it turns; odd: all at top
    else:
        th, lift = 0.0, 0.0
        top_l = top if not odd else 1 - top      # odd: the top bulb FILLS from below
    cv = math.cos(th)
    ext = H + CAP
    # shadow on the shelf
    sw = 36
    c.drawOval(skia.Rect(x - sw, y + ext - 4, x + sw, y + ext + 6),
               skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45 - .15 * abs(math.sin(th))),
                          MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    c.save(); c.translate(x, y - lift)
    sv = cv if abs(cv) > .02 else math.copysign(.02, cv if cv != 0 else 1)
    c.save(); c.scale(1, sv)
    # back posts
    post = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-4, 0), (4, 0)], [rgb((.25, .14, .07)), rgb((.62, .42, .24)), rgb((.25, .14, .07))]))
    for px in (-WB - 6, WB + 6):
        c.save(); c.translate(px, 0); c.drawRect(skia.Rect(-3.2, -H - 1, 3.2, H + 1), post); c.restore()
    # glass back + sand + glass front
    c.drawPath(BULB, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.75, .85, .95, .07)))
    draw_sand(c, top_l, col, t, not flipping, (c_ * 7 + r * 3) * .137, rev=odd)
    c.drawPath(BULB, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3,
                                Color4f=skia.Color4f(.9, .95, 1, .42)))
    for sgn in (-1, 1):                          # symmetric glints (look the same after the flip)
        g = skia.Path(); s = np.linspace(H * .25, H * .85, 20); w = wid(s)
        g.moveTo(-w[0] * .62, sgn * s[0])
        for si, wi in zip(s, w): g.lineTo(-wi * .62, sgn * si)
        c.drawPath(g, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                                 StrokeCap=skia.Paint.kRound_Cap, Color4f=skia.Color4f(1, 1, 1, .26)))
    # caps (walnut, brass rim)
    capp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-WB - 11, 0), (WB + 11, 0)], [rgb((.22, .12, .06)), rgb((.55, .34, .18)), rgb((.74, .52, .31)), rgb((.45, .27, .13)), rgb((.2, .11, .05))],
        [0, .3, .45, .7, 1]))
    for sgn in (-1, 1):
        yc = sgn * (H + CAP / 2)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-WB - 11, yc - CAP / 2, WB + 11, yc + CAP / 2), 3, 3), capp)
        c.drawLine(-WB - 10, yc - sgn * CAP / 2, WB + 10, yc - sgn * CAP / 2,
                   skia.Paint(AntiAlias=True, StrokeWidth=1.4, Color4f=skia.Color4f(.95, .76, .42, .7)))
    c.restore()
    # cap face seen end-on mid-tumble
    sn = abs(math.sin(th))
    if sn > .05:
        ey = -(H + CAP) * cv
        ry = (WB + 11) * .32 * sn
        c.drawOval(skia.Rect(-WB - 11, ey - ry, WB + 11, ey + ry), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (0, ey), WB + 11, [rgb((.72, .5, .3)), rgb((.4, .24, .12))]), Alphaf=min(1, sn * 1.6)))
    c.restore()

def draw_shelf(c, y):
    c.drawRect(skia.Rect(130, y + 2, 950, y + 22), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(130, y - 4, 950, y + 10), 3, 3), skia.Paint(AntiAlias=True,
        Shader=skia.GradientShader.MakeLinear([(0, y - 4), (0, y + 10)], [rgb((.66, .44, .25)), rgb((.42, .25, .12)), rgb((.2, .11, .05))], [0, .35, 1])))

def countdown(c, t):
    cx, cy, R = 540, 538, 30
    left = LOOP - t
    c.drawCircle(cx, cy, R, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(*CREAM, .12)))
    c.drawArc(skia.Rect(cx - R, cy - R, cx + R, cy + R), -90, -360 * left / LOOP, False,
              skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap,
                         Color4f=skia.Color4f(*AMBER, .75)))
    text(c, str(int(math.ceil(left - 1e-6)) if left > 1e-6 else 0), cx, cy + 12, F_CD, CREAM, .8)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
        text(c, "One of these", W / 2, 278, F_Q, CREAM, .97)
        text(c, "breaks physics.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
        fi = font(TF_SERIF_I, 32); fe = font(TF_EMOJI, 26)
        s1 = "Like it if you found it "
        w1 = fi.measureText(s1); w2 = fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, 466, fi, CREAM, .5, align="left")
        c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))
        countdown(c, t)
        for ci in range(NC):
            x, _ = pos(ci, 0)
            text(c, LETTERS[ci], x, 618, F_LBL, CREAM, .5)
        for r in range(NR):
            _, y = pos(0, r)
            draw_shelf(c, y + H + CAP)
            text(c, str(r + 1), 112, y + 9, F_NUM, CREAM, .42)
        for r in range(NR):
            for ci in range(NC):
                if not cycle(ci, r, t)[0]:
                    draw_hourglass(c, *pos(ci, r), ci, r, t)
        for r in range(NR):                 # tumbling ones on top
            for ci in range(NC):
                if cycle(ci, r, t)[0]:
                    draw_hourglass(c, *pos(ci, r), ci, r, t)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def knock(f0, dur=.25):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 30) + .45 * np.sin(2 * np.pi * f0 * 2.31 * t) * np.exp(-t * 45)
    s += .3 * np.sin(2 * np.pi * f0 * 4.02 * t) * np.exp(-t * 60)   # glass tink on top
    n = np.random.default_rng(int(f0)).standard_normal(len(t)) * np.exp(-t * 900) * .3
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 3000)

def swell(f0, dur=.55):
    t = np.arange(int(dur * SR)) / SR
    fm = f0 * (1 + .5 * t / dur)
    ph = 2 * np.pi * np.cumsum(fm) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return (np.sin(ph) + .4 * np.sin(2.76 * ph) + .2 * np.sin(5.2 * ph)) * env

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for r in range(NR):
        for ci in range(NC):
            for k in range(-2, 4):
                tt = offset(ci, r) + FD * P + k * P     # landing of the flip
                if 0 <= tt < LOOP: ev.append((tt, ci, r))
    times = np.array([e[0] for e in ev])
    for tt, ci, r in ev:
        x, _ = pos(ci, r)
        dens = ((np.abs(times - tt) < .06) | (np.abs(times - tt) > LOOP - .06)).sum()
        g = .55 / math.sqrt(dens)
        if (ci, r) == ODD:
            m.add(swell(note(r, 261.63) * .75), tt - .25, .22, x)
        else:
            m.add(knock(note(NR - 1 - r + 3, 261.63) * (1 + .004 * ci)), tt, g, x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)                # faint periodic sand hiss
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 3500) / 2500) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .035; m.R += np.roll(bed, 7000) * .035
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_hourglasses.mp4"))
