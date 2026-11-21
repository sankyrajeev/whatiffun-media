"""SPOT IT v3 (13:00, 2026-11-21): BREAKS PHYSICS. 48 identical brass-and-glass hourglasses in CHEVRON rows
(8 columns A-H x 6 rows, every row a shallow ^ peaking between D and E). Every hourglass drains for ~2.3-3.3 s,
then is flipped a whole half-turn (180 deg, random direction) and set down again, on a 3 s or 4 s cycle with a
random phase. The odd one flips like the rest but its sand flows UP: the full bulb is always at the bottom after
a flip, the stream of grains climbs through the neck, and the sand piles on the CEILING of the top bulb.
Sound: a soft wood-and-brass knock as each hourglass is set down (pentatonic by row, panned by x,
density-normalised) over a quiet sand hiss; the odd one's knock comes with a reversed (rising) hiss and a lower
tone (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/hg"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 8, 6
LET = "ABCDEFGH"
SX, SY = 104.0, 158.0
X0 = 540 - (NC - 1) / 2 * SX + 20
Y0 = 600.0
CHEV = 14.0                                   # px lower per column away from the centre
HH, HW = 64.0, 37.0                           # half height / half width of the hourglass
T_FLIP = .72
PCT = int(os.environ.get("PCT", "4"))
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))

def cy(i, r): return Y0 + r * SY + CHEV * abs(i - (NC - 1) / 2)

D = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = 3.0 if odd else (3.0 if rng.uniform() < .6 else 4.0)
        D.append(dict(lab=lab, odd=odd, x=X0 + i * SX, y=cy(i, r), r=r, i=i, P=P, ph=rng.uniform(0, 1),
                      dirs=[(1 if rng.uniform() < .5 else -1) for _ in range(8)]))
print(len(D), "hourglasses")
assert sum(d["odd"] for d in D) == 1

def state(d, t):
    """-> (a = fraction of sand in the upper bulb in 'normal' coords, angle deg, lift px, draining?)"""
    P = d["P"]; Td = P - T_FLIP
    v = t / P + d["ph"]
    k = int(math.floor(v)); u = (v - k) * P
    if u < Td:
        return 1 - u / Td, 0.0, 0.0, True, u
    w = (u - Td) / T_FLIP
    e = ss(w)
    return 0.0, 180 * e * d["dirs"][k % int(round(LOOP / P))], 16 * math.sin(math.pi * w), False, u

# ---------- geometry (local coords, y down, neck at 0) ----------
TOP, CAP = -HH, 9.0
GL = HH - CAP                                 # glass half height
NECK, WMAX = 3.2, HW - 7
def wid(s):                                   # half width of glass at s = |y|/GL
    s = min(1, max(0, s))
    return NECK + (WMAX - NECK) * (1 - (1 - s) ** 2.3) * (1 - .18 * s ** 7)
SS = np.linspace(0, 1, 400)
def bulb_path(sign):
    p = skia.Path()
    pts = [(wid(s), sign * s * GL) for s in SS]
    p.moveTo(-pts[0][0], pts[0][1])
    for x, y in pts: p.lineTo(-x, y)
    for x, y in pts[::-1]: p.lineTo(x, y)
    p.close(); return p
GLASS = skia.Path(); GLASS.addPath(bulb_path(-1)); GLASS.addPath(bulb_path(1))
UPPER, LOWER = bulb_path(-1), bulb_path(1)
AREA = np.trapezoid(2 * np.array([wid(s) for s in SS]), SS * GL)
# upper bulb: sand fills from the neck up to level L (s units) with a little dip; lookup amount -> L
CUM = np.concatenate([[0], np.cumsum(2 * np.array([wid(s) for s in SS[1:]]) * np.diff(SS * GL))])
def level_up(a): return float(np.interp(a * AREA, CUM, SS))
# lower bulb: mound from the floor; area of a cone mound of base height hb (s from floor) ~ use same table mirrored
CUMF = np.concatenate([[0], np.cumsum(2 * np.array([wid(1 - s) for s in SS[1:]]) * np.diff(SS * GL))])
def level_low(b): return float(np.interp(b * AREA, CUMF, SS))

SAND_SH = skia.GradientShader.MakeLinear([(-WMAX, 0), (WMAX, 0)],
    [skia.Color4f(.80, .50, .20, 1).toColor(), skia.Color4f(.97, .74, .38, 1).toColor(), skia.Color4f(.76, .46, .18, 1).toColor()],
    [0, .4, 1])
CAP_SH = skia.GradientShader.MakeLinear([(-HW, 0), (HW, 0)],
    [skia.Color4f(.45, .32, .15, 1).toColor(), skia.Color4f(.93, .76, .46, 1).toColor(), skia.Color4f(.52, .37, .17, 1).toColor()],
    [0, .38, 1])
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
SANDP = skia.Paint(AntiAlias=True, Shader=SAND_SH)

def draw_sand(c, a, drain, u, seed):
    """normal-coords sand: a in the upper bulb resting on the neck, 1-a heaped on the floor of the lower bulb"""
    if a > .004:
        L = level_up(a) * GL
        dip = min(10, 4 + 10 * (1 - a)) if drain else 0
        p = skia.Path()
        p.moveTo(-WMAX - 2, 2)
        p.lineTo(-WMAX - 2, -L); p.quadTo(0, -L + 2 * dip, WMAX + 2, -L); p.lineTo(WMAX + 2, 2); p.close()
        c.save(); c.clipPath(UPPER, doAntiAlias=True); c.drawPath(p, SANDP); c.restore()
    b = 1 - a
    if b > .004:
        hb = level_low(b) * GL
        peak = min(12, 3 + 18 * b) if b < .999 else 6
        base = GL - hb + peak * .45
        p = skia.Path()
        p.moveTo(-WMAX - 2, GL + 2); p.lineTo(-WMAX - 2, base); p.quadTo(0, base - 2 * peak, WMAX + 2, base)
        p.lineTo(WMAX + 2, GL + 2); p.close()
        c.save(); c.clipPath(LOWER, doAntiAlias=True); c.drawPath(p, SANDP); c.restore()
        top = base - peak
    else:
        top = GL
    if drain and a > .004:
        c.drawRect(skia.Rect(-2.0, -2, 2.0, top), P_((.95, .70, .34), .95))
        # grains racing down the stream
        for k in range(7):
            yy = ((u * 260 + k * 13 + seed * 7) % max(8, top + 2)) - 2
            c.drawCircle(((k * 37 + seed) % 3 - 1) * .9, yy, 2.8, P_((1, .86, .55), 1.0))

def draw_hg(c, d, t):
    a, ang, lift, drain, u = state(d, t)
    x, y = d["x"], d["y"]
    c.drawOval(skia.Rect(x - HW - 2, y + HH - 4, x + HW + 2, y + HH + 10),
               P_((0, 0, 0), .5 - .25 * lift / 16, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.save()
    c.translate(x, y - lift)
    c.rotate(ang)
    if d["odd"]: c.scale(1, -1)               # the odd one: same picture mirrored -> sand runs upward
    # glass back
    c.drawPath(GLASS, P_((1, .97, .9), .12))
    draw_sand(c, a, drain, u, d["i"] * 5 + d["r"])
    c.drawPath(GLASS, P_((.98, .94, .86), .55, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0))
    c.drawPath(GLASS, P_((1, 1, 1), .10, Style=skia.Paint.kStroke_Style, StrokeWidth=5.0))
    # highlights
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-WMAX + 6, -GL + 9, -WMAX + 10, -GL * .45), 2, 2), P_((1, 1, 1), .28))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-WMAX + 6, GL * .45, -WMAX + 10, GL - 9), 2, 2), P_((1, 1, 1), .22))
    # posts + caps
    for sx in (-1, 1):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx * (HW - 4) - 2.6, -GL, sx * (HW - 4) + 2.6, GL), 2, 2),
                    skia.Paint(AntiAlias=True, Shader=CAP_SH))
    for sy in (-1, 1):
        r0 = skia.Rect(-HW, GL if sy > 0 else -HH, HW, HH if sy > 0 else -GL)
        c.drawRRect(skia.RRect.MakeRectXY(r0, 4, 4), skia.Paint(AntiAlias=True, Shader=CAP_SH))
        c.drawRRect(skia.RRect.MakeRectXY(r0, 4, 4), P_((.3, .2, .08), .5, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2))
    c.restore()

BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_LAB = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s) + 2 * (len(s) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        # faint chevron shelves under each row
        for r in range(NR):
            p = skia.Path()
            p.moveTo(X0 - SX / 2 + 6, cy(0, r) + HH + 3)
            p.lineTo(540 + 12, cy(3.5, r) + HH + 3)
            p.lineTo(X0 + (NC - 1) * SX + SX / 2 - 6, cy(NC - 1, r) + HH + 3)
            c.drawPath(p, P_((.62, .46, .26), .30, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))
        for i in range(NC):
            text(c, LET[i], X0 + i * SX, cy(i, 0) - HH - 26, F_LAB, CREAM, .85)
        for r in range(NR):
            text(c, str(r + 1), X0 - SX / 2 - 18, cy(0, r) + 11, F_LAB, CREAM, .85)
        for d in sorted(D, key=lambda d: state(d, t)[2]):
            draw_hg(c, d, t)
        yb = 1566
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1648, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def knock(f0, seed, dur=.3, dull=False):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    parts = ((1, 34, .7), (2.7, 55, .25), (5.1, 80, .12)) if not dull else ((1, 20, .85), (2.1, 38, .2))
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + rg.uniform(0, 6)) * np.exp(-t * dd) for m, dd, a in parts)
    nz = rg.standard_normal(len(t)) * np.exp(-t * 260) * .2
    return (s + nz) * np.minimum(1, t * 4000)
def hiss(seed, dur, rev=False):
    n = int(dur * SR); rg = np.random.default_rng(seed)
    x = rg.standard_normal(n)
    sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    sp *= np.exp(-((fr - 5200) / 2600) ** 2); x = np.fft.irfft(sp, n); x /= np.abs(x).max() + 1e-9
    env = np.linspace(0, 1, n) ** 2 if rev else np.exp(-np.linspace(0, 6, n))
    return x * env

def audio(path):
    m = Mix(LOOP + 1.8)
    ev = []
    for k, d in enumerate(D):
        for n in range(-2, 7):
            t_land = (n + 1 - d["ph"]) * d["P"]          # end of flip = the moment it's set down
            ev.append((t_land, k))
    lt = np.array([e[0] for e in ev])
    for tt, k in ev:
        if not (0 <= tt < LOOP): continue
        d = D[k]
        dens = math.sqrt(max(1, (np.abs(lt - tt) < .4).sum()))
        if d["odd"]:
            m.add(knock(note(1, 110.0), k * 100 + int(tt * 50), .45, dull=True), tt, .6 / dens, d["x"])
            m.add(hiss(k * 7 + int(tt * 10), .9, rev=True), tt - .9, .10, d["x"])
        else:
            m.add(knock(note(6 - d["r"] + 6, 220.0), k * 100 + int(tt * 50)), tt, .45 / dens, d["x"])
            m.add(hiss(k * 7 + int(tt * 10), .5), tt + .02, .03 / dens, d["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    for ch, seed in ((m.L, 3), (m.R, 4)):
        x = np.random.default_rng(seed).standard_normal(n)
        sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
        sp *= np.exp(-((fr - 4800) / 2400) ** 2)       # continuous trickling-sand bed
        bed = np.fft.irfft(sp, n); bed /= np.abs(bed).max(); ch += bed * .035
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print(audio(f"{OUT}/spot.wav"))
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_hourglasses.mp4"))
