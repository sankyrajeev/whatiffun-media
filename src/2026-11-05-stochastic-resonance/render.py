"""Render No. 4: stochastic resonance. 1,000 beads in double wells, a beat too weak to tip any of them,
each bead shaken a little harder than the last. 1080x1920 @30."""
import sys, math, subprocess
import numpy as np, skia
TOTAL, F_N0, F_N1, F_FRZ, F_RES, F_OFF = 750, 40, 100, 100, 145, 560
def _ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def knob(f):
    if f >= F_OFF: return 1 - _ss((f - F_OFF) / 5)
    return _ss((f - F_N0) / (F_N1 - F_N0))
W, H, FPS = 1080, 1920, 30
D = np.load("sr.npz"); POS, TS, SIG, A, T = D["POS"], D["TS"], D["SIG"], float(D["A"]), float(D["T"])
S = np.load("state.npy").astype(np.float32)
N = POS.shape[2]; NO = 4
CREAM = (0.96, 0.92, 0.84); AMBER = (0.88, 0.64, 0.30)
X0, X1, CY, SC, CLIP = 120.0, 960.0, 870.0, 150.0, 1.85
XS = np.linspace(X0, X1, N)
HERO = 500
F_REV, F_NERVE, F_TAKE, F_CARD, XF = 300, 430, 525, 650, 20
PY0, PY1 = 1300.0, 1420.0
# live "how well each follows the beat" curve: running correlation since release
LAG = 0.6
ref = np.sign(np.sin(2 * np.pi * TS / T - LAG)).astype(np.float32)
act = np.zeros(TOTAL, np.float32); act[F_RES:F_OFF] = 1
CUM = np.cumsum(S * ref[:, None] * act[:, None], 0); CNT = np.cumsum(act)
KER = np.ones(41) / 41
def curve(f):
    if CNT[f] < 5: return None
    v = CUM[f] / CNT[f]
    v = np.convolve(np.pad(v, 20, mode="edge"), KER, mode="valid")
    return np.clip(v, 0, 1)
def beat(t): return math.tanh(2.5 * math.sin(2 * math.pi * t / T)) / math.tanh(2.5)

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
F_KICK = font(tf_semi, 28); F_H = font(tf_serif, 88); F_HI = font(tf_serif_i, 88)
F_MONO = font(tf_mono, 29); F_SMALL = font(tf_mono, 21); F_MARK = font(tf_semi, 25)
F_CHIP = font(tf_serif, 40); F_CHIPL = font(tf_semi, 30)
def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

BEATS = [(0, "A beat too weak", "to tip a single bead."),
         (52, "So shake each one", "a little harder."),
         (F_FRZ, "Which ones will", "hear the beat?"),
         (F_RES + 10, "1,000 beads.", "One hidden beat."),
         (F_REV, "The noise lets", "them hear it."),
         (F_NERVE, "Your nerves use", "this trick too."),
         (F_TAKE, "Take the noise away", "and they go deaf."),
         ]
GROUPS = [(0, 333, "A", "gentle"), (333, 667, "B", "medium"), (667, 1000, "C", "hardest")]
def yof(x): return CY - SC * np.clip(x, -CLIP, CLIP)

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
def build_bg():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.clear(skia.Color4f(0.059, 0.051, 0.043, 1))
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, CY), 1100, [skia.Color4f(0.12, 0.095, 0.07, 1), skia.Color4f(0.065, 0.055, 0.045, 1),
                                skia.Color4f(0.035, 0.03, 0.026, 1)], [0, .55, 1])))
        dash = skia.DashPathEffect.Make([6, 10], 0)
        for yy, a in [(CY - SC, .10), (CY + SC, .10), (CY, .05)]:
            c.drawLine(X0 - 10, yy, X1 + 10, yy, skia.Paint(AntiAlias=True, StrokeWidth=1.2, Color4f=C(CREAM, a), PathEffect=dash))
        text(c, "UP", X0 - 14, CY - SC + 7, F_SMALL, CREAM, .30, align="right")
        text(c, "DOWN", X0 + 26, CY + SC + 34, F_SMALL, CREAM, .0, align="right")
        # noise wedge
        y = 1196
        path = skia.Path(); path.moveTo(X0, y); path.lineTo(X1, y - 9); path.lineTo(X1, y + 9); path.close()
        c.drawPath(path, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(X0, 0), (X1, 0)],
                   [C(AMBER, .15), C(AMBER, .7)])))
        text(c, "SHAKEN GENTLY", X0, y - 22, F_SMALL, CREAM, .40, align="left", spacing=1.5)
        text(c, "SHAKEN HARD", X1, y - 22, F_SMALL, CREAM, .40, align="right", spacing=1.5)
        for k in (1, 2):
            xx = X0 + (X1 - X0) * k / 3
            c.drawLine(xx, y + 16, xx, y + 30, skia.Paint(StrokeWidth=1.2, Color4f=C(CREAM, .25)))
    return s.makeImageSnapshot()
