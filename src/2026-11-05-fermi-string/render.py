"""Render No. 3: a plucked string of 32 brass beads (FPUT-alpha chain) scrambles, then rebuilds itself.
1080x1920 @30. Beads = real snapshots (one per swing, interpolated); the haze = every position of the last swing."""
import sys, math, subprocess, os
import numpy as np, skia

W, H, FPS = 1080, 1920, 30
D = np.load("fput.npz")
X, Ef, DT, Ts = D["X"], D["Ef"], float(D["DT"]), float(D["Ts"])
N = X.shape[1]
NO = 3
CREAM = (0.96, 0.92, 0.84); AMBER = (0.88, 0.64, 0.30)
X0, X1, CY, SC = 110.0, 970.0, 790.0, 150.0
XS = np.linspace(X0, X1, N + 2)
HERO = 15
REC = 90                                   # recurrence swing

# ---------------- timeline: frame -> (swings s, mode) ----------------
F_IN, F_FRZ, F_RES, F_REC = 40, 330, 375, 600
F_CARD, TOTAL, XF = 666, 750, 20
def s_of(f):
    if f <= F_IN: return f / 40.0, "real"
    if f <= F_FRZ:
        u = (f - F_IN) / (F_FRZ - F_IN); b = .165
        return 1 + 44 * (b * u + (1 - b) * u * u), "strobe"
    if f <= F_RES: return 45.0, "freeze"
    if f <= F_REC:
        u = (f - F_RES) / (F_REC - F_RES); a = .125
        return 45 + 45 * (a * u + (1 - a) * (1 - (1 - u) ** 3)), "strobe"
    return REC + (f - F_REC) / 40.0, "real"
SS = [s_of(f) for f in range(TOTAL)]
np.save("timeline.npy", np.array([s for s, _ in SS]))

def at_time(t):
    i = t / DT; k = int(i); fr = i - k
    k = min(k, len(X) - 2)
    return X[k] * (1 - fr) + X[k + 1] * fr
def snap(s, mode):
    if mode == "real": return at_time(s * Ts)
    k = int(math.floor(s)); fr = s - k
    return at_time(k * Ts) * (1 - fr) + at_time((k + 1) * Ts) * fr
def e1(s):
    return float(Ef[min(len(Ef) - 1, int(round(s * Ts / DT))), 0])

# strain strip: one row per swing
ROWS = np.array([np.diff(np.concatenate([[0], at_time(n * Ts), [0]])) for n in range(REC + 1)])
lo, hi = np.percentile(ROWS, 1), np.percentile(ROWS, 99.5)
STRIP = np.clip((ROWS - lo) / (hi - lo), 0, 1)

# ---------------- fonts / text ----------------
tf_serif = skia.Typeface.MakeFromFile("fonts/InstrumentSerif-Regular.ttf")
tf_serif_i = skia.Typeface.MakeFromFile("fonts/InstrumentSerif-Italic.ttf")
tf_mono = skia.Typeface.MakeFromFile("fonts/JetBrainsMono-Regular.ttf")
tf_semi = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
def font(tf, size):
    f = skia.Font(tf, size); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
def C(rgb, a): return skia.Color4f(rgb[0], rgb[1], rgb[2], a)
def text(c, s, x, y, f, rgb, a, align="center", spacing=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=C(rgb, a))
    ws = [f.measureText(ch) for ch in s] if spacing else None
    w = sum(ws) + spacing * (len(s) - 1) if spacing else f.measureText(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    if not spacing: c.drawString(s, x, y, f, p); return
    for ch, cw in zip(s, ws): c.drawString(ch, x, y, f, p); x += cw + spacing
F_KICK = font(tf_semi, 28); F_H = font(tf_serif, 90); F_HI = font(tf_serif_i, 90)
F_MONO = font(tf_mono, 29); F_SMALL = font(tf_mono, 21); F_MARK = font(tf_semi, 25)
F_CHIP = font(tf_serif, 46); F_CHIPL = font(tf_semi, 30)
def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

BEATS = [(0, "Pluck it once.", "Never touch it again."),
         (150, "Physics says it should", "melt into noise."),
         (F_FRZ, "Swing 45.", "What happens next?"),
         (F_RES + 12, "Los Alamos, 1953.", "Fermi expected noise."),
         (F_REC - 40, "It rebuilds", "the first pluck."),
         ]

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
def build_bg():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.clear(skia.Color4f(0.059, 0.051, 0.043, 1))
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, CY), 1100, [skia.Color4f(0.12, 0.095, 0.07, 1), skia.Color4f(0.065, 0.055, 0.045, 1),
                                skia.Color4f(0.035, 0.03, 0.026, 1)], [0, .55, 1])))
        # rest line + anchors
        c.drawLine(X0, CY, X1, CY, skia.Paint(AntiAlias=True, StrokeWidth=1.2, Color4f=C(CREAM, .08),
                                               PathEffect=skia.DashPathEffect.Make([6, 10], 0)))
        for x in (X0, X1):
            c.drawRoundRect(skia.Rect(x - 7, CY - 70, x + 7, CY + 70), 5, 5, skia.Paint(AntiAlias=True,
                Shader=skia.GradientShader.MakeLinear([(x - 7, 0), (x + 7, 0)],
                    [skia.Color4f(.45, .32, .15, 1), skia.Color4f(.95, .78, .45, 1), skia.Color4f(.35, .24, .12, 1)])))
        # strip frame + labels
        c.drawRect(skia.Rect(X0, SY0 - 1, X1, SY1 + 1), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                   StrokeWidth=1, Color4f=C(CREAM, .10)))
        text(c, "ONE ROW = ONE SWING", X0, SY0 - 16, F_SMALL, CREAM, .38, align="left", spacing=1.5)
        text(c, "STRETCH ALONG THE STRING", X1, SY0 - 16, F_SMALL, CREAM, .38, align="right", spacing=1.5)
        for n in range(0, REC + 1, 15):
            y = SY0 + (n + .5) * RH
            c.drawLine(X0 - 12, y, X0 - 4, y, skia.Paint(StrokeWidth=1.2, Color4f=C(CREAM, .25)))
            text(c, str(n), X0 - 16, y + 7, F_SMALL, CREAM, .3, align="right")
    return s.makeImageSnapshot()
