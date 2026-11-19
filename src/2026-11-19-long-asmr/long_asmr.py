"""YouTube LONG-FORM test (owner 2026-11-19: "try some Physics ASMR long videos on youtube").
10 minutes, landscape 1920x1080, no talking, no puzzles, no balls. Four calm scenes (150 s each, 2 s crossfades):
  1. Pendulum wave      - 24 brass lens bobs, pendulum i swings 51+i times per 60 s -> snakes, chaos, re-unison
  2. Metronomes         - 16 metronomes on two sliding shelves; Kuramoto coupling pulls a rain of ticks into one beat
  3. Sand pendulum      - a damped harmonograph pouring a fine sand line on slate; the rosette slowly precesses
  4. Wave machine       - 72 brass rods on a torsion spine; pulses travel, reflect and interfere (1D wave equation)
Each scene's sound comes from its own events (kit.Mix), rendered per scene and crossfaded.
Usage: python long_asmr.py preview <sec,sec,...> OUT | render OUT | audio OUT"""
import sys, os, math, wave, subprocess
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
import kit as K
K.W, K.H = 1920, 1080
K.INFO = skia.ImageInfo.Make(1920, 1080, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
W, H, FPS, SR = 1920, 1080, 30, 48000
INFO = K.INFO
SC = 150.0                       # seconds per scene
XF = 2.0                         # crossfade
NS = 4
TOTAL_S = NS * SC
TOTAL = int(TOTAL_S * FPS)
CREAM, AMBER = K.CREAM, K.AMBER
BG = K.background(540)

def c4(rgb, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in rgb], a)
def col(rgb, a=1.0): return c4(rgb, a).toColor()
F_CAP = K.font(K.TF_SERIF_I, 44); F_SUB = K.font(K.TF_SEMI, 22); F_MARK = K.font(K.TF_SERIF_I, 30)
F_BIG = K.font(K.TF_SERIF, 76); F_BIGI = K.font(K.TF_SERIF_I, 76)

# =============================== 1. PENDULUM WAVE ===============================
PN, PT, PN0 = 24, 60.0, 51
P_X = np.linspace(330, 1590, PN)
P_RAIL = 250
P_REST = np.linspace(700, 560, PN)          # longest (slowest, i=0) hangs lowest
P_AMP = 150
def p_phase(i, t): return 2 * math.pi * (PN0 + i) * t / PT
def p_disp(i, t): return math.cos(p_phase(i, t))
def lens_sprite(rgb, w=50, h=34):
    sz = int(w + 12)
    def fn(c):
        cx, cy = sz / 2, sz / 2
        r = skia.Rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        light = tuple(min(1, x * .45 + .6) for x in rgb); dark = tuple(x * .4 for x in rgb)
        sh = skia.GradientShader.MakeLinear([(cx, cy - h / 2), (cx, cy + h / 2)], [col(light), col(rgb), col(dark)], [0, .45, 1])
        c.drawOval(r, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawOval(skia.Rect(cx - w * .32, cy - h * .38, cx + w * .12, cy - h * .12), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .55)))
    return K.sprite(fn, sz)
P_HUES = 48
P_SPR = [lens_sprite(K.hsv(32 + 40 * math.sin(2 * math.pi * k / P_HUES), .55, 1.0)) for k in range(P_HUES)]
P_GLOW = K.glow((1, .8, .5), 20, .35)

def draw_pendulums(c, t):
    # rail + posts
    p = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap, StrokeWidth=12)
    p.setShader(skia.GradientShader.MakeLinear([(0, P_RAIL - 6), (0, P_RAIL + 6)], [col((.98, .8, .5)), col((.5, .35, .18))]))
    c.drawLine(P_X[0] - 70, P_RAIL, P_X[-1] + 70, P_RAIL, p)
    for x in (P_X[0] - 60, P_X[-1] + 60):
        q = skia.Paint(AntiAlias=True, StrokeWidth=10, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.45, .32, .18)))
        c.drawLine(x, P_RAIL, x, 960, q)
    # soft floor shadow band
    c.drawRect(skia.Rect(0, 880, W, 1080), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 880), (0, 1080)], [col((0, 0, 0), 0), col((0, 0, 0), .35)])))
    st = skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color4f=skia.Color4f(.92, .82, .66, .5))
    for i in range(PN):
        d = p_disp(i, t)
        bx = P_X[i] + 18 * d
        by = P_REST[i] + P_AMP * d
        rel = ((i * t / PT) % 1.0)
        c.drawLine(P_X[i], P_RAIL, bx, by, st)
        # floor shadow
        c.drawOval(skia.Rect(bx - 26, 925 + 40 * d - 6, bx + 26, 925 + 40 * d + 6), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        hi = int(rel * P_HUES) % P_HUES
        K.blit(c, P_GLOW, bx, by, 1.2, skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=.25))
        K.blit(c, P_SPR[hi], bx, by)
        c.drawCircle(P_X[i], P_RAIL, 5, skia.Paint(AntiAlias=True, Color4f=c4((.95, .78, .5))))