BG = build_bg()

def bead(c, x, y, r):
    c.drawCircle(x, y, r * 3.4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x, y), r * 3.4, [skia.Color4f(1, .9, .6, .38), skia.Color4f(1, .8, .4, 0)], [0, 1])))
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - r * .35, y - r * .4), r * 1.5, [skia.Color4f(1, .99, .94, 1), skia.Color4f(1, .86, .55, 1),
                                             skia.Color4f(.6, .42, .18, 1)], [0, .45, 1])))

def headline(c, f):
    idx = max(i for i, b in enumerate(BEATS) if f >= b[0])
    def draw(b, al, dy):
        if al <= 0: return
        text(c, b[1], W / 2, 350 + dy, F_H, CREAM, al)
        text(c, b[2], W / 2, 436 + dy, F_HI, CREAM, al * .92)
    u = (f - BEATS[idx][0]) / 14 if idx > 0 else 1
    if idx > 0 and u < 1:
        draw(BEATS[idx - 1], 1 - ss(u * 2), -12 * ss(u * 2)); draw(BEATS[idx], ss(u * 2 - 1), 12 * (1 - ss(u * 2 - 1)))
    else: draw(BEATS[idx], 1, 0)

def chips(c, f):
    a = ss((f - F_FRZ) / 8) * (1 - ss((f - F_RES - 6) / 12))
    if a <= 0: return
    for i, (lo, hi, lab, txt) in enumerate(GROUPS):
        x = X0 + (X1 - X0) * (i + .5) / 3; y = 1262
        r = skia.Rect(x - 128, y - 34, x + 128, y + 34)
        c.drawRoundRect(r, 34, 34, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.06, .05, .045, .92 * a)))
        c.drawRoundRect(r, 34, 34, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, Color4f=C(AMBER, .8 * a)))
        text(c, lab, x - 92, y + 11, F_CHIPL, AMBER, a)
        text(c, txt, x + 18, y + 12, F_CHIP, CREAM, a)
    if F_FRZ <= f <= F_RES:
        u = (f - F_FRZ) / (F_RES - F_FRZ)
        c.drawRoundRect(skia.Rect(W / 2 - 200, 1316, W / 2 - 200 + 400 * (1 - u), 1321), 3, 3,
                        skia.Paint(AntiAlias=True, Color4f=C(AMBER, .7 * a)))

def panel(c, f):
    v = curve(f)
    a = ss((f - F_RES - 20) / 20)
    if v is None or a <= 0: return
    text(c, "HOW WELL EACH ONE FOLLOWS THE BEAT", W / 2, PY0 - 14, F_SMALL, CREAM, .40 * a, spacing=1.5)
    c.drawLine(X0, PY1, X1, PY1, skia.Paint(StrokeWidth=1, Color4f=C(CREAM, .15 * a)))
    path = skia.Path(); path.moveTo(X0, PY1)
    step = 4
    for i in range(0, N, step): path.lineTo(float(XS[i]), float(PY1 - (PY1 - PY0 - 10) * v[i]))
    path.lineTo(X1, PY1); path.close()
    c.drawPath(path, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, PY0), (0, PY1)],
               [C(AMBER, .45 * a), C(AMBER, .03 * a)])))
    line = skia.Path(); line.moveTo(float(XS[0]), float(PY1 - (PY1 - PY0 - 10) * v[0]))
    for i in range(step, N, step): line.lineTo(float(XS[i]), float(PY1 - (PY1 - PY0 - 10) * v[i]))
    c.drawPath(line, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, Color4f=C(CREAM, .75 * a)))
    rv = ss((f - F_REV) / 20)
    if rv > 0:
        i = int(np.argmax(v)); x = float(XS[i]); y = float(PY1 - (PY1 - PY0 - 10) * v[i])
        c.drawCircle(x, y, 6, skia.Paint(AntiAlias=True, Color4f=C(AMBER, rv)))
        text(c, f"best · noise {SIG[i]:.2f}", x, y - 16, F_SMALL, AMBER, .9 * rv)