SY0, SY1 = 1110.0, 1400.0
RH = (SY1 - SY0) / (REC + 1)
BG = build_bg()

# amber map for strip: dark -> amber -> cream-white
def amber_map(v):
    v = v[..., None]
    c0 = np.array([.06, .05, .045]); c1 = np.array(AMBER) * .85; c2 = np.array([1.0, .93, .78])
    return np.where(v < .6, c0 + (c1 - c0) * (v / .6), c1 + (c2 - c1) * ((v - .6) / .4))
def strip_image(s):
    nrows = REC + 1
    rgba = np.zeros((nrows, N + 1, 4), np.uint8)
    col = amber_map(STRIP)
    shown = np.clip(s + 1 - np.arange(nrows), 0, 1)       # current row fades in
    a = shown[:, None]
    rgba[..., :3] = (col * a[..., None] * 255).astype(np.uint8)
    rgba[..., 3] = (a * 255).astype(np.uint8).repeat(N + 1, 1)
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)

def bead(c, x, y, r, hero=False):
    if hero:
        c.drawCircle(x, y, r * 3.2, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (x, y), r * 3.2, [skia.Color4f(1, .9, .6, .35), skia.Color4f(1, .8, .4, 0)], [0, 1])))
        cols = [skia.Color4f(1, .99, .94, 1), skia.Color4f(1, .86, .55, 1), skia.Color4f(.6, .42, .18, 1)]
    else:
        cols = [skia.Color4f(1, .9, .66, 1), skia.Color4f(.80, .57, .26, 1), skia.Color4f(.30, .20, .09, 1)]
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - r * .35, y - r * .4), r * 1.5, cols, [0, .45, 1])))

def headline(c, f):
    idx = max(i for i, b in enumerate(BEATS) if f >= b[0])
    def draw(b, al, dy):
        if al <= 0: return
        text(c, b[1], W / 2, 350 + dy, F_H, CREAM, al)
        text(c, b[2], W / 2, 438 + dy, F_HI, CREAM, al * .92)
    u = (f - BEATS[idx][0]) / 16 if idx > 0 else 1
    if idx > 0 and u < 1:
        draw(BEATS[idx - 1], 1 - ss(u * 2), -12 * ss(u * 2)); draw(BEATS[idx], ss(u * 2 - 1), 12 * (1 - ss(u * 2 - 1)))
    else:
        draw(BEATS[idx], 1, 0)

def chips(c, f):
    a = ss((f - F_FRZ) / 8) * (1 - ss((f - F_RES - 20) / 14))
    if a <= 0: return
    for i, (lab, txt) in enumerate([("A", "stays a mess"), ("B", "rebuilds itself")]):
        x = W / 2 + (-215 if i == 0 else 215); y = 1020
        r = skia.Rect(x - 195, y - 36, x + 195, y + 36)
        c.drawRoundRect(r, 36, 36, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.06, .05, .045, .92 * a)))
        c.drawRoundRect(r, 36, 36, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2,
                                              Color4f=C(AMBER, .8 * a)))
        text(c, lab, x - 150, y + 11, F_CHIPL, AMBER, a)
        text(c, txt, x + 18, y + 14, F_CHIP, CREAM, a)
    # countdown bar
    if F_FRZ <= f <= F_RES:
        u = (f - F_FRZ) / (F_RES - F_FRZ)
        c.drawRoundRect(skia.Rect(W / 2 - 200, 1066, W / 2 - 200 + 400 * (1 - u), 1071), 3, 3,
                        skia.Paint(AntiAlias=True, Color4f=C(AMBER, .7 * a)))

