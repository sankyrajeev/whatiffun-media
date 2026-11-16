"""THREE FLOORS render: four bands of rainbow glass balls on three brick floors that give way one after another."""
import sys, math, pickle, os
import numpy as np, skia
import sim as S
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[2] if len(sys.argv) > 2 else HERE
frames, events, meta = pickle.load(open(os.path.join(HERE, "sim.pkl"), "rb"))
BAND, SUB, Y0, RAD, BR = meta["band"], meta["sub"], meta["y0"], meta["rad"], meta["bricks"]
N = len(BAND); NBR = len(BR)
CNT = [S.fallen(f[0], Y0) for f in frames]
REL = [e for e in events if e[1] in ("release", "all")]
T_LAST = max(e[0] for e in REL if e[1] == "all")
mx = max(CNT)
T_DONE = next(k for k, x in enumerate(CNT) if k / FPS > T_LAST and x >= mx - 8) / FPS + .25
CARD = T_DONE + .6
XF = 18
TOTAL = int((CARD + 2.9) * FPS) + XF
print("done", T_DONE, "total s", TOTAL / FPS, "final", mx)
ALL_T = [e[0] for e in REL if e[1] == "all"]

HUES = [268, 318, 8, 40]
NB = 12
SPR = [[glass_ball(hsv(HUES[k] + 16 * (j / (NB - 1) - .5), .64, 1.0), S.RMAX) for j in range(NB)] for k in range(4)]
SC = RAD / S.RMAX
BI = np.clip((SUB * NB).astype(int), 0, NB - 1)
ORDER = np.argsort(-Y0)    # draw bottom first
GL_F = glow((1, .85, .55), 30, .9)
GL_S = glow((1, .9, .7), 8, .7)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)

# brick sprites: glossy sandstone/terracotta, a few tones
def brick_sprite(col):
    w, h = S.BW - 3, S.BH - 2
    sz = w + 8
    def fn(c):
        x0, y0 = (sz - w) / 2, (sz - h) / 2
        rr = skia.RRect.MakeRectXY(skia.Rect(x0, y0, x0 + w, y0 + h), 4, 4)
        light = tuple(min(1, v * 1.25 + .08) for v in col); dark = tuple(v * .55 for v in col)
        c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y0), (0, y0 + h)],
                    [skia.Color4f(*light, 1).toColor(), skia.Color4f(*col, 1).toColor(), skia.Color4f(*dark, 1).toColor()], [0, .45, 1])))
        c.drawRRect(rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=skia.Color4f(1, .95, .85, .35)))
        c.drawRect(skia.Rect(x0 + 5, y0 + 2.5, x0 + w - 5, y0 + 4.5), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .35),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1)))
    return sprite(fn, sz)
_r = np.random.default_rng(3)
BTONES = [brick_sprite((.80 + _r.uniform(-.05, .05), .55 + _r.uniform(-.05, .05), .36 + _r.uniform(-.04, .04))) for _ in range(6)]
BT = _r.integers(0, 6, NBR)

BG = background(1000)
static = skia.Surface.MakeRaster(INFO)
glass = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(.80, .87, .95, .42))
glass_hi = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8, StrokeJoin=skia.Paint.kRound_Join, Color4f=skia.Color4f(1, 1, 1, .5))
with static as c:
    c.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Path(); p.moveTo(S.JX0, S.JTOP); p.lineTo(S.JX0, S.TY); p.lineTo(S.JX1, S.TY); p.lineTo(S.JX1, S.JTOP)
    c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.6, .75, .9, .04)))
    c.drawPath(p, glass); c.save(); c.translate(-2, -1.5); c.drawPath(p, glass_hi); c.restore()
STATIC = static.makeImageSnapshot()

F_L = font(TF_SERIF_I, 46)
def head(c, n, pulse, done, floors_left):
    text(c, "THREE FLOORS", W / 2, 196, F_KICK, AMBER, .9, spacing=7)
    text(c, "Three floors of loose bricks.", W / 2, 272, F_RULE, CREAM, .97)
    text(c, f"{N:,} balls stacked on them.", W / 2, 336, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 412); c.scale(1 + .08 * pulse, 1 + .08 * pulse); c.translate(-W / 2, -412)
    text(c, f"{n:,}", W / 2, 452, F_CNT, (1, .82, .55) if n > 0 else CREAM)
    c.restore()
    text(c, "all floors down" if done else "balls fallen", W / 2, 508, F_L, AMBER if done else CREAM, .95 if done else .8)