def frame(f, first_img=None):
    out = skia.Surface.MakeRaster(INFO)
    t = TS[f]
    with out as c:
        c.drawImage(BG, 0, 0)
        # reveal: glow band behind group B
        rv = ss((f - F_REV) / 20) * (1 - ss((f - F_TAKE) / 20))
        if rv > 0:
            xa, xb = X0 + (X1 - X0) / 3, X0 + 2 * (X1 - X0) / 3
            c.drawRect(skia.Rect(xa, CY - 300, xb, CY + 300), skia.Paint(AntiAlias=True, Color4f=C(AMBER, .07 * rv),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
        P = POS[f]
        Y = yof(P[2]); Yp = yof(P[1])
        recent = np.zeros(N)
        for k in range(1, 5):
            if f - k >= 0: recent = np.maximum(recent, (S[f] != S[f - k]) * (1 - (k - 1) / 4))
        dim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap,
                         BlendMode=skia.BlendMode.kPlus, Color4f=skia.Color4f(.88 * .55, .64 * .55, .30 * .55, 1))
        hot = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6.5, StrokeCap=skia.Paint.kRound_Cap,
                         BlendMode=skia.BlendMode.kPlus, Color4f=skia.Color4f(.75, .58, .34, 1))
        pd, ph_ = skia.Path(), skia.Path()
        for i in range(N):
            if i == HERO: continue
            x = float(XS[i]); y = float(Y[i])
            pp = ph_ if recent[i] > .5 else pd
            dy = max(-14.0, min(14.0, (float(Yp[i]) - y) * .35)); pp.moveTo(x, y + dy); pp.lineTo(x, y)
        c.drawPath(pd, dim); c.drawPath(ph_, hot)
        Y = [None, None, Y]
        bead(c, float(XS[HERO]), float(Y[2][HERO]), 8.5)
        # type
        text(c, f"ONE RULE  ·  NO. {NO}", W / 2, 236, F_KICK, CREAM, .55, spacing=4.5)
        headline(c, f)
        paused = F_FRZ <= f < F_RES
        tt = t / T
        text(c, f"t {tt:05.2f}s" + ("  ‖" if paused else ""), 150, 532, F_MONO, CREAM, .55, align="left")
        g = knob(f)
        text(c, f"noise ×{g:.2f}", W / 2 - 40, 532, F_MONO, CREAM, .55)
        b = beat(t)
        bs = f"beat {A * abs(b):.2f}/0.385"
        text(c, bs, W - 150, 532, F_MONO, CREAM, .55, align="right")
        c.drawCircle(W - 150 - F_MONO.measureText(bs) - 16, 522, 4 + 5 * max(0, abs(b)), skia.Paint(AntiAlias=True, Color4f=C(AMBER, .35 + .5 * abs(b))))
        chips(c, f)
        panel(c, f)
        text(c, "@whatiffun", W / 2, 1488, F_MARK, CREAM, .42, spacing=1.0)
        if f >= F_CARD:
            a = ss((f - F_CARD) / 14) * (1 - ss((f - (TOTAL - XF)) / 10)); dy = 18 * (1 - ss((f - F_CARD) / 14))
            if a > 0:
                c.drawRoundRect(skia.Rect(190, 700 + dy, 890, 1050 + dy), 36, 36,
                                skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.045, .04, .035, .93 * a)))
                c.drawRoundRect(skia.Rect(190, 700 + dy, 890, 1050 + dy), 36, 36, skia.Paint(AntiAlias=True,
                                Style=skia.Paint.kStroke_Style, StrokeWidth=1.5, Color4f=C(AMBER, .45 * a)))
                text(c, "ONE RULE  ·  A NEW ONE EVERY DAY", W / 2, 775 + dy, font(tf_semi, 22), AMBER, .8 * a, spacing=3.5)
                text(c, "Follow", W / 2, 865 + dy, font(tf_serif, 76), CREAM, a)
                text(c, "@whatiffun", W / 2, 947 + dy, font(tf_serif_i, 76), AMBER, a)
                text(c, "for more", W / 2, 997 + dy, font(tf_serif_i, 40), CREAM, .6 * a)
        if first_img is not None and f >= TOTAL - XF:
            c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    return out

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