def frame(f, first_img=None):
    s, mode = SS[f]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        # strain strip
        c.drawImageRect(strip_image(s), skia.Rect(X0, SY0, X1, SY1), skia.SamplingOptions(skia.FilterMode.kLinear))
        # long exposure: every position of the last swing
        t_end = s * Ts if mode == "real" else snap_t(s)
        t0 = max(0.0, t_end - Ts)
        K = 44
        hz = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6, BlendMode=skia.BlendMode.kPlus)
        for kk in range(K):
            t = t0 + (t_end - t0) * kk / (K - 1)
            if t_end - t0 < 1e-6 and kk > 0: break
            y = CY - SC * np.concatenate([[0], at_time(t), [0]])
            hz.setColor4f(C(AMBER, .035 + .07 * kk / K))
            path = skia.Path(); path.moveTo(XS[0], y[0])
            for i in range(1, N + 2): path.lineTo(XS[i], float(y[i]))
            c.drawPath(path, hz)
        # beads
        x = snap(s, mode)
        y = CY - SC * np.concatenate([[0], x, [0]])
        path = skia.Path(); path.moveTo(XS[0], y[0])
        for i in range(1, N + 2): path.lineTo(XS[i], float(y[i]))
        pulse = math.exp(-max(0, f - F_REC) / 18) * ss((f - F_REC + 6) / 6)
        if pulse > 0.01:
            c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                       StrokeCap=skia.Paint.kRound_Cap, Color4f=C(AMBER, .22 * pulse),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=C(CREAM, .55)))
        for i in range(N):
            if i != HERO: bead(c, float(XS[i + 1]), float(y[i + 1]), 9.5)
        bead(c, float(XS[HERO + 1]), float(y[HERO + 1]), 11, hero=True)
        # type
        text(c, f"ONE RULE  ·  NO. {NO}", W / 2, 236, F_KICK, CREAM, .55, spacing=4.5)
        headline(c, f)
        rec_glow = ss((f - F_REC + 30) / 30) * (1 - ss((f - F_CARD) / 20))
        text(c, f"swing {int(math.floor(s + 1e-6)):02d}", 150, 532, F_MONO, CREAM, .55, align="left")
        e = e1(s)
        text(c, f"first note {e * 100:5.1f}%", W - 150, 532, F_MONO,
             tuple(CREAM[i] + (AMBER[i] - CREAM[i]) * rec_glow for i in range(3)), .55 + .4 * rec_glow, align="right")
        chips(c, f)
        text(c, "@whatiffun", W / 2, 1478, F_MARK, CREAM, .42, spacing=1.0)
        # end card
        if f >= F_CARD:
            a = ss((f - F_CARD) / 14) * (1 - ss((f - (TOTAL - XF)) / 10)); dy = 18 * (1 - ss((f - F_CARD) / 14))
            if a > 0:
                c.drawRoundRect(skia.Rect(190, 830 + dy, 890, 1180 + dy), 36, 36,
                                skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.045, .04, .035, .93 * a)))
                c.drawRoundRect(skia.Rect(190, 830 + dy, 890, 1180 + dy), 36, 36, skia.Paint(AntiAlias=True,
                                Style=skia.Paint.kStroke_Style, StrokeWidth=1.5, Color4f=C(AMBER, .45 * a)))
                text(c, "ONE RULE  ·  A NEW ONE EVERY DAY", W / 2, 905 + dy, font(tf_semi, 22), AMBER, .8 * a, spacing=3.5)
                text(c, "Follow", W / 2, 995 + dy, font(tf_serif, 76), CREAM, a)
                text(c, "@whatiffun", W / 2, 1077 + dy, font(tf_serif_i, 76), AMBER, a)
                text(c, "for more", W / 2, 1127 + dy, font(tf_serif_i, 40), CREAM, .6 * a)
        if first_img is not None and f >= TOTAL - XF:
            c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    return out

def snap_t(s):
    return s * Ts

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for f in [int(v) for v in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG); print("saved", f, flush=True)
    else:
        first = frame(0).makeImageSnapshot()
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                               "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "silent.mp4"], stdin=subprocess.PIPE)
        for f in range(TOTAL):
            ff.stdin.write(frame(f, first).makeImageSnapshot().toarray().tobytes())
            if f % 60 == 0: print("frame", f, flush=True)
        ff.stdin.close(); print("ok" if ff.wait() == 0 else "FAIL", flush=True)
