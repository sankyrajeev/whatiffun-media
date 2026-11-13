"""BREAK OUT render: look, sound, header, end card (based on No. 23 one-gap/render.py)."""
import sys, math, pickle, os
import numpy as np, skia
import sim as S
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[2] if len(sys.argv) > 2 else HERE
frames, events, broken, T_OUT, PARAMS, SRC = pickle.load(open(os.path.join(HERE, "sim.pkl"), "rb"))
GA = PARAMS[2]
CX, CY, RC = S.CX, S.CY, S.RC
T_CLEAR = broken[-1][0]
CARD = T_CLEAR + 1.7
XF = 18
TOTAL = int((CARD + 2.4) * FPS) + XF
print("out", round(T_OUT, 2), "clear", round(T_CLEAR, 2), "total s", round(TOTAL / FPS, 2))
HALF = S.GAPW / 2 / RC
POSTS = [(CX + RC * math.cos(GA + s * HALF), CY + RC * math.sin(GA + s * HALF)) for s in (-1, 1)]
GX, GY = CX + RC * math.cos(GA), CY + RC * math.sin(GA)

# --- near misses: rim hits close to the gap + post touches (deduped), before the escape
near = []
for e in events:
    if e[0] >= T_OUT: break
    if e[1] == "post" or (e[1] == "cage" and abs(e[4]) < 72):
        if not near or e[0] - near[-1][0] > .15: near.append((e[0], e[2], e[3], abs(e[4]), e[1]))
cage_hits = [(e[0], e[2], e[3]) for e in events if e[1] == "cage" and e[0] < T_OUT]
print("near misses", [(round(a, 1), round(d), k) for a, _, _, d, k in near])

def sector_path(k, sct, inset=1.3):
    n = S.NSEC[k]; r0 = S.RB0 + k * S.BT + inset; r1 = S.RB0 + (k + 1) * S.BT - inset
    a0 = sct / n * 360; a1 = (sct + 1) / n * 360
    da = math.degrees(inset / ((r0 + r1) / 2))
    p = skia.Path()
    p.arcTo(skia.Rect(CX - r1, CY - r1, CX + r1, CY + r1), a0 + da, a1 - a0 - 2 * da, True)
    p.arcTo(skia.Rect(CX - r0, CY - r0, CX + r0, CY + r0), a1 - da, -(a1 - a0 - 2 * da), False)
    p.close(); return p
def brick_col(k, sct):
    a = (sct + .5) / S.NSEC[k] * 360
    return hsv(a + 200 + 6 * k, .74 - .02 * k, .97)       # rainbow wheel by angle, slight twist per ring

BG = background(CY)
board = skia.Surface.MakeRaster(INFO)
with board as c:
    c.drawImage(BG, 0, 0)
    # outer steel wall + dark well
    c.drawCircle(CX, CY, S.RO + 6, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35)))
    c.drawCircle(CX, CY, S.RO + 4, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7,
                 Shader=skia.GradientShader.MakeSweep(CX, CY, [skia.Color(120, 112, 104), skia.Color(60, 56, 52), skia.Color(150, 140, 128), skia.Color(60, 56, 52), skia.Color(120, 112, 104)])))
    c.drawCircle(CX, CY, S.RO + 9, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5, Color4f=skia.Color4f(*AMBER, .45)))
    for k in range(S.NRING):
        for sct in range(S.NSEC[k]):
            col = brick_col(k, sct)
            light = tuple(min(1, x * .5 + .55) for x in col); dark = tuple(x * .5 for x in col)
            r0 = S.RB0 + k * S.BT; r1 = r0 + S.BT
            sh = skia.GradientShader.MakeRadial((CX, CY), r1, [skia.Color4f(*dark, 1).toColor(), skia.Color4f(*col, 1).toColor(), skia.Color4f(*light, 1).toColor()],
                                                [r0 / r1, (r0 + .55 * S.BT) / r1, 1])
            c.drawPath(sector_path(k, sct), skia.Paint(AntiAlias=True, Shader=sh))
BOARD0 = board.makeImageSnapshot()

def draw_cage(c, t):
    sealed = t >= T_OUT
    pg = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9, StrokeCap=skia.Paint.kRound_Cap,
                    Color4f=skia.Color4f(.80, .86, .92, .55))
    hi = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=skia.Color4f(1, 1, 1, .55))
    rr = RC + 4.5
    rect = skia.Rect(CX - rr, CY - rr, CX + rr, CY + rr)
    g0 = math.degrees(GA + HALF); sweep = 360 - math.degrees(2 * HALF)
    if sealed:
        c.drawCircle(CX, CY, rr, pg); c.drawCircle(CX, CY, rr - 2.5, hi)
    else:
        p = skia.Path(); p.addArc(rect, g0, sweep); c.drawPath(p, pg)
        r2 = rr - 2.5; p = skia.Path(); p.addArc(skia.Rect(CX - r2, CY - r2, CX + r2, CY + r2), g0, sweep); c.drawPath(p, hi)
    c.drawCircle(CX, CY, rr - 6, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.6, .75, .9, .05)))

