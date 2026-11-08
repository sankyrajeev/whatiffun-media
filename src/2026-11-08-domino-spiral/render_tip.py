import pickle, sys, math
import numpy as np, skia
from kit import *
from scipy.signal import butter, sosfilt

d = pickle.load(open("tip.pkl", "rb"))
P, T, HD, PA, NK, G = d["P"], d["T"], d["H"], d["PA"], d["NK"], d["geom"]
CX, CY, R, S, DT = G["CX"], G["CY"], G["R"], G["S"], G["DT"]
N = len(P)
T0 = .3                                   # frame 0 = sim time 0.3 s: the first domino is already tipping
TH, WD, HT = 6.0, 15.0, 30.0              # thickness, width, height (px)
TC = math.asin(min(.99, S / HT))          # angle at which a falling domino reaches the next
TF = DT / math.sqrt(TC / (math.pi / 2))   # time to fall flat under the u^2 law
REST = np.where(NK > 0, math.radians(80), math.radians(90))
T_END = float(T.max() + TF + .3)          # every domino down
SH0, SH1 = T_END + .2, T_END + 2.2        # a soft shimmer ring runs out across the finished spiral
NF = int((SH1 + .5 - T0) * FPS)
HOLD, CARD, XF = 16, 66, 18
TOTAL = NF + HOLD + CARD + XF

RAD = np.hypot(P[:, 0] - CX, P[:, 1] - CY)
U = np.clip(RAD / R, 0, 1)
STOPS = [(0, (.42, .86, .95)), (.3, (.55, .70, 1.0)), (.55, (.78, .58, 1.0)), (.78, (1.0, .55, .72)), (1.0, (1.0, .80, .42))]
def ocol(u):
    for (u0, c0), (u1, c1) in zip(STOPS, STOPS[1:]):
        if u <= u1:
            w = (u - u0) / (u1 - u0); return tuple(a + (b - a) * w for a, b in zip(c0, c1))
    return STOPS[-1][1]
COL = np.array([ocol(u) for u in U])
ORDER = np.argsort(-T, kind="stable")     # later ones first: a falling domino lies on top of the next
BG = background(CY)
SAMP_GLOW = [glow(tuple(c), 12, .9) for c in [ocol(i / 23) for i in range(24)]]
RING = glow((1, .95, .85), 14, .8)

def theta(t):
    tau = t - T
    th = (math.pi / 2) * np.clip(tau / TF, 0, None) ** 2
    th = np.minimum(th, REST)
    # a tiny settle-bounce when it lands
    land = np.sqrt(REST / (math.pi / 2)) * TF
    since = tau - land
    b = np.where(since > 0, .05 * np.exp(-since * 9) * np.abs(np.sin(since * 26)), 0)
    return np.where(tau > 0, th - b, 0.0)

def table(c):
    c.drawCircle(CX, CY + 16, R + 46, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
    c.drawCircle(CX, CY, R + 40, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (CX - 90, CY - 150), R + 260, [skia.Color(40, 34, 29), skia.Color(23, 20, 17), skia.Color(13, 11, 9)], [0, .6, 1])))
    c.drawCircle(CX, CY, R + 40, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2,
                 Color4f=skia.Color4f(*AMBER, .22)))

