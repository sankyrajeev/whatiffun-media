import pickle, sys, math
import numpy as np, skia
from kit import *

d = pickle.load(open("notes.pkl", "rb"))
FR, CNT, BORN, SRC, EV, CH, G = d["frames"], d["counts"], d["born"], d["src"], d["events"], d["chimes"], d["geom"]
LEFT, RIGHT, TOP, FLOOR, BR = G["LEFT"], G["RIGHT"], G["TOP"], G["FLOOR"], G["BR"]
SIM_END = int(sys.argv[2]) if len(sys.argv) > 2 else 650
HOLD, CARD, XF = 24, 66, 18
TOTAL = SIM_END + HOLD + CARD + XF
NC = len(CH)
RING = 150

# chime colours: soft spectrum
COLS = [hsv(h, .55, 1.0) for h in np.linspace(12, 300, NC)]
ORDER = sorted(range(NC), key=lambda k: CH[k]["y"])     # top -> bottom
BALL = {k: glass_ball(COLS[k], BR) for k in range(NC)}
BALL[-1] = glass_ball((1.0, .93, .78), BR)
GLOW = {k: glow(COLS[k], 26, .9) for k in range(NC)}
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35))

rings = [[] for _ in range(TOTAL + 1)]
for e in EV:
    if e[4] == "chime" and e[3] >= RING:
        f = int(e[0] * FPS)
        if f < SIM_END: rings[f].append(e)
last_ring = np.full(NC, -999)
BG = background()

def chime_draw(c, k, flash):
    a, b = CH[k]["a"], CH[k]["b"]; col = COLS[k]
    if flash > 0:
        c.drawLine(a[0], a[1], b[0], b[1], skia.Paint(AntiAlias=True, StrokeWidth=34, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(*col, .35 * flash), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
    c.drawLine(a[0] + 2, a[1] + 5, b[0] + 2, b[1] + 5, skia.Paint(AntiAlias=True, StrokeWidth=14, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=skia.Color4f(0, 0, 0, .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    base = tuple(x * (.55 + .45 * flash) + (1 - x) * .5 * flash for x in col)
    c.drawLine(a[0], a[1], b[0], b[1], skia.Paint(AntiAlias=True, StrokeWidth=14, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=skia.Color4f(*base, 1)))
    c.drawLine(a[0], a[1] - 3, b[0], b[1] - 3, skia.Paint(AntiAlias=True, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=skia.Color4f(1, 1, 1, .35 + .5 * flash)))

first = None
def frame(f):
    global first
    k = min(f, SIM_END - 1)
    pos = FR[k]; n = len(pos)
    for e in rings[f] if f < SIM_END else []:
        last_ring[e[5]] = f
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        # glass container
        cp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(*CREAM, .22))
        path = skia.Path(); path.moveTo(LEFT - 6, TOP - 95); path.lineTo(LEFT - 6, FLOOR + 6); path.lineTo(RIGHT + 6, FLOOR + 6); path.lineTo(RIGHT + 6, TOP - 95)
        c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=12, Color4f=skia.Color4f(1, .95, .85, .04)))
        c.drawPath(path, cp)
        for i in range(n):
            c.drawCircle(float(pos[i, 0]) + 1.4, float(pos[i, 1]) + 2.2, BR, SH)
        for kk in range(NC):
            fl = max(0.0, 1 - (f - last_ring[kk]) / 9) if f < SIM_END + 2 else 0.0
            chime_draw(c, kk, fl)
        for i in range(n):
            age = k - BORN[i]
            blit(c, BALL[int(SRC[i])], float(pos[i, 0]), float(pos[i, 1]), 1 + (.6 * (1 - age / 6) if 0 < BORN[i] and age < 6 else 0))
        for kk in range(NC):
            fl = max(0.0, 1 - (f - last_ring[kk]) / 7) if f < SIM_END else 0.0
            if fl > 0:
                blit(c, GLOW[kk], CH[kk]["x"], CH[kk]["y"], 1.2, skia.Paint(Alphaf=.5 * fl, BlendMode=skia.BlendMode.kPlus))
        header(c, "Every note drops", "a new ball.", count=int(CNT[k]))
        watermark(c)
        if f >= SIM_END + HOLD:
            a = ss((f - SIM_END - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

def audio(path):
    m = Mix(TOTAL / FPS + .5)
    notes = {kk: mallet(note(NC - 1 - ORDER.index(kk), 392.0)) for kk in range(NC)}   # top chime = highest
    for f in range(SIM_END):
        es = sorted(rings[f], key=lambda e: -e[3])
        per = {}
        dens = len(es)
        for e in es[:12]:
            kk = e[5]
            if per.get(kk, 0) >= 2: continue
            per[kk] = per.get(kk, 0) + 1
            g = .5 * min(1.4, (e[3] / 300) ** .5) / (1 + .05 * max(0, dens - 4))
            m.add(notes[kk], e[0] + np.random.uniform(0, .006), g, e[1])
    # soft ticks for ball/floor/wall contacts
    rng = np.random.default_rng(3)
    ticks = [glass_click(rng.uniform(3500, 5200), rng.uniform(110, 160), .045, .4) for _ in range(24)]
    other = [e for e in EV if e[4] != "chime" and e[0] * FPS < SIM_END]
    byf = {}
    for e in other: byf.setdefault(int(e[0] * FPS), []).append(e)
    for f, es in byf.items():
        es.sort(key=lambda e: -e[3])
        for e in es[:10]:
            g = .07 * min(1.5, (e[3] / 80) ** .5) / (1 + .02 * len(es))
            m.add(ticks[rng.integers(24)], e[0], g, e[1])
    # end: soft resolving chord
    tc = (SIM_END + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4]):
        m.add(mallet(note(nn, 392.0 / 2), 3.0, .5), tc + i * .07, .18, 540 + (i - 1) * 120)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[3].split(",")]
        for f in range(max(fs) + 1):
            s = frame(f)
            if f in fs: s.makeImageSnapshot().save(f"A_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("A_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("A.wav"))
        print("mux", mux("A_silent.mp4", "A.wav", "sample_A_notes.mp4"))
