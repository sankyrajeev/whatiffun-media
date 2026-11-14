"""SPOT IT (BIG FIELD, SPIRAL): ~147 brass pocket compasses laid along a 5-turn Archimedean spiral around a
glossy bar magnet. The magnet clicks a quarter turn every 1.5 s (8 steps = 2 turns per 12 s loop); every needle
swings to follow the dipole field at its spot, overshoots and wobbles back (damped pendulum, torque ~ sin), the
outer ones a touch slower, so each click sends a ripple of swinging needles out along the spiral.
One needle (ODD) has a sticky pivot (heavier damping): it never overshoots, it just creeps into place late.
Addressing: letters A-L around (12 sectors, A at 12 o'clock), numbers 1-5 = which turn of the spiral (outward);
the spiral starts each turn at the seam between L and A, where the turn numbers are printed.
Sound: magnet click (brass clack + low thump) per step; a tiny brass tick per needle when it first swings
through its new heading (pentatonic by turn, panned by x); the sticky one gives a late, low, dull scrape.
Simulated for 6 loops, the last one used -> frame 0 == frame N (seamless)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spotm"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
CX, CY = 540, 1010
R0, PITCH, TURNS = 132, 50.0, 5
SEAM = math.radians(-15)            # screen angle (clockwise from 12 o'clock) where each turn starts
LETTERS = "ABCDEFGHIJKL"
HR = 20.0                           # compass housing radius
STEPS = [0.3 + 1.5 * k for k in range(8)]
STEP_DUR = .42
ODD_CELL = ("I", 3)
ZETA, ZETA_ODD = .26, float(os.environ.get("ZODD", "0.85"))

def layout(sp=53.5, gap=26):
    phis = np.linspace(0, 2 * math.pi * TURNS, 200000)
    rr = R0 + PITCH * phis / (2 * math.pi)
    a = SEAM + phis
    S = np.cumsum(np.hypot(np.gradient(rr * np.sin(a)), np.gradient(rr * np.cos(a))))
    out, last = [], -1e9
    for k in range(len(phis)):
        if S[k] - last >= sp:
            phi, r = phis[k], rr[k]; fr = phi % (2 * math.pi)
            if min(fr, 2 * math.pi - fr) * r < gap / 2 + HR: continue
            ang = (SEAM + phi) % (2 * math.pi)
            out.append(dict(phi=phi, r=r, a=ang, x=CX + r * math.sin(ang), y=CY - r * math.cos(ang),
                            turn=int(phi // (2 * math.pi)) + 1, sec=LETTERS[int(((ang + math.pi / 12) % (2 * math.pi)) // (math.pi / 6))]))
            last = S[k]
    return out
C = layout()
NC = len(C)
# odd one: in ODD_CELL, closest to the sector centre
cands = [i for i, c in enumerate(C) if (c["sec"], c["turn"]) == ODD_CELL]
ODD = min(cands, key=lambda i: abs(((C[i]["a"] - LETTERS.index(ODD_CELL[0]) * math.pi / 6 + math.pi) % (2 * math.pi)) - math.pi))

def ease(u): u = min(1, max(0, u)); return u ** 3 * (u * (u * 6 - 15) + 10)
def magnet_angle(t):      # screen angle of N pole, clockwise from 12 o'clock
    tt = t % LOOP; k = math.floor(t / LOOP)
    a = sum(ease((tt - s) / STEP_DUR) for s in STEPS)
    return math.radians(20) + (a + 8 * k) * math.pi / 2

def field_dir(x, y, ma):
    # dipole at the centre, moment along the magnet's N direction; screen coords (y down)
    mx, my = math.sin(ma), -math.cos(ma)
    rx, ry = x - CX, y - CY; r = math.hypot(rx, ry); ux, uy = rx / r, ry / r
    d = mx * ux + my * uy
    bx, by = 3 * d * ux - mx, 3 * d * uy - my
    return math.atan2(bx, -by)        # heading, clockwise from up

def simulate():
    dt = 1 / 600
    n_loops = 6
    steps = int(n_loops * LOOP / dt)
    sub = int(round(1 / (FPS * dt)))
    X = np.array([c["x"] for c in C]); Y = np.array([c["y"] for c in C]); R = np.array([c["r"] for c in C])
    w0 = 2 * math.pi * 1.55 * (R0 / R) ** .45
    zeta = np.full(NC, ZETA); zeta[ODD] = ZETA_ODD
    def psi(t):
        ma = magnet_angle(t)
        mx, my = math.sin(ma), -math.cos(ma)
        rx, ry = X - CX, Y - CY; ux, uy = rx / R, ry / R
        d = mx * ux + my * uy
        return np.arctan2(3 * d * ux - mx, -(3 * d * uy - my))
    th = psi(0.0).copy(); om = np.zeros(NC)
    rec = np.zeros((NC, TOTAL)); tgt = np.zeros((NC, TOTAL))
    p_prev = psi(0.0); unwrap = np.zeros(NC)
    start = (n_loops - 1) * int(LOOP / dt)
    for s in range(steps):
        t = s * dt
        p = psi(t)
        jump = (p - p_prev + math.pi) % (2 * math.pi) - math.pi
        unwrap += jump; p_prev = p
        err = np.angle(np.exp(1j * (th - p)))
        acc = -w0 ** 2 * np.sin(err) - 2 * zeta * w0 * om
        om += acc * dt; th += om * dt
        if s >= start and (s - start) % sub == 0 and (s - start) // sub < TOTAL:
            f = (s - start) // sub
            rec[:, f] = th; tgt[:, f] = p
    return rec, tgt, w0

TH, PSI, W0 = simulate()

def tick_times():
    """per needle per step: time when the needle first swings through its new heading (or gets within 3 deg)"""
    out = []
    for k, s in enumerate(STEPS):
        f0 = int(s * FPS); f1 = int((s + 1.45) * FPS)
        fe = min(int((s + 1.48) * FPS), TOTAL - 1)
        for i in range(NC):
            e = np.angle(np.exp(1j * (TH[i, f0:f1] - PSI[i, fe])))
            big = np.abs(e[0]) if len(e) else 0
            if big < math.radians(8): continue
            hit = None
            for j in range(1, len(e)):
                if np.sign(e[j]) != np.sign(e[j - 1]) or abs(e[j]) < math.radians(3):
                    hit = j; break
            if hit is None: continue
            swing = float(np.abs(np.angle(np.exp(1j * (TH[i, f0 + hit] - TH[i, max(f0 + hit - 1, 0)]))))) * FPS
            out.append((s + hit / FPS, i, big, swing))
    return out

# ---------------- look ----------------
BG = background(1000)
F_LBL = font(TF_MONO, 24); F_NUM = font(TF_MONO, 21)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
PLUS = skia.Paint(BlendMode=skia.BlendMode.kPlus)
def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()

def face_col(c):
    u = (c["phi"] / (2 * math.pi * TURNS))
    return hsv(195 + 120 * u, .55, .30)     # teal -> indigo -> plum along the spiral

def housing_sprite(col):
    sz = HR * 2 + 16
    def fn(c):
        x = y = sz / 2
        c.drawCircle(x + 2.5, y + 3.5, HR + 1.5, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.5)))
        c.drawCircle(x, y, HR, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeSweep(x, y,
            [rgb((.55, .36, .15)), rgb((1, .84, .52)), rgb((.62, .42, .18)), rgb((.32, .2, .08)), rgb((.85, .64, .34)), rgb((.55, .36, .15))],
            [0, .2, .42, .62, .85, 1])))
        c.drawCircle(x, y, HR - 3.4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (x - 4, y - 5), HR * 1.1, [rgb(tuple(v * 1.7 + .05 for v in col)), rgb(col), rgb(tuple(v * .5 for v in col))], [0, .55, 1])))
        for k in range(12):
            a = k * math.pi / 6; L = 3.2 if k % 3 == 0 else 1.6
            r1 = HR - 4.2
            c.drawLine(x + r1 * math.sin(a), y - r1 * math.cos(a), x + (r1 - L) * math.sin(a), y - (r1 - L) * math.cos(a),
                       skia.Paint(AntiAlias=True, StrokeWidth=1.0, Color4f=skia.Color4f(.96, .92, .84, .5 if k % 3 == 0 else .28)))
    return sprite(fn, sz)

GLASS = sprite(lambda c: (c.drawCircle(HR + 8, HR + 8, HR - 3.4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
    [(HR + 8 - HR, HR + 8 - HR), (HR + 8 + HR, HR + 8 + HR)], [skia.Color4f(1, 1, 1, .16).toColor(), skia.Color4f(1, 1, 1, 0).toColor(),
     skia.Color4f(1, 1, 1, 0).toColor(), skia.Color4f(1, 1, 1, .06).toColor()], [0, .45, .7, 1]))),
    c.drawArc(skia.Rect(HR + 8 - HR + 6, HR + 8 - HR + 6, HR + 8 + HR - 6, HR + 8 + HR - 6), 200, 50, False,
              skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6, StrokeCap=skia.Paint.kRound_Cap,
                         Color4f=skia.Color4f(1, 1, 1, .55)))), HR * 2 + 16)
HOUS = [housing_sprite(face_col(c)) for c in C]
SWING_GLOW = glow((1.0, .7, .35), 13, .55)

def draw_needle(c, x, y, th):
    L = HR - 5.5; w = 3.3
    s, co = math.sin(th), math.cos(th)
    fx, fy = s, -co; nx, ny = co, s
    north = skia.Path(); north.moveTo(x + fx * L, y + fy * L); north.lineTo(x + nx * w, y + ny * w)
    north.lineTo(x - nx * w, y - ny * w); north.close()
    south = skia.Path(); south.moveTo(x - fx * L, y - fy * L); south.lineTo(x + nx * w, y + ny * w)
    south.lineTo(x - nx * w, y - ny * w); south.close()
    sh = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.6))
    c.save(); c.translate(1.6, 2.2); c.drawPath(north, sh); c.drawPath(south, sh); c.restore()
    c.drawPath(north, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - nx * w, y - ny * w), (x + nx * w, y + ny * w)], [rgb((1, .45, .36)), rgb((.78, .16, .14))])))
    c.drawPath(south, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x - nx * w, y - ny * w), (x + nx * w, y + ny * w)], [rgb((.97, .95, .9)), rgb((.62, .62, .64))])))
    c.drawCircle(x, y, 2.3, skia.Paint(AntiAlias=True, Color4f=rgb((1, .85, .55))))
    c.drawCircle(x - .6, y - .6, .9, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .8)))

def field_lines_img():
    """faint dipole field lines (magnet frame, N pointing up), drawn once and rotated with the magnet"""
    S = 1100
    s = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(S, S))
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        o = S / 2
        for Lr in (70, 105, 150, 210, 300, 430, 620, 900):
            for side in (1, -1):
                p = skia.Path(); first = True
                for b in np.linspace(.02, math.pi - .02, 400):
                    r = Lr * math.sin(b) ** 2
                    if r < 78: first = True; continue
                    x, y = o + side * r * math.sin(b), o - r * math.cos(b)
                    if first: p.moveTo(x, y); first = False
                    else: p.lineTo(x, y)
                c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0,
                           Color4f=skia.Color4f(.9, .75, .5, .085)))
        # radial fade
        c.drawPaint(skia.Paint(BlendMode=skia.BlendMode.kDstIn, Shader=skia.GradientShader.MakeRadial(
            (o, o), o, [skia.Color4f(1, 1, 1, 1).toColor(), skia.Color4f(1, 1, 1, 1).toColor(), skia.Color4f(1, 1, 1, 0).toColor()], [0, .62, .82])))
    return s.makeImageSnapshot()
FIELD = field_lines_img()

def plate_img():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        R = 456
        c.drawCircle(CX, CY + 14, R, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
        c.drawCircle(CX, CY, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX - 60, CY - 90), R * 1.15, [rgb((.17, .12, .085)), rgb((.11, .08, .06)), rgb((.065, .05, .04))], [0, .6, 1])))
        rg = np.random.default_rng(3)    # fine brushed circular grain
        for k in range(110):
            rr = rg.uniform(30, R - 6); a0 = rg.uniform(0, 360); sw = rg.uniform(20, 120)
            c.drawArc(skia.Rect(CX - rr, CY - rr, CX + rr, CY + rr), a0, sw, False,
                      skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=rg.uniform(.5, 1.3),
                                 Color4f=skia.Color4f(1, .9, .7, rg.uniform(.012, .035))))
        c.drawCircle(CX, CY, R, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                     Color4f=skia.Color4f(.86, .62, .34, .45)))
        # the spiral track (faint groove)
        p = skia.Path(); first = True
        for phi in np.linspace(0, 2 * math.pi * TURNS, 3000):
            r = R0 + PITCH * phi / (2 * math.pi); a = SEAM + phi
            x, y = CX + r * math.sin(a), CY - r * math.cos(a)
            if first: p.moveTo(x, y); first = False
            else: p.lineTo(x, y)
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4, Color4f=skia.Color4f(.96, .85, .6, .13)))
        # sector ticks + letters
        for i, L in enumerate(LETTERS):
            a = i * math.pi / 6
            text(c, L, CX + 420 * math.sin(a), CY - 420 * math.cos(a) + 9, F_LBL, CREAM, .52)
            ab = a + math.pi / 12
            c.drawLine(CX + 398 * math.sin(ab), CY - 398 * math.cos(ab), CX + 440 * math.sin(ab), CY - 440 * math.cos(ab),
                       skia.Paint(AntiAlias=True, StrokeWidth=1.3, Color4f=skia.Color4f(.96, .92, .84, .22)))
        # turn numbers at the seam
        for k in range(TURNS):
            r = R0 + PITCH * k
            text(c, str(k + 1), CX + r * math.sin(SEAM), CY - r * math.cos(SEAM) + 6, F_NUM, AMBER, .75)
    return s.makeImageSnapshot()
PLATE = plate_img()

def draw_magnet(c, ma, pulse):
    c.save(); c.translate(CX, CY); c.rotate(math.degrees(ma))
    L, Wd = 74, 19
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-Wd + 5, -L + 8, Wd + 5, L + 8), 8, 8),
                skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
    for half, cols in ((-1, [rgb((.62, .1, .1)), rgb((1, .42, .34)), rgb((.78, .16, .14)), rgb((.42, .06, .06))]),
                       (1, [rgb((.5, .52, .56)), rgb((.97, .96, .93)), rgb((.72, .72, .74)), rgb((.34, .35, .38))])):
        r = skia.Rect(-Wd, -L, Wd, 0) if half < 0 else skia.Rect(-Wd, 0, Wd, L)
        rr = skia.RRect.MakeRectXY(r, 7, 7)
        c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-Wd, 0), (Wd, 0)], cols, [0, .3, .65, 1])))
    c.drawLine(-Wd, 0, Wd, 0, skia.Paint(AntiAlias=True, StrokeWidth=1.2, Color4f=skia.Color4f(0, 0, 0, .35)))
    f = font(TF_SEMI, 22)
    text(c, "N", 0, -L + 30, f, (1, .93, .88), .85)
    text(c, "S", 0, L - 14, f, (.2, .2, .24), .7)
    c.restore()
    c.drawCircle(CX, CY, 7, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (CX - 2, CY - 2), 8, [rgb((1, .9, .62)), rgb((.7, .5, .24))])))
    if pulse > 0:
        c.drawCircle(CX, CY, 80 + 30 * (1 - pulse), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                     Color4f=skia.Color4f(1, .8, .5, .16 * pulse), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))

def header(c):
    text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
    text(c, "One needle has", W / 2, 278, F_Q, CREAM, .97)
    text(c, "a sticky pivot.", W / 2, 346, F_QI, CREAM, .9)
    text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 38), CREAM, .55)
    fi = font(TF_SERIF_I, 32); fe = font(TF_EMOJI, 26)
    s1 = "Like it if you found it "
    w1 = fi.measureText(s1); w2 = fe.measureText("👍")
    x0 = W / 2 - (w1 + w2) / 2
    text(c, s1, x0, 466, fi, CREAM, .5, align="left")
    c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))

def frame(f, mark_odd=False):
    t = f / FPS
    ma = magnet_angle(t)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        header(c)
        c.drawImage(PLATE, 0, 0)
        c.save(); c.translate(CX, CY); c.rotate(math.degrees(ma)); c.translate(-550, -550)
        c.drawImage(FIELD, 0, 0); c.restore()
        pulse = 0.0
        for s in STEPS:
            u = (t - s) / .7
            if 0 <= u <= 1: pulse = max(pulse, 1 - u)
        draw_magnet(c, ma, pulse)
        for i, cc in enumerate(C):
            x, y = cc["x"], cc["y"]
            blit(c, HOUS[i], x, y)
            fp, fn_ = (f - 1) % TOTAL, (f + 1) % TOTAL
            sp = abs(np.angle(np.exp(1j * (TH[i, fn_] - TH[i, fp])))) * FPS / 2
            if sp > 1.2: blit(c, SWING_GLOW, x, y, 1.0, skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=min(1, (sp - 1.2) / 9)))
            draw_needle(c, x, y, TH[i, f])
            blit(c, GLASS, x, y)
            if mark_odd and i == ODD:
                c.drawCircle(x, y, HR + 6, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(0, 1, 0, 1)))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def brass_tick(f0, dur=.09):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .5 * np.sin(2 * np.pi * f0 * 2.92 * t + 1) * np.exp(-t * 50)
         + .25 * np.sin(2 * np.pi * f0 * 5.4 * t) * np.exp(-t * 90)) * np.exp(-t * 42)
    return s * np.minimum(1, t * 6000)

def scrape(f0, dur=.26):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(int(f0)).standard_normal(len(t))
    n = sosfilt(butter(2, [f0 * .8, f0 * 2.4], btype="band", fs=SR, output="sos"), n)
    env = np.minimum(1, t / .05) * np.exp(-t * 14)
    tone = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 18) * .6
    return (n * 1.6 + tone) * env

def clack(dur=.25):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(9).standard_normal(len(t))
    hi = sosfilt(butter(2, [1800, 6000], btype="band", fs=SR, output="sos"), n) * np.exp(-t * 160)
    body = np.sin(2 * np.pi * 620 * t) * np.exp(-t * 55) + .5 * np.sin(2 * np.pi * 1530 * t) * np.exp(-t * 80)
    return (hi * .9 + body * .6) * np.minimum(1, t * 8000)

def audio(path):
    m = Mix(LOOP)
    # wrap helper: add, then fold the tail past LOOP back to the start
    def addw(sig, t0, g, x):
        t0 %= LOOP
        m.add(sig, t0, g, x)
        over = t0 + len(sig) / SR - LOOP
        if over > 0:
            k = int(round((LOOP - t0) * SR)); tail = sig[k:]
            m.add(tail, 0.0, g, x)
    for s in STEPS:
        addw(clack(), s + .02, .30, CX)
        addw(thud(70, .5), s + .02, .30, CX)
        addw(mallet(note(0, 130.81), .9, .4), s + STEP_DUR * .7, .05, CX)
    ticks = tick_times()
    # density normalise per step
    for tt, i, big, sw in ticks:
        cc = C[i]
        g = .055 * min(1, big / math.radians(45)) ** .7
        if i == ODD:
            addw(scrape(note(cc["turn"] - 1, 130.81) * 1.0), tt - .08, .16, cc["x"])
        else:
            f0 = note(cc["turn"] + 4, 261.63) * (1 + np.random.default_rng(i).uniform(-.006, .006))
            addw(brass_tick(f0), tt + np.random.default_rng(i * 7 + int(tt * 10)).uniform(0, .008), g, cc["x"])
    # soft circular air bed so it never goes dead
    n = m.N; rg = np.random.default_rng(4)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 450) / 380) ** 2) + .12 * np.exp(-((fr - 2600) / 1400) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("compasses", NC, "odd", ODD, C[ODD]["sec"], C[ODD]["turn"], round(C[ODD]["x"]), round(C[ODD]["y"]))
    print("seam diff (deg)", float(np.degrees(np.abs(np.angle(np.exp(1j * (TH[:, 0] - TH[:, -1] - (TH[:, -1] - TH[:, -2]))))).max())))
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f, mark_odd=os.environ.get("MARK") == "1").makeImageSnapshot().save(f"{OUT}/M_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "stats":
        pass
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_compasses.mp4"))