first = None
REL_T = np.array([e[0] for e in REL])
def frame(f):
    global first
    t = f / FPS
    fi = min(f, len(frames) - 1)
    P, B = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.save(); c.clipRect(skia.Rect(0, 526, W, H))
        jo = 0
        for e in REL:
            u = t - e[0]
            if 0 <= u < .4: jo += (4 if e[1] == "release" else 13) * math.exp(-u / (.08 if e[1] == "release" else .12)) * math.sin(u * 85)
        z = 1.0 + .27 * ss((t - 8.4) / 3.4)
        c.translate(540, 1592 + jo); c.scale(z, z); c.translate(-540, -1592)
        c.drawImage(STATIC, 0, 0)
        # flashes along a floor when a column lets go / the whole floor goes
        for e in REL:
            u = t - e[0]
            if 0 <= u < .6:
                fy = S.FLOORS[int(e[4])] + S.FH / 2
                if e[1] == "release": blit(c, GL_F, e[2], fy, 1.0, pa(.8 * math.exp(-u / .15)))
                else:
                    for xx in np.linspace(S.JX0 + 40, S.JX1 - 40, 7): blit(c, GL_F, xx, fy, 1.4, pa(.7 * math.exp(-u / .2)))
        for i in ORDER:
            blit(c, SPR[BAND[i]][BI[i]], P[i, 0], P[i, 1], SC[i])
        for j in range(NBR):
            x, y, a = B[j]
            if y > 1700: continue
            c.save(); c.translate(x, y); c.rotate(math.degrees(a)); blit(c, BTONES[BT[j]], 0, 0); c.restore()
        c.restore()
        n = CNT[fi]
        pulse = max([math.exp(-(t - a_) / .3) for a_ in ALL_T if t >= a_], default=0)
        done = t >= T_DONE
        if done: pulse = max(pulse, math.exp(-(t - T_DONE) / .3))
        head(c, n, pulse, done, 0)
        watermark(c, 1628)
        if t >= CARD:
            a = ss((t - CARD) / .45)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

def audio(path):
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(9)
    m = Mix(TOTAL / FPS)
    # tension bed in the build-up: low hum + filtered strain noise rising to the first collapse, soft tick speeding up
    TB = ALL_T[0]; n = int((TB + .3) * SR); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 98 * tt) + .4 * np.sin(2 * np.pi * 147 * tt)) * (.5 + .5 * tt / TB) * np.minimum(1, tt * 8)
    m.add(hum * .10, 0, 1, 540)
    sw = sosfilt(butter(2, [500, 3500], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    m.add(sw * (.25 + .75 * np.clip(tt / TB, 0, 1) ** 2) * .10, 0, 1, 540)
    tk = glass_click(880, 240, .05, .5); t = 0.12
    while t < TB:
        m.add(tk, t, .2 + .1 * t / TB, 540); t += 1 / (2 + 2.5 * (t / TB) ** 1.4)
    per = {}
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if kind == "release":
            fl = int(e[4])
            m.add(thud(85 - 8 * fl, .35), t, .55, e[2])
            nn = sosfilt(butter(2, [300, 2500], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.3 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 12), t, .35, e[2])          # stone scrape
            m.add(glass_click(1200 - 120 * fl, 60, .15, .6), t, .5, e[2])
        elif kind == "all":
            fl = int(e[4])
            m.add(thud(58 - 4 * fl, 1.0), t, 1.25, 540); m.add(mallet(note(7 - 2 * fl, 196), 1.6, .8), t, .45, 540)
            m.add(mallet(98, 1.2, .5), t, .35, 540)
            nn = sosfilt(butter(2, [200, 3000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(1.0 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 4), t, .5, 540)
        elif kind in ("ballbrick", "ball", "wall", "brick", "brick2"):
            key = (kind, fk); per[key] = per.get(key, 0) + 1
            lim = {"ballbrick": 4, "ball": 4, "wall": 2, "brick": 2, "brick2": 2}[kind]
            if per[key] > lim: continue
            v = min(1, e[4] / 600)
            if kind == "ball":
                h = int(np.clip((1600 - e[3]) / 100, 0, 9))
                m.add(glass_click(note(h + 5, 261.63) * 2, 150, .07, .3), t + rng.uniform(0, .02), .1 + .12 * v, e[2])
            elif kind == "ballbrick":
                m.add(glass_click(1500 + rng.uniform(-200, 200), 120, .08, .35), t + rng.uniform(0, .02), .12 + .14 * v, e[2])
            elif kind in ("brick", "brick2"):
                m.add(thud(110 + rng.uniform(-15, 15), .2), t, .25 + .3 * v, e[2])
                m.add(glass_click(700 + rng.uniform(-80, 80), 90, .1, .7), t, .15 + .15 * v, e[2])
            else:
                m.add(glass_click(1400, 200, .05, .35), t, .08, e[2])
    # pour bed: rushing sound shaped by the fall rate
    flow = np.clip(np.diff(np.array(CNT, float), prepend=0), 0, None)
    fl = np.repeat(np.convolve(flow, np.ones(6) / 6, "same"), SR // FPS)
    nn = sosfilt(butter(2, [700, 5000], btype="band", fs=SR, output="sos"), rng.standard_normal(len(fl)))
    m.add(nn[:m.N] * np.clip(fl / 10, 0, 1)[:m.N] * .08, 0, 1, 540)
    for j, n_ in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), T_DONE + .05 + j * .07, .32, 380 + j * 80)
    for j, n_ in enumerate((0, 4, 7)):
        m.add(mallet(note(n_, 196), 2.2, .4), CARD + .1 + j * .06, .2, 450 + j * 90)
    n = int((TOTAL / FPS - CARD) * SR); tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * note(k, 130.81) * tt) for k in (0, 2, 4, 7)) * np.minimum(1, tt / .6) * np.exp(-tt / 2.5)
    m.add(pad * .05, CARD, 1, 540)
    return m.save(path, fade_in=.0, fade_out=.3)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[3].split(",")]
        frame(0)
        for f in fs: frame(f).makeImageSnapshot().save(f"{OUTD}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print("rms", audio(f"{OUTD}/a.wav"))
    else:
        w = Writer(f"{OUTD}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print("rms", audio(f"{OUTD}/a.wav"))
        print("mux", mux(f"{OUTD}/silent.mp4", f"{OUTD}/a.wav", f"{OUTD}/out.mp4"))
