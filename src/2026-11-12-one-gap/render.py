import sys, math, pickle
import numpy as np, skia
sys.argv_save = sys.argv[:]; sys.argv = ["x", "none"]
import gap as G
sys.argv = sys.argv_save
from kit import *

frames, events, broken = pickle.load(open("/home/claude/gap/sim.pkl", "rb"))
TOT = int((G.make_grid(G.GAP) == G.PINK).sum())
T_IN = broken[0][0]
T_CLEAR = broken[-1][0]
T_SEAL = next(e[0] for e in events if e[1] == "seal")
CARD = T_CLEAR + 1.7
XF = 18
TOTAL = int((CARD + 2.5) * FPS) + XF
print("in", round(T_IN, 2), "seal", round(T_SEAL, 2), "clear", round(T_CLEAR, 2), "total s", round(TOTAL / FPS, 2))
C = G.CELL; AX0, AY0 = G.AX0, G.AY0

def cell_rect(i, j, inset=1.6): return skia.Rect(AX0 + i * C + inset, AY0 + j * C + inset, AX0 + (i + 1) * C - inset, AY0 + (j + 1) * C - inset)
def block_col(i, j):
    u = j / (G.NR - 1); v = i / (G.NC - 1)
    return hsv(318 + 62 * u + 10 * (v - .5), .78 - .1 * u, .98)
def draw_block(c, i, j, col, a=1.0):
    r = cell_rect(i, j)
    light = tuple(min(1, x * .5 + .55) for x in col); dark = tuple(x * .55 for x in col)
    sh = skia.GradientShader.MakeLinear([(r.left(), r.top()), (r.right(), r.bottom())],
        [skia.Color4f(*light, a).toColor(), skia.Color4f(*col, a).toColor(), skia.Color4f(*dark, a).toColor()], [0, .45, 1])
    c.drawRRect(skia.RRect.MakeRectXY(r, 3.5, 3.5), skia.Paint(AntiAlias=True, Shader=sh))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(r.left() + 2.5, r.top() + 2, r.right() - 6, r.top() + 4.5), 1.5, 1.5),
                skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .35 * a)))
RING_COL = (.36, .34, .33)

BG = background(1050)
g0 = G.make_grid(G.GAP)
board = skia.Surface.MakeRaster(INFO)
with board as c:
    c.drawImage(BG, 0, 0)
    rr = skia.RRect.MakeRectXY(skia.Rect(AX0 - 6, AY0 - 6, G.AX1 + 6, G.AY1 + 6), 14, 14)
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35)))
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(*AMBER, .55)))
    for i in range(G.NC):
        for j in range(G.NR):
            if g0[i, j] == G.RING: draw_block(c, i, j, RING_COL)
            elif g0[i, j] == G.PINK: draw_block(c, i, j, block_col(i, j))
BOARD0 = board.makeImageSnapshot()
BALL = glass_ball((1, .97, .92), 5)
GL_B = glow((1, .9, .7), 7, .6)
BALL_BIG = glass_ball((1, .97, .92), 7)
GL_SOLO = glow((1, .85, .55), 12, .8)
GL_GAP = glow((1, .72, .3), 12, .9)
GL_HIT = glow((1, .85, .6), 10, .9)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)
gx, gy = AX0 + (G.GAP[0] + .5) * C, AY0 + (G.GAP[1] + .5) * C
near_hits = [(e[0], e[2], e[3]) for e in events if e[1] == "ring" and e[0] < T_IN and abs(e[2] - gx) < 2.6 * C and abs(e[3] - gy) < 1.6 * C]
print("near misses", len(near_hits))

F_K = font(TF_SEMI, 27); F_L = font(TF_SERIF_I, 34)
def head(c, balls, pulse, done):
    text(c, "ONE GAP", W / 2, 196, F_K, AMBER, .9, spacing=7)
    text(c, "Find the gap.", W / 2, 272, F_RULE, CREAM, .97)
    text(c, "Then it multiplies.", W / 2, 336, F_RULE_I, CREAM, .9)
    c.save(); c.translate(W / 2, 412); c.scale(1 + .07 * pulse, 1 + .07 * pulse); c.translate(-W / 2, -412)
    text(c, f"{balls:,}", W / 2, 452, F_CNT, (1, .82, .55) if balls > 1 else CREAM)
    c.restore()
    text(c, "balls" if not done else "board cleared", W / 2, 500, F_L, CREAM if not done else AMBER, .55 if not done else .9)

