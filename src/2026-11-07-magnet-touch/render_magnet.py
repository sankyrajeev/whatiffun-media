import pickle, sys, math
import numpy as np, skia
from kit import *

d = pickle.load(open("magnet.pkl", "rb"))
FR, CNT, ORD, TM, CONV, CLK, G = d["frames"], d["counts"], d["order"], d["tmag"], d["conv"], d["clacks"], d["geom"]
CX, CY, RD, BR, N = G["CX"], G["CY"], G["RD"], G["BR"], G["N"]
NF = min(len(FR), int((d['gather'] + float(sys.argv[3] if len(sys.argv) > 3 else 4.7)) * FPS))
HOLD, CARD, XF = 24, 66, 18
TOTAL = NF + HOLD + CARD + XF
FM = np.where(TM >= 0, (TM * FPS).astype(int), 10 ** 9)          # frame each bead turned

# colour by turning order: teal -> violet -> rose -> gold
STOPS = [(0, (.36, .86, .86)), (.33, (.62, .48, 1.0)), (.66, (1.0, .45, .72)), (1.0, (1.0, .80, .38))]
def ocol(u):
    for (u0, c0), (u1, c1) in zip(STOPS, STOPS[1:]):
        if u <= u1:
            w = (u - u0) / (u1 - u0); return tuple(a + (b - a) * w for a, b in zip(c0, c1))
    return STOPS[-1][1]
LV = 32
SPR = [glass_ball(ocol(i / (LV - 1)), BR) for i in range(LV)]
LVL = np.clip(np.round(ORD / max(1, N - 1) * (LV - 1)), 0, LV - 1).astype(int)
STEEL = glass_ball((.62, .64, .70), BR)
GLW = [glow(ocol(i / (LV - 1)), BR * 1.7, .9) for i in range(LV)]
FIRSTG = glow((1, .9, .6), BR * 2.2, .7)
BG = background(1050)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .4))

def dish(c):
    c.drawCircle(CX, CY + 10, RD + 22, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
    c.drawCircle(CX, CY, RD + 16, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (CX, CY - 120), RD + 160, [skia.Color(34, 28, 24), skia.Color(19, 16, 14), skia.Color(11, 9, 8)], [0, .6, 1])))
    c.drawCircle(CX, CY, RD + 14, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                 Color4f=skia.Color4f(1, .95, .85, .05)))
    c.drawCircle(CX, CY, RD + 18, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5,
                 Color4f=skia.Color4f(*CREAM, .24)))
    c.drawArc(skia.Rect(CX - RD - 8, CY - RD - 8, CX + RD + 8, CY + RD + 8), 200, 70, False,
              skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap,
                         Color4f=skia.Color4f(1, 1, 1, .12)))

first = None
def frame(f):
    global first
    k = min(f, NF - 1)
    P = FR[k]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        dish(c)
        for i in range(N):
            c.drawCircle(float(P[i, 0]) + 1.6, float(P[i, 1]) + 2.4, BR, SH)
        on = FM <= k
        for i in np.nonzero(~on)[0]:
            blit(c, STEEL, float(P[i, 0]), float(P[i, 1]))
        for i in np.nonzero(on)[0]:
            age = k - FM[i]
            sc = 1 + (.45 * (1 - age / 6) if age < 6 else 0)
            blit(c, SPR[LVL[i]], float(P[i, 0]), float(P[i, 1]), sc)
        for i in np.nonzero(on & (k - FM < 9))[0]:
            age = k - FM[i]
            blit(c, GLW[LVL[i]], float(P[i, 0]), float(P[i, 1]), 1.0, skia.Paint(Alphaf=.85 * (1 - age / 9), BlendMode=skia.BlendMode.kPlus))
        if k < 75:   # soft halo marks the first magnet
            blit(c, FIRSTG, float(P[0, 0]), float(P[0, 1]), 1.0, skia.Paint(Alphaf=.55 * (1 - ss((k - 30) / 45)), BlendMode=skia.BlendMode.kPlus))
        u = (CNT[k] - 1) / max(1, N - 1)
        header(c, "Whatever it touches", "becomes a magnet.", count=int(CNT[k]), count_col=CREAM)
        watermark(c, 1580)
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
    rng = np.random.default_rng(11)
    GT = d["gather"]
    # 1) every turning: a small glass bell, pitch climbs with the colour (teal low -> gold high)
    bells = {i: mallet(note(i, 293.66), .9, .8) for i in range(16)}
    byf = {}
    CT = np.array([c[0] for c in CONV])
    for c in CONV: byf.setdefault(int(c[0] * FPS), []).append(c)
    for f, es in byf.items():
        if f >= NF: continue
        n = len(es)
        for c in es[:7]:
            u = c[4] / max(1, N - 1)
            i = int(round(u * 10)) + int(rng.choice([0, 0, 1, 2]))
            dens = np.sum(np.abs(CT - c[0]) < .25)        # turns in the surrounding half second
            g = .30 * (8 / max(8, dens)) ** .65 / (1 + .08 * max(0, n - 1))
            m.add(bells[min(15, i)], c[0] + rng.uniform(0, .004), g, c[1])
    # 2) the steel beads tapping each other (soft, sparse); 3) the magnets snapping together
    taps = [glass_click(rng.uniform(2400, 3400), rng.uniform(140, 200), .05, .35) for _ in range(20)]
    snaps = [glass_click(rng.uniform(3600, 5600), rng.uniform(170, 240), .05, .55) for _ in range(28)]
    thumps = [thud(rng.uniform(52, 66), .45) for _ in range(6)]
    cb = {}
    for c in CLK:
        f = int(c[0] * FPS)
        if f < NF: cb.setdefault(f, []).append(c)
    for f, es in cb.items():
        t = f / FPS
        if t < GT:
            es = [e for e in es if not e[4]]
            rng.shuffle(es)
            for e in es[:3]:
                m.add(taps[rng.integers(20)], e[0], .035 * min(1.6, (e[3] / 40) ** .5), e[1])
        else:
            es.sort(key=lambda e: -e[3])
            dens = len(es)
            for e in es[:10]:
                g = .62 * min(1.5, (e[3] / 120) ** .4) / (1 + .015 * min(60, dens))
                m.add(snaps[rng.integers(28)], e[0] + rng.uniform(0, .02), g, e[1])
    # 4) soft low thump under every hundred
    last = 0
    for c in CONV:
        if c[4] // 100 > last and c[0] * FPS < NF:
            last = c[4] // 100; m.add(thumps[last % 6], c[0], .22, 540)
    # 5) the gather lands: a few deeper thumps as the clumps meet
    for k, t in enumerate(np.linspace(GT + .6, GT + 3.0, 5)):
        m.add(thud(48 + 4 * k, .7), t, .40 + .05 * k, 540 + (k - 2) * 60)
    # end: soft resolving chord
    tc = (NF + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 293.66 / 2), 3.0, .5), tc + i * .08, .24, 540 + (i - 1.5) * 110)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[2].split(",")]
        if len(sys.argv) > 4: print(audio("M.wav")); sys.exit()
        for f in fs:
            if f >= TOTAL - XF and first is None: frame(0)
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
        print("NF", NF, "TOTAL", TOTAL)
    else:
        w = Writer("M_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("M.wav"))
        print("mux", mux("M_silent.mp4", "M.wav", "magnet.mp4"))
