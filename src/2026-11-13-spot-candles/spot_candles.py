"""SPOT IT (BREAKS PHYSICS): 120 tea lights on a round walnut table, 12 spokes (A-L, a clock face) x 10 rings
(1 = inner, 10 = outer), seen from above in perspective. A brass puffer in the middle breathes out three
gusts per 12 s loop (gentle, medium, strong); each gust is a ring of air rolling outward and every flame bends
away from it, then springs back with a little wobble. One flame (K6) leans INTO the wind, toward the puffer.
Its flutter sound when the gust reaches it is a soft reversed swell, lower than its ring's note (audio clue).
Flame lean = damped spring driven by the wind; simulated for 4 loops and the last one used, flicker uses
integer cycles per loop, so frame 0 == frame N (seamless)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spotc"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NS, NR = 12, 10
LETTERS = "ABCDEFGHIJKL"
RADII = np.linspace(132, 382, NR)
CX, CY, K = 540, 1080, 0.95          # table centre on screen, depth squash
ODD = (10, 5)                         # spoke K, ring 6
GUSTS = [(0.7, .38), (4.7, .72), (8.7, 1.0)]   # (time, strength)
V = 300.0                             # gust front speed px/s
DMAX = 27.0                           # max flame tip offset (px)
FH = 27.0                             # flame height (screen px)

def spoke_ang(i): return i * 2 * math.pi / NS            # clockwise from 12 o'clock (back of the table)
def table_xy(r, a): return r * math.sin(a), -r * math.cos(a)
def scr(X, Z): return CX + X, CY + Z * K

def wind(r, t):
    w = 0.0
    for tk, A in GUSTS:
        for sh in (-LOOP, 0.0):
            x = V * (t - tk - sh) - r          # distance the front has passed this radius
            if x < -60: continue
            w += A * (1 / (1 + math.exp(-x / 14))) * math.exp(-max(x, 0) / 480) * (1 - .3 * (r - 132) / 250)
    return w

# ---- simulate flame leans (damped spring) for 4 loops, keep the last ----
def simulate():
    dt = 1 / 240
    om, ze = 2 * math.pi * 1.7, .62
    rng = np.random.default_rng(7)
    lean = np.zeros((NS, NR, TOTAL))
    for j, r in enumerate(RADII):
        d = v = 0.0
        steps = int(4 * LOOP / dt)
        tgt_cache = [wind(r, (s * dt) % LOOP) for s in range(int(LOOP / dt))]
        rec = np.zeros(TOTAL)
        for s in range(steps):
            tgt = DMAX * tgt_cache[s % len(tgt_cache)]
            acc = om * om * (tgt - d) - 2 * ze * om * v
            v += acc * dt; d += v * dt
            if s >= 3 * len(tgt_cache):
                ss_ = s - 3 * len(tgt_cache)
                if ss_ % 8 == 0 and ss_ // 8 < TOTAL: rec[ss_ // 8] = d
        lean[:, j, :] = rec
    return lean

LEAN = simulate()
RNG = np.random.default_rng(11)
FLK = RNG.integers(14, 44, (NS, NR, 3)); FLP = RNG.uniform(0, 2 * math.pi, (NS, NR, 3))

def flicker(i, j, t):
    n, p = FLK[i, j], FLP[i, j]
    w = 2 * math.pi * t / LOOP
    sway = 1.3 * math.sin(n[0] * w + p[0]) + .7 * math.sin(n[1] * w + p[1])
    h = 1 + .06 * math.sin(n[2] * w + p[2]) + .03 * math.sin(n[1] * w * 1 + p[0])
    return sway, h

BG = background(1080)
F_LBL = font(TF_MONO, 24); F_NUM = font(TF_MONO, 18)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
HALO = glow((1.0, .62, .25), 22, .30)
POOL = glow((1.0, .55, .2), 40, .16)
BLUE = glow((.35, .55, 1.0), 3.2, .9)
PLUS = skia.Paint(BlendMode=skia.BlendMode.kPlus)

def table_img():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        R = 440
        rect = skia.Rect(CX - R, CY - R * K, CX + R, CY + R * K)
        c.drawOval(rect.makeOffset(0, 22), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
        c.drawOval(rect.makeOffset(0, 12), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.13, .075, .04, 1)))
        c.drawOval(rect, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX, CY - 40), R * 1.05, [skia.Color4f(.25, .15, .085, 1).toColor(), skia.Color4f(.17, .1, .055, 1).toColor(),
                                      skia.Color4f(.10, .06, .035, 1).toColor()], [0, .6, 1])))
        # fine wood grain arcs
        rg = np.random.default_rng(3)
        for k in range(70):
            rr = rg.uniform(30, R - 6)
            a0 = rg.uniform(0, 360); sw = rg.uniform(20, 90)
            c.drawArc(skia.Rect(CX - rr, CY - rr * K, CX + rr, CY + rr * K), a0, sw, False,
                      skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=rg.uniform(.6, 1.6),
                                 Color4f=skia.Color4f(0, 0, 0, rg.uniform(.05, .14))))
        c.drawOval(rect, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                   Color4f=skia.Color4f(.86, .62, .34, .45)))
    return s.makeImageSnapshot()
TABLE = table_img()

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()

def ellipse(cx, cy, rx, ry): return skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)

def draw_cup(c, x, y):
    # y = table contact point (bottom centre)
    rx, ry, hh = 14, 14 * K * .62, 7
    side = skia.Path()
    side.addRect(skia.Rect(x - rx, y - hh, x + rx, y))
    side.addOval(ellipse(x, y, rx, ry))
    c.drawOval(ellipse(x + 3, y + 4, rx + 3, ry + 2), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    c.drawPath(side, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - rx, 0), (x + rx, 0)], [rgb((.55, .52, .5)), rgb((.92, .9, .86)), rgb((.62, .58, .54)), rgb((.3, .28, .27))], [0, .3, .65, 1])))
    c.drawOval(ellipse(x, y - hh, rx, ry), skia.Paint(AntiAlias=True, Color4f=rgb((.85, .83, .8))))
    c.drawOval(ellipse(x, y - hh + .6, rx - 2.2, ry - 1.8), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x, y - hh), rx, [rgb((1, .93, .75)), rgb((.93, .84, .68)), rgb((.72, .62, .5))], [0, .5, 1])))
    c.drawLine(x, y - hh, x, y - hh - 4, skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color4f=skia.Color4f(.12, .08, .06, 1)))
    return x, y - hh - 3.5

def flame_path(bx, by, dx, dy, h, wmax, s_end=1.0):
    n = 14
    ss_ = np.linspace(0, 1, n)
    L, R = [], []
    for s in ss_:
        e = s ** 1.5
        px, py = bx + dx * e, by + dy * e - h * s
        # tangent
        de = 1.5 * s ** .5
        tx, ty = dx * de, dy * de - h
        nl = math.hypot(tx, ty) or 1
        nx, ny = -ty / nl, tx / nl
        w = wmax * 2.6 * (s ** .55) * (1 - s) ** 1.15
        L.append((px + nx * w, py + ny * w)); R.append((px - nx * w, py - ny * w))
    p = skia.Path(); p.moveTo(*L[0])
    for q in L[1:]: p.lineTo(*q)
    for q in R[::-1]: p.lineTo(*q)
    p.close(); return p

def draw_flame(c, bx, by, dx, dy, hmul):
    h = FH * hmul * (1 + .12 * min(1, math.hypot(dx, dy) / DMAX))
    mid = (bx + dx * .35, by + dy * .35 - h * .5)
    outer = flame_path(bx, by, dx, dy, h, 5.6)
    c.drawPath(outer, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (bx + dx * .1, by - h * .2), h * .95, [rgb((1, .78, .38)), rgb((1, .52, .14)), rgb((.85, .22, .05))], [0, .5, 1]),
        Alphaf=.92))
    inner = flame_path(bx, by - 1, dx * .8, dy * .8, h * .62, 3.4)
    c.drawPath(inner, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .97, .85, .95)))
    blit(c, BLUE, bx, by + .5)
    blit(c, HALO, mid[0], mid[1], 1.0, PLUS)

def cand_list():
    out = []
    for i in range(NS):
        a = spoke_ang(i)
        for j, r in enumerate(RADII):
            X, Z = table_xy(r, a)
            out.append((Z, i, j, a, r, X))
    out.sort()
    return out
CANDS = cand_list()

def puff_ring(c, t):
    for tk, A in GUSTS:
        for sh in (-LOOP, 0.0):
            age = t - tk - sh
            if age < 0 or age > 1.9: continue
            R = 60 + V * age
            a = A * .34 * (1 - age / 1.9) ** 1.2
            for k, (dr, wd) in enumerate(((0, 10), (-24, 18))):
                rr = R + dr
                if rr < 40: continue
                c.drawOval(ellipse(CX, CY, rr, rr * K), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                           StrokeWidth=wd, Color4f=skia.Color4f(.85, .9, 1, a * (1 if k == 0 else .5)),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
            # drifting motes riding the gust
            rg = np.random.default_rng(int(tk * 10))
            for m in range(60):
                ang = rg.uniform(0, 2 * math.pi); lag = rg.uniform(0, 70)
                rr = R - lag
                if rr < 50 or rr > 430: continue
                mx, my = CX + rr * math.sin(ang), CY - rr * math.cos(ang) * K
                c.drawCircle(mx, my, rg.uniform(.8, 1.7), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .95, .85, a * 2.2)))

def puffer(c, t):
    e = 0.0
    for tk, A in GUSTS:
        for sh in (-LOOP, 0.0):
            age = t - tk - sh
            if -.15 < age < .8: e = max(e, A * math.exp(-max(age, 0) * 5) * (1 if age > 0 else (age + .15) / .15))
    rx, ry, hh = 34, 34 * K * .6, 40
    x, y = CX, CY + 6
    c.drawOval(ellipse(x + 6, y + 6, rx + 8, ry + 5), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
    body = skia.Path(); body.addRect(skia.Rect(x - rx, y - hh, x + rx, y)); body.addOval(ellipse(x, y, rx, ry))
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - rx, 0), (x + rx, 0)], [rgb((.45, .3, .14)), rgb((.98, .8, .48)), rgb((.72, .5, .24)), rgb((.3, .19, .08))], [0, .32, .62, 1])))
    for yy in (y - hh * .35, y - hh * .7):   # vent slots
        for k in range(7):
            u = -1 + 2 * (k + .5) / 7
            c.drawOval(ellipse(x + u * rx * .9, yy, 2.2 * math.sqrt(1 - u * u) + .5, 3.6),
                       skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.08, .05, .03, .9)))
    c.drawOval(ellipse(x, y - hh, rx, ry), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - 8, y - hh - 5), rx * 1.2, [rgb((1, .9, .62)), rgb((.8, .58, .3)), rgb((.45, .3, .14))], [0, .5, 1])))
    c.drawOval(ellipse(x, y - hh, rx * .45, ry * .45), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.12, .08, .05, 1)))
    if e > 0:
        c.drawOval(ellipse(x, y - hh, rx * (.5 + .9 * e), ry * (.5 + .9 * e)), skia.Paint(AntiAlias=True,
                   Color4f=skia.Color4f(.85, .92, 1, .35 * e), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
        text(c, "One of these", W / 2, 278, F_Q, CREAM, .97)
        text(c, "breaks physics.", W / 2, 346, F_QI, CREAM, .9)
        text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
        fi = font(TF_SERIF_I, 32); fe = font(TF_EMOJI, 26)
        s1 = "Like it if you found it "
        w1 = fi.measureText(s1); w2 = fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, 466, fi, CREAM, .5, align="left")
        c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))
        c.drawImage(TABLE, 0, 0)
        # warm light pools on the table
        for Z, i, j, a, r, X in CANDS:
            sx, sy = scr(X, Z)
            blit(c, POOL, sx, sy, 1.0, PLUS)
        puff_ring(c, t)
        for i in range(NS):
            a = spoke_ang(i); X, Z = table_xy(426, a); sx, sy = scr(X, Z)
            text(c, LETTERS[i], sx, sy + 9, F_LBL, CREAM, .5)
        for j, r in enumerate(RADII):
            for sgn in (1, -1):
                text(c, str(j + 1), CX + sgn * r, CY + 31, F_NUM, CREAM, .38)
        drew_puffer = False
        for Z, i, j, a, r, X in CANDS:
            if not drew_puffer and Z > 0:
                puffer(c, t); drew_puffer = True
            sx, sy = scr(X, Z)
            bx, by = draw_cup(c, sx, sy)
            d = LEAN[i, j, f] * (-1 if (i, j) == ODD else 1)
            sway, hm = flicker(i, j, t)
            dx = d * math.sin(a) + sway
            dy = -d * math.cos(a) * K * .75
            draw_flame(c, bx, by, dx, dy, hm)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def flutter(f0, dur=.16, rev=False):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .35 * np.sin(2 * np.pi * f0 * 2.01 * t)) * np.exp(-t * 34)
    n = np.random.default_rng(int(f0)).standard_normal(len(t))
    n = sosfilt(butter(2, [900, 5000], btype="band", fs=SR, output="sos"), n) * np.exp(-t * 60) * .9
    s = (s + n) * np.minimum(1, t * 3000)
    if rev:
        s = s[::-1] * np.minimum(1, (len(t) - np.arange(len(t))) / (SR * .004))
    return s

def whoosh(dur=1.6, A=1.0, seed=0):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(seed).standard_normal(len(t))
    lo = sosfilt(butter(2, [120, 700], btype="band", fs=SR, output="sos"), n)
    hi = sosfilt(butter(2, [1500, 4500], btype="band", fs=SR, output="sos"), n) * .25
    env = (1 - np.exp(-t * 25)) * np.exp(-t * 2.6)
    return (lo + hi) * env

def audio(path):
    m = Mix(LOOP)
    for tk, A in GUSTS:
        m.add(whoosh(A=A, seed=int(tk * 10)) * .9, tk - .05, .38 * (.5 + .5 * A), CX)
        m.add(thud(48, .5), tk - .03, .25 * A, CX)
        for i in range(NS):
            a = spoke_ang(i)
            for j, r in enumerate(RADII):
                tt = tk + (r - 0) / V
                X, Z = table_xy(r, a); sx, _ = scr(X, Z)
                if (i, j) == ODD:
                    m.add(flutter(note(j, 261.63) * .5, .22, rev=True), tt - .18, .26 * (.45 + .55 * A), sx)
                else:
                    f0 = note(j + 3, 261.63)
                    jit = np.random.default_rng(i * 31 + j + int(tk)).uniform(0, .02)
                    m.add(flutter(f0), (tt + jit) % LOOP, .085 * (.45 + .55 * A), sx)
    # periodic soft flame-crackle bed (circular spectrum -> seamless)
    n = m.N
    rg = np.random.default_rng(4)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 600) / 500) ** 2) + .15 * np.exp(-((fr - 3000) / 1500) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    crack = np.zeros(n)
    for k in range(70):
        i0 = int(rg.uniform(0, n - 2000)); L = 600
        crack[i0:i0 + L] += rg.standard_normal(L) * np.exp(-np.arange(L) / 90) * rg.uniform(.2, 1)
    crack = sosfilt(butter(2, 2500, btype="high", fs=SR, output="sos"), crack)
    m.L += bed * .13 + crack * .035; m.R += np.roll(bed, 4000) * .13 + np.roll(crack, 9000) * .035
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/C_{f:04d}.png", skia.kPNG)
    else:
        print("loop seam lean diff", float(np.abs(LEAN[..., 0] - LEAN[..., -1]).max()))
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_candles.mp4"))
