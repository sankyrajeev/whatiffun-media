"""Chladni plate: 80,000 grains of sand on a vibrating steel plate. Sim + render in one pass.
Grains random-walk with a step size proportional to the local vibration amplitude |u|, plus a drift
down the amplitude gradient, so they pile up on the nodal lines. 1080x1920 @30."""
import sys, math, subprocess, os
import numpy as np, skia
from scipy.ndimage import gaussian_filter

W, H, FPS = 1080, 1920, 30
NG = 150000
PS = 840                         # plate size px
PX0, PY0 = (W - PS) // 2, 560    # plate top-left
SS = 2                           # sand supersample

MODES = [(1, 3), (3, 5), (3, 7), (5, 7), (5, 9), (7, 9)]
HZ = [9 * (n * n + m * m) for n, m in MODES]
INTRO, SWEEP, RES = 36, 26, 78
PASS = [None, (2, 4), (4, 6), (4, 6), (6, 8), (6, 8)]
CARD, XF = 78, 18
T_MODES = INTRO + len(MODES) * (SWEEP + RES)
TOTAL = T_MODES + CARD + XF

# ---- timeline: per frame -> (mode index or -1, envelope, freq) ----
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
TL = []
for f in range(TOTAL):
    if f < INTRO:
        TL.append((-1, 0.0, 0.0, 0.0, 0.0)); continue
    if f >= T_MODES:
        k = f - T_MODES
        TL.append((len(MODES) - 1, 0.0, HZ[-1], max(0.0, 1 - k / 12), 0.0)); continue
    j, k = divmod(f - INTRO, SWEEP + RES)
    if k < SWEEP:
        f0 = HZ[j - 1] if j > 0 else HZ[0] * 0.7
        fr = f0 * (HZ[j] / f0) ** ss(k / SWEEP)
        TL.append((j, 0.04, fr, 0.35 + 0.15 * ss(k / SWEEP), math.sin(math.pi * k / SWEEP) if j > 0 else 0.0))
    else:
        r = k - SWEEP
        env = ss(r / 7) * (1 - 0.25 * ss((r - 40) / 40))
        TL.append((j, env, HZ[j], 0.5 + 0.5 * env, 0.0))

rng = np.random.default_rng(42)
pos = rng.uniform(0.004, 0.996, (NG, 2))
shade = rng.uniform(0.72, 1.12, NG)

def field(n, m, p):
    x, y = p[:, 0] * math.pi, p[:, 1] * math.pi
    cnx, cmy, cmx, cny = np.cos(n * x), np.cos(m * y), np.cos(m * x), np.cos(n * y)
    snx, smy, smx, sny = np.sin(n * x), np.sin(m * y), np.sin(m * x), np.sin(n * y)
    u = (cnx * cmy + cmx * cny) / 2
    gx = (-n * snx * cmy - m * smx * cny) * math.pi / 2
    gy = (-m * cnx * smy - n * cmx * sny) * math.pi / 2
    return u, gx, gy

SUB, JIT, DRIFT = 4, 0.0050, 0.0010
energy, pan_x = [], []
def step(f):
    global pos
    j, env, _, _, pe = TL[f]
    if pe > 0.05:
        n, m = PASS[j]; env = 0.85 * pe
    elif j < 0 or env <= 0:
        energy.append(0.0); pan_x.append(0.5); return
    else:
        n, m = MODES[j]
    kk = math.pi * math.sqrt(n * n + m * m) / 2
    sc = (17.9 / kk) ** 0.7
    old = pos.copy()
    for _ in range(SUB):
        u, gx, gy = field(n, m, pos)
        a = np.abs(u)[:, None]
        pos = pos + JIT * sc * env * a * rng.standard_normal((NG, 2)) \
            - DRIFT * sc * env * (u[:, None] * np.stack([gx, gy], 1) / kk)
        pos = np.where(pos < 0.003, 0.006 - pos, pos)
        pos = np.where(pos > 0.997, 1.994 - pos, pos)
    d = np.linalg.norm(pos - old, axis=1)
    energy.append(float(d.mean()))
    w = d / (d.sum() + 1e-12)
    pan_x.append(float((pos[:, 0] * w).sum()))

# ---------------- static art ----------------
INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
tf_serif = skia.Typeface.MakeFromFile("InstrumentSerif-Regular.ttf")
tf_serif_i = skia.Typeface.MakeFromFile("InstrumentSerif-Italic.ttf")
tf_mono = skia.Typeface.MakeFromFile("JetBrainsMono-Regular.ttf")
tf_semi = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
def font(tf, s):
    f = skia.Font(tf, s); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
