"""Render: 1,000 double pendulums, forward into chaos, then exact rewind. 1080x1920 @30."""
import sys, math, subprocess, os
import numpy as np, skia

W, H, FPS = 1080, 1920, 30
PX, PY, LPX = 540.0, 1050.0, 212.0
FR = np.load("frames.npy")          # (nf, 2, N)  theta1, theta2
N = FR.shape[2]

# ---------- timeline: output frame -> playback position (fractional sim frame) ----------
A, D, Rv, HOLD_END = 435, 30, 240, 12
F_END = A + D / 2.0
def smoother(u):
    return u * u * u * (u * (u * 6 - 15) + 10)
P = []
for f in range(A):
    P.append(float(f))
for k in range(D):
    u = (k + 1) / D
    P.append(A + D * (u - u * u / 2))
for k in range(Rv):
    u = (k + 1) / Rv
    P.append(F_END * (1 - smoother(u)))
for k in range(HOLD_END):
    P.append(0.0)
P = np.array(P)
TOTAL = len(P)
np.save("timeline.npy", P)

def state(p):
    i = int(math.floor(p)); fr = p - i
    if i >= len(FR) - 1:
        return FR[-1]
    return FR[i] * (1 - fr) + FR[i + 1] * fr

def geom(p):
    t1, t2 = state(p)
    jx = PX + LPX * np.sin(t1); jy = PY + LPX * np.cos(t1)
    tx = jx + LPX * np.sin(t2); ty = jy + LPX * np.cos(t2)
    return jx, jy, tx, ty

def wrapd(a):
    return (a + np.pi) % (2 * np.pi) - np.pi

def spread(p):
    t2 = state(p)[1]
    return float(np.degrees(np.max(np.abs(wrapd(t2 - t2[0])))))

# ---------- palette across pendulum index ----------
STOPS = [(0.00, (0.36, 0.55, 1.00)), (0.28, (0.25, 0.88, 0.82)), (0.52, (0.97, 0.89, 0.63)),
         (0.76, (1.00, 0.54, 0.36)), (1.00, (1.00, 0.31, 0.60))]
def ramp(x):
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if x <= b:
            u = (x - a) / (b - a)
            return tuple(ca[j] + (cb[j] - ca[j]) * u for j in range(3))
    return STOPS[-1][1]
COLS = [ramp(i / (N - 1)) for i in range(N)]

# ---------- fonts ----------
tf_serif = skia.Typeface.MakeFromFile("fonts/InstrumentSerif-Regular.ttf")
tf_serif_i = skia.Typeface.MakeFromFile("fonts/InstrumentSerif-Italic.ttf")
tf_mono = skia.Typeface.MakeFromFile("fonts/JetBrainsMono-Regular.ttf")
tf_semi = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")

def font(tf, size):
    f = skia.Font(tf, size); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True)
    return f

def draw_text(c, s, x, y, f, color, align="center", spacing=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=color)
    if spacing == 0:
        w = f.measureText(s)
        if align == "center": x -= w / 2
        elif align == "right": x -= w
        c.drawString(s, x, y, f, p)
        return
    ws = [f.measureText(ch) for ch in s]
    total = sum(ws) + spacing * (len(s) - 1)
    if align == "center": x -= total / 2
    for ch, w in zip(s, ws):
        c.drawString(ch, x, y, f, p); x += w + spacing

F_KICK = font(tf_semi, 30)
F_H = font(tf_serif, 92)
F_HI = font(tf_serif_i, 92)
F_MONO = font(tf_mono, 30)

BEATS = [  # (start_frame, line1, line2)
    (0, "Each one released", "0.000001° apart."),
    (226, "Then chaos", "takes over."),
    (A + 6, "Now play it", "backwards."),
]
XF = 16

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
INFO16 = skia.ImageInfo.Make(W, H, skia.kRGBA_F16_ColorType, skia.kPremul_AlphaType)

bg = skia.Surface.MakeRaster(INFO)
with bg as c:
    c.clear(skia.Color(9, 8, 11))
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (PX, PY), 1150, [skia.Color(28, 24, 30), skia.Color(13, 12, 16), skia.Color(6, 6, 8)], [0, 0.5, 1])))
    # faint reach circle + fine tick marks
    c.drawCircle(PX, PY, 2 * LPX + 14, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                 StrokeWidth=1.2, Color4f=skia.Color4f(1, 1, 1, 0.07)))
    tp = skia.Paint(AntiAlias=True, StrokeWidth=1.5, Color4f=skia.Color4f(1, 1, 1, 0.10))
    for k in range(72):
        a = 2 * math.pi * k / 72
        r0 = 2 * LPX + 22; r1 = r0 + (14 if k % 6 == 0 else 7)
        c.drawLine(PX + r0 * math.sin(a), PY + r0 * math.cos(a), PX + r1 * math.sin(a), PY + r1 * math.cos(a), tp)
BG = bg.makeImageSnapshot()

trail = skia.Surface.MakeRaster(INFO16)
with trail as c:
    c.clear(skia.Color4f(0, 0, 0, 0))

