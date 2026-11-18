"""WRECKING BALL render: a glass tank of rainbow glass balls held by one brick wall; a brass wrecking ball
swings at it: a near miss, a kiss that knocks bricks loose, then the smash and the flood."""
import sys, math, pickle, os
import numpy as np, skia
import sim as S
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[2] if len(sys.argv) > 2 else HERE
frames, events, meta = pickle.load(open(os.path.join(HERE, "sim.pkl"), "rb"))
RAD, NB, Y0, X0 = meta["rad"], meta["nb"], meta["y0"], meta["x0"]
N = len(RAD)
CNT = list(np.maximum.accumulate([S.out_count(f[0], meta['x0'], meta['y0']) for f in frames]))
SMASH = next(e[0] for e in events if e[1] == "smash")
KISS = next(e[0] for e in events if e[1] == "kiss")
mx = max(CNT)
T_DONE = next(k for k, x in enumerate(CNT) if x >= mx - 4) / FPS + .1
CARD = T_DONE + 1.0
XF = 18
TOTAL = int((CARD + 3.0) * FPS) + XF
print("smash", SMASH, "done", T_DONE, "total s", TOTAL / FPS, "final", mx)

yy = (S.FY - Y0) / (S.FY - S.WTOP)          # 0 bottom .. 1 top
xx = (X0 - S.WX0) / (S.X1 - S.WX0)
qq = np.clip(.62 * xx + .38 * yy, 0, 1)      # gold (front, low) -> coral -> magenta -> violet (back, high)
NBK = 16
HUE = lambda q: 42 - 134 * q
SPR = [glass_ball(hsv(HUE(j / (NBK - 1)) % 360, .66, 1.0), S.RMAX) for j in range(NBK)]
BI = np.clip((qq * NBK).astype(int), 0, NBK - 1)
SC = RAD / S.RMAX
GL_F = glow((1, .85, .55), 34, .9)
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
BRS = [brick_sprite((.80 + _r.uniform(-.05, .05), .48 + _r.uniform(-.05, .05), .30 + _r.uniform(-.04, .04)), S.BW - 2, S.BH - 2) for _ in range(6)]
BT = _r.integers(0, 6, NB)

def wrecker():
    r = S.WR; sz = r * 2 + 6
    def fn(c):
        cx = cy = sz / 2
        sh = skia.GradientShader.MakeRadial((cx - r * .35, cy - r * .4), r * 1.4,
             [skia.Color4f(1, .93, .72, 1).toColor(), skia.Color4f(.78, .56, .26, 1).toColor(), skia.Color4f(.30, .19, .08, 1).toColor()], [0, .5, 1])
        c.drawCircle(cx, cy, r, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawCircle(cx + r * .3, cy + r * .32, r * .5, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .85, .6, .14),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * .2)))
        c.drawCircle(cx - r * .36, cy - r * .4, r * .2, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, .95, .85),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2)))
        c.drawCircle(cx, cy, r - 1, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, Color4f=skia.Color4f(1, .9, .7, .3)))
        # lifting eye
        c.drawCircle(cx, cy - r + 2, 9, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color4f=skia.Color4f(.62, .45, .22, 1)))
    return sprite(fn, sz)
WREK = wrecker()

BG = background(1050)
glass = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                   Color4f=skia.Color4f(.80, .87, .95, .45))
glass_hi = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                      Color4f=skia.Color4f(1, 1, 1, .55))
static = skia.Surface.MakeRaster(INFO)
with static as c:
    c.clear(skia.Color4f(0, 0, 0, 0))
    c.drawRect(skia.Rect(S.WX0 + S.BW, S.WTOP - 40, S.X1, S.FY), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.6, .75, .9, .05)))
    p = skia.Path(); p.moveTo(S.XL, 760); p.lineTo(S.XL, S.FY); p.lineTo(S.X1, S.FY); p.lineTo(S.X1, 560)
    p.moveTo(S.WX0 + S.BW, S.FY - 2); p.lineTo(S.X1, S.FY - S.SLOPE)
    c.drawPath(p, glass); c.save(); c.translate(-2, -1.5); c.drawPath(p, glass_hi); c.restore()
    # crane beam + pivot
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(S.PVX - 120, S.PVY - 14, S.PVX + 120, S.PVY + 2), 6, 6),
                skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, S.PVY - 14), (0, S.PVY + 2)],
                [skia.Color4f(.95, .78, .45, 1).toColor(), skia.Color4f(.45, .30, .12, 1).toColor()])))
    c.drawCircle(S.PVX, S.PVY, 10, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.95, .8, .5, 1)))
STATIC = static.makeImageSnapshot()
LINK_A = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2, Color4f=skia.Color4f(.86, .70, .42, 1))