CREAM = (0.96, 0.92, 0.84); AMBER = (0.86, 0.63, 0.30)
def text(c, s, x, y, f, rgb, a=1.0, align="center", spacing=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgb, a))
    ws = [f.measureText(ch) for ch in s] if spacing else None
    w = (sum(ws) + spacing * (len(s) - 1)) if spacing else f.measureText(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    if not spacing: c.drawString(s, x, y, f, p); return
    for ch, cw in zip(s, ws): c.drawString(ch, x, y, f, p); x += cw + spacing

PLATE_RECT = skia.Rect(PX0, PY0, PX0 + PS, PY0 + PS)
PLATE_RR = skia.RRect.MakeRectXY(PLATE_RECT, 16, 16)

def build_bg():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, PY0 + PS / 2), 1250, [skia.Color(30, 25, 20), skia.Color(16, 13, 11), skia.Color(8, 7, 6)], [0, 0.5, 1])))
        c.drawRRect(PLATE_RR.makeOffset(0, 22), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.55),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
    img = s.makeImageSnapshot().toarray().astype(np.float32) / 255
    # brushed, warm-dark steel plate
    r = np.random.default_rng(3)
    brush = gaussian_filter(r.standard_normal((PS, PS)), (0.6, 22)) * 9
    yy, xx = np.mgrid[0:PS, 0:PS] / PS
    sheen = 0.11 + 0.05 * np.exp(-((xx - 0.3) ** 2 + (yy - 0.25) ** 2) / 0.12) - 0.03 * ((xx - .5) ** 2 + (yy - .5) ** 2)
    v = np.clip(sheen + brush * 0.004, 0, 1)
    plate = np.stack([v * 1.06, v * 0.98, v * 0.88], -1)
    sub = img[PY0:PY0 + PS, PX0:PX0 + PS, :3]
    mask = np.zeros((PS, PS), np.float32)
    ms = skia.Surface.MakeRaster(skia.ImageInfo.MakeA8(PS, PS))
    with ms as c: c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(0, 0, PS, PS), 16, 16), skia.Paint(AntiAlias=True))
    mask = ms.makeImageSnapshot().toarray().astype(np.float32).reshape(PS, PS) / 255
    img[PY0:PY0 + PS, PX0:PX0 + PS, :3] = sub * (1 - mask[..., None]) + plate * mask[..., None]
    out = skia.Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), colorType=skia.kRGBA_8888_ColorType)
    s2 = skia.Surface.MakeRaster(INFO)
    with s2 as c:
        c.drawImage(out, 0, 0)
        c.drawRRect(PLATE_RR, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                         Color4f=skia.Color4f(*AMBER, 0.28)))
        F_K = font(tf_semi, 27)
        text(c, "150,000 GRAINS OF SAND  ·  ONE STEEL PLATE", W / 2, 236, F_K, CREAM, 0.5, spacing=3.4)
        text(c, "Sound, made visible.", W / 2, 336, font(tf_serif_i, 84), CREAM, 0.95)
        text(c, "sound on.", W / 2, 400, font(tf_serif_i, 40), AMBER, 0.75)
    return s2.makeImageSnapshot()
BG = build_bg()

def bolt(c):
    cx, cy = PX0 + PS / 2, PY0 + PS / 2
    c.drawCircle(cx + 2, cy + 4, 15, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.5),
                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    sh = skia.GradientShader.MakeRadial((cx - 5, cy - 6), 20, [skia.Color(236, 205, 150), skia.Color(170, 125, 64),
                                                              skia.Color(86, 60, 30)], [0, 0.55, 1])
    c.drawCircle(cx, cy, 14, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawCircle(cx, cy, 5.5, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.2, 0.14, 0.08, 0.9)))

SAND = np.array([0.93, 0.80, 0.56], np.float32)
def sand_layer():
    q = PS * SS
    ix = np.clip((pos[:, 0] * q).astype(np.int32), 0, q - 1)
    iy = np.clip((pos[:, 1] * q).astype(np.int32), 0, q - 1)
    idx = iy * q + ix
    d = np.bincount(idx, minlength=q * q).astype(np.float32).reshape(q, q)
    b = np.bincount(idx, weights=shade, minlength=q * q).astype(np.float32).reshape(q, q)
    d = d.reshape(PS, SS, PS, SS).sum((1, 3)); b = b.reshape(PS, SS, PS, SS).sum((1, 3))
    cov = 1 - np.exp(-d * 1.25)
    tone = np.where(d > 0, b / np.maximum(d, 1e-6), 1.0)
    hgt = gaussian_filter(np.minimum(d, 6.0), 1.4)
    lx = np.zeros_like(hgt); lx[:, 1:] = hgt[:, 1:] - hgt[:, :-1]
    ly = np.zeros_like(hgt); ly[1:] = hgt[1:] - hgt[:-1]
    light = np.clip(1.0 - 0.10 * (lx + ly) + 0.06 * np.minimum(d, 4), 0.55, 1.35)
    rgb = SAND[None, None] * (tone * light)[..., None]
    rgba = np.empty((PS, PS, 4), np.uint8)
    glow = gaussian_filter(cov, 5.0) * 0.42 + gaussian_filter(cov, 14.0) * 0.18
    pre = rgb * cov[..., None] + SAND[None, None] * glow[..., None] * (1 - cov[..., None])
    alpha = np.clip(cov + glow * (1 - cov), 0, 1)
    rgba[..., :3] = (np.clip(pre, 0, 1) * 255).astype(np.uint8)   # premultiplied
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    # contact shadow under the sand
    sh = gaussian_filter(cov, 2.0)
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType), sh