def audio_pendulums():
    m = K.Mix(SC + XF)
    rng = np.random.default_rng(7)
    ticks = [K.glass_click(K.note(i // 2 + 2, 220) * 2, 95, .08, .2) for i in range(PN)]
    ev = []
    for i in range(PN):
        n = PN0 + i                                  # turning points: phase = k*pi
        for k in range(int(2 * n * (SC + XF) / PT) + 2):
            tt = k * PT / (2 * n)
            if tt < SC + XF: ev.append((tt, i))
    ev.sort(); times = np.array([e[0] for e in ev])
    for tt, i in ev:
        dens = ((times > tt - .02) & (times < tt + .02)).sum()
        m.add(ticks[i], tt + rng.uniform(0, .003), .16 / math.sqrt(dens), 540 + (P_X[i] - 960) * .45)
    for kk in range(1, 3):                           # unison chords at 60 s and 120 s
        for j, f0 in enumerate([K.note(5, 220), K.note(7, 220), K.note(9, 220)]):
            m.add(K.mallet(f0, 2.6, .7), kk * PT + .02 * j, .09, 540)
    return m

# =============================== 2. METRONOMES ===============================
MN = 16
mrng = np.random.default_rng(11)
M_OM = 2 * math.pi * 1.1 * (1 + .025 * mrng.standard_normal(MN))
M_TH0 = mrng.uniform(0, 2 * math.pi, MN)
def m_sim():
    dt = 1 / (FPS * 8); n = int((SC + XF) * FPS * 8)
    th = M_TH0.copy(); out = np.zeros((int((SC + XF) * FPS) + 1, MN)); ticks = []
    prev = np.sin(th)
    for k in range(n):
        t = k * dt
        K_ = 1.1 * min(1.0, t / 95.0) ** 1.6       # coupling grows as the shelves start to rock
        z = np.exp(1j * th).mean()
        th = th + dt * (M_OM + K_ * np.abs(z) * np.sin(np.angle(z) - th))
        s = np.sin(th)
        for i in np.where(np.sign(s) != np.sign(prev))[0]: ticks.append((t, i))
        prev = s
        if k % 8 == 0: out[k // 8] = th
    return out, ticks
M_PH, M_TICKS = m_sim()
M_POS = [(330 + 180 * (i % 8), 470 if i < 8 else 880) for i in range(MN)]

def draw_metronome(c, x, y, ang):
    # walnut pyramid body
    body = skia.Path(); body.moveTo(x - 62, y); body.lineTo(x + 62, y); body.lineTo(x + 26, y - 250); body.lineTo(x - 26, y - 250); body.close()
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - 62, 0), (x + 62, 0)],
               [col((.42, .25, .14)), col((.62, .40, .23)), col((.30, .18, .10))], [0, .45, 1])))
    face = skia.Path(); face.moveTo(x - 30, y - 30); face.lineTo(x + 30, y - 30); face.lineTo(x + 13, y - 225); face.lineTo(x - 13, y - 225); face.close()
    c.drawPath(face, skia.Paint(AntiAlias=True, Color4f=c4((.93, .87, .74), .9)))
    for k in range(-3, 4):
        a = math.radians(k * 7)
        c.drawLine(x + math.sin(a) * 150, y - 45 - math.cos(a) * 150, x + math.sin(a) * 160, y - 45 - math.cos(a) * 160,
                   skia.Paint(AntiAlias=True, StrokeWidth=1.4, Color4f=c4((.3, .2, .12), .6)))
    px, py = x, y - 45
    ex, ey = px + math.sin(ang) * 175, py - math.cos(ang) * 175
    c.drawLine(px, py, ex, ey, skia.Paint(AntiAlias=True, StrokeWidth=3.4, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.72, .55, .3))))
    wx, wy = px + math.sin(ang) * 120, py - math.cos(ang) * 120
    c.save(); c.translate(wx, wy); c.rotate(math.degrees(ang))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-11, -9, 11, 9), 3, 3), skia.Paint(AntiAlias=True,
                Shader=skia.GradientShader.MakeLinear([(-11, 0), (11, 0)], [col((1, .86, .55)), col((.6, .42, .2))])))
    c.restore()
    c.drawCircle(px, py, 6, skia.Paint(AntiAlias=True, Color4f=c4((.85, .66, .38))))

