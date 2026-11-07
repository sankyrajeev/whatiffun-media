import pickle, sys, math
import numpy as np, skia
from kit import *
from scipy.signal import butter, sosfilt

d = pickle.load(open("drops.pkl", "rb"))
FR, CNT, EV, DR, G = d["frames"], d["counts"], d["events"], d["drained"], d["geom"]
X0, X1, Y0, Y1 = G["X0"], G["X1"], G["Y0"], G["Y1"]
NF = len(FR)
HOLD, CARD, XF = 22, 66, 18
TOTAL = NF + HOLD + CARD + XF
TY0, TY1 = Y1 + 22, Y1 + 118          # trough interior
FILL_MAX = 76.0

def rcol(r):
    u = min(1, max(0, (r - 2.5) / 20)) ** .75
    return hsv(188 + 210 * u, .55 + .08 * u * u, .78 + .22 * u)
RB = list(range(2, 41))
SPR = {rb: glass_ball(rcol(rb), rb) for rb in RB}
POP = {rb: glow(rcol(rb), max(4, rb) * 1.15, .75) for rb in RB}
def rbk(r): return int(min(40, max(2, round(r))))
BG = background(1000)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .38))
GOLD = (1.0, .78, .38)
first = None
MERGE = {}; POUR = {}; LAND = {}
for e in EV:
    k = int(e[0] * FPS)
    {"merge": MERGE, "pour": POUR, "land": LAND}[e[1]].setdefault(k, []).append(e)
PANE = skia.RRect.MakeRectXY(skia.Rect(X0 - 16, Y0 - 16, X1 + 16, Y1 + 8), 26, 26)
TROUGH = skia.RRect.MakeRectXY(skia.Rect(X0 - 16, TY0 - 8, X1 + 16, TY1 + 8), 22, 22)

def pane(c):
    c.drawRRect(PANE.makeOffset(0, 16), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 28)))
    c.drawRRect(PANE, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(X0, Y0), (X1, Y1)], [skia.Color(30, 31, 34), skia.Color(17, 16, 17), skia.Color(23, 21, 20)], [0, .55, 1])))
    # soft diagonal reflections on the glass
    p = skia.Path(); p.moveTo(X0 + 60, Y0 - 16); p.lineTo(X0 + 230, Y0 - 16); p.lineTo(X0 - 16, Y0 + 420); p.lineTo(X0 - 16, Y0 + 120); p.close()
    c.save(); c.clipRRect(PANE, doAntiAlias=True)
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .97, .92, .025)))
    c.restore()
def pane_rim(c):
    c.drawRRect(PANE, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=skia.Color4f(*CREAM, .26)))

def trough(c, k, f):
    c.drawRRect(TROUGH, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.07, .06, .05, 1)))
    fill = FILL_MAX * (DR[k] / max(1, DR[-1]))
    if fill > .5:
        top = TY1 - fill
        # surface ripples from recent pours
        xs = np.linspace(X0 - 8, X1 + 8, 120); ys = np.zeros_like(xs)
        for back in range(0, 40):
            for e in POUR.get(k - back, [])[:6]:
                a = min(5, e[4] * .28) * math.exp(-back / 14)
                ys += a * np.exp(-((xs - e[2]) / (20 + back * 5)) ** 2) * math.cos(back * .6)
        path = skia.Path(); path.moveTo(xs[0], TY1 + 8)
        for xx, yy in zip(xs, ys): path.lineTo(float(xx), float(top - yy))
        path.lineTo(xs[-1], TY1 + 8); path.close()
        c.save(); c.clipRRect(TROUGH, doAntiAlias=True)
        c.drawPath(path, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, top - 6), (0, TY1 + 8)], [skia.Color4f(1, .86, .52, 1).toColor(), skia.Color4f(.86, .55, .2, 1).toColor(),
                                           skia.Color4f(.45, .25, .08, 1).toColor()], [0, .35, 1])))
        hl = skia.Path(); hl.moveTo(xs[0], float(top - ys[0]))
        for xx, yy in zip(xs, ys): hl.lineTo(float(xx), float(top - yy))
        c.drawPath(hl, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5, Color4f=skia.Color4f(1, .96, .82, .7)))
        c.restore()
    c.drawRRect(TROUGH, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=skia.Color4f(*CREAM, .26)))
    hi = skia.RRect.MakeRectXY(skia.Rect(X0 + 10, TY0 + 2, X1 - 10, TY0 + 8), 3, 3)
    c.drawRRect(hi, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .05)))