BALL = glass_ball((1, .97, .92), 5)
NB = 24
BALLS = [glass_ball(hsv(h * 360 / NB + 200, .42, 1), 5) for h in range(NB)]
def ball_spr(i):
    if i == 0 or SRC[i] is None: return BALL
    k, sct = SRC[i]; return BALLS[int((sct + .5) / S.NSEC[k] * NB) % NB]
GL_B = glow((1, .9, .7), 7, .6)
HERO = glass_ball((1, .96, .88), S.RH)
GL_HERO = glow((1, .82, .5), 22, .75)
GL_GAP = glow((1, .7, .28), 16, .95)
GL_HIT = glow((1, .85, .6), 10, .9)
GL_POST = glow((1, .75, .35), 8, 1)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)

F_L = font(TF_SERIF_I, 34)
def head(c, balls, pulse, done):
    text(c, "BREAK OUT", W / 2, 196, F_KICK, AMBER, .9, spacing=7)
    text(c, "One way out.", W / 2, 272, F_RULE, CREAM, .97)
    text(c, "Every brick adds a ball.", W / 2, 336, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 412); c.scale(1 + .07 * pulse, 1 + .07 * pulse); c.translate(-W / 2, -412)
    text(c, f"{balls:,}", W / 2, 452, F_CNT, (1, .82, .55) if balls > 1 else CREAM)
    c.restore()
    if done: text(c, "ring cleared", W / 2, 500, F_L, AMBER, .9)
    else: text(c, "ball" if balls == 1 else "balls", W / 2, 500, F_L, CREAM, .55)

