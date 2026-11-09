"""'Every ball moves in a straight line.'  Escalation ladder 2 → 8 → 64 → 512 → 4,096.
Ball i slides on its own diameter at angle θ_i: p = R·cos(ωt − k·θ_i)·(cosθ_i, sinθ_i).
Together they trace a rolling circle (k=1), then rotating roses (k=3, 5, 7)."""
import sys, math
import numpy as np, skia
from kit import *

CX, CY, R = 540.0, 1000.0, 372.0
NMAX = 4096
TH = np.pi * np.arange(NMAX) / NMAX
PERIOD = 2.4
OM = 2 * math.pi / PERIOD
STAGES = [(2, 1), (8, 1), (64, 1), (512, 3), (4096, 5)]
SLEN = [84, 114, 132, 140, 180]
SSTART = [sum(SLEN[:i]) for i in range(len(SLEN))]
ACTION = sum(SLEN)
STAGE = 132
HOLD, CARD, XF = 12, 66, 18
TOTAL = ACTION + HOLD + CARD + XF
RAD = {2: 21, 8: 15, 64: 9.5, 512: 5.2, 4096: 2.5}
LA = {2: .26, 8: .2, 64: .11, 512: .05, 4096: .022}

def stage_at(f):
    s = 0
    for i, st in enumerate(SSTART):
        if f >= st: s = i
    return s, f - SSTART[s]
def k_at(f):
    s, u = stage_at(min(f, ACTION - 1))
    k_prev = STAGES[s - 1][1] if s > 0 else STAGES[0][1]
    k_now = STAGES[s][1]
    if s == len(STAGES) - 1 and u > 95:                   # last stage: 5 → 7
        return k_now + 2 * ss((u - 95) / 34)
    return k_prev + (k_now - k_prev) * ss(u / 30)
def t_of(f): return min(f, ACTION + HOLD) / FPS
def phase(f, idx):
    return OM * t_of(f) - k_at(f) * TH[idx]

HUE = (TH / np.pi * 360 + 20) % 360
LEVELS = 48
def hidx(h): return (h / 360 * LEVELS).astype(int) % LEVELS
SPR = {n: [glass_ball(hsv(i * 360 / LEVELS + 4, .5, 1.0), RAD[n]) for i in range(LEVELS)] for n in RAD}
GLW = {n: glow((1, .9, .75), RAD[n] * 1.3, .5) for n in RAD}
BG = background(CY)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35))
first = None

def active(f):
    s, u = stage_at(min(f, ACTION - 1))
    n = STAGES[s][0]; step = NMAX // n
    idx = np.arange(0, NMAX, step)
    born = np.zeros(len(idx))
    if s > 0:
        nprev = STAGES[s - 1][0]; pstep = NMAX // nprev
        new = (idx % pstep) != 0
        born[new] = min(1.0, u / 18)
        born[~new] = 1.0
    else:
        born[:] = min(1.0, (f + 6) / 10)
    return n, idx, born, s, u