def draw_metronomes(c, t):
    fi = min(int(t * FPS), len(M_PH) - 1)
    th = M_PH[fi]
    ang = .42 * np.sin(th)
    shift = -9.0 * np.sin(th).mean() * min(1.0, t / 95.0)
    for row, y in ((0, 470), (1, 880)):
        sx = shift * (1 if row == 0 else -1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(190 + sx, y, 1730 + sx, y + 26), 6, 6), skia.Paint(AntiAlias=True,
                    Shader=skia.GradientShader.MakeLinear([(0, y), (0, y + 26)], [col((.55, .36, .2)), col((.28, .17, .09))])))
        for rx in (300, 960, 1620):
            c.drawCircle(rx + sx * .3, y + 40, 13, skia.Paint(AntiAlias=True, Color4f=c4((.35, .26, .16))))
        c.drawRect(skia.Rect(150, y + 52, 1770, y + 58), skia.Paint(Color4f=c4((.2, .14, .09), .9)))
    for i in range(MN):
        x, y = M_POS[i]
        draw_metronome(c, x + shift * (1 if i < 8 else -1), y, ang[i])

def audio_metronomes():
    m = K.Mix(SC + XF)
    tk = [K.glass_click(1150 + 45 * (i % 8), 230, .06, .55) for i in range(MN)]
    times = np.array([e[0] for e in M_TICKS])
    for tt, i in M_TICKS:
        dens = ((times > tt - .015) & (times < tt + .015)).sum()
        m.add(tk[i] + .5 * K.thud(140, .06), tt, .32 / math.sqrt(dens), 540 + (M_POS[i][0] - 960) * .45)
    return m

# =============================== 3. SAND PENDULUM ===============================
S_CX, S_CY = 960, 560
def s_pos(t):
    """damped 3:2 harmonograph, slightly detuned so the lobes slowly precess; spirals inward over the scene."""
    e = math.exp(-t / 95.0)
    x = e * 360 * math.sin(2 * math.pi * .40 * t + .4)
    y = e * 360 * math.sin(2 * math.pi * .6012 * t + 1.3) * .95 + e * 30 * math.sin(2 * math.pi * .40 * t)
    return S_CX + x, S_CY + y
SAND = {"surf": None, "last": -1}
def sand_layer(t):
    """persistent sand trace; deterministic for any t (re-draws from 0 when asked to go back)."""
    target = int(t * FPS * 3)
    if SAND["surf"] is None or target < SAND["last"]:
        SAND["surf"] = skia.Surface.MakeRaster(INFO)
        with SAND["surf"] as c: c.clear(skia.Color4f(0, 0, 0, 0))
        SAND["last"] = 0
    p = skia.Paint(AntiAlias=True, StrokeWidth=1.5, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.95, .84, .64), .38))
    with SAND["surf"] as c:
        for k in range(SAND["last"], target):
            a = s_pos(k / (FPS * 3)); b = s_pos((k + 1) / (FPS * 3))
            c.drawLine(a[0], a[1], b[0], b[1], p)
    SAND["last"] = target
    return SAND["surf"].makeImageSnapshot()
SLATE = None
def slate():
    global SLATE
    if SLATE is None:
        s = skia.Surface.MakeRaster(INFO)
        with s as c:
            c.drawImage(BG, 0, 0)
            r = skia.RRect.MakeRectXY(skia.Rect(440, 120, 1480, 1000), 30, 30)
            c.drawRRect(r.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
            c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((960, 540), 700,
                        [col((.16, .16, .17)), col((.08, .08, .09))])))
            c.drawRRect(r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                        Shader=skia.GradientShader.MakeLinear([(440, 120), (1480, 1000)], [col((.6, .4, .22)), col((.32, .2, .11)), col((.55, .36, .2))])))
        SLATE = s.makeImageSnapshot()
    return SLATE