F_MONO = font(tf_mono, 30)
F_CARD, F_CARD_I = font(tf_serif, 76), font(tf_serif_i, 76)
first_img = None

def draw(f):
    global first_img
    sand, sh = sand_layer()
    j, env, hz, tamp, _pe = TL[f]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.save(); c.clipRRect(PLATE_RR, skia.ClipOp.kIntersect, True)
        shimg = np.zeros((PS, PS, 4), np.uint8); shimg[..., 3] = (np.clip(sh * 0.55, 0, 1) * 255).astype(np.uint8)
        c.drawImage(skia.Image.fromarray(shimg, colorType=skia.kRGBA_8888_ColorType,
                                         alphaType=skia.kPremul_AlphaType), PX0 + 1.5, PY0 + 2.5)
        c.drawImage(sand, PX0, PY0)
        c.restore()
        bolt(c)
        # readouts
        ry = PY0 + PS + 62
        a_hz = 0.85 if j >= 0 and f < T_MODES else 0.4
        text(c, ("f  %4d Hz" % round(hz)) if j >= 0 else "f     — Hz", PX0 + 4, ry, F_MONO, CREAM, a_hz, align="left")
        if j >= 0:
            n, m = MODES[j]
            text(c, f"mode {n}·{m}", PX0 + PS - 4, ry, F_MONO, AMBER, 0.85 if f < T_MODES else 0.4, align="right")
        # resonance meter: thin bar that fills with envelope
        bw = PS
        c.drawRect(skia.Rect(PX0, ry + 26, PX0 + bw, ry + 28), skia.Paint(Color4f=skia.Color4f(*CREAM, 0.12)))
        if env > 0:
            c.drawRect(skia.Rect(PX0, ry + 26, PX0 + bw * env, ry + 28), skia.Paint(Color4f=skia.Color4f(*AMBER, 0.85)))
        # end card
        if f >= T_MODES:
            k = f - T_MODES
            a = ss(k / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            card = skia.RRect.MakeRectXY(skia.Rect(150, 820, W - 150, 1100), 34, 34)
            c.drawRRect(card.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.55 * a),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
            c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.09, 0.075, 0.06, 0.93 * a)))
            c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                         Color4f=skia.Color4f(*AMBER, 0.45 * a)))
            dy = 12 * (1 - a)
            text(c, "Follow", W / 2, 940 + dy, F_CARD, CREAM, a)
            text(c, "@whatiffun", W / 2, 1022 + dy, F_CARD_I, AMBER, a)
            text(c, "for more", W / 2, 1072 + dy, font(tf_serif_i, 40), CREAM, 0.6 * a)
        if f >= TOTAL - XF:
            c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0:
        first_img = out.makeImageSnapshot()
    return out

if __name__ == "__main__":
    mode = sys.argv[1]
    want = set(int(x) for x in sys.argv[2].split(",")) if mode == "preview" else None
    last = max(want) if want else TOTAL - 1
    ff = None
    if mode == "full":
        print("frames", TOTAL, "%.1fs" % (TOTAL / FPS), flush=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                               "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "chl_tmp.mp4"],
                              stdin=subprocess.PIPE)
    for f in range(last + 1):
        step(f)
        if ff is not None or f == 0 or f in want:
            img = draw(f)
            if ff is not None:
                ff.stdin.write(img.makeImageSnapshot().toarray().tobytes())
                if f % 90 == 0: print("frame", f, flush=True)
            elif f in want:
                img.makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG); print("saved", f, flush=True)
    if ff is not None:
        ff.stdin.close()
        np.save("timeline.npy", np.array([list(t) for t in TL], np.float64))
        np.save("energy.npy", np.array([energy, pan_x]))
        if ff.wait() == 0:
            os.replace("chl_tmp.mp4", "chladni_silent.mp4"); print("ok", flush=True)
