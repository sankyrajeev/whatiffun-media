"""TIPPING TRAY render: a glass tray of 1,000+ rainbow glass balls tips further and further against a dam of
loose bricks; bricks pop, the dam bursts, the weir goes, and it all pours onto a brick pyramid in the bin."""
import sys, math, pickle, os
import numpy as np, skia
import sim as S
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[2] if len(sys.argv) > 2 else HERE
frames, events, meta = pickle.load(open(os.path.join(HERE, "sim.pkl"), "rb"))
U, RAD, ND, NP = meta["u"], meta["rad"], meta["ndam"], meta["npyr"]
N = len(U)
CNT = list(np.maximum.accumulate([S.out_count(f[0], f[2]) for f in frames]))
CNT = [min(x, max(CNT[:int(S.TBACK * FPS)])) for x in CNT]
REL = [e for e in events if e[1] in ("release", "all")]
FIRST_ALL = {}
for e in REL:
    if e[1] == 'all': FIRST_ALL.setdefault(round(e[0], 3), e)
BIG_T = sorted(set(round(e[0], 3) for e in REL if e[1] == "all"))
mx = max(CNT[:int(S.TBACK * FPS)])
T_DONE = next(k for k, x in enumerate(CNT) if x >= mx - 3) / FPS + .2
CARD = max(T_DONE + 1.0, S.TBACK + 1.45)
XF = 18
TOTAL = int((CARD + 3.1) * FPS) + XF
print("done", T_DONE, "total s", TOTAL / FPS, "final", mx, "big", BIG_T)

# colour: left (violet) -> right (gold) along the tray, a little by height
uu = (U[:, 0] + S.HW) / (2 * S.HW) * .85 + (U[:, 1] + S.HH) / (2 * S.HH) * .15
NB = 16
HUE = lambda q: 268 + 132 * q
SPR = [glass_ball(hsv(HUE(j / (NB - 1)) % 360, .64, 1.0), S.RMAX) for j in range(NB)]
BI = np.clip((uu * NB).astype(int), 0, NB - 1)
SC = RAD / S.RMAX
GL_F = glow((1, .85, .55), 30, .9)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)

def brick_sprite(col, w, h):
    sz = max(w, h) + 8
    def fn(c):
        x0, y0 = (sz - w) / 2, (sz - h) / 2
        rr = skia.RRect.MakeRectXY(skia.Rect(x0, y0, x0 + w, y0 + h), 4, 4)
        light = tuple(min(1, v * 1.25 + .08) for v in col); dark = tuple(v * .55 for v in col)
        c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x0, y0), (x0 + w * .3, y0 + h)],
                    [skia.Color4f(*light, 1).toColor(), skia.Color4f(*col, 1).toColor(), skia.Color4f(*dark, 1).toColor()], [0, .45, 1])))
        c.drawRRect(rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=skia.Color4f(1, .95, .85, .35)))
        c.drawRect(skia.Rect(x0 + 4, y0 + 2.5, x0 + w - 4, y0 + 4.5), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .35),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1)))
    return sprite(fn, sz)
_r = np.random.default_rng(3)
DAMS = [brick_sprite((.82 + _r.uniform(-.04, .04), .56 + _r.uniform(-.04, .04), .34), S.DW - 3, S.DH - 3) for _ in range(4)]
PYRS = [brick_sprite((.80 + _r.uniform(-.05, .05), .55 + _r.uniform(-.05, .05), .36 + _r.uniform(-.04, .04)), S.PB_W - 3, S.PB_H - 2) for _ in range(6)]
BT = _r.integers(0, 4, ND); PT = _r.integers(0, 6, NP)

BG = background(1000)
glass = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(.80, .87, .95, .45))
glass_hi = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                      Color4f=skia.Color4f(1, 1, 1, .55))
static = skia.Surface.MakeRaster(INFO)
with static as c:
    c.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Path(); p.moveTo(S.BX0, S.BTOP); p.lineTo(S.BX0, S.BY); p.lineTo(S.BX1, S.BY); p.lineTo(S.BX1, S.BRTOP)
    c.drawPath(p, glass); c.save(); c.translate(-2, -1.5); c.drawPath(p, glass_hi); c.restore()
STATIC = static.makeImageSnapshot()
TRAYP = skia.Path(); TRAYP.moveTo(-S.HW, -S.HH - 20); TRAYP.lineTo(-S.HW, S.HH); TRAYP.lineTo(S.HW, S.HH)
# pivot stand
def stand(c):
    p = skia.Path(); p.moveTo(S.PX - 40, S.PY + S.HH + 150); p.lineTo(S.PX, S.PY); p.lineTo(S.PX + 40, S.PY + S.HH + 150)
    c.drawCircle(S.PX, S.PY, 15, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color4f=skia.Color4f(.88, .68, .35, .95)))
    c.drawCircle(S.PX, S.PY, 4, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.35, .25, .15, 1)))

F_L = font(TF_SERIF_I, 46)
def head(c, n, pulse, done):
    text(c, "THE DAM", W / 2, 192, F_KICK, AMBER, .9, spacing=7)
    text(c, "The tray keeps tipping.", W / 2, 262, F_RULE, CREAM, .97)
    text(c, "One brick wall holds it.", W / 2, 324, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 400); c.scale(1 + .08 * pulse, 1 + .08 * pulse); c.translate(-W / 2, -400)
    text(c, f"{n:,}", W / 2, 438, F_CNT, (1, .82, .55) if n > 0 else CREAM)
    c.restore()
    text(c, "poured out" if done else "balls out", W / 2, 488, F_L, AMBER if done else CREAM, .95 if done else .8)