def frame(f):
    global first
    k = min(f, NF - 1)
    D = FR[k]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        pane(c)
        trough(c, k, f)
        c.save(); c.clipRRect(PANE, doAntiAlias=True)
        for x, y, r, b in D:
            c.drawCircle(float(x) + r * .1 + 1, float(y) + r * .22 + 1.5, float(r), SH)
        for x, y, r, b in D:
            rb = rbk(r); s = r / rb
            age = k - b
            if age < 4: s *= .55 + .45 * ss(age / 4)
            blit(c, SPR[rb], float(x), float(y), float(s))
        for back in range(0, 6):
            al = .42 * (1 - back / 6)
            for e in MERGE.get(k - back, [])[:120]:
                blit(c, POP[rbk(e[4])], e[2], e[3], 1.0, skia.Paint(Alphaf=al, BlendMode=skia.BlendMode.kPlus))
        c.restore()
        for back in range(0, 8):
            for e in POUR.get(k - back, [])[:20]:
                rb = rbk(e[4] * 1.4)
                blit(c, POP[rb], e[2], TY1 - FILL_MAX * DR[k] / max(1, DR[-1]), 1.0,
                     skia.Paint(Alphaf=.5 * (1 - back / 8), BlendMode=skia.BlendMode.kPlus))
        pane_rim(c)
        header(c, "When drops touch,", "they become one.", count=int(CNT[k]))
        watermark(c, 1622)
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
    rng = np.random.default_rng(3)
    cache = {}
    def plip(step):
        if ("p", step) not in cache:
            f0 = note(step, 261.63)
            dur = .5; t = np.arange(int(dur * SR)) / SR
            fr = f0 * (1 + .35 * (1 - np.exp(-t * 60)))          # little upward glide = water drop
            phs = 2 * np.pi * np.cumsum(fr) / SR
            s = np.sin(phs) * np.exp(-t * 11) + .3 * np.sin(2.76 * phs + 1) * np.exp(-t * 24)
            n = rng.standard_normal(len(t)) * np.exp(-t * 1600) * .2
            cache[("p", step)] = (s + np.diff(n, prepend=0)) * np.minimum(1, t * 5000)
        return cache[("p", step)]
    taps = [glass_click(rng.uniform(1700, 2900), 650, .05, .35) for _ in range(8)]
    for f, es in LAND.items():
        rng.shuffle(es)
        for e in es[:5]:
            m.add(taps[rng.integers(8)], e[0], .035 / (1 + .12 * max(0, len(es) - 3)), e[2])
    for f, es in MERGE.items():
        es = sorted(es, key=lambda e: -e[4])[:8]
        for e in es:
            u = min(1, (e[4] - 3) / 20)
            step = int(round(14 - 12 * u))
            g = (.16 + .22 * u) / (1 + .14 * max(0, len(es) - 2))
            m.add(plip(step), e[0] + rng.uniform(0, .008), g, e[2])
    for f, es in POUR.items():
        es = sorted(es, key=lambda e: -e[4])[:4]
        for e in es:
            u = min(1, e[4] / 22)
            m.add(mallet(note(int(4 - 4 * u), 130.81), .9, .25), e[0], .1 + .12 * u, e[2])
            m.add(thud(55 + 20 * (1 - u), .35), e[0], .12 + .15 * u, e[2])
    # soft rain air
    nl = np.zeros(TOTAL)
    for f, es in LAND.items():
        if f < TOTAL: nl[f] = len(es)
    nl = np.convolve(nl, np.ones(15) / 15, "same")
    env = np.interp(np.arange(m.N) / SR, (np.arange(TOTAL) + .5) / FPS, np.clip(nl / 15, 0, 1))
    air = sosfilt(butter(2, [1800, 7000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, m.N)), axis=1)
    m.L += air[0] * env * .025; m.R += air[1] * env * .025
    # gentle levelling: slow gain riding so the quiet start and the busy middle sit closer together
    w = int(1.2 * SR); e2 = (m.L ** 2 + m.R ** 2) / 2
    env = np.sqrt(np.convolve(e2, np.ones(w) / w, "same")) + 1e-6
    tgt = np.percentile(env[:int(NF / FPS * SR)], 70)
    gain = np.clip((tgt / env) ** .55, .7, 2.2)
    gain[int((NF / FPS - .6) * SR):] = gain[int((NF / FPS - .6) * SR)]
    gain = np.convolve(gain, np.ones(SR // 4) / (SR // 4), "same")
    m.L *= gain; m.R *= gain
    tc = (NF + HOLD) / FPS - .2
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63), 3.6, .35), tc + i * .12, .32, 540 + (i - 1.5) * 110)
    m.add(thud(48, .9), tc, .35)
    tt = np.arange(int(3.2 * SR)) / SR
    pad = sum(np.sin(2 * np.pi * note(nn, 130.81) * tt) for nn in (0, 2, 4)) * np.exp(-tt * 1.1) * np.minimum(1, tt * 8)
    m.add(pad, tc + .1, .07)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        frame(0)
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print(audio("drops.wav"))
    else:
        w = Writer("drops_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("drops.wav"))
        print("mux", mux("drops_silent.mp4", "drops.wav", sys.argv[2]))
