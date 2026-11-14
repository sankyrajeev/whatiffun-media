"""Render: 300 fireflies over a night meadow, pulse-coupled (sim.py). Opens mid-action with a big left swarm
and a rival right swarm flashing just after it; the echo gap closes (0.29 s -> 0.07 s) and then the whole
meadow flashes as one."""
import sys, os, math
import numpy as np, skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "2026-11-05-asmr-samples"))
from kit import *
import sim, search

KW = dict(seed=1, left_df=0.08, lam=60, eps=[0.03, 0.35], ramp=[0, 22], T=28)
T0 = 9.6            # sim time at video frame 0 (open mid-action)
ACT = 14.2          # video seconds of action before the end card
TAIL = 2.6
DUR = ACT + TAIL
TOTAL = int(round(DUR * FPS))
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ff"

P, FREQ, FL = sim.run(**KW)
N = len(P)
FT = np.array([a for a, b in FL]); FI = np.array([b for a, b in FL])
CNT = search.sync_counts(P, FL, KW["T"])            # per 1/30 s of sim time
def count_at(ts): return int(CNT[min(len(CNT) - 1, int(round(ts * 30)))])
# merge moment = first sim frame with >= 297 in sync
T_MERGE = np.nonzero(CNT >= 297)[0][0] / 30
rng = np.random.default_rng(11)
DRIFT = rng.uniform(0, 2 * math.pi, (N, 4)); DSP = rng.uniform(.25, .55, (N, 2))
SIZE = rng.uniform(.8, 1.15, N)

def pos(i, ts):
    a = DRIFT[i]
    return (P[i, 0] + 16 * math.sin(DSP[i, 0] * ts + a[0]) + 6 * math.sin(1.7 * DSP[i, 1] * ts + a[2]),
            P[i, 1] + 11 * math.sin(DSP[i, 1] * ts + a[1]) + 4 * math.sin(2.1 * DSP[i, 0] * ts + a[3]))

def brightness(ts):
    """per firefly: glow from its most recent flash"""
    b = np.zeros(N)
    m = (FT <= ts) & (FT > ts - 1.2)
    for t, i in zip(FT[m], FI[m]):
        tau = ts - t
        b[i] = max(b[i], min(1, tau / .035) * math.exp(-tau / .2))
    return b

GLOW_COL = (0.78, 1.0, 0.42)
G_BIG = glow(GLOW_COL, 30, .55)
G_MID = glow((0.92, 1.0, 0.62), 10, .9)
CORE = glow((1.0, 1.0, 0.86), 3.2, 1.0)
DIM = glow((0.62, 0.78, 0.36), 5, .5)
BG = background(1050)
F_KICK2 = font(TF_SEMI, 30); F_SMALL = font(TF_SERIF_I, 38)

# grass silhouettes (three layers, swaying)
GR = []
for layer, (n, y0, hmin, hmax, shade) in enumerate([(70, 1500, 120, 260, .075), (60, 1580, 160, 330, .05), (55, 1680, 200, 380, .03)]):
    for k in range(n):
        x = rng.uniform(60, 1020); GR.append((layer, x, y0 + rng.uniform(-20, 40), rng.uniform(hmin, hmax),
                                              rng.uniform(-.5, .5), rng.uniform(0, 6.28), shade, rng.uniform(5, 10)))

def grass(c, ts, light):
    p = skia.Paint(AntiAlias=True)
    for layer, x, y0, h, lean, ph, shade, w in GR:
        sway = 10 * math.sin(.6 * ts + ph + x * .004) * (1 + layer * .3)
        tipx = x + lean * h * .5 + sway; tipy = y0 - h
        path = skia.Path(); path.moveTo(x - w / 2, H)
        path.quadTo(x - w * .3 + sway * .3, y0 - h * .5, tipx, tipy)
        path.quadTo(x + w * .3 + sway * .3, y0 - h * .5, x + w / 2, H); path.close()
        v = shade + .05 * light * (1 - layer * .3)
        p.setColor4f(skia.Color4f(v * 1.0, v * 1.05, v * .7, 1)); c.drawPath(path, p)

def scene(c, ts):
    b = brightness(ts)
    light = float(min(1, (b > .25).sum() / 220))
    # ambient bloom over the meadow when many flash at once
    if b.sum() > 1:
        cx = float((np.array([pos(i, ts)[0] for i in range(N)]) * b).sum() / b.sum())
        amb = min(1.0, b.sum() / 160)
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(BlendMode=skia.BlendMode.kPlus, Shader=skia.GradientShader.MakeRadial(
            (cx, 1080), 820, [skia.Color4f(.16, .2, .07, .55 * amb).toColor(), skia.Color4f(0, 0, 0, 0).toColor()], [0, 1])))
    add = skia.Paint(BlendMode=skia.BlendMode.kPlus)
    for i in range(N):
        x, y = pos(i, ts); s = SIZE[i]; bi = b[i]
        if bi < .04:
            blit(c, DIM, x, y, s * .8, skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=.35)); continue
        add.setAlphaf(min(1, bi * .85)); blit(c, G_BIG, x, y, s * (.7 + .5 * bi), add)
        add.setAlphaf(min(1, bi)); blit(c, G_MID, x, y, s, add)
        add.setAlphaf(min(1, bi * 1.2)); blit(c, CORE, x, y, s * (.8 + .4 * bi), add)
    grass(c, ts, light)
    c.drawRect(skia.Rect(0, 1560, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1560), (0, H)],
        [skia.Color4f(0, 0, 0, 0).toColor(), skia.Color4f(.03, .025, .02, .9).toColor()])))