def chain(c, x, y):
    dx, dy = x - S.PVX, y - S.PVY; Ln = math.hypot(dx, dy); ux, uy = dx / Ln, dy / Ln
    n = int((Ln - S.WR) / 18)
    for k in range(n):
        px, py = S.PVX + ux * (k * 18 + 9), S.PVY + uy * (k * 18 + 9)
        c.save(); c.translate(px, py); c.rotate(math.degrees(math.atan2(uy, ux)))
        if k % 2: c.drawLine(-7, 0, 7, 0, LINK_A)
        else: c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-10, -4.5, 10, 4.5), 4.5, 4.5), LINK_A)
        c.restore()

F_L = font(TF_SERIF_I, 46)
def head(c, n, pulse, done):
    text(c, "WRECKING BALL", W / 2, 192, F_KICK, AMBER, .9, spacing=7)
    text(c, "Four brick walls.", W / 2, 262, F_RULE, CREAM, .97)
    text(c, "It keeps swinging harder.", W / 2, 324, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 400); c.scale(1 + .08 * pulse, 1 + .08 * pulse); c.translate(-W / 2, -400)
    text(c, f"{n:,}", W / 2, 438, F_CNT, (1, .82, .55) if n > 0 else CREAM)
    c.restore()
    text(c, "all walls down" if done else "balls knocked loose", W / 2, 488, F_L, AMBER if done else CREAM, .95 if done else .8)

HITS = [e for e in events if e[1] in ("kiss", "smash", "smash2", "smash3", "smash4")]
first = None
def frame(f):
    global first
    t = f / FPS
    fi = min(f, len(frames) - 1)
    P, B, a, (wx, wy) = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.save(); c.clipRect(skia.Rect(0, 506, W, H))
        jo = 0
        for e in HITS:
            u = t - e[0]
            if 0 <= u < .5: jo += (4 if e[1] == "kiss" else 12) * math.exp(-u / (.08 if e[1] == "kiss" else .14)) * math.sin(u * 80)
        c.translate(jo * .6, jo)
        c.drawImage(STATIC, 0, 0)
        for i in range(N):
            blit(c, SPR[BI[i]], P[i, 0], P[i, 1], SC[i])
        for j in range(NB):
            x, y, aa = B[j]
            if y > 1700: continue
            c.save(); c.translate(x, y); c.rotate(math.degrees(aa)); blit(c, BRS[BT[j]], 0, 0); c.restore()
        for e in HITS:
            u = t - e[0]
            if 0 <= u < .7 and (e[1] != "kiss" or e is HITS[0]):
                blit(c, GL_F, {"smash": S.WX0, "smash2": S.WX2, "smash3": S.WX3, "smash4": S.WX4}.get(e[1], S.WX0), e[3], 1.2 if e[1] == "kiss" else 3.2, pa((.8 if e[1] == "kiss" else 1.0) * math.exp(-u / (.15 if e[1] == "kiss" else .3))))
        # near-miss glint: wall face lights when the ball passes close
        gap = S.WX0 - (wx + S.WR)
        if 0 < gap < 60 and t < SMASH - .2: blit(c, GL_F, S.WX0 - 4, wy, .8, pa(.5 * (1 - gap / 60)))
        chain(c, wx, wy)
        blit(c, WREK, wx, wy)
        c.restore()
        n = CNT[fi]
        pulse = max([math.exp(-(t - e[0]) / .3) for e in HITS if e[1] != "kiss" and t >= e[0]], default=0)
        done = t >= T_DONE
        if done: pulse = max(pulse, math.exp(-(t - T_DONE) / .3))
        head(c, n, pulse, done)
        watermark(c, 1636)
        if t >= CARD:
            al = ss((t - CARD) / .45)
            if f >= TOTAL - XF: al *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, al)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

