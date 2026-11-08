import pickle, sys, math
import numpy as np, skia
from kit import *

d = pickle.load(open("born.pkl", "rb"))
FR, RA, CNT, BORN, BIR, CLK, G = d["frames"], d["rads"], d["counts"], d["born"], d["births"], d["clacks"], d["geom"]
CX, CY, RH, BR, VERT = G["CX"], G["CY"], G["RH"], G["BR"], G["VERT"]
N = len(BORN)
NF = min(len(FR), int((d["stop"] + float(sys.argv[3] if len(sys.argv) > 3 else 4.4)) * FPS))
HOLD, CARD, XF = 33, 66, 18
TOTAL = NF + HOLD + CARD + XF
FB = np.where(BORN > 0, (BORN * FPS).astype(int), -99)
# colour by birth order on a log scale so it shifts evenly through the build: sky -> mint -> lilac -> rose -> honey gold
STOPS = [(0, (.50, .78, 1.0)), (.3, (.52, .92, .78)), (.55, (.74, .62, 1.0)), (.78, (1.0, .56, .70)), (1.0, (1.0, .82, .40))]
def ocol(u):
    for (u0, c0), (u1, c1) in zip(STOPS, STOPS[1:]):
        if u <= u1:
            w = (u - u0) / (u1 - u0); return tuple(a + (b - a) * w for a, b in zip(c0, c1))
    return STOPS[-1][1]
LV = 40
U = np.log(np.arange(N) + 1) / math.log(N)
LVL = np.clip(np.round(U * (LV - 1)), 0, LV - 1).astype(int)
SPR = [glass_ball(ocol(i / (LV - 1)), BR) for i in range(LV)]
GLW = [glow(ocol(i / (LV - 1)), BR * 1.9, .9) for i in range(LV)]
BG = background(CY)
FIRSTG = glow((.7, .88, 1), BR * 2.4, .7)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .38))

def hexpath(r, cx=CX, cy=CY):
    p = skia.Path()
    for k in range(6):
        a = math.radians(-90 + 60 * k); x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        (p.moveTo if k == 0 else p.lineTo)(x, y)
    p.close(); return p
def cell(c):
    c.drawPath(hexpath(RH + 30, CX, CY + 12), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
    c.drawPath(hexpath(RH + 12), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (CX, CY - 160), RH + 220, [skia.Color(36, 30, 26), skia.Color(20, 17, 15), skia.Color(11, 9, 8)], [0, .6, 1])))
    j = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeJoin=skia.Paint.kRound_Join)
    j.setStrokeWidth(12); j.setColor4f(skia.Color4f(1, .95, .85, .05)); c.drawPath(hexpath(RH + 9), j)
    j.setStrokeWidth(2.5); j.setColor4f(skia.Color4f(*CREAM, .26)); c.drawPath(hexpath(RH + 15), j)
    # glint on the upper-left edge
    a0, a1 = [(CX + (RH + 4) * math.cos(math.radians(a)), CY + (RH + 4) * math.sin(math.radians(a))) for a in (150, 210)]
    hp = skia.Path(); hp.moveTo(a0[0] + (a1[0] - a0[0]) * .2, a0[1] + (a1[1] - a0[1]) * .2); hp.lineTo(a0[0] + (a1[0] - a0[0]) * .75, a0[1] + (a1[1] - a0[1]) * .75)
    c.drawPath(hp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=skia.Color4f(1, 1, 1, .13)))

