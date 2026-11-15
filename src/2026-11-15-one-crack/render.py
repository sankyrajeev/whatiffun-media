"""ONE CRACK render: hopper of rainbow glass balls on one cracking pane -> shatter -> pour through brass pegs."""
import sys, math, pickle, os
import numpy as np, skia
import sim as S
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[2] if len(sys.argv) > 2 else HERE
frames, events, layer, polys, RAD = pickle.load(open(os.path.join(HERE, "sim.pkl"), "rb"))
N = len(layer); NBASE = S.N_BASE
OUTC = [int((f[0][:N, 1] > S.NY + 20).sum()) for f in frames]
T_EMPTY = next(k for k, x in enumerate(OUTC) if x >= N) / FPS
CARD = T_EMPTY + .7
XF = 18
TOTAL = int((CARD + 2.6) * FPS) + XF
print("empty", T_EMPTY, "total s", TOTAL / FPS)
TB = S.T_BREAK
PX, PY = 540.0, S.NY + 4

# rainbow layers: top of the pile violet -> magenta -> coral -> amber -> gold at the bottom
NB = 32
SPR = [glass_ball(hsv(268 + 140 * (k / (NB - 1)), .62, 1.0), 8.6) for k in range(NB)]
SC = RAD / 8.6
BI = np.clip((layer * NB).astype(int), 0, NB - 1)
BASE = [glass_ball(hsv(178 + 40 * k / 7, .62, .95), S.R) for k in range(8)]
GL_P = glow((1, .8, .45), 10, .9)
GL_C = glow((.75, .9, 1), 26, .9)
GL_S = glow((.8, .9, 1), 8, .7)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)

# crack pattern: branches out from an impact point near the pane centre; grows one step per crack event
rng = np.random.default_rng(4)
CRK = []   # (step, polyline)
for st in range(len(S.CRACKS)):
    for b in range(3 + st // 2 + (2 if st > 6 else 0)):
        ang = rng.uniform(-math.pi, math.pi) if st < 2 else (0 if b % 2 == 0 else math.pi) + rng.normal(0, .5)
        x, y = PX + rng.normal(0, 6 + 5 * st), PY + rng.normal(0, 1)
        pts = [(x, y)]
        L = 30 + 7 * st
        for k in range(5):
            ang += rng.normal(0, .5); x += math.cos(ang) * L / 5; y += math.sin(ang) * L / 5 * .35
            y = min(PY + 8, max(PY - 8, y)); pts.append((x, y))
        CRK.append((st, pts))
crack_t = [e[0] for e in events if e[1] == "crack"]

BG = background(980)
static = skia.Surface.MakeRaster(INFO)
glass = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(.80, .87, .95, .42))
glass_hi = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8, StrokeJoin=skia.Paint.kRound_Join, Color4f=skia.Color4f(1, 1, 1, .5))
PEGS = S.pegs()
PEG = sprite(lambda c: (c.drawCircle(9, 9, 6.5, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((7, 6.5), 8,
             [skia.Color(255, 236, 190), skia.Color(205, 150, 70), skia.Color(90, 60, 25)], [0, .5, 1])))), 18)
with static as c:
    c.clear(skia.Color4f(0, 0, 0, 0))
    hop = skia.Path(); hop.moveTo(S.JX0, S.JY0 - 40); hop.lineTo(S.JX0, S.JY1); hop.lineTo(S.NX0, S.NY); hop.lineTo(S.NX1, S.NY); hop.lineTo(S.JX1, S.JY1); hop.lineTo(S.JX1, S.JY0 - 40)
    c.drawPath(hop, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.6, .75, .9, .045)))
    tray = skia.Path(); tray.moveTo(S.TX0, 1005); tray.lineTo(S.TX0, S.TY); tray.lineTo(S.TX1, S.TY); tray.lineTo(S.TX1, 1005)
    c.drawPath(tray, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.6, .75, .9, .03)))
    for p_ in (hop, tray):
        c.drawPath(p_, glass)
        c.save(); c.translate(-2, -1.5); c.drawPath(p_, glass_hi); c.restore()
    for x, y in PEGS: blit(c, PEG, x, y)
STATIC = static.makeImageSnapshot()

peg_hits = [(e[0], e[2], e[3]) for e in events if e[1] == "peg"]
PH_T = np.array([e[0] for e in peg_hits])
F_L = font(TF_SERIF_I, 46)
def head(c, n, pulse, done):
    text(c, "ONE CRACK", W / 2, 196, F_KICK, AMBER, .9, spacing=7)
    text(c, "One cracked pane.", W / 2, 272, F_RULE, CREAM, .97)
    text(c, f"{N:,} balls resting on it.", W / 2, 336, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 412); c.scale(1 + .07 * pulse, 1 + .07 * pulse); c.translate(-W / 2, -412)
    text(c, f"{n:,}", W / 2, 452, F_CNT, (1, .82, .55) if n > 0 else CREAM)
    c.restore()
    text(c, "hopper empty" if done else "balls through", W / 2, 508, F_L, AMBER if done else CREAM, .95 if done else .8)