def frame(f):
    global first
    n, idx, born, s, u = active(f)
    nprev = STAGES[s - 1][0] if s > 0 else n
    grow = ss(u / 24)
    rad_now = RAD[nprev] + (RAD[n] - RAD[nprev]) * grow
    la = LA[nprev] + (LA[n] - LA[nprev]) * grow
    ph = phase(f, idx)
    r = R * np.cos(ph)
    cx, cy = np.cos(TH[idx]), np.sin(TH[idx])
    x = CX + r * cx; y = CY + r * cy
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.drawCircle(CX, CY, R + 30, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX - 110, CY - 150), R * 1.5, [skia.Color(33, 27, 22), skia.Color(18, 15, 12)])))
        # rails
        lp = skia.Paint(AntiAlias=True, StrokeWidth=1.3 if n < 512 else 1.0)
        for j in range(len(idx)):
            a = la * born[j]
            if a <= .003: continue
            hcol = hsv(HUE[idx[j]], .35, 1.0)
            lp.setColor4f(skia.Color4f(*hcol, a))
            ex, ey = (R + 8) * cx[j], (R + 8) * cy[j]
            c.drawLine(CX - ex, CY - ey, CX + ex, CY + ey, lp)
        # ring
        c.drawCircle(CX, CY, R + 30, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                     Color4f=skia.Color4f(*CREAM, .3)))
        # balls
        scale_r = rad_now / RAD[n]
        for j in range(len(idx)):
            b = born[j]
            if b <= 0: continue
            if n <= 64:
                c.drawCircle(float(x[j]) + rad_now * .15, float(y[j]) + rad_now * .25, rad_now, SH)
            sc = scale_r * (b if b < 1 else 1) * (1 + .5 * (1 - b) if b < 1 else 1)
            blit(c, SPR[n][hidx(HUE[idx[j:j + 1]])[0]], float(x[j]), float(y[j]), sc)
        # soft glow at turning points (where |cos| ~ 1)
        if n <= 512:
            near = np.nonzero(np.abs(np.cos(ph)) > .985)[0]
            for j in near[:200]:
                blit(c, GLW[n], float(x[j]), float(y[j]), 1.0, skia.Paint(Alphaf=.35, BlendMode=skia.BlendMode.kPlus))
        pulse = math.exp(-u / 6) if s > 0 and f < ACTION else 0
        header(c, "Every ball moves", "in a straight line.", count=n, pulse=pulse)
        watermark(c, 1600)
        if f >= ACTION + HOLD:
            a = ss((f - ACTION - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

def audio(path):
    m = Mix(TOTAL / FPS + .5)
    rng = np.random.default_rng(4)
    cache = {}
    def tick(step, bright):
        key = (step, bright)
        if key not in cache:
            f0 = note(step, 261.63)
            t = np.arange(int(.7 * SR)) / SR
            s = (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 6) + .35 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 14)
                 + .12 * np.sin(2 * np.pi * f0 * 5.4 * t) * np.exp(-t * 30))
            nn = rng.standard_normal(len(t)) * np.exp(-t * 1800) * .18 * bright
            cache[key] = (s + np.diff(nn, prepend=0)) * np.minimum(1, t * 5000)
        return cache[key]
    SUBS = 4
    for f in range(ACTION + HOLD):
        n, idx, born, s, u = active(min(f, ACTION - 1))
        for q in range(SUBS):
            t0 = (f + q / SUBS) / FPS; t1 = (f + (q + 1) / SUBS) / FPS
            k = k_at(f)
            p0 = OM * t0 - k * TH[idx]; p1 = OM * t1 - k * TH[idx]
            # turning point when phase crosses a multiple of pi
            hits = np.nonzero(np.floor(p0 / np.pi) != np.floor(p1 / np.pi))[0]
            if len(hits) == 0: continue
            cap = 5 if n >= 4096 else 3
            if len(hits) > cap: hits = hits[np.linspace(0, len(hits) - 1, cap).astype(int)]
            for j in hits:
                side = 1 if math.cos(p1[j]) > 0 else -1
                x = CX + side * R * math.cos(TH[idx[j]])
                step = int(round((TH[idx[j]] / np.pi) * 9)) % 10
                g = {2: .75, 8: .5, 64: .3, 512: .26, 4096: .26}[n] * born[j]
                m.add(tick(step, 1.0 if n <= 64 else .5), t0, g, x)
    # stage changes: soft thump + chord
    for s in range(1, len(STAGES)):
        t0 = SSTART[s] / FPS
        m.add(thud(55, .6), t0, .35, 540)
        for i, nn in enumerate([0, 2, 4]):
            m.add(mallet(note(nn + s, 196.0), 2.2, .45), t0 + i * .05, .07, 540 + (i - 1) * 140)
    # shimmer bed grows with the count
    tt = np.arange(m.N) / SR
    env = np.interp(tt, [0, SSTART[2] / FPS, SSTART[3] / FPS, SSTART[4] / FPS, ACTION / FPS, (ACTION + HOLD) / FPS + .5, tt[-1]],
                    [0, 0, .25, .55, 1.0, .0, 0])
    from scipy.signal import butter, sosfilt
    bed = sosfilt(butter(2, [3000, 9000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, m.N)), axis=1)
    m.L += bed[0] * env * .045; m.R += bed[1] * env * .045
    tc = (ACTION + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63), 3.0, .5), tc + i * .06, .14, 540 + (i - 1.5) * 90)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        frame(0)
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("glide_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), TOTAL, "frames", TOTAL / FPS, "s")
        print(audio("glide.wav"))
        print("mux", mux("glide_silent.mp4", "glide.wav", "straight_lines.mp4"))