FUNNEL = None
def draw_sand(c, t):
    c.drawImage(slate(), 0, 0)
    c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(445, 125, 1475, 995), 26, 26), skia.ClipOp.kIntersect, True)
    c.drawImage(sand_layer(t), 0, 0)
    c.restore()
    x, y = s_pos(t)
    # cord from the pivot far above + the brass funnel
    c.drawLine(960, -40, x, y - 70, skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color4f=skia.Color4f(.9, .8, .62, .45)))
    cone = skia.Path(); cone.moveTo(x - 34, y - 78); cone.lineTo(x + 34, y - 78); cone.lineTo(x + 4, y - 8); cone.lineTo(x - 4, y - 8); cone.close()
    c.drawPath(cone, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - 34, 0), (x + 34, 0)],
               [col((1, .86, .55)), col((.75, .55, .3)), col((.45, .3, .15))], [0, .4, 1])))
    c.drawOval(skia.Rect(x - 34, y - 84, x + 34, y - 72), skia.Paint(AntiAlias=True, Color4f=c4((.35, .24, .12))))
    c.drawLine(x, y - 8, x, y, skia.Paint(AntiAlias=True, StrokeWidth=2, Color4f=c4((.95, .85, .65), .8)))
    c.drawCircle(x, y, 4, skia.Paint(AntiAlias=True, Color4f=c4((1, .9, .7), .6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))

def audio_sand():
    m = K.Mix(SC + XF)
    rng = np.random.default_rng(3)
    from scipy.signal import butter, sosfilt
    n = int((SC + XF) * SR)
    noise = sosfilt(butter(2, [1800, 7500], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    grains = (rng.random(n) < .004) * rng.standard_normal(n) * 2.5
    grains = sosfilt(butter(2, [3000, 9000], btype="band", fs=SR, output="sos"), grains)
    t = np.arange(n) / SR
    tt = np.arange(0, SC + XF, .05)
    sp = np.array([math.hypot(*(np.subtract(s_pos(a + .01), s_pos(a)))) for a in tt]) / .01
    env = np.interp(t, tt, sp); env = env / env.max()
    xs = np.interp(t, tt, np.array([s_pos(a)[0] for a in tt]))
    pan = np.clip((xs - 960) / 600, -.9, .9)
    sig = (noise * .5 + grains) * (.25 + .75 * env)
    m.L += sig * np.cos((pan + 1) * math.pi / 4) * .08
    m.R += sig * np.sin((pan + 1) * math.pi / 4) * .08
    # a soft low wooden note each time the funnel passes the top of its loop (every ~2.4 s), pentatonic walk
    k = 0
    for a in tt[1:]:
        y0, y1 = s_pos(a - .05)[1], s_pos(a)[1]
        if y0 > S_CY > y1 or (y1 < y0 and s_pos(a + .05)[1] > y1 and y1 < S_CY - 150):
            m.add(K.mallet(K.note([0, 2, 4, 2, 5, 4, 2, 1][k % 8], 196), 2.2, .35), a, .07, 540 + (s_pos(a)[0] - 960) * .45); k += 1
    return m

# =============================== 4. WAVE MACHINE ===============================
WN = 72
W_X = np.linspace(230, 1690, WN)
W_Y = 560
W_L = 250
def w_sim():
    dt = 1 / (FPS * 6); n = int((SC + XF) * FPS * 6)
    phi = np.zeros(WN); v = np.zeros(WN); out = np.zeros((int((SC + XF) * FPS) + 1, WN)); kicks = []
    c2 = 900.0; gam = .07
    rng = np.random.default_rng(5)
    nxt = 0.0
    for k in range(n):
        t = k * dt
        if t >= nxt:
            kicks.append((t, rng.uniform(.7, 1.15), rng.random() < .3))
            nxt = t + rng.uniform(3.0, 5.0)
        lap = np.zeros(WN); lap[1:-1] = phi[2:] - 2 * phi[1:-1] + phi[:-2]
        lap[0] = phi[1] - phi[0]; lap[-1] = phi[-2] - phi[-1]
        drive = .75 * math.sin(2 * math.pi * .32 * t) * (.6 + .4 * math.sin(2 * math.pi * t / 37.0))
        for (tk, amp, both) in kicks[-2:]:
            u = t - tk
            if 0 <= u < 1.6: drive += amp * 1.35 * math.sin(math.pi * u / 1.6) ** 2 * math.sin(2 * math.pi * .62 * u)
        a = c2 * lap / 25 - gam * v - .04 * phi
        v += dt * a; phi += dt * v
        phi[0] = drive
        if kicks and kicks[-1][2] and t - kicks[-1][0] < 1.6:
            u = t - kicks[-1][0]; phi[-1] = .85 * math.sin(math.pi * u / 1.6) ** 2 * math.sin(2 * math.pi * .62 * u + 1)
        if k % 6 == 0: out[k // 6] = phi
    return out, kicks
W_PHI, W_KICKS = w_sim()
def draw_wave(c, t):
    fi = min(int(t * FPS), len(W_PHI) - 1)
    phi = W_PHI[fi]
    # spine
    c.drawLine(W_X[0] - 40, W_Y, W_X[-1] + 40, W_Y, skia.Paint(AntiAlias=True, StrokeWidth=6, Color4f=c4((.55, .4, .24))))
    for x in (W_X[0] - 40, W_X[-1] + 40):
        c.drawRect(skia.Rect(x - 10, W_Y - 30, x + 10, 960), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                   [(x - 10, 0), (x + 10, 0)], [col((.5, .32, .18)), col((.3, .19, .1))])))
    order = np.argsort(np.sin(phi))                    # far ends first
    for i in range(WN):
        ph = phi[i]
        dy = W_L * math.cos(ph); depth = math.sin(ph)
        x = W_X[i]
        br = .55 + .45 * (1 - abs(depth))
        p = skia.Paint(AntiAlias=True, StrokeWidth=4.2, StrokeCap=skia.Paint.kRound_Cap,
                       Shader=skia.GradientShader.MakeLinear([(x, W_Y - dy), (x, W_Y + dy)],
                       [col((1 * br, .82 * br, .52 * br)), col((.55 * br, .4 * br, .22 * br)), col((1 * br, .82 * br, .52 * br))], [0, .5, 1]))
        c.drawLine(x + depth * 46, W_Y - dy, x - depth * 46, W_Y + dy, p)
        for sgn in (1, -1):
            ex, ey = x + sgn * depth * 46, W_Y - sgn * dy
            c.drawCircle(ex, ey, 7 + 2 * sgn * depth, skia.Paint(AntiAlias=True, Color4f=c4((.95 * br, .74 * br, .42 * br))))
    c.drawRect(skia.Rect(0, 900, W, 1080), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 900), (0, 1080)], [col((0, 0, 0), 0), col((0, 0, 0), .35)])))

