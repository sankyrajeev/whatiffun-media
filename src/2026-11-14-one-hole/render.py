"""ONE HOLE / FILL IT render: look, sound, header, end card (based on No. 26 break-out/render.py)."""
import sys, math, pickle, os
import numpy as np, skia
import sim as S
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[2] if len(sys.argv) > 2 else HERE
frames, events, settle, T_IN, PARAMS = pickle.load(open(os.path.join(HERE, "sim.pkl"), "rb"))
HX = PARAMS[2]
T_FULL = settle[-1][0]
CARD = T_FULL + 1.7
XF = 18
TOTAL = int((CARD + 2.4) * FPS) + XF
print("in", round(T_IN, 2), "full", round(T_FULL, 2), "total s", round(TOTAL / FPS, 2))
XL, XR, YTOP, YLID, YLB, YFL = S.XL, S.XR, S.YTOP, S.YLID, S.YLB, S.YFL
POSTS = [(HX - S.HW, YLID), (HX + S.HW, YLID)]

near = []
for e in events:
    if e[0] >= T_IN: break
    if e[1] == "rim" or (e[1] == "lid" and abs(e[4]) < 85):
        if not near or e[0] - near[-1][0] > .15: near.append((e[0], e[2], e[3], abs(e[4]), e[1]))
lid_hits = [(e[0], e[2]) for e in events if e[1] == "lid" and e[0] < T_IN]
print("near misses", [(round(a, 1), round(d), k) for a, _, _, d, k in near])

def row_col(r):
    return hsv(272 + r * 128 / max(1, S.NROW - 1), .62, 1)   # violet at the bottom -> pink -> coral -> amber at the top
NB = 18
GENC = [glass_ball(hsv(268 - g * 12, .5, 1), S.RS) for g in range(NB)]
ROWC = [glass_ball(row_col(r), S.RS) for r in range(S.NROW)]
HERO = glass_ball((1, .96, .88), S.RH)
GL_HERO = glow((1, .82, .5), 26, .75)
GL_B = glow((1, .9, .7), 8, .6)
GL_GAP = glow((1, .7, .28), 18, .95)
GL_HIT = glow((1, .85, .6), 10, .9)
GL_POST = glow((1, .75, .35), 8, 1)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)

BG = background(1050)
JAR = skia.RRect.MakeRectXY(skia.Rect(XL - 6, YTOP - 6, XR + 6, YFL + 6), 30, 30)
base = skia.Surface.MakeRaster(INFO)
with base as c:
    c.drawImage(BG, 0, 0)
    c.drawRRect(JAR, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .28)))
    c.drawRRect(JAR, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(XL, 0), (XR, 0)], [skia.Color4f(.7, .8, .9, .07).toColor(), skia.Color4f(.7, .8, .9, .0).toColor(), skia.Color4f(.7, .8, .9, .05).toColor()], [0, .5, 1])))
    # floor shadow line
    c.drawLine(XL + 20, YFL + 1, XR - 20, YFL + 1, skia.Paint(AntiAlias=True, StrokeWidth=2, Color4f=skia.Color4f(1, .9, .7, .08)))
BASE = base.makeImageSnapshot()

def draw_jar_glass(c):
    c.drawRRect(JAR, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9, Color4f=skia.Color4f(.80, .86, .92, .42)))
    c.drawRRect(JAR.makeOffset(0, 0), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, Color4f=skia.Color4f(1, 1, 1, .45)))
    # vertical glints
    for x0, a in ((XL + 16, .16), (XL + 30, .07), (XR - 22, .08)):
        c.drawRect(skia.Rect(x0, YTOP + 40, x0 + 5, YFL - 60), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, a),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))