def audio(path):
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(9)
    m = Mix(TOTAL / FPS)
    Tn = TOTAL / FPS
    # swing whoosh: band noise shaped by the wrecking ball's speed, panned with it
    n = int(Tn * SR); tt = np.arange(n) / SR
    xs = np.array([S.wpos(t)[0] for t in tt[::480]]); ys = np.array([S.wpos(t)[1] for t in tt[::480]])
    sp = np.hypot(np.gradient(xs), np.gradient(ys)) * 100
    spd = np.interp(tt, tt[::480], sp)
    wh = sosfilt(butter(2, [250, 1400], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    env = np.clip(spd / 700, 0, 1) ** 1.5 * np.where(tt < CARD, 1, np.exp(-(tt - CARD) * 3))
    m.add(wh * env * .16 * np.where(tt < SMASH, 3.6, 1), 0, 1, 540)
    # chain creak at each turn-around + a soft tick
    for (tp, ap) in S.PEAKS[1:]:
        if tp > CARD: break
        cr = sosfilt(butter(2, [300, 900], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.35 * SR)))
        m.add(cr * np.hanning(len(cr)) * (.10 + .004 * abs(ap)), tp - .15, 1, 540 + ap * 8)
        m.add(glass_click(660 + ap * 6, 200, .08, .4), tp, .16, 540 + ap * 8)
    # tension hum + strain swell until the first smash
    TS = SMASH; n2 = int((TS + .2) * SR); t2 = np.arange(n2) / SR
    hum = (np.sin(2 * np.pi * 98 * t2) + .4 * np.sin(2 * np.pi * 147 * t2)) * (.5 + .5 * t2 / TS) * np.minimum(1, t2 * 8)
    m.add(hum * .34, 0, 1, 540)
    tk = glass_click(880, 240, .05, .5); t_ = 0.05
    while t_ < TS:
        m.add(tk, t_, .45 + .15 * t_ / TS, 540); t_ += 1 / (2.2 + 3 * (t_ / TS) ** 1.4)
    sw = sosfilt(butter(2, [500, 3500], btype="band", fs=SR, output="sos"), rng.standard_normal(n2))
    m.add(sw * (.4 + .6 * np.clip(t2 / TS, 0, 1) ** 2) * .12, 0, 1, 540)
    # near miss: a bright pass-by glint
    m.add(glass_click(1760, 90, .25, .3), .33, .35, 450); m.add(glass_click(2200, 120, .2, .2), .37, .2, 450)
    per = {}; seen = set()
    stage = {"smash": 0, "smash2": 1, "smash3": 2, "smash4": 3}
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if kind == "kiss":
            if "kiss" in seen: continue
            seen.add("kiss")
            m.add(thud(85, .45), t, .8, e[2]); m.add(glass_click(900, 60, .2, .7), t, .5, e[2])
            nn = sosfilt(butter(2, [300, 2500], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.4 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 10), t, .35, e[2])
        elif kind in stage:
            k = stage[kind]
            m.add(thud(52 - 4 * k, 1.1), t, 1.25 + .1 * k, 540); m.add(mallet(note(5 + 2 * k, 196), 1.8, .8), t, .45, 540)
            m.add(mallet(98, 1.3, .5), t, .35, 540)
            nn = sosfilt(butter(2, [200, 3000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(1.1 * SR)))
            m.add(nn * np.exp(-np.arange(len(nn)) / SR * 4), t, .5, e[2])
        elif kind == "fall":
            continue
        else:
            key = (kind, fk); per[key] = per.get(key, 0) + 1
            lim = {"ballbrick": 2, "ball": 2, "wall": 1, "brick": 2, "brick2": 1, "wb": 1, "wbbrick": 1}[kind]
            if per[key] > lim: continue
            v = min(1, e[4] / 600)
            if kind == "ball":
                h = int(np.clip((1600 - e[3]) / 90, 0, 9))
                m.add(glass_click(note(h + 5, 261.63) * 2, 150, .07, .3), t + rng.uniform(0, .02), .1 + .12 * v, e[2])
            elif kind == "ballbrick":
                m.add(glass_click(1500 + rng.uniform(-200, 200), 120, .08, .35), t + rng.uniform(0, .02), .12 + .14 * v, e[2])
            elif kind in ("brick", "brick2", "wbbrick"):
                m.add(thud(110 + rng.uniform(-15, 15), .2), t, .25 + .3 * v, e[2])
                m.add(glass_click(700 + rng.uniform(-80, 80), 90, .1, .7), t, .15 + .15 * v, e[2])
            elif kind == "wb":
                m.add(glass_click(1100 + rng.uniform(-100, 100), 80, .1, .5), t, .14 + .12 * v, e[2])
            else:
                m.add(glass_click(1400, 200, .05, .35), t, .08, e[2])
    flow = np.clip(np.diff(np.array(CNT, float), prepend=0), 0, None)
    fl = np.repeat(np.convolve(flow, np.ones(6) / 6, "same"), SR // FPS)
    nn = sosfilt(butter(2, [700, 5000], btype="band", fs=SR, output="sos"), rng.standard_normal(len(fl)))
    m.add(nn[:m.N] * np.clip(fl / 8, 0, 1)[:m.N] * .2, 0, 1, 540)
    for k, fv in enumerate(flow):
        t = k / FPS
        if t > CARD: break
        for q in range(int(min(3, fv / 3))):
            m.add(glass_click(note(int(rng.integers(3, 12)), 261.63) * 2, 140, .06, .35), t + rng.uniform(0, 1 / FPS), .12, rng.uniform(250, 950))
    for j, n_ in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), T_DONE + .05 + j * .07, .32, 380 + j * 80)
    for j, n_ in enumerate((0, 4, 7)):
        m.add(mallet(note(n_, 196), 2.2, .4), CARD + .1 + j * .06, .2, 450 + j * 90)
    n3 = int((Tn - CARD) * SR); t3 = np.arange(n3) / SR
    pad = sum(np.sin(2 * np.pi * note(k, 130.81) * t3) for k in (0, 2, 4, 7)) * np.minimum(1, t3 / .6) * np.exp(-t3 / 2.5)
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