first = None
def frame(f):
    global first
    t = f / FPS
    fi = min(f, len(frames) - 1)
    P, B, th = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.save(); c.clipRect(skia.Rect(0, 506, W, H))
        jo = 0
        for e in REL:
            u = t - e[0]
            if 0 <= u < .4: jo += (4 if e[1] == "release" else 9) * math.exp(-u / (.08 if e[1] == "release" else .12)) * math.sin(u * 85)
        c.translate(0, jo)
        c.drawImage(STATIC, 0, 0)
        # tray (glass back + walls)
        c.save(); c.translate(S.PX, S.PY); c.rotate(math.degrees(th))
        c.drawRect(skia.Rect(-S.HW, -S.HH - 20, S.HW, S.HH), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.6, .75, .9, .05)))
        c.restore()
        for e in REL:
            u = t - e[0]
            if 0 <= u < .6:
                if e[1] == "release": blit(c, GL_F, e[6], e[7], 1.0, pa(.85 * math.exp(-u / .15)))
                elif e is FIRST_ALL.get(round(e[0], 3)): blit(c, GL_F, e[6], e[7], 2.6, pa(1.0 * math.exp(-u / .3)))
        for i in range(N):
            blit(c, SPR[BI[i]], P[i, 0], P[i, 1], SC[i])
        for j in range(ND + NP):
            x, y, a = B[j]
            if y > 1700: continue
            if j < ND and abs(a - th) < 1e-6 and t < S.TB:   # still-held dam bricks strain and tremble
                amp = 1.0 + 3.5 * (t / S.TB) ** 1.5
                x += amp * math.sin(t * 47 + j * 1.7) * math.cos(th); y += amp * math.sin(t * 47 + j * 1.7) * math.sin(th)
            c.save(); c.translate(x, y); c.rotate(math.degrees(a)); blit(c, DAMS[BT[j]] if j < ND else PYRS[PT[j - ND]], 0, 0); c.restore()
        c.save(); c.translate(S.PX, S.PY); c.rotate(math.degrees(th))
        c.drawPath(TRAYP, glass); c.save(); c.translate(-2, -1.5); c.drawPath(TRAYP, glass_hi); c.restore()
        c.restore()
        c.restore()
        n = CNT[fi]
        pulse = max([math.exp(-(t - a_) / .3) for a_ in BIG_T if t >= a_], default=0)
        done = t >= T_DONE
        if done: pulse = max(pulse, math.exp(-(t - T_DONE) / .3))
        head(c, n, pulse, done)
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
    TB = S.TB; n = int((TB + .3) * SR); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 98 * tt) + .4 * np.sin(2 * np.pi * 147 * tt)) * (.5 + .5 * tt / TB) * np.minimum(1, tt * 8)
    m.add(hum * .11, 0, 1, 540)
    sw = sosfilt(butter(2, [500, 3500], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    m.add(sw * (.3 + .7 * np.clip(tt / TB, 0, 1) ** 2) * .11, 0, 1, 540)
    # wood/glass creak of the tray as it tips, all the way through
    n2 = int(11 * SR); t2 = np.arange(n2) / SR
    cr = sosfilt(butter(2, [150, 600], btype="band", fs=SR, output="sos"), rng.standard_normal(n2)) * (.6 + .4 * np.sin(2 * np.pi * .7 * t2))
    m.add(cr * .05 * np.minimum(1, t2 * 4), 0, 1, 540)
    tk = glass_click(880, 240, .05, .5); t = 0.1
    while t < TB:
        m.add(tk, t, .24 + .1 * t / TB, 540); t += 1 / (2 + 2.5 * (t / TB) ** 1.4)
    per = {}
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if kind == "release":
            m.add(thud(90, .35), t, .6, e[2])
            nn = sosfilt(butter(2, [300, 2500], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.3 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 12), t, .35, e[2])
            m.add(glass_click(1200, 60, .15, .6), t, .5, e[2])
        elif kind == "all":
            key = ("all", round(t, 2))
            if key in per: continue
            per[key] = 1
            big = t < S.TB + .1
            m.add(thud(55, 1.0), t, 1.3 if big else .9, 540); m.add(mallet(note(7 if big else 4, 196), 1.6, .8), t, .45, 540)
            m.add(mallet(98, 1.2, .5), t, .35, 540)
            nn = sosfilt(butter(2, [200, 3000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(1.0 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 4), t, .5, 540)
        else:
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
    flow = np.clip(np.diff(np.array(CNT, float), prepend=0), 0, None)
    fl = np.repeat(np.convolve(flow, np.ones(6) / 6, "same"), SR // FPS)
    nn = sosfilt(butter(2, [700, 5000], btype="band", fs=SR, output="sos"), rng.standard_normal(len(fl)))
    m.add(nn[:m.N] * np.clip(fl / 6, 0, 1)[:m.N] * .2, 0, 1, 540)
    # rain of small glass clicks shaped by the pour rate (balls landing on the heap), <= 4 per frame
    for k, fv in enumerate(flow):
        t = k / FPS
        if t > CARD: break
        for q in range(int(min(4, fv / 1.5))):
            m.add(glass_click(note(int(rng.integers(3, 12)), 261.63) * 2, 140, .06, .35), t + rng.uniform(0, 1 / FPS), .13, rng.uniform(450, 950))
    for j, n_ in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), T_DONE + .05 + j * .07, .32, 380 + j * 80)
    m.add(thud(75, .5), S.TBACK + 1.45, .7, 300); m.add(glass_click(900, 50, .2, .5), S.TBACK + 1.45, .3, 300)
    n3 = int(1.5 * SR); t3 = np.arange(n3) / SR
    cr3 = sosfilt(butter(2, [180, 700], btype="band", fs=SR, output="sos"), rng.standard_normal(n3)) * np.sin(np.pi * t3 / 1.5)
    m.add(cr3 * .12, S.TBACK, 1, 540)
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