def audio_wave():
    m = K.Mix(SC + XF)
    from scipy.signal import butter, sosfilt
    n = int((SC + XF) * SR); rg = np.random.default_rng(4)
    bed = sosfilt(butter(2, [180, 900], btype="band", fs=SR, output="sos"), rg.standard_normal(n))
    sw = .6 + .4 * np.sin(2 * np.pi * .32 * np.arange(n) / SR)
    m.L += bed * sw * .05; m.R += np.roll(bed, 4000) * sw * .05
    for (tk, amp, both) in W_KICKS:
        m.add(K.mallet(K.note(int(amp * 6) % 5 + 3, 196), 2.4, .5), tk + .3, .12, 300)
        m.add(K.thud(70, .5), tk + .3, .12, 300)
        if both: m.add(K.mallet(K.note(int(amp * 6) % 5 + 5, 196), 2.4, .5), tk + .3, .1, 1700)
    # a faint tick whenever a rod flips through face-on fast (density-limited)
    rng = np.random.default_rng(8)
    tick = K.glass_click(2400, 160, .05, .3)
    prev = np.cos(W_PHI[0])
    for f in range(1, len(W_PHI)):
        cur = np.cos(W_PHI[f])
        crossed = np.where((np.sign(cur - .98) != np.sign(prev - .98)))[0]
        for i in crossed[:4]:
            m.add(tick, f / FPS + rng.uniform(0, .02), .07, 540 + (W_X[i] - 960) * .45)
        prev = cur
    return m

# =============================== assembly ===============================
SCENES = [("Pendulum wave", "24 pendulums  ·  one rail", draw_pendulums, audio_pendulums),
          ("Metronomes finding the beat", "16 metronomes  ·  two sliding shelves", draw_metronomes, audio_metronomes),
          ("Sand pendulum", "one funnel  ·  ten thousand grains", draw_sand, audio_sand),
          ("Wave machine", "72 brass rods  ·  one spine", draw_wave, audio_wave)]