FIRST = None
def frame(f):
    v = f / FPS; ts = T0 + v
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        scene(c, ts)
        text(c, "FIREFLIES", W / 2, 196, F_KICK2, AMBER, .9, spacing=8)
        text(c, "Every flash nudges", W / 2, 272, F_RULE, CREAM, .97)
        text(c, "its neighbours.", W / 2, 338, F_RULE_I, CREAM, .9)
        n = min(N, count_at(ts))
        if ts >= T_MERGE: n = max(n, 297)
        pulse = max(0.0, 1 - abs(ts - T_MERGE - .1) / .4) if ts > T_MERGE - .3 else 0
        col = AMBER if n >= 297 else CREAM
        cy = 430
        c.save(); c.translate(W / 2, cy); c.scale(1 + .12 * pulse, 1 + .12 * pulse); c.translate(-W / 2, -cy)
        text(c, f"{n}", W / 2, 458, F_CNT, col); c.restore()
        text(c, f"of {N} in sync", W / 2, 506, F_SMALL, CREAM, .55)
        watermark(c, 1640)
        ea = ss((v - (ACT + .2)) / .6)
        if ea > 0:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(0, 0, 0, .35 * ea)))
            end_card(c, ea)
    xf = ss((v - (DUR - .6)) / .6)
    if xf > 0 and FIRST is not None:
        with out as c: c.drawImage(FIRST, 0, 0, SAMP, skia.Paint(Alphaf=xf))
    return out

def chirp(f0=4400, dur=.22):
    t = np.arange(int(dur * SR)) / SR
    am = (np.sin(2 * np.pi * 38 * t) > 0).astype(float) * np.sin(np.pi * t / dur) ** 2
    return np.sin(2 * np.pi * f0 * t) * am
def audio(path):
    m = Mix(DUR)
    r = np.random.default_rng(3)
    tick = [glass_click(note(k, 440), 70, .09, .12) for k in range(10)]
    sel = (FT >= T0) & (FT < T0 + DUR)
    ft, fi = FT[sel] - T0, FI[sel]
    for tv, i in zip(ft, fi):
        dens = ((ft > tv - .03) & (ft < tv + .03)).sum()
        x, y = pos(i, tv + T0)
        k = int(np.clip((1460 - y) / 82, 0, 9))
        fade = 1.0 if tv < ACT + .3 else max(0, 1 - (tv - ACT - .3) / 1.5)
        m.add(tick[k], tv + r.uniform(0, .004), .2 / math.sqrt(dens) * fade, 540 + (x - 540) * 1.3)
    # a soft low pulse under every big burst (size-tied)
    sim.P_X = P[:, 0]
    for t, n, x in sim.bursts([e for e in FL if T0 <= e[0] < T0 + DUR], gap=.012):
        if n >= 30:
            tv = t - T0; fade = 1.0 if tv < ACT + .3 else max(0, 1 - (tv - ACT - .3) / 1.5)
            m.add(thud(48 + 20 * (n / 300), .5), tv, .07 + .16 * (n / 300) ** 1.2 * fade, 540 + (x - 540) * .8)
            m.add(mallet(note(2, 220) * (1 + .5 * (x > 560)), .7, .3), tv, .02 + .03 * n / 300 * fade, 540 + (x - 540))
    # night bed: distant crickets
    for k in range(int(DUR / .9)):
        tv = k * .9 + r.uniform(0, .3)
        m.add(chirp(r.uniform(4100, 4700)), tv, .006, r.uniform(150, 930))
    # tension swell into the merge
    tm = T_MERGE - T0
    t = np.arange(int(tm * SR)) / SR
    sw = sum(np.sin(2 * np.pi * f * t) for f in (110, 165, 220.5)) * (t / tm) ** 3
    m.add(sw, 0, .02, 540)
    for k, f0 in enumerate([note(5, 220), note(7, 220), note(9, 220), note(10, 220)]):
        m.add(mallet(f0, 2.8, .8), tm + .015 * k, .10, 540 + (k - 1.5) * 140)
    m.add(thud(52, .9), tm, .3, 540)
    te = ACT + .25
    for k, f0 in enumerate([note(0, 130.8), note(2, 130.8), note(4, 130.8), note(5, 130.8)]):
        m.add(mallet(f0, 3.0, .45), te + .06 * k, .11, 540 + (k - 1.5) * 140)
    return m.save(path, fade_in=0, fade_out=.5)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("merge at video", round(T_MERGE - T0, 2))
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[3].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print(audio(f"{OUT}/ff.wav"))
    else:
        FIRST = frame(0).makeImageSnapshot()
        w = Writer(f"{OUT}/ff_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/ff.wav"))
        print("mux", mux(f"{OUT}/ff_silent.mp4", f"{OUT}/ff.wav", f"{OUT}/firefly_sync.mp4"))