SW0, SW1 = d["stop"] + 1.2, d["stop"] + 3.0          # a glint sweeps down the packed cell as it locks
YT, YB = CY - RH, CY + RH
def sweep_y(t): return YT - 60 + (YB - YT + 120) * ss((t - SW0) / (SW1 - SW0))
GL2 = glow((1, .95, .85), BR * 1.4, .8)
first = None
def frame(f):
    global first
    k = min(f, NF - 1)
    P, R = FR[k], RA[k]; n = len(P)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        cell(c)
        for i in range(n):
            c.drawCircle(float(P[i, 0]) + 1.5, float(P[i, 1]) + 2.3, float(R[i]), SH)
        for i in range(n):
            blit(c, SPR[LVL[i]], float(P[i, 0]), float(P[i, 1]), float(R[i]) / BR)
        fresh = np.nonzero((FB[:n] >= 0) & (k - FB[:n] < 10))[0]
        ga = .9 * min(1, (40 / max(40, len(fresh))) ** .6)
        for i in fresh:
            age = k - FB[i]
            blit(c, GLW[LVL[i]], float(P[i, 0]), float(P[i, 1]), 1.0,
                 skia.Paint(Alphaf=ga * (1 - age / 10), BlendMode=skia.BlendMode.kPlus))
        t = k / FPS
        if SW0 <= t <= SW1 + .3:
            yb = sweep_y(t)
            for i in np.nonzero(np.abs(P[:, 1] - yb) < 70)[0]:
                a = .3 * (1 - abs(float(P[i, 1]) - yb) / 70) ** 2
                blit(c, GL2, float(P[i, 0]), float(P[i, 1]), 1.0, skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kPlus))
        if k < 60:   # soft halo marks the first two
            for i in (0, 1):
                blit(c, FIRSTG, float(P[i, 0]), float(P[i, 1]), 1.0,
                     skia.Paint(Alphaf=.6 * (1 - ss((k - 20) / 40)), BlendMode=skia.BlendMode.kPlus))
        bump = 0.0
        if k > 0 and CNT[k] > CNT[k - 1] and CNT[k] < 40: bump = .5
        header(c, "When two touch,", "a new one is born.", count=int(CNT[k]), count_col=CREAM, pulse=bump)
        watermark(c, 1585)
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
    # 1) every birth: a soft glass bell, pitch climbs with the colour; plus a tiny bubble-pop of the bud
    bells = {i: mallet(note(i, 261.63), 1.0, .75) for i in range(16)}
    pops = [glass_click(rng.uniform(1800, 2600), rng.uniform(110, 150), .06, .25) for _ in range(16)]
    BT = np.array([b[0] for b in BIR])
    byf = {}
    for b in BIR: byf.setdefault(int(b[0] * FPS), []).append(b)
    for f, es in byf.items():
        if f >= NF: continue
        for b in es[:10]:
            u = U[b[3]]
            i = int(round(u * 10)) + int(rng.choice([0, 0, 1, 2]))
            dens = np.sum(np.abs(BT - b[0]) < .25)
            g = .34 * (6 / max(6, dens)) ** .35 / (1 + .06 * (len(es) - 1))
            m.add(bells[min(15, i)], b[0] + rng.uniform(0, .004), g, b[1])
            m.add(pops[rng.integers(16)], b[0], g * .5, b[1])
    # 2) pearls tapping each other and the glass
    taps = [glass_click(rng.uniform(2600, 3800), rng.uniform(150, 210), .05, .35) for _ in range(24)]
    cb = {}
    for c in CLK:
        f = int(c[0] * FPS)
        if f < NF: cb.setdefault(f, []).append(c)
    for f, es in cb.items():
        rng.shuffle(es)
        for e in es[:4]:
            m.add(taps[rng.integers(24)], e[0] + rng.uniform(0, .015), .05 * min(1.6, (e[3] / 40) ** .5), e[1])
    # 3) soft low thump at 10, 25, 50, 100, then every hundred
    thumps = [thud(rng.uniform(52, 64), .5) for _ in range(6)]
    marks = [10, 25, 50] + list(range(100, 2000, 100)); mi = 0
    for b in BIR:
        cnt = b[3] + 1
        if mi < len(marks) and cnt >= marks[mi] and b[0] * FPS < NF:
            m.add(thumps[mi % 6], b[0], .26, 540); mi += 1
    # 4) it fills: two deep soft thumps as the cell packs and settles
    st = d["stop"]
    m.add(thud(46, .9), st + .1, .45, 540); m.add(thud(50, .9), st + 1.2, .35, 540)
    # 5) the glint sweep: soft glass ticks across the honeycomb, pitch falling from top to bottom
    Pend = FR[min(len(FR) - 1, int(SW1 * FPS))]
    ticks = {i: mallet(note(i, 523.25), .6, .5) for i in range(12)}
    for tt in np.arange(SW0, SW1, .045):
        yb = sweep_y(tt); row = np.nonzero(np.abs(Pend[:, 1] - yb) < 14)[0]
        if not len(row): continue
        i = int(rng.choice(row)); lvl = int(round(9 * (1 - (yb - YT) / (YB - YT)))) + int(rng.integers(0, 2))
        m.add(ticks[max(0, min(11, lvl))], tt + rng.uniform(0, .01), .07, float(Pend[i, 0]))
    tc = (NF + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63 / 2), 3.0, .5), tc + i * .08, .24, 540 + (i - 1.5) * 110)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[2].split(",")]
        if len(sys.argv) > 4: print(audio("B.wav")); sys.exit()
        for f in fs:
            if f >= TOTAL - XF and first is None: frame(0)
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
        print("NF", NF, "TOTAL", TOTAL)
    else:
        w = Writer("B_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("B.wav"))
        print("mux", mux("B_silent.mp4", "B.wav", "born.mp4"))