state = {"surf": None, "k": 0}
first = None; trail = []
BT_ = np.array([b[0] for b in broken])
def frame(f):
    global first
    t = f / FPS
    if state["surf"] is None:
        s = skia.Surface.MakeRaster(INFO)
        with s as c: c.drawImage(BOARD0, 0, 0)
        state["surf"] = s
    with state["surf"] as c:      # erase broken bricks up to now (permanent)
        while state["k"] < len(broken) and broken[state["k"]][0] <= t:
            _, k, sct = broken[state["k"]]
            c.save(); c.clipPath(sector_path(k, sct, -.6), doAntiAlias=True); c.drawImage(BG, 0, 0); c.restore(); state["k"] += 1
    fi = min(f, len(frames) - 1)
    P, nbr, rh = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(state["surf"].makeImageSnapshot(), 0, 0)
        draw_cage(c, t)
        # rim marks: every hit leaves an amber tick on the glass that fades (shows the creep toward the gap)
        for th, x, y in cage_hits:
            if 0 <= t - th < 2.6:
                a = math.atan2(y - CY, x - CX); u = (t - th) / 2.6
                mx, my = CX + (RC + 4.5) * math.cos(a), CY + (RC + 4.5) * math.sin(a)
                blit(c, GL_HIT, mx, my, .55, pa(.7 * (1 - u) ** 2))
        # the gap: two glowing posts + a breathing glow, until it seals
        if t < T_OUT:
            close = 0.0
            for th, x, y, d, kind in near:
                if 0 <= t - th < .7: close = max(close, math.exp(-(t - th) / .22) * (1.6 if kind == "post" else 1.0))
            blit(c, GL_GAP, GX, GY, 1.3 + .6 * close, pa(.6 + .2 * math.sin(t * 5) + .5 * close))
            for px, py in POSTS:
                c.drawCircle(px, py, 8.5, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .8, .45, 1)))
                blit(c, GL_POST, px, py, 1.3 + .9 * close, pa(.8 + .2 * close))
            for th, x, y, d, kind in near:   # close-call flash at the contact point
                if 0 <= t - th < .5:
                    a = math.atan2(y - CY, x - CX)
                    hx, hy = (x, y) if kind == "post" else (CX + RC * math.cos(a), CY + RC * math.sin(a))
                    blit(c, GL_HIT, hx, hy, 2.2, pa(math.exp(-(t - th) / .14)))
                    rr_ = 16 + 60 * (t - th)
                    c.drawCircle(hx, hy, rr_, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5,
                                 Color4f=skia.Color4f(1, .8, .5, .8 * max(0, 1 - (t - th) / .5))))
        else:
            u = t - T_OUT
            blit(c, GL_GAP, GX, GY, 2.4, pa(1.4 * math.exp(-u / .35)))
            c.drawCircle(GX, GY, 20 + 260 * u, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                         Color4f=skia.Color4f(1, .82, .5, .7 * max(0, 1 - u / .8))))
        # shards from fresh breaks
        k0 = np.searchsorted(BT_, t - .35)
        for bt, k, sct in broken[k0:state["k"]]:
            u = (t - bt) / .35
            col = brick_col(k, sct)
            a = (sct + .5) / S.NSEC[k] * 2 * math.pi; rm = S.RB0 + (k + .5) * S.BT
            bx, by = CX + rm * math.cos(a), CY + rm * math.sin(a)
            s_ = 7 + 16 * u
            c.drawCircle(bx, by, s_, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=skia.Color4f(*col, .85 * (1 - u))))
            blit(c, GL_HIT, bx, by, 1.0, pa(.5 * (1 - u)))
        fade = 1.0 if t < CARD else max(0, 1 - (t - CARD) / .5)
        if len(P) == 1 or rh > S.RS + .5:
            x, y = P[0]
            trail.append((x, y)); del trail[:-8]
            for q_, pt in enumerate(trail[:-1]): blit(c, GL_B, pt[0], pt[1], 1.4 * rh / S.RH + .4, pa(.1 * (q_ + 1)))
            sc = rh / S.RH
            blit(c, GL_HERO, x, y, sc, pa(.6)); blit(c, HERO, x, y, sc)
            i0 = 1
        else: i0 = 0
        fp = skia.Paint(Alphaf=fade)
        for i in range(i0, len(P)): blit(c, ball_spr(i), P[i, 0], P[i, 1], paint=fp)
        lit = len(P)
        pulse = math.exp(-(t - T_OUT) / .3) if t >= T_OUT else 0
        if t >= T_CLEAR: pulse = max(pulse, math.exp(-(t - T_CLEAR) / .3))
        if t >= T_CLEAR:   # cleared: a soft light ring glides out over the empty well
            u = (t - T_CLEAR) / 1.2
            if u < 1: c.drawCircle(CX, CY, RC + 20 + (S.RO - RC) * u, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                                    Color4f=skia.Color4f(1, .85, .55, .6 * (1 - u)), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        head(c, lit, pulse, t >= T_CLEAR)
        watermark(c, 1600)
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
    # build-up bed: a soft wooden clock tick that speeds up toward the escape (2 Hz -> 4 Hz) + a low glassy hum
    tk = glass_click(900, 260, .05, .5); t = 0.0
    while t < T_OUT:
        m.add(tk, t, .16 + .1 * t / T_OUT, 540); t += 1 / (2 + 2 * (t / T_OUT) ** 1.5)
    n = int(T_OUT * SR); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 110 * tt) + .4 * np.sin(2 * np.pi * 165 * tt)) * (.5 + .5 * tt / T_OUT) * np.minimum(1, tt * 2)
    m.add(hum * .05, 0, 1, 540)
    sw = sosfilt(butter(2, [400, 3000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(2.5 * SR)))
    m.add(sw * np.linspace(0, 1, len(sw)) ** 2 * .12, T_OUT - 2.5, 1, 540)          # tension swell into the escape
    per = {}
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if t < T_OUT:
            if kind == "cage":
                d = abs(e[4]); close = d < 72
                m.add(glass_click(2300 if close else 1560, 150, .08, .35), t, 1.25 if close else .75, e[2])
                m.add(thud(150, .18), t, .25, e[2])
                if close:
                    nn = sosfilt(butter(2, [2500, 7000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.3 * SR)))
                    m.add(nn * np.exp(-np.arange(len(nn)) / SR * 9), t, .5, e[2])
            elif kind == "post":
                if per.get("post", -1) < t - .15:
                    m.add(mallet(1318, .9, 1.2), t, .55, e[2]); per["post"] = t
        else:
            if kind == "wall":
                per[fk] = per.get(fk, 0) + 1
                if per[fk] <= 3: m.add(glass_click(1700, 190, .05, .35), t, .12, e[2])
            elif kind == "pop":
                key = ("p", fk); per[key] = per.get(key, 0) + 1
                if per[key] <= 5:
                    ring = e[4]
                    m.add(glass_click(note(4 + ring, 261.63), 70, .14, .2), t + rng.uniform(0, .02), .3, e[2])
    m.add(thud(58, .8), T_OUT, 1.1, GX); m.add(mallet(392, 1.6, .8), T_OUT, .45, GX); m.add(mallet(98, 1.2, .6), T_OUT + .02, .4, GX)
    for j, n_ in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), T_CLEAR + .05 + j * .07, .3, 380 + j * 80)
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