SHP = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .42))
LSH = (.55, .85)   # light from the upper left -> shadows fall down-right
first = None
def frame(f):
    global first
    t = T0 + f / FPS if f < NF else T0 + (NF - 1) / FPS
    th = theta(t)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        table(c)
        # shadows (one blurred layer)
        c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(2.2, 2.2)))
        for i in ORDER:
            a = float(th[i]); ca, sa = math.cos(a), math.sin(a)
            u0, u1 = TH / 2 - TH * ca, TH / 2 + HT * sa
            z = HT * ca + TH * sa
            c.save(); c.translate(float(P[i, 0]), float(P[i, 1])); c.rotate(math.degrees(HD[i]))
            # offset of the shadow in local coords
            gx, gy = LSH[0] * z * .55, LSH[1] * z * .55
            cs, sn = math.cos(-HD[i]), math.sin(-HD[i])
            lx, ly = gx * cs - gy * sn, gx * sn + gy * cs
            p = skia.Path()
            p.addPoly([(u0, -WD / 2), (u1, -WD / 2), (u1 + lx, -WD / 2 + ly), (u1 + lx, WD / 2 + ly),
                       (u0 + lx, WD / 2 + ly), (u0, WD / 2), (u0, -WD / 2)], True)
            p.addRect(skia.Rect(u0, -WD / 2, u1, WD / 2)); p.addRect(skia.Rect(u0 + lx, -WD / 2 + ly, u1 + lx, WD / 2 + ly))
            c.drawPath(p, SHP); c.restore()
        c.restore()
        fp = skia.Paint(AntiAlias=True)
        for i in ORDER:
            a = float(th[i]); ca, sa = math.cos(a), math.sin(a)
            col = COL[i]
            u0, u1 = TH / 2 - TH * ca, TH / 2 + HT * sa
            c.save(); c.translate(float(P[i, 0]), float(P[i, 1])); c.rotate(math.degrees(HD[i]))
            face = HT * sa                     # projected back face (towards the viewer as it tips)
            top = TH * ca                      # projected top edge
            lit = .55 + .45 * (a / (math.pi / 2))
            if face > .6:
                rr = skia.RRect.MakeRectXY(skia.Rect(u0, -WD / 2, u0 + face + top, WD / 2), 2.6, 2.6)
                light = tuple(min(1, x * lit * .5 + .5) for x in col); base = tuple(x * lit for x in col)
                dark = tuple(x * lit * .55 for x in col)
                gp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(u0, -WD / 2), (u0 + face, WD / 2)],
                             [skia.Color4f(*light, 1).toColor(), skia.Color4f(*base, 1).toColor(), skia.Color4f(*dark, 1).toColor()], [0, .45, 1]))
                c.drawRRect(rr, gp)
                # divider line + specular glint
                mid = u0 + top + face * .5
                fp.setColor4f(skia.Color4f(*dark, .9)); c.drawRect(skia.Rect(mid - .7, -WD / 2 + 2.5, mid + .7, WD / 2 - 2.5), fp)
                fp.setColor4f(skia.Color4f(1, 1, 1, .55 * sa))
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(u0 + top + 2, -WD / 2 + 2, u0 + top + max(3, face * .38), -WD / 2 + 3.6), .8, .8), fp)
            # top edge (the thin end you see while it stands): pale, tinted
            if top > .5:
                tc = tuple(.34 + .44 * x for x in col)
                fp.setColor4f(skia.Color4f(*tc, 1))
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(u0 + face, -WD / 2, u0 + face + top, WD / 2), 1.6, 1.6), fp)
                fp.setColor4f(skia.Color4f(1, 1, 1, .28 * ca))
                c.drawRect(skia.Rect(u0 + face + .8, -WD / 2 + 1.5, u0 + face + top * .45, WD / 2 - 1.5), fp)
            c.restore()
        # soft glow at each fresh contact
        fresh = np.nonzero((T <= t) & (t - T < .3) & (PA >= 0))[0]
        ga = .55 * min(1, (30 / max(30, len(fresh))) ** .5)
        for i in fresh:
            age = (t - T[i]) / .3
            blit(c, SAMP_GLOW[int(U[i] * 23)], float(P[i, 0]), float(P[i, 1]), 1.0,
                 skia.Paint(Alphaf=ga * (1 - age), BlendMode=skia.BlendMode.kPlus))
        if t < 1.2:
            blit(c, SAMP_GLOW[0], CX, CY, 1.6, skia.Paint(Alphaf=.7 * (1 - ss((t - .3) / .9)), BlendMode=skia.BlendMode.kPlus))
        # the shimmer ring after everything is down
        if SH0 <= t <= SH1 + .2:
            rr = (R + 60) * ss((t - SH0) / (SH1 - SH0))
            for i in np.nonzero(np.abs(RAD - rr) < 34)[0]:
                a = .32 * (1 - abs(RAD[i] - rr) / 34) ** 2
                blit(c, RING, float(P[i, 0]), float(P[i, 1]), 1.0, skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kPlus))
        cnt = int((T <= t).sum())
        pc = int((T <= t - 1 / FPS).sum())
        header(c, "Every one that falls", "tips the next.", count=cnt, pulse=.5 if (cnt > pc and cnt < 30) else 0)
        watermark(c, 1600)
        if f >= NF + HOLD:
            a = ss((f - NF - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

def audio(path):
    m = Mix(TOTAL / FPS + .5)
    rng = np.random.default_rng(21)
    cache = {}
    def tink(step):                       # glass domino striking glass domino
        if step not in cache:
            f0 = note(step, 293.66)
            tt = np.arange(int(.7 * SR)) / SR
            s = (np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 7) + .38 * np.sin(2 * np.pi * f0 * 2.76 * tt) * np.exp(-tt * 15)
                 + .12 * np.sin(2 * np.pi * f0 * 5.4 * tt) * np.exp(-tt * 30))
            n = rng.standard_normal(len(tt)) * np.exp(-tt * 1700) * .3
            cache[step] = (s + np.diff(n, prepend=0)) * np.minimum(1, tt * 6000)
        return cache[step]
    taps = [glass_click(rng.uniform(900, 1300), rng.uniform(140, 190), .06, .5) for _ in range(12)]
    ts = lambda x: x - T0                 # sim time -> video time
    hits = np.nonzero(PA >= 0)[0]
    byf = {}
    for i in hits:
        byf.setdefault(int(ts(T[i]) * FPS), []).append(i)
    rate = np.zeros(TOTAL)
    for f, es in byf.items():
        if f < 0: continue
        rate[f] = len(es)
        rng.shuffle(es)
        g = .45 / (1 + .14 * max(0, len(es) - 1))
        for i in es[:8]:
            step = int(min(13, round(U[i] * 11))) + int(rng.choice([0, 0, 0, 2]))
            m.add(tink(min(14, step)), ts(T[i]) + rng.uniform(0, .006), g, float(P[i, 0]))
    # landing taps of the last domino on each line (it falls flat onto the table)
    land = T + np.sqrt(REST / (math.pi / 2)) * TF
    for i in np.nonzero(NK == 0)[0]:
        m.add(taps[rng.integers(12)], ts(land[i]), .09, float(P[i, 0]))
    # soft clatter bed following the rate of falls
    sm = np.convolve(rate, np.ones(9) / 9, mode="same")
    env = np.interp(np.arange(m.N) / SR, (np.arange(TOTAL) + .5) / FPS, np.clip(sm / 9, 0, 1))
    air = sosfilt(butter(2, [1800, 7000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, m.N)), axis=1)
    m.L += air[0] * env * .022; m.R += air[1] * env * .022
    # low soft thumps at 10, 25, 50, 100 and every hundred after
    marks = [10, 25, 50] + list(range(100, 2000, 100))
    TS = np.sort(T)
    for k, mk in enumerate(marks):
        if mk <= N: m.add(thud(56 + 4 * (k % 3), .5), ts(TS[mk - 1]), .24, 540)
    # the shimmer ring: rising glass ticks outward, then the resolving chord under the end card
    for j, tt in enumerate(np.arange(SH0, SH1, .07)):
        rr = (R + 60) * ss((tt - SH0) / (SH1 - SH0))
        near = np.nonzero(np.abs(RAD - rr) < 12)[0]
        x = float(P[rng.choice(near), 0]) if len(near) else 540
        m.add(mallet(note(5 + int(9 * (tt - SH0) / (SH1 - SH0)), 293.66), .8, .45), ts(tt), .16, x)
    m.add(thud(46, .9), ts(T_END), .32, 540)
    tc = (NF + HOLD) / FPS
    tt = np.arange(int(3.2 * SR)) / SR
    for i, nn in enumerate([0, 2, 4, 7]):
        f0 = note(nn, 293.66 / 2)
        bell = (np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 1.1) + .3 * np.sin(2 * np.pi * f0 * 3.93 * tt) * np.exp(-tt * 4)) * np.minimum(1, tt * 3000)
        m.add(bell, tc + i * .08, .3, 540 + (i - 1.5) * 110)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            if f >= TOTAL - XF and first is None: frame(0)
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
        print("NF", NF, "TOTAL", TOTAL, TOTAL / FPS, "T_END", T_END)
    elif sys.argv[1] == "audio":
        print(audio("tip.wav"))
    else:
        w = Writer("tip_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("tip.wav"))
        print("mux", mux("tip_silent.mp4", "tip.wav", "tip.mp4"))