def scene_img(k, t):
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        if k != 2: c.drawImage(BG, 0, 0)
        SCENES[k][2](c, t)
        # caption at the start of each scene
        a = K.ss(t / 1.2) * (1 - K.ss((t - 6.5) / 1.5))
        if a > 0:
            K.text(c, SCENES[k][0], 120, 1000, F_CAP, CREAM, .9 * a, align="left")
            K.text(c, SCENES[k][1].upper(), 122, 1036, F_SUB, AMBER, .7 * a, align="left", spacing=3)
        K.text(c, "@whatiffun", 1800, 1040, F_MARK, CREAM, .35, align="right")
    return s.makeImageSnapshot()

def frame(f):
    T = f / FPS
    k = min(int(T // SC), NS - 1); t = T - k * SC
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(scene_img(k, t), 0, 0)
        if k > 0 and t < XF:                      # previous scene's last XF seconds fade out over the new one
            c.drawImage(scene_img(k - 1, SC + t), 0, 0, K.SAMP, skia.Paint(Alphaf=1 - K.ss(t / XF)))
        if k == 0 and t < 1.0:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(0, 0, 0, 1 - K.ss(t))))
        # outro over the last 7 s
        ea = K.ss((T - (TOTAL_S - 7)) / 1.5)
        if ea > 0:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(0, 0, 0, .55 * ea)))
            K.text(c, "Follow", W / 2, 470, F_BIG, CREAM, ea)
            K.text(c, "@whatiffun", W / 2, 570, F_BIGI, AMBER, ea)
            K.text(c, "a new physics puzzle every day", W / 2, 640, K.font(K.TF_SERIF_I, 40), CREAM, .6 * ea)
    return out

def build_audio(path):
    import tempfile
    parts = []
    for k, sc in enumerate(SCENES):
        m = sc[3]()
        tmp = path.replace(".wav", f"_{k}.wav")
        print("scene", k, "rms", m.save(tmp, fade_in=.05, fade_out=.05)[:6], flush=True)
        with wave.open(tmp) as w_: a = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767
        # slow automatic level ride: RMS per 0.5 s, smoothed over ~6 s, steered to one calm target (gain 0.4-3)
        hop = SR // 2; nb = len(a) // hop
        r = np.array([np.sqrt((a[j * hop:(j + 1) * hop] ** 2).mean()) + 1e-6 for j in range(nb)])
        ker = np.ones(12) / 12; rs = np.convolve(np.pad(r, 6, mode="edge"), ker, mode="same")[6:-6]
        g = np.clip(.15 / rs, .4, 3.0)
        a = a * np.interp(np.arange(len(a)), np.arange(nb) * hop + hop / 2, g)[:, None]
        parts.append(a.astype(np.float32))
    n = int(TOTAL_S * SR); out = np.zeros((n, 2), np.float32); xf = int(XF * SR)
    for k, a in enumerate(parts):
        s0 = int(k * SC * SR)
        a = a.copy()
        if k > 0: a[:xf] *= np.linspace(0, 1, xf)[:, None]
        if k < NS - 1: a[int(SC * SR):int(SC * SR) + xf] *= np.linspace(1, 0, xf)[:, None]
        e = min(n, s0 + len(a)); out[s0:e] += a[:e - s0]
    fo = int(4 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    out[:SR] *= np.linspace(0, 1, SR)[:, None]
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    out = out / np.abs(out).max() * .85
    with wave.open(path, "wb") as w_:
        w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((out * 32767).astype(np.int16).tobytes())
    return [round(float(np.sqrt((out[s * SR * 10:(s + 1) * SR * 10] ** 2).mean())), 3) for s in range(int(TOTAL_S / 10))]

if __name__ == "__main__":
    mode, OUT = sys.argv[1], sys.argv[-1]
    os.makedirs(OUT, exist_ok=True)
    if mode == "preview":
        for s in sys.argv[2].split(","):
            f = int(float(s) * FPS); frame(f).makeImageSnapshot().save(f"{OUT}/L_{int(float(s)):04d}.png", skia.kPNG)
    elif mode == "audio":
        print(build_audio(f"{OUT}/long.wav"))
    else:
        tmp = f"{OUT}/long_silent_tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for f in range(TOTAL):
            p.stdin.write(frame(f).makeImageSnapshot().toarray().tobytes())
            if f % 1800 == 0: print("frame", f, flush=True)
        p.stdin.close(); p.wait(); os.replace(tmp, f"{OUT}/long_silent.mp4")
        print("video done", flush=True)