def pane_path(sag):
    w0, w1 = S.NX0 - 8, S.NX1 + 8
    p = skia.Path(); p.moveTo(w0, PY - 9); p.quadTo(PX, PY - 9 + 2 * sag, w1, PY - 9); p.lineTo(w1, PY + 9); p.quadTo(PX, PY + 9 + 2 * sag, w0, PY + 9); p.close()
    return p

first = None
def zoom(t):
    if t < TB: return 1.8 + .3 * ss(t / TB)
    return 1.0 + 1.1 * (1 - ss((t - TB - .1) / 2.2)) + .22 * ss((t - T_EMPTY + .8) / 2.5)
SPECKS = []
_r = np.random.default_rng(11)
for te in crack_t:
    for k in range(16): SPECKS.append((te + _r.uniform(0, .15), PX + _r.normal(0, 30), _r.normal(0, 40), _r.uniform(20, 120), _r.uniform(.3, .75)))
def frame(f):
    global first
    t = f / FPS
    fi = min(f, len(frames) - 1)
    P, SH, sag = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        z = zoom(t); sy = (994 + (z - 1) / 1.1 * 366) if t < T_EMPTY - .8 else 994 + (z - 1) / .22 * (-40)
        c.save(); c.clipRect(skia.Rect(0, 528, W, H))
        jl = max([x for x in crack_t if x <= t], default=-9)
        jo = 7 * math.exp(-(t - jl) / .09) * math.sin((t - jl) * 90) if 0 <= t - jl < .4 and t < TB else 0
        if 0 <= t - TB < .5: jo = 14 * math.exp(-(t - TB) / .12) * math.sin((t - TB) * 80)
        c.translate(540, sy + jo); c.scale(z, z); c.translate(-540, -994)
        c.drawImage(STATIC, 0, 0)
        # peg glints
        k0 = np.searchsorted(PH_T, t - .25); k1 = np.searchsorted(PH_T, t)
        for th, x, y in peg_hits[k0:k1][-60:]:
            blit(c, GL_P, x, y, .9, pa(.55 * (1 - (t - th) / .25)))
        fade = 1.0
        fp = skia.Paint(Alphaf=fade)
        for i in range(NBASE): blit(c, BASE[i % 8], P[N + i, 0], P[N + i, 1], paint=fp)
        for i in range(N): blit(c, SPR[BI[i]], P[i, 0], P[i, 1], SC[i], paint=fp)
        # pane
        if sag is not None:
            ns = sum(1 for x in crack_t if x <= t)
            last = max([x for x in crack_t if x <= t], default=-9)
            fl = math.exp(-(t - last) / .18) if t - last < 1 else 0
            pp = pane_path(sag * .5); pp.offset(0, sag)
            strain = ns / len(S.CRACKS)
            pc = [(1 - strain) * a_ + strain * b_ for a_, b_ in zip((.72, .88, 1), (1, .86, .62))]
            c.drawPath(pp, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*pc, .55 + .25 * fl + .15 * strain)))
            c.drawPath(pp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5, Color4f=skia.Color4f(1, 1, 1, .85)))
            strain = ns / len(S.CRACKS)
            blit(c, GL_C, PX, PY + sag, 1.0 + 1.2 * strain + .8 * fl, pa(.25 + .35 * strain + .7 * fl))
            for st, pts in CRK:
                if st >= ns: continue
                grow = min(1, (t - crack_t[st]) / .12)
                m = max(2, int(round(grow * len(pts))))
                path = skia.Path(); path.moveTo(*pts[0])
                for q in pts[1:m]: path.lineTo(q[0], q[1] + sag * 1.2 * (1 - abs(q[0] - PX) / 80))
                c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(1, 1, 1, 1)))
                c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color4f=skia.Color4f(.7, .9, 1, .35 * (.4 + fl)),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
            # ring pulse per crack
            if False:
                u = 0
                c.drawCircle(PX, PY, 20 + 140 * u, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                             Color4f=skia.Color4f(.8, .92, 1, .7 * (1 - u))))
        else:
            u = t - TB
            blit(c, GL_C, PX, PY, 5.0, pa(1.6 * math.exp(-u / .35)))
            if False:
                c.drawCircle(PX, PY, 30 + 420 * u, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                             Color4f=skia.Color4f(.85, .95, 1, .7 * (1 - u / .9))))
            for (x, y, a), poly in zip(SH, polys):
                c.save(); c.translate(x, y); c.rotate(math.degrees(a))
                p = skia.Path(); p.moveTo(*poly[0]); [p.lineTo(*q) for q in poly[1:]]; p.close()
                c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.78, .9, 1, .55 * fade)))
                c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4, Color4f=skia.Color4f(1, 1, 1, .9 * fade)))
                c.restore()
                blit(c, GL_S, x, y, 1, pa(.3 * fade))
        for (te, x0, vx, vy0, sz) in SPECKS:
            u = t - te
            if 0 <= u < 1.2:
                x = x0 + vx * u; y = PY + 10 + vy0 * u + 700 * u * u
                if y < S.TY: blit(c, GL_S, x, y, sz, pa(.9 * (1 - u / 1.2)))
        c.restore()
        n = OUTC[fi]
        pulse = math.exp(-(t - TB) / .3) if t >= TB else 0
        if t >= T_EMPTY:
            pulse = max(pulse, math.exp(-(t - T_EMPTY) / .3))
            u = (t - T_EMPTY) / 1.2
            if False:
                y = S.JY1 + 100 - 380 * u
                c.drawRect(skia.Rect(S.JX0, y - 6, S.JX1, y + 6), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .85, .55, .5 * (1 - u)),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
        head(c, n, pulse, t >= T_EMPTY)
        watermark(c, 1625)
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
    # build-up: slow heartbeat-like creak bed + rising glass strain tone
    n = int(TB * SR); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 98 * tt) + .4 * np.sin(2 * np.pi * 147 * tt)) * (.5 + .5 * tt / TB) * np.minimum(1, tt * 8)
    m.add(hum * .11, 0, 1, 540)
    sw = sosfilt(butter(2, [500, 3500], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    m.add(sw * (.25 + .75 * (tt / TB) ** 2) * .13, 0, 1, 540)
    tk = glass_click(880, 240, .05, .5); t = 0.15
    while t < TB:
        m.add(tk, t, .24 + .12 * t / TB, 540); t += 1 / (2 + 2.5 * (t / TB) ** 1.4)
    per = {}
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if kind == "crack":
            k = e[4]
            m.add(glass_click(2600 + 180 * k, 90, .2, .9), t, 1.1 + .08 * k, 540)
            nn = sosfilt(butter(2, [2000, 8000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.25 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 14), t, .55, 540)
            m.add(thud(90, .3), t, .35 + .05 * k, 540)
        elif kind == "break":
            m.add(thud(55, .9), t, 1.2, 540); m.add(mallet(392, 1.6, .9), t, .4, 540); m.add(mallet(98, 1.2, .6), t, .4, 540)
            nn = sosfilt(butter(2, [1800, 9000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.8 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 5), t, .8, 540)
        elif kind in ("peg", "ball", "wall", "shard"):
            key = (kind, fk); per[key] = per.get(key, 0) + 1
            lim = {"peg": 5, "ball": 3, "wall": 2, "shard": 2}[kind]
            if per[key] > lim: continue
            v = min(1, e[4] / 600)
            if kind == "peg":
                row = int(round((e[3] - S.PEGY0) / 55))
                m.add(glass_click(note(9 - row, 261.63), 80, .12, .2), t + rng.uniform(0, .02), .22 + .2 * v, e[2])
            elif kind == "ball":
                m.add(glass_click(1900 + rng.uniform(-300, 300), 160, .06, .3), t + rng.uniform(0, .02), .1 + .12 * v, e[2])
            elif kind == "shard":
                m.add(glass_click(3400, 120, .1, .6), t, .3, e[2])
            else:
                m.add(glass_click(1400, 200, .05, .35), t, .1, e[2])
    # pour bed: soft rushing sound shaped by the flow rate
    flow = np.diff(np.array(OUTC, float), prepend=0)
    fl = np.repeat(np.convolve(flow, np.ones(6) / 6, "same"), SR // FPS)
    nn = sosfilt(butter(2, [700, 5000], btype="band", fs=SR, output="sos"), rng.standard_normal(len(fl)))
    m.add(nn * np.clip(fl / 8, 0, 1) * .09, 0, 1, 540)
    for j, n_ in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), T_EMPTY + .05 + j * .07, .32, 380 + j * 80)
    for j, n_ in enumerate((0, 4, 7)):
        m.add(mallet(note(n_, 196), 2.2, .4), CARD + .1 + j * .06, .2, 450 + j * 90)
    return m.save(path, fade_in=.0, fade_out=.3)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[3].split(",")]
        for f in fs: frame(0) if first is None else None; frame(f).makeImageSnapshot().save(f"{OUTD}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print("rms", audio(f"{OUTD}/a.wav"))
    else:
        w = Writer(f"{OUTD}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print("rms", audio(f"{OUTD}/a.wav"))
        print("mux", mux(f"{OUTD}/silent.mp4", f"{OUTD}/a.wav", f"{OUTD}/out.mp4"))
