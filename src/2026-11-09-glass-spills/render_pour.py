"""No. 12 render — 'When a glass fills, / it spills over.'"""
import pickle, sys, math
import numpy as np, skia
from kit import *

d = pickle.load(open("pour.pkl", "rb"))
FR, CNT, TB, HITS, OCC, G = d["frames"], d["counts"], d["tb"], d["hits"], d["occs"], d["geom"]
CUPS, WA, WB, STEP, TABLE, TL, TR, BR, SPY, BASIN = (G[k] for k in ("CUPS", "WA", "WB", "STEP", "TABLE", "TL", "TR", "BR", "SPY", "BASIN"))
STOP = d["stop"]
N = len(TB)
NF = min(len(FR), int((STOP + float(__import__('os').environ.get('ACT', 4.0))) * FPS))
HOLD, CARD, XF = 30, 66, 18
TOTAL = NF + HOLD + CARD + XF
FULLN = 62
FULL_F = [int(np.argmax(OCC[:, c] >= FULLN)) if (OCC[:, c] >= FULLN).any() else 10 ** 6 for c in range(len(CUPS))]
LASTFULL = max(FULL_F)
print("full frames", FULL_F, "NF", NF, "TOTAL", TOTAL, TOTAL / FPS)

# colour of the stream drifts with time: mint -> aqua -> violet -> rose -> honey gold
STOPS = [(0, (.55, .95, .80)), (.25, (.45, .80, 1.0)), (.5, (.72, .60, 1.0)), (.75, (1.0, .56, .72)), (1.0, (1.0, .80, .40))]
def ocol(u):
    for (u0, c0), (u1, c1) in zip(STOPS, STOPS[1:]):
        if u <= u1:
            w = (u - u0) / (u1 - u0); return tuple(a + (b - a) * w for a, b in zip(c0, c1))
    return STOPS[-1][1]
LV = 40
U = np.clip((TB - TB.min()) / (STOP - TB.min()), 0, 1)
LVL = np.clip(np.round(U * (LV - 1)), 0, LV - 1).astype(int)
SPR = [glass_ball(ocol(i / (LV - 1)), BR + .4) for i in range(LV)]
BG = background(1000)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35))
CUPGLOW = glow((1, .93, .78), WA * .9, .5)
GL2 = glow((1, .95, .85), BR * 2.2, .8)

def bowl_path(x, y, inset=0.0):
    p = skia.Path(); a, b = WA - inset, WB - inset
    p.moveTo(x - a - 5, y - 3)
    for t in np.linspace(0, math.pi, 40): p.lineTo(x - a * math.cos(t), y + b * math.sin(t))
    p.lineTo(x + a + 5, y - 3); return p

def draw_back(c, f):
    # glass tank the tower stands in
    tank = skia.Path(); tank.moveTo(*BASIN[0])
    for q in BASIN[1:]: tank.lineTo(*q)
    c.drawPath(tank, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10, StrokeJoin=skia.Paint.kRound_Join,
               Color4f=skia.Color4f(1, .95, .85, .04)))
    fill = skia.Path(tank); fill.close()
    c.drawPath(fill, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .95, .85, .025)))
    # soft floor shadow under the tower
    c.drawOval(skia.Rect(150, TABLE - 26, 930, TABLE + 18), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
    for (r, x, y) in CUPS:
        # stem + foot (behind beads)
        st = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap, Style=skia.Paint.kStroke_Style)
        st.setStrokeWidth(7); st.setColor4f(skia.Color4f(1, .96, .88, .10)); c.drawLine(x, y + WB + 2, x, y + STEP - 8, st)
        st.setStrokeWidth(2); st.setColor4f(skia.Color4f(1, .96, .88, .30)); c.drawLine(x - 1.5, y + WB + 4, x - 1.5, y + STEP - 10, st)
        c.drawOval(skia.Rect(x - 34, y + STEP - 11, x + 34, y + STEP - 1), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .96, .88, .13)))
        c.drawOval(skia.Rect(x - 34, y + STEP - 11, x + 34, y + STEP - 1), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                   StrokeWidth=1.5, Color4f=skia.Color4f(1, .96, .88, .28)))
        # tinted inside of the bowl
        c.drawPath(bowl_path(x, y), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(x, y), (x, y + WB)], [skia.Color4f(1, .95, .85, .03).toColor(), skia.Color4f(1, .95, .85, .07).toColor()])))
    # brass spout
    sp = skia.Path(); sp.moveTo(510, 488); sp.lineTo(570, 488); sp.lineTo(552, 528); sp.lineTo(528, 528); sp.close()
    c.drawPath(sp, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(510, 0), (570, 0)],
               [skia.Color(120, 84, 40), skia.Color(232, 184, 110), skia.Color(150, 104, 50)], [0, .4, 1])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(522, 524, 558, 536), 4, 4), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.80, .60, .32, 1)))

def draw_front(c, f):
    for ci, (r, x, y) in enumerate(CUPS):
        p = bowl_path(x, y)
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=skia.Color4f(1, .96, .88, .42)))
        # rim line + highlight streak on the left of the bowl
        c.drawLine(x - WA - 5, y - 3, x + WA + 5, y - 3, skia.Paint(AntiAlias=True, StrokeWidth=1.2, Color4f=skia.Color4f(1, .96, .88, .22)))
        hp = skia.Path(); first = True
        for t in np.linspace(.35, 1.05, 14):
            px, py = x - (WA - 9) * math.cos(t), y + (WB - 9) * math.sin(t)
            (hp.moveTo if first else hp.lineTo)(px, py); first = False
        c.drawPath(hp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(1, 1, 1, .16)))
        # soft warm bloom when it fills
        age = f - FULL_F[ci]
        if 0 <= age < 40:
            a = .55 * (1 - age / 40) ** 1.5
            blit(c, CUPGLOW, x, y + WB * .35, 1.0, skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kPlus))
    # tank walls front highlight
    for xw in (TL, TR):
        c.drawLine(xw, TABLE - 190, xw, TABLE - 40, skia.Paint(AntiAlias=True, StrokeWidth=2, Color4f=skia.Color4f(1, .96, .88, .30)))
    c.drawLine(TL + 40, TABLE, TR - 40, TABLE, skia.Paint(AntiAlias=True, StrokeWidth=2, Color4f=skia.Color4f(1, .96, .88, .30)))

