"""No. 14 render — 'Every bead pushes / the others away.'
usage: python render_bloom.py preview 0,120,270   |   python render_bloom.py audio   |   python render_bloom.py full"""
import pickle, sys, math, os
import numpy as np, skia
from scipy.interpolate import PchipInterpolator
from kit import *

E = lambda k, d: float(os.environ.get(k, d))
d = pickle.load(open("bloom.pkl", "rb"))
TB, PHI, OFF, NEND = d["tb"].copy(), d["phi"], d["OFF"], d["NEND"]
TB[0] = -.22                     # the first bead is already welling up on frame 1
_lp = PchipInterpolator(d["KT"], np.log(d["KN"]))
def Ncont(t): return float(np.exp(_lp(min(max(t, 0.0), 40.0))))
CX, CY = 540.0, E("CY", 1010)
RMAX = E("RMAX", 418)            # outer bead edge in px once the disc is full
SMAX = E("SMAX", 68)             # px per spacing unit while the disc is still small
BRW = .79                        # bead radius in spacing units (nn spacing is 1.633)
T_END = TB[-1]                   # last bead
GL0, GL1 = T_END + .45, T_END + 2.35     # glint runs out along the spiral arms
NF = int((GL1 + .55) * FPS)
HOLD, CARD, XF = 18, 60, 18
TOTAL = NF + HOLD + CARD + XF
ARMS = int(E("ARMS", 34))
MILES = [10, 100, 1000]
MILE_T = [float(TB[m - 1]) for m in MILES]
print("NF", NF, "TOTAL", TOTAL, round(TOTAL / FPS, 2), "milestones", [round(x, 2) for x in MILE_T], "end", round(T_END, 2))

def scale(N): return min(SMAX, RMAX / (math.sqrt(N - 1 + OFF) + BRW))

# colours: hue follows the landing direction (a rainbow wheel the spirals cut through),
# warming slightly as each bead glides outward
LV = 60
def bead_col(k):
    return hsv(k / LV * 360 + 200, .58, 1.0)
TWIST = E("TWIST", 140)          # degrees of hue shift from the first bead to the last: the wheel twists as it grows
HUE = ((PHI / (2 * math.pi) + TWIST / 360 * (np.arange(NEND) / NEND) ** .7) * LV).astype(int) % LV
SPR_B = [glass_ball(bead_col(k), 60) for k in range(LV)]
SPR_S = [glass_ball(bead_col(k), 10) for k in range(LV)]
BG = background(CY)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .38))
GLW = glow((1, .96, .86), 20, .9)
POOL = None

def positions(t):
    N = Ncont(t); n = int(np.searchsorted(TB, t, side="right"))
    i = np.arange(n)
    rk = np.sqrt(np.maximum(N - 1 - i, 0) + OFF)
    s = scale(N)
    x = CX + s * rk * np.cos(PHI[:n]); y = CY + s * rk * np.sin(PHI[:n])
    age = t - TB[:n]
    pop = np.clip(age / .16, 0, 1); pop = pop * pop * (3 - 2 * pop)
    rad = s * BRW * (.25 + .75 * pop)
    return x, y, rad, s, N, n

def glint_amp(t, n):
    """glint travelling out along each of ARMS spiral arms, one arm after another (rainbow order)"""
    if not (GL0 <= t <= GL1 + .4): return None
    u = (t - GL0) / (GL1 - GL0)
    i = np.arange(n); arm = (i % ARMS); rank = (n - 1 - i)
    # arm a lights at u_a = a/ARMS*0.6, the light runs from centre to rim in 0.4 of the sweep
    ua = arm / ARMS * .6
    front = (u - ua) / .4                     # 0 at centre .. 1 at rim
    rr = np.sqrt(rank / max(1, n - 1))
    g = np.exp(-((rr - front) / .07) ** 2) * (front > -.1) * (front < 1.15)
    return g

