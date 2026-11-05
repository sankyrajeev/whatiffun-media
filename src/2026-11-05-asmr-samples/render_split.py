import pickle, sys, math
import numpy as np, skia
from kit import *

d = pickle.load(open("split.pkl", "rb"))
FR, RF, CNT, BORN, EV, G = d["frames"], d["radf"], d["counts"], d["born"], d["events"], d["geom"]
CX, CY, R, R0 = G["CX"], G["CY"], G["R"], G["R0"]
NF = len(FR); GRAV = d["gravity_at"]
HOLD, CARD, XF = 18, 66, 18
TOTAL = NF + HOLD + CARD + XF

def gen_of(r): return int(round(2 * math.log2(R0 / r)))
MAXG = gen_of(min(RF[-1]))
def gcol(g):
    u = g / max(1, MAXG)
    return hsv(268 + 140 * u, .66 - .22 * u, .80 + .20 * u)
SPR = {g: glass_ball(gcol(g), R0 / 2 ** (g / 2)) for g in range(MAXG + 1)}
POP = {g: glow(gcol(g), max(4, R0 / 2 ** (g / 2)) * 1.1, .7) for g in range(MAXG + 1)}
BG = background(CY)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .33))
first = None

def frame(f):
    global first
    k = min(f, NF - 1)
    pos, rad = FR[k], RF[k]; n = len(pos)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.drawCircle(CX, CY + 16, R + 8, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
        c.drawCircle(CX, CY, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX - 120, CY - 160), R * 1.4, [skia.Color(34, 28, 24), skia.Color(19, 16, 13)])))
        for i in range(n):
            r = float(rad[i]); c.drawCircle(float(pos[i, 0]) + r * .12 + 1, float(pos[i, 1]) + r * .2 + 1.5, r, SH)
        for i in range(n):
            r = float(rad[i]); g = gen_of(r)
            age = k - BORN[i]
            blit(c, SPR[g], float(pos[i, 0]), float(pos[i, 1]))
        # split pops (recent splits)
        for e in EV:
            pass
        c.drawCircle(CX, CY, R + 3, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                     Color4f=skia.Color4f(1, .95, .85, .06)))
        c.drawCircle(CX, CY, R + 3, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5,
                     Color4f=skia.Color4f(*CREAM, .32)))
        arc = skia.Path(); arc.addArc(skia.Rect(CX - R + 10, CY - R + 10, CX + R - 10, CY + R - 10), 200, 50)
        c.drawPath(arc, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(1, .97, .9, .14)))
        header(c, "Every bounce", "splits it in two.", count=int(CNT[k]))
        watermark(c)
        if f >= NF + HOLD:
            a = ss((f - NF - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

# split pop overlay: draw glow where splits happened in the last few frames
SPLITS = {}
for e in EV:
    if e[4] == "split": SPLITS.setdefault(int(e[0] * FPS), []).append(e)
_frame = frame
def frame(f):
    s = _frame(f)
    with s as c:
        for back in range(0, 6):
            for e in SPLITS.get(f - back, []):
                g = gen_of(e[5]) if e[5] > 0 else 0
                blit(c, POP[min(MAXG, g)], e[1], e[2], 1.0, skia.Paint(Alphaf=.55 * (1 - back / 6), BlendMode=skia.BlendMode.kPlus))
    return s

def audio(path):
    m = Mix(TOTAL / FPS + .5)
    rng = np.random.default_rng(9)
    def pitch(r): return 95 * (R0 / r) ** .72
    cache = {}
    def bonk(r, kind):
        key = (round(r, 1), kind)
        if key not in cache:
            f0 = pitch(r) * (1.0 if kind == "wall" else 1.5)
            dur = .35 if r > 20 else .12
            t = np.arange(int(dur * SR)) / SR
            dec = 10 + 900 / max(r, 1)
            body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * dec) + .35 * np.sin(2 * np.pi * f0 * 2.7 * t) * np.exp(-t * dec * 1.8)
            click = rng.standard_normal(len(t)) * np.exp(-t * 2500) * .5
            sig = body + np.diff(click, prepend=0)
            if r > 25: sig += thud(f0 * .5, dur) * .45
            cache[key] = sig * np.minimum(1, t * 5000)
        return cache[key]
    byf = {}
    for e in EV:
        if e[4] in ("wall", "ball") and e[0] * FPS < NF: byf.setdefault(int(e[0] * FPS), []).append(e)
    for f, es in byf.items():
        es.sort(key=lambda e: -e[5] * 1000 - e[3])
        dens = len(es)
        for e in es[:22]:
            r = e[5]
            g = (.34 if e[4] == "wall" else .2) * (1.0 if r < 20 else .55) / (1 + .006 * max(0, dens - 6))
            m.add(bonk(r, e[4]), e[0] + rng.uniform(0, .004), g, e[1])
    for f, es in SPLITS.items():
        for e in es[:6]:
            r = e[5]; f0 = pitch(r) * 2.1
            t = np.arange(int(.09 * SR)) / SR
            s = (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 60) + rng.standard_normal(len(t)) * np.exp(-t * 900) * .3)
            m.add(s, e[0], .16 / (1 + .15 * len(es)), e[1])
    tc = (NF + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63), 3.0, .5), tc + i * .06, .14, 540 + (i - 1.5) * 90)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            if f > 0: frame(0)
            frame(f).makeImageSnapshot().save(f"B_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("B_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("B.wav"))
        print("mux", mux("B_silent.mp4", "B.wav", "sample_B_split.mp4"))