SW0 = (LASTFULL / FPS) + .5; SW1 = SW0 + 1.8     # a glint climbs the tower once the last glass is full
YT, YB = CUPS[0][2] - 40, TABLE
def sweep_y(t): return YB + 40 - (YB - YT + 80) * ss((t - SW0) / (SW1 - SW0))
first = None
def frame(f):
    global first
    k = min(f, NF - 1)
    P = FR[min(f, len(FR) - 1)]; n = len(P)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        draw_back(c, k)
        for i in range(n):
            c.drawCircle(float(P[i, 0]) + 1.2, float(P[i, 1]) + 1.8, BR, SH)
        for i in range(n):
            blit(c, SPR[LVL[i]], float(P[i, 0]), float(P[i, 1]))
        draw_front(c, k)
        t = k / FPS
        if SW0 <= t <= SW1 + .3:
            yb = sweep_y(t)
            for i in np.nonzero(np.abs(P[:, 1] - yb) < 40)[0]:
                a = .32 * (1 - abs(float(P[i, 1]) - yb) / 40) ** 2
                blit(c, GL2, float(P[i, 0]), float(P[i, 1]), 1.0, skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kPlus))
        header(c, "When a glass fills,", "it spills over.", count=int(CNT[k]), count_col=CREAM)
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
    hits = [h for h in HITS if 0 <= h[0] * FPS < NF]
    byf = {}
    for h in hits: byf.setdefault(int(h[0] * FPS), []).append(h)
    # 1) bead on glass: crisp clicks, the higher the glass the higher the click
    clicks = {r: [glass_click(rng.uniform(1.0, 1.12) * (2300 + 520 * (3 - r)), rng.uniform(150, 200), .06, .3) for _ in range(8)] for r in range(4)}
    # 2) bead on bead: tiny soft ticks (a quiet patter that grows with the flow)
    ticks = [glass_click(rng.uniform(3200, 4400), rng.uniform(220, 300), .04, .45) for _ in range(24)]
    # 3) bead on the tank floor: soft low glassy tock
    tocks = [glass_click(rng.uniform(900, 1250), rng.uniform(70, 95), .12, .15) for _ in range(10)]
    for f, es in byf.items():
        rng.shuffle(es)
        cg = [e for e in es if e[4] >= 0][:4]
        bb = [e for e in es if e[4] == -2][:5]
        tk = [e for e in es if e[4] == -3][:2]
        for e in cg:
            r = CUPS[e[4]][0]
            m.add(clicks[r][rng.integers(8)], e[0] + rng.uniform(0, .02), .11 * min(1.5, (e[3] / 60) ** .5), e[1])
        for e in bb:
            m.add(ticks[rng.integers(24)], e[0] + rng.uniform(0, .03), .028 * min(1.5, (e[3] / 60) ** .5), e[1])
        for e in tk:
            m.add(tocks[rng.integers(10)], e[0] + rng.uniform(0, .02), .07 * min(1.4, (e[3] / 60) ** .5), e[1])
    # 4) each glass that fills rings like a struck crystal glass — pentatonic, top glass highest
    order = sorted(range(len(CUPS)), key=lambda c: FULL_F[c])
    NOTE = {0: 12, 1: 10, 2: 9, 3: 7, 4: 8, 5: 6, 6: 3, 7: 5, 8: 4, 9: 2}
    for c in order:
        r, x, y = CUPS[c]; tf = FULL_F[c] / FPS
        if FULL_F[c] >= NF: continue
        m.add(mallet(note(NOTE[c], 261.63), 2.6, .7), tf, .22, x)
        m.add(thud(rng.uniform(54, 62), .5), tf, .13, 540)
    # 5) the last glass: a deeper soft thump
    m.add(thud(46, .9), LASTFULL / FPS + .05, .35, 540)
    # 6) the glint climbing the tower: rising soft glass ticks
    tk2 = {i: mallet(note(i, 523.25), .6, .5) for i in range(12)}
    Pend = FR[min(NF - 1, int(SW1 * FPS))]
    for tt in np.arange(SW0, SW1, .05):
        yb = sweep_y(tt); row = np.nonzero(np.abs(Pend[:, 1] - yb) < 12)[0]
        if not len(row): continue
        i = int(rng.choice(row)); lvl = int(round(10 * (YB - yb) / (YB - YT))) + int(rng.integers(0, 2))
        m.add(tk2[max(0, min(11, lvl))], tt + rng.uniform(0, .01), .06, float(Pend[i, 0]))
    tc = (NF + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63 / 2), 3.0, .5), tc + i * .08, .24, 540 + (i - 1.5) * 110)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[2].split(",")]
        if len(sys.argv) > 3: print(audio("A.wav")); sys.exit()
        for f in fs:
            if f >= TOTAL - XF and first is None: frame(0)
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("A_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("A.wav"))
        print("mux", mux("A_silent.mp4", "A.wav", "pour.mp4"))