def frame(f, first=[None]):
    t = min(f, NF - 1) / FPS
    x, y, rad, s, N, n = positions(t)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        R = s * (math.sqrt(N - 1 + OFF) + BRW)
        # a soft warm pool of light under the bloom
        c.drawCircle(CX, CY, R + 70, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX, CY), R + 70, [skia.Color4f(1, .9, .75, .07).toColor(), skia.Color4f(1, .9, .75, .03).toColor(),
                               skia.Color4f(1, .9, .75, 0).toColor()], [0, .7, 1])))
        # ripples where the newest beads well up
        act = int(np.sum(TB[max(0, n - 300):n] > t - .9))      # many ripples at once -> each one fainter
        for j in range(max(0, n - 12), n):
            age = t - TB[j]
            if age > .9: continue
            age += 0 * act
            rr = s * (math.sqrt(OFF) + .3 + 2.6 * age) + 6 * age
            a = .30 * (1 - age / .9) ** 2 / max(1, act) ** .65
            c.drawCircle(CX, CY, rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6,
                         Color4f=skia.Color4f(1, .95, .85, a)))
        sh = max(1.0, s * .12)
        for k in range(n):
            c.drawCircle(float(x[k]) + sh * .6, float(y[k]) + sh, float(rad[k]), SH)
        big = s * BRW > 14
        for k in range(n):
            spr = (SPR_B if rad[k] > 14 else SPR_S)[HUE[k]]
            blit(c, spr, float(x[k]), float(y[k]), float(rad[k]) / (60 if rad[k] > 14 else 10))
        # newborn glint
        for j in range(max(0, n - 6), n):
            age = t - TB[j]
            if age < .35:
                blit(c, GLW, float(x[j]), float(y[j]), max(.25, rad[j] / 18), skia.Paint(Alphaf=.55 * (1 - age / .35), BlendMode=skia.BlendMode.kPlus))
        g = glint_amp(t, n)
        # each rung of the ladder: a soft ring of light glides out across the bloom
        for mt in MILE_T:
            u = (t - mt) / .9
            if 0 <= u <= 1:
                rr = np.sqrt(np.maximum(N - 1 - np.arange(n), 0) / max(1, N))
                gm = .6 * np.exp(-((rr - u * 1.05) / .08) ** 2) * (1 - u) ** .5
                g = gm if g is None else np.maximum(g, gm)
        if g is not None:
            for k in np.nonzero(g > .04)[0]:
                blit(c, GLW, float(x[k]), float(y[k]), max(.3, rad[k] / 14), skia.Paint(Alphaf=float(.75 * g[k]), BlendMode=skia.BlendMode.kPlus))
        pulse = 0.0
        for mt in MILE_T + [T_END]:
            if 0 <= t - mt < .5: pulse = max(pulse, (1 - (t - mt) / .5) ** 2)
        header(c, "Every bead pushes", "the others away.", count=int(math.floor(N + 1e-6)) if t < T_END else NEND,
               count_col=CREAM, pulse=pulse)
        watermark(c, 1585)
        if f >= NF + HOLD:
            a = ss((f - NF - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF and first[0] is not None:
            c.drawImage(first[0], 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first[0] = out.makeImageSnapshot()
    return out

def audio(path):
    m = Mix(TOTAL / FPS + .5)
    rng = np.random.default_rng(14)
    # 1) each bead welling up: a soft water plip + a small glass bell, pitch by landing direction (pentatonic)
    bells = {k: mallet(note(k, 523.25), 1.6, .8) for k in range(10)}
    short = {k: [glass_click(note(k, 698.46) * rng.uniform(.995, 1.005), rng.uniform(70, 110), .25, .12) for _ in range(3)] for k in range(10)}
    def plip(f0):
        tt = np.arange(int(.09 * SR)) / SR
        return np.sin(2 * np.pi * (f0 * tt + 900 * tt * tt)) * np.exp(-tt * 55) * np.minimum(1, tt * 3000)
    plips = [plip(rng.uniform(520, 760)) for _ in range(12)]
    ticks = [glass_click(rng.uniform(2200, 3300), rng.uniform(220, 320), .04, .3) for _ in range(24)]
    byf = {}
    for i, tb in enumerate(TB):
        byf.setdefault(int(tb * FPS), []).append(i)
    for f, ids in byf.items():
        tt = f / FPS; rate = max(1.0, (Ncont(tt + .25) - Ncont(tt - .25)) / .5)     # beads per second right now
        voiced = ids if len(ids) <= 3 else list(rng.choice(ids, 3, replace=False))
        vr = min(rate, 3 * FPS)                                   # voiced events per second
        g = .30 / max(1, vr / 1.5) ** .5 * (1 if rate < 25 else float(os.environ.get('CK', 4.4)))
        for i in voiced:
            k = int((PHI[i] / (2 * math.pi)) * 10) % 10
            pan = 540 + 380 * math.cos(PHI[i])
            if rate < 25:
                m.add(bells[k], TB[i], g, pan); m.add(plips[rng.integers(12)], TB[i], g * .45, pan)
            else:
                m.add(short[k][rng.integers(3)], TB[i] + rng.uniform(0, .02), g, pan)
        # the crowd being nudged outward: a fine glassy patter that thickens with the flow
        if rate >= 25:
            for _ in range(min(6, len(ids) // 3 + 1)):
                m.add(ticks[rng.integers(24)], f / FPS + rng.uniform(0, 1 / FPS), .018, 540 + rng.uniform(-400, 400))
    # 2) each rung of the ladder: soft low thump + a chord
    chords = [[0, 2, 4], [2, 4, 7], [4, 7, 9]]
    for mt, ch in zip(MILE_T, chords):
        m.add(thud(56, .7), mt, .17, 540)
        for j, nn in enumerate(ch):
            m.add(mallet(note(nn, 261.63), 2.4, .6), mt + j * .05, .075, 540 + (j - 1) * 160)
    m.add(thud(48, .9), T_END, .2, 540)
    # 3) the glint runs out along the arms: one rising pentatonic tick per arm
    for a in range(ARMS):
        ta = GL0 + (GL1 - GL0) * (a / ARMS * .6 + .15)
        ang = PHI[(NEND - 1 - a)] if a < NEND else 0
        m.add(mallet(note(a % 15, 523.25), .7, .5), ta, .035, 540 + 380 * math.cos(ang))
    tc = (NF + HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63 / 2), 3.0, .5), tc + i * .08, .11, 540 + (i - 1.5) * 110)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        frame(0)
        for f in [int(v) for v in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print(audio("A.wav"))
    else:
        import time; t0 = time.time()
        w = Writer("A_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
            if f % 60 == 0: print(f, round(time.time() - t0), flush=True)
        print("video", w.close(), "frames", TOTAL)
        print(audio("A.wav"))
        print("mux", mux("A_silent.mp4", "A.wav", "bloom.mp4"))