BRASS = skia.GradientShader.MakeLinear([(0, YLID), (0, YLB)], [skia.Color(250, 214, 140), skia.Color(196, 146, 70), skia.Color(110, 74, 34)], [0, .45, 1])
def draw_plate(c, t):
    p = skia.Paint(AntiAlias=True, Shader=BRASS)
    if t < T_IN:
        c.drawRect(skia.Rect(XL, YLID, HX - S.HW, YLB), p)
        c.drawRect(skia.Rect(HX + S.HW, YLID, XR, YLB), p)
    else:
        c.drawRect(skia.Rect(XL, YLID, XR, YLB), p)
        u = t - T_IN
        if u < 1.2:   # the seal: a molten seam that cools
            c.drawRect(skia.Rect(HX - S.HW, YLID, HX + S.HW, YLB), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .8, .45, max(0, 1 - u / 1.2))))
    c.drawLine(XL, YLID + .5, XR, YLID + .5, skia.Paint(AntiAlias=True, StrokeWidth=1.5, Color4f=skia.Color4f(1, .95, .8, .6)))

F_L = font(TF_SERIF_I, 34)
def head(c, balls, pulse, done):
    text(c, "FILL IT", W / 2, 196, F_KICK, AMBER, .9, spacing=7)
    text(c, "One hole in the lid.", W / 2, 272, F_RULE, CREAM, .97)
    text(c, "Every bounce adds a ball.", W / 2, 336, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 412); c.scale(1 + .07 * pulse, 1 + .07 * pulse); c.translate(-W / 2, -412)
    text(c, f"{balls:,}", W / 2, 452, F_CNT, (1, .82, .55) if balls > 1 else CREAM)
    c.restore()
    if done: text(c, "jar full", W / 2, 500, F_L, AMBER, .9)
    else: text(c, "ball" if balls == 1 else "balls", W / 2, 500, F_L, CREAM, .55)