def headline(c, f):
    # find active beat and blend with previous
    idx = 0
    for i, (s, _, _) in enumerate(BEATS):
        if f >= s: idx = i
    s0 = BEATS[idx][0]
    u = min(1.0, (f - s0) / XF) if idx > 0 else 1.0
    # loop: fade beat 3 back into beat 1 over the end hold
    end_u = 0.0
    if f >= TOTAL - XF:
        end_u = (f - (TOTAL - XF)) / XF
    def draw(beat, alpha, dy):
        if alpha <= 0: return
        _, l1, l2 = beat
        draw_text(c, l1, W / 2, 352 + dy, F_H, skia.Color4f(1, 0.97, 0.93, alpha))
        draw_text(c, l2, W / 2, 440 + dy, F_HI, skia.Color4f(1, 0.97, 0.93, alpha * 0.92))
    def ss(x):
        x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
    if end_u > 0:
        draw(BEATS[idx], 1 - ss(end_u * 2), -14 * ss(end_u * 2))
        draw(BEATS[0], ss(end_u * 2 - 1), 14 * (1 - ss(end_u * 2 - 1)))
    elif idx > 0 and u < 1:
        draw(BEATS[idx - 1], 1 - ss(u * 2), -14 * ss(u * 2))
        draw(BEATS[idx], ss(u * 2 - 1), 14 * (1 - ss(u * 2 - 1)))
    else:
        draw(BEATS[idx], 1.0, 0)

def meter(c, f, p):
    sp = spread(p)
    if sp < 0.01: s = f"{sp:.6f}°"
    elif sp < 1: s = f"{sp:.4f}°"
    else: s = f"{sp:.1f}°"
    t = p / FPS
    rew = A + D <= f < TOTAL - HOLD_END
    a = skia.Color4f(1, 1, 1, 0.5)
    draw_text(c, "Δ " + s, 150, 540, F_MONO, a, align="left")
    tstr = ("◂◂ " if rew else "") + f"t {t:05.2f}s"
    draw_text(c, tstr, W - 150, 540, F_MONO, skia.Color4f(1, 0.85, 0.6, 0.75) if rew else a, align="right")

prev_tip = None

def frame(f):
    global prev_tip
    p = P[f]
    jx, jy, tx, ty = geom(p)
    # trails
    with trail as c:
        c.drawPaint(skia.Paint(Color4f=skia.Color4f(0, 0, 0, 0.085), BlendMode=skia.BlendMode.kDstOut))
        if prev_tip is not None:
            sp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4,
                            StrokeCap=skia.Paint.kButt_Cap, BlendMode=skia.BlendMode.kPlus)
            ox, oy = prev_tip
            for i in range(N):
                r, g, b = COLS[i]
                sp.setColor4f(skia.Color4f(r, g, b, 0.06))
                c.drawLine(float(ox[i]), float(oy[i]), float(tx[i]), float(ty[i]), sp)
    prev_tip = (tx, ty)
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.drawImage(trail.makeImageSnapshot(), 0, 0, skia.SamplingOptions(),
                    skia.Paint(BlendMode=skia.BlendMode.kPlus))
        glow = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9,
                          StrokeCap=skia.Paint.kRound_Cap, BlendMode=skia.BlendMode.kPlus)
        arm = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.8,
                         StrokeCap=skia.Paint.kRound_Cap, BlendMode=skia.BlendMode.kPlus)
        dot = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus)
        for i in range(N):
            r, g, b = COLS[i]
            x1, y1, x2, y2 = float(jx[i]), float(jy[i]), float(tx[i]), float(ty[i])
            glow.setColor4f(skia.Color4f(r, g, b, 0.004))
            path = skia.Path(); path.moveTo(PX, PY); path.lineTo(x1, y1); path.lineTo(x2, y2)
            c.drawPath(path, glow)
            arm.setColor4f(skia.Color4f(r, g, b, 0.075))
            c.drawPath(path, arm)
            dot.setColor4f(skia.Color4f(r, g, b, 0.4))
            c.drawCircle(x2, y2, 3.6, dot)
            dot.setColor4f(skia.Color4f(r, g, b, 0.12))
            c.drawCircle(x1, y1, 2.6, dot)
        # pivot
        c.drawCircle(PX, PY, 7, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.06, 0.06, 0.07, 1)))
        c.drawCircle(PX, PY, 7, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2,
                                           Color4f=skia.Color4f(1, 1, 1, 0.8)))
        # type
        draw_text(c, "1,000 DOUBLE PENDULUMS", W / 2, 236, F_KICK, skia.Color4f(1, 1, 1, 0.5), spacing=5)
        headline(c, f)
        meter(c, f, p)
    return out

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        want = sorted(int(x) for x in sys.argv[2].split(","))
        for f in range(max(want) + 1):
            s = frame(f)
            if f in want:
                s.makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG); print("saved", f, flush=True)
    else:
        print("frames", TOTAL, TOTAL / FPS, "s", flush=True)
        tmp = "pend_tmp.mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                               "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                               "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        for f in range(TOTAL):
            ff.stdin.write(frame(f).makeImageSnapshot().toarray().tobytes())
            if f % 60 == 0: print("frame", f, flush=True)
        ff.stdin.close()
        if ff.wait() == 0:
            os.replace(tmp, "pend_silent.mp4"); print("ok", flush=True)