state = {"surf": None, "k": 0}
first = None; trail = []
def frame(f):
    global first
    t = f / FPS
    if state["surf"] is None:
        s = skia.Surface.MakeRaster(INFO)
        with s as c: c.drawImage(BOARD0, 0, 0)
        state["surf"] = s
    with state["surf"] as c:   # erase broken blocks up to now (permanent)
        while state["k"] < len(broken) and broken[state["k"]][0] <= t:
            _, i, j = broken[state["k"]]
            r = skia.Rect(AX0 + i * C, AY0 + j * C, AX0 + (i + 1) * C, AY0 + (j + 1) * C)
            c.save(); c.clipRect(r); c.drawImage(BG, 0, 0); c.restore(); state["k"] += 1
    fi = min(f, len(frames) - 1)
    P, nb = frames[fi]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(state["surf"].makeImageSnapshot(), 0, 0)
        # the gap: glowing target until sealed, then a fresh ring block with a flash
        if t < T_SEAL:
            blit(c, GL_GAP, gx, gy, 1.0, pa(.35 + .2 * math.sin(t * 5)))
        else:
            draw_block(c, G.GAP[0], G.GAP[1], RING_COL)
            blit(c, GL_HIT, gx, gy, 2.0, pa(math.exp(-(t - T_SEAL) / .25)))
        for th, x, y in near_hits:
            if 0 <= t - th < .4: blit(c, GL_HIT, x, y + (C * .6 if y < gy else -C * .6), 1.4, pa(.9 * math.exp(-(t - th) / .12)))
        # shards from fresh breaks
        k0 = np.searchsorted([b[0] for b in broken], t - .35)
        for bt, i, j in broken[k0:state["k"]]:
            u = (t - bt) / .35
            col = block_col(i, j); cx, cy = AX0 + (i + .5) * C, AY0 + (j + .5) * C
            s = 8 + 14 * u
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2), 3, 3),
                        skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=skia.Color4f(*col, .9 * (1 - u))))
            blit(c, GL_HIT, cx, cy, 1.0, pa(.5 * (1 - u)))
        # balls (+ a short trail while there is only one)
        if len(P) == 1:
            trail.append(P[0].copy()); del trail[:-7]
            for q, pt in enumerate(trail[:-1]):
                blit(c, GL_B, pt[0], pt[1], .8, pa(.12 * (q + 1)))
        fade = 1.0 if t < CARD else max(0, 1 - (t - CARD) / .5)
        if len(P) <= 3:
            for x, y in P: blit(c, GL_SOLO, x, y, 1.0, pa(.55)); blit(c, BALL_BIG, x, y)
        else:
            for x, y in P: blit(c, BALL, x, y, paint=skia.Paint(Alphaf=fade))
        lit = len(P)
        pulse = math.exp(-(t - T_IN) / .3) if t >= T_IN else 0
        if t >= T_CLEAR: pulse = max(pulse, math.exp(-(t - T_CLEAR) / .3))
        head(c, lit, pulse, t >= T_CLEAR)
        watermark(c, 1640)
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
    tick_w = glass_click(1480, 150, .06, .35); tick_r = glass_click(2050, 190, .05, .35)
    per = {}
    for e in events:
        t, kind = e[0], e[1]
        if t > CARD + .3: continue
        fk = int(t * FPS)
        if kind in ("wall", "ring"):
            if t < T_IN:
                nearg = kind == "ring" and abs(e[2] - gx) < 2.6 * C and abs(e[3] - gy) < 1.6 * C
                m.add(glass_click(2600, 160, .07, .4) if nearg else (tick_r if kind == "ring" else tick_w), t, 1.3 if nearg else .9, e[2])
                if nearg:
                    n = sosfilt(butter(2, [2500, 7000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(.3 * SR)))
                    m.add(n * np.exp(-np.arange(len(n)) / SR * 9), t, .45, e[2])
            else:
                per[fk] = per.get(fk, 0) + 1
                if per[fk] <= 3: m.add(tick_w if kind == "wall" else tick_r, t, .12, e[2])
        elif kind == "pop":
            key = ("p", fk); per[key] = per.get(key, 0) + 1
            if per[key] <= 5:
                row = e[4]
                m.add(glass_click(note(14 - int(row * 10 / G.NR), 261.63), 70, .14, .2), t + rng.uniform(0, .02), .3, e[2])
        elif kind == "seal":
            m.add(mallet(98, 1.2, .6), t, .5, e[2]); m.add(thud(55, .5), t, .6, e[2])
    m.add(thud(60, .7), T_IN, 1.0, gx); m.add(mallet(392, 1.5, .8), T_IN, .4, gx)
    for j, n in enumerate((0, 2, 4, 7, 9)):
        m.add(mallet(note(n, 261.63), 2.4, .5), T_CLEAR + .05 + j * .07, .3, 380 + j * 80)
    for j, n in enumerate((0, 4, 7)):
        m.add(mallet(note(n, 196), 2.2, .4), CARD + .1 + j * .06, .2, 450 + j * 90)
    return m.save(path, fade_in=.0, fade_out=.3)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        fs = [int(x) for x in sys.argv[2].split(",")]
        for f in range(max(fs) + 1):
            s = frame(f)
            if f in fs: s.makeImageSnapshot().save(f"/home/claude/gap/P_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("/home/claude/gap/gap_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print("rms", audio("/home/claude/gap/gap.wav"))
        print("mux", mux("/home/claude/gap/gap_silent.mp4", "/home/claude/gap/gap.wav", "/home/claude/gap/one_gap.mp4"))