ST_T = np.array([s[0] for s in settle])
state = {"surf": None, "k": 0}
first = None; trail = []
SETTLE_D = .12
def frame(f):
    global first
    t = f / FPS
    if state["surf"] is None:
        s = skia.Surface.MakeRaster(INFO)
        with s as c: c.drawImage(BASE, 0, 0)
        state["surf"] = s
    with state["surf"] as c:      # stamp settled balls (permanent)
        while state["k"] < len(settle) and settle[state["k"]][0] + SETTLE_D <= t:
            _, sl, k, x, y = settle[state["k"]]
            r_, sx, sy = S.SL[sl]
            blit(c, ROWC[int(r_)], sx, sy); state["k"] += 1
    fi = min(f, len(frames) - 1)
    hero, P, act, rh = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(state["surf"].makeImageSnapshot(), 0, 0)
        # balls settling right now (glide into their slot)
        k0 = np.searchsorted(ST_T, t - SETTLE_D)
        settling = set()
        for st, sl, k, x, y in settle[k0:]:
            if st > t: break
            u = ss((t - st) / SETTLE_D); r_, sx, sy = S.SL[sl]
            blit(c, ROWC[int(r_)], x + (sx - x) * u, y + (sy - y) * u); settling.add(k)
            if u > .7: blit(c, GL_HIT, sx, sy, .8, pa(.35 * (1 - u) * 3))
        draw_plate(c, t)
        # landing marks on the plate (show the creep toward the hole)
        for th, x in lid_hits:
            if 0 <= t - th < 2.8:
                u = (t - th) / 2.8
                blit(c, GL_HIT, x, YLID, .6, pa(.7 * (1 - u) ** 2))
                c.drawLine(x - 9, YLID + 1, x + 9, YLID + 1, skia.Paint(AntiAlias=True, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap,
                           Color4f=skia.Color4f(1, .85, .55, .8 * (1 - u))))
        if t < T_IN:
            close = 0.0
            for th, x, y, d, kind in near:
                if 0 <= t - th < .7: close = max(close, math.exp(-(t - th) / .22) * (1.6 if kind == "rim" else 1.0))
            # the hole: a dark opening with a breathing amber glow
            c.drawRect(skia.Rect(HX - S.HW, YLID, HX + S.HW, YLB), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.02, .015, .01, 1)))
            # a faint amber beam falls from the hole into the empty jar (the way in)
            bm = skia.Path(); bm.moveTo(HX - S.HW + 4, YLB); bm.lineTo(HX + S.HW - 4, YLB); bm.lineTo(HX + 120, YFL - 40); bm.lineTo(HX - 120, YFL - 40); bm.close()
            c.drawPath(bm, skia.Paint(AntiAlias=True, BlendMode=ADD, Shader=skia.GradientShader.MakeLinear([(0, YLB), (0, YFL - 40)],
                       [skia.Color4f(1, .7, .3, .16 + .05 * math.sin(t * 5) + .12 * close).toColor(), skia.Color4f(1, .7, .3, 0).toColor()]),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
            blit(c, GL_GAP, HX, YLID + 9, 2.0 + .6 * close, pa(.8 + .2 * math.sin(t * 5) + .5 * close))
            for px, py in POSTS:
                c.drawCircle(px, py + 2, 6.5, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .82, .48, 1)))
                blit(c, GL_POST, px, py + 2, 1.3 + .9 * close, pa(.8 + .2 * close))
            for th, x, y, d, kind in near:
                if 0 <= t - th < .5:
                    hx_, hy_ = (x, y) if kind == "rim" else (x, YLID)
                    blit(c, GL_HIT, hx_, hy_, 2.2, pa(math.exp(-(t - th) / .14)))
                    c.drawCircle(hx_, hy_, 18 + 70 * (t - th), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5,
                                 Color4f=skia.Color4f(1, .8, .5, .8 * max(0, 1 - (t - th) / .5))))
        else:
            u = t - T_IN
            blit(c, GL_GAP, HX, YLID + 9, 2.6, pa(1.4 * math.exp(-u / .35)))
            c.drawCircle(HX, YLID + 9, 20 + 300 * u, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                         Color4f=skia.Color4f(1, .82, .5, .7 * max(0, 1 - u / .8))))
        fade = 1.0 if t < CARD else max(0, 1 - (t - CARD) / .5)
        # hero
        if hero is not None or (P is not None and rh > S.RS + .5 and act[0]):
            x, y = hero if hero is not None else P[0]
            sc = 1.0 if hero is not None else rh / S.RH
            trail.append((x, y)); del trail[:-8]
            for q_, pt in enumerate(trail[:-1]): blit(c, GL_B, pt[0], pt[1], 2.0 * sc + .3, pa(.09 * (q_ + 1)))
            blit(c, GL_HERO, x, y, sc, pa(.6)); blit(c, HERO, x, y, sc)
            i0 = 1
        else: i0 = 0
        count = 1
        if P is not None:
            count = len(P)
            fp = skia.Paint(Alphaf=fade)
            idx = np.where(act)[0]
            for i in idx:
                if i < i0: continue
                rr_ = int(min(S.NROW - 1, max(0, (YFL - P[i, 1]) / 19.5)))
                blit(c, ROWC[rr_], P[i, 0], P[i, 1], paint=fp)
        draw_jar_glass(c)
        pulse = math.exp(-(t - T_IN) / .3) if t >= T_IN else 0
        if t >= T_FULL:
            pulse = max(pulse, math.exp(-(t - T_FULL) / .3))
            u = (t - T_FULL) / 1.3     # full: a soft light sweep rises through the packed jar
            if u < 1:
                yy = YFL - (YFL - YLB) * u
                c.drawRect(skia.Rect(XL, yy - 30, XR, yy + 30), skia.Paint(AntiAlias=True, BlendMode=ADD, Color4f=skia.Color4f(1, .85, .55, .32 * (1 - u)),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
        head(c, count, pulse, t >= T_FULL)
        watermark(c, 1626)
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
    tk = glass_click(900, 260, .05, .5); t = 0.0
    while t < T_IN:          # soft clock tick speeding 2 -> 4 Hz into the drop
        m.add(tk, t, .2 + .12 * t / T_IN, 540); t += 1 / (2 + 2 * (t / T_IN) ** 1.5)
    n = int(T_IN * SR); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 110 * tt) + .4 * np.sin(2 * np.pi * 165 * tt)) * (.5 + .5 * tt / T_IN) * np.minimum(1, tt * 2)
    m.add(hum * .06, 0, 1, 540)
    sw = sosfilt(butter(2, [400, 3000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(2.5 * SR)))
    m.add(sw * np.linspace(0, 1, len(sw)) ** 2 * .13, T_IN - 2.5, 1, 540)
    per = {}; last_r = -1
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if t < T_IN:
            if kind == "lid":
                d = abs(e[4]); close = d < 85
                m.add(mallet(196 if not close else 262, .5, .6), t, .55 if close else .35, e[2])     # brass plate tonk
                m.add(thud(120, .2), t, .45, e[2])
                m.add(glass_click(2300 if close else 1500, 150, .08, .35), t, 1.1 if close else .55, e[2])
                if close:
                    nn = sosfilt(butter(2, [2500, 7000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.3 * SR)))
                    m.add(nn * np.exp(-np.arange(len(nn)) / SR * 9), t, .5, e[2])
            elif kind == "rim" and t - last_r > .12:
                m.add(mallet(1318, .9, 1.2), t, .6, e[2]); m.add(glass_click(3000, 120, .1, .3), t, .6, e[2]); last_r = t
            elif kind == "side":
                m.add(glass_click(1700, 190, .05, .35), t, .3, e[2])
        else:
            if kind == "bounce":
                key = ("b", fk); per[key] = per.get(key, 0) + 1
                if per[key] <= 5:
                    row = int((YFL - e[3]) / 19.5)
                    m.add(glass_click(note(3 + row // 2, 261.63), 70, .14, .2), t + rng.uniform(0, .02), .3 + .45 * max(0, 1 - (t - T_IN) / 4.5), e[2])
                    if t < T_IN + 4: m.add(thud(140, .15), t, .25, e[2])
            elif kind == "settle":
                key = ("s", fk); per[key] = per.get(key, 0) + 1
                if per[key] <= 3: m.add(glass_click(note(8 + e[4] // 3, 261.63), 160, .06, .4), t + .1, .12, e[2])
    # a soft glassy pad that swells as the jar fills
    n = int((T_FULL - T_IN + 1.5) * SR); tt = np.arange(n) / SR
    env = np.minimum(1, tt / (T_FULL - T_IN)) ** 1.2 * np.minimum(1, (n / SR - tt) / 1.5)
    pad = sum(np.sin(2 * np.pi * note(k_, 130.81) * tt + k_) for k_ in (0, 2, 4)) / 3
    m.add(pad * (.05 + .06 * env), T_IN, 1, 540)
    m.add(thud(58, .8), T_IN, 1.1, HX); m.add(mallet(392, 1.6, .8), T_IN, .45, HX); m.add(mallet(98, 1.2, .6), T_IN + .02, .4, HX)
    for j, n_ in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), T_FULL + .05 + j * .07, .3, 380 + j * 80)
    for j, n_ in enumerate((0, 4, 7)):
        m.add(mallet(note(n_, 196), 2.2, .4), CARD + .1 + j * .06, .2, 450 + j * 90)
    return m.save(path, fade_in=.0, fade_out=.3)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[3].split(",")]
        for f in range(max(fs) + 1):
            s = frame(f)
            if f in fs: s.makeImageSnapshot().save(f"{OUTD}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print("rms", audio(f"{OUTD}/a.wav"))
    else:
        w = Writer(f"{OUTD}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print("rms", audio(f"{OUTD}/a.wav"))
        print("mux", mux(f"{OUTD}/silent.mp4", f"{OUTD}/a.wav", f"{OUTD}/out.mp4"))
