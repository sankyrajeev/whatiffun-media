"""Render the Galton board ASMR reel. 1080x1920 @30."""
import pickle, sys, math, subprocess, os
import numpy as np, skia

d = pickle.load(open("sim.pkl", "rb"))
FR, G, PINS, DIVS, COUNTS = d["frames"], d["geom"], d["pins"], d["dividers"], d["counts"]
W, H, FPS = 1080, 1920, 30
NF = len(FR)
NB = FR.shape[1]
CX, BR, PR = G["CX"], G["BR"], G["PR"]
BX0, BX1, FLOOR, BIN_TOP, PITCH = G["BX0"], G["BX1"], G["FLOOR"], G["BIN_TOP"], G["PITCH"]

CURVE, HOLD, CARD, XF = 45, 30, 84, 18
TOTAL = NF + CURVE + HOLD + CARD + XF
INK = (0.17, 0.15, 0.13)

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
FD = "/home/claude/pend/fonts/"
tf_serif = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Regular.ttf")
tf_serif_i = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Italic.ttf")
tf_semi = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")

def font(tf, size):
    f = skia.Font(tf, size); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f

def text(c, s, x, y, f, rgba, spacing=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgba))
    ws = [f.measureText(ch) for ch in s] if spacing else None
    w = (sum(ws) + spacing * (len(s) - 1)) if spacing else f.measureText(s)
    x -= w / 2
    if not spacing:
        c.drawString(s, x, y, f, p); return
    for ch, cw in zip(s, ws):
        c.drawString(ch, x, y, f, p); x += cw + spacing

def C4(rgb, a=1.0): return skia.Color4f(rgb[0], rgb[1], rgb[2], a)
def hexc(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))

# ---------- sprites ----------
S = 4  # supersample
def make_sprite(draw_fn, size):
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(int(size * S), int(size * S)))
    with surf as c:
        c.clear(skia.Color4f(0, 0, 0, 0)); c.scale(S, S); draw_fn(c)
    return surf.makeImageSnapshot()

PALETTE = [hexc(h) for h in ("#E8B45A", "#DDA049", "#D08C3A", "#C27A2E", "#EAC27A", "#B86E28")]
def marble_sprite(col):
    sz = BR * 2 + 4
    def fn(c):
        cx = cy = sz / 2
        light = tuple(min(1, x * 0.55 + 0.45) for x in col)
        dark = tuple(x * 0.62 for x in col)
        sh = skia.GradientShader.MakeRadial((cx - BR * 0.35, cy - BR * 0.4), BR * 1.35,
                                            [C4(light).toColor(), C4(col).toColor(), C4(dark).toColor()], [0, 0.55, 1])
        c.drawCircle(cx, cy, BR, skia.Paint(AntiAlias=True, Shader=sh))
        # inner glow (glass refraction) near bottom-right
        c.drawCircle(cx + BR * 0.28, cy + BR * 0.3, BR * 0.42,
                     skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, 0.16),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.2)))
        c.drawCircle(cx - BR * 0.38, cy - BR * 0.42, BR * 0.24, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, 0.92)))
        c.drawCircle(cx, cy, BR - 0.4, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=0.6,
                                                  Color4f=C4(dark, 0.6)))
    return make_sprite(fn, sz), sz
MARBLES = [marble_sprite(c) for c in PALETTE]
rng = np.random.default_rng(2)
BALL_COL = rng.integers(0, len(PALETTE), NB)

def shadow_sprite():
    sz = BR * 2 + 12
    def fn(c):
        c.drawCircle(sz / 2, sz / 2, BR * 0.95, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.25, 0.18, 0.1, 0.28),
                                                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2.2)))
    return make_sprite(fn, sz), sz
SHADOW = shadow_sprite()

def pin_sprite():
    sz = PR * 2 + 4
    def fn(c):
        cx = cy = sz / 2
        sh = skia.GradientShader.MakeRadial((cx - PR * 0.35, cy - PR * 0.4), PR * 1.4,
                                            [skia.Color(250, 226, 170), skia.Color(196, 152, 82), skia.Color(120, 86, 40)], [0, 0.5, 1])
        c.drawCircle(cx, cy, PR, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawCircle(cx - PR * 0.35, cy - PR * 0.4, PR * 0.28, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, 0.8)))
    return make_sprite(fn, sz), sz
PIN = pin_sprite()
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)

def blit(c, spr, x, y):
    img, sz = spr
    c.drawImageRect(img, skia.Rect(x - sz / 2, y - sz / 2, x + sz / 2, y + sz / 2), SAMP)

# ---------- static background ----------
def build_bg():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, 900), 1250, [skia.Color(244, 238, 228), skia.Color(234, 225, 211), skia.Color(214, 202, 184)], [0, 0.6, 1])))
        # paper grain
        g = (np.random.default_rng(1).normal(0, 1, (H, W)) * 7).clip(-20, 20)
        grain = np.zeros((H, W, 4), np.uint8)
        grain[..., :3] = np.where(g[..., None] > 0, 255, 0).astype(np.uint8)
        grain[..., 3] = np.abs(g).astype(np.uint8)
        gi = skia.Image.fromarray(grain, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        c.drawImage(gi, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.35))
        # board panel with soft shadow
        panel = skia.RRect.MakeRectXY(skia.Rect(BX0 - 34, G["PIN_Y0"] - 58, BX1 + 34, FLOOR + 30), 28, 28)
        c.drawRRect(panel.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.35, 0.25, 0.15, 0.18),
                                                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
        c.drawRRect(panel, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, G["PIN_Y0"]), (0, FLOOR)], [skia.Color(248, 244, 236), skia.Color(238, 230, 218)])))
        c.drawRRect(panel, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                      Color4f=skia.Color4f(0.45, 0.35, 0.22, 0.25)))
        # hopper glass
        hw = G["HW"]; top = G["HOP_TOP"] - 70
        path = skia.Path()
        path.moveTo(CX - hw - 6, top); path.lineTo(CX - hw - 6, G["HOP_BOT"] + 2)
        path.lineTo(CX - G["OUTLET"] / 2 - 5, G["OUT_Y"] + 4)
        path.moveTo(CX + hw + 6, top); path.lineTo(CX + hw + 6, G["HOP_BOT"] + 2)
        path.lineTo(CX + G["OUTLET"] / 2 + 5, G["OUT_Y"] + 4)
        c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=14,
                                    StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                                    Color4f=skia.Color4f(1, 1, 1, 0.55)))
        c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5,
                                    StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                                    Color4f=skia.Color4f(0.4, 0.33, 0.25, 0.45)))
        for p_ in PINS:
            c.drawCircle(p_[0] + 1.2, p_[1] + 2, PR, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.3, 0.2, 0.1, 0.18),
                                                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.5)))
            blit(c, PIN, p_[0], p_[1])
    return s.makeImageSnapshot()
BG = build_bg()

def build_wood():
    """walnut slats + base, drawn above marbles"""
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        wood = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, BIN_TOP), (0, FLOOR)], [skia.Color(140, 102, 68), skia.Color(104, 72, 46)]))
        hi = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 0.9, 0.75, 0.35))
        for x in DIVS:
            r = skia.RRect.MakeRectXY(skia.Rect(x - 2.5, BIN_TOP - 2, x + 2.5, FLOOR), 2.5, 2.5)
            c.drawRRect(r.makeOffset(1.5, 2), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.3, 0.2, 0.1, 0.2),
                                                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2)))
            c.drawRRect(r, wood)
            c.drawRect(skia.Rect(x - 2, BIN_TOP - 1, x - 0.8, FLOOR), hi)
        base = skia.RRect.MakeRectXY(skia.Rect(BX0 - 12, FLOOR + 3, BX1 + 12, FLOOR + 22), 6, 6)
        c.drawRRect(base.makeOffset(0, 5), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.3, 0.2, 0.1, 0.25),
                                                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
        c.drawRRect(base, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, FLOOR + 3), (0, FLOOR + 22)], [skia.Color(150, 110, 72), skia.Color(96, 66, 42)])))
        for x in (BX0 - 6, BX1 + 6):
            r = skia.RRect.MakeRectXY(skia.Rect(x - 4, G["PIN_Y0"] - 30, x + 4, FLOOR + 4), 4, 4)
            c.drawRRect(r, wood)
    return s.makeImageSnapshot()
WOOD = build_wood()

F_KICK = font(tf_semi, 27)
F_SUB = font(tf_serif_i, 46)
F_LBL = font(tf_serif_i, 40)
F_CARD = font(tf_serif, 74)
F_CARD_I = font(tf_serif_i, 74)

# ---------- bell curve from the actual result ----------
final = FR[-1]
xs = final[:, 0]
mu, sd = float(xs.mean()), float(xs.std())
tops = {}
for k in range(G["NBINS"]):
    sel = final[(final[:, 0] >= BX0 + k * PITCH) & (final[:, 0] < BX0 + (k + 1) * PITCH)]
    tops[k] = FLOOR - sel[:, 1].min() + BR if len(sel) else 0
peak = max(tops.values()) + 10
curve = skia.Path()
for i, x in enumerate(np.linspace(BX0 + 4, BX1 - 4, 300)):
    y = FLOOR - peak * math.exp(-((x - mu) ** 2) / (2 * sd * sd))
    (curve.moveTo if i == 0 else curve.lineTo)(float(x), float(y))

first_img = None
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)

def frame(f):
    global first_img
    out = skia.Surface.MakeRaster(INFO)
    k = min(f, NF - 1)
    pos = FR[k]
    with out as c:
        c.drawImage(BG, 0, 0)
        # shadows then marbles
        for i in range(NB):
            x, y = float(pos[i, 0]), float(pos[i, 1])
            if y > -20:
                blit(c, SHADOW, x + 2.2, y + 3.4)
        for i in range(NB):
            x, y = float(pos[i, 0]), float(pos[i, 1])
            if y > -20:
                blit(c, MARBLES[BALL_COL[i]][:2] if False else MARBLES[BALL_COL[i]], x, y)
        c.drawImage(WOOD, 0, 0)
        # header
        text(c, "440 GLASS MARBLES  ·  16 ROWS OF PINS", W / 2, 196, F_KICK, (*INK, 0.55), spacing=3.2)
        text(c, "sound on.", W / 2, 250, F_SUB, (*INK, 0.7))
        t = f - NF
        if t >= 0:
            u = ease(t / CURVE)
            if u > 0:
                pe = skia.TrimPathEffect.Make(0, u)
                c.drawPath(curve, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                                             PathEffect=pe, Color4f=skia.Color4f(1, 1, 1, 0.6),
                                             StrokeCap=skia.Paint.kRound_Cap))
                c.drawPath(curve, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.5,
                                             PathEffect=pe, Color4f=skia.Color4f(*INK, 0.85),
                                             StrokeCap=skia.Paint.kRound_Cap))
                la = ease((t - CURVE * 0.7) / 15)
                if la > 0:
                    text(c, "the bell curve.", mu, FLOOR - peak - 40 - 10 * (1 - la), F_LBL, (*INK, 0.85 * la))
            # end card
            ct = t - CURVE - HOLD
            if ct >= 0:
                a = ease(ct / 14)
                if f >= TOTAL - XF:
                    a *= 1 - ease((f - (TOTAL - XF)) / XF)
                card = skia.RRect.MakeRectXY(skia.Rect(110, 700, W - 110, 980), 36, 36)
                c.drawRRect(card.makeOffset(0, 12), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.3, 0.2, 0.1, 0.16 * a),
                                                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24)))
                c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.985, 0.97, 0.945, 0.96 * a)))
                c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                             Color4f=skia.Color4f(0.45, 0.35, 0.22, 0.3 * a)))
                dy = 12 * (1 - a)
                text(c, "Follow", W / 2, 818 + dy, F_CARD, (*INK, a))
                text(c, "@whatiffun", W / 2, 900 + dy, F_CARD_I, (0.62, 0.38, 0.24, a))
                text(c, "for more", W / 2, 950 + dy, font(tf_serif_i, 40), (*INK, 0.6 * a))
        if f >= TOTAL - XF:
            u = ease((f - (TOTAL - XF) + 1) / XF)
            c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=u))
    if f == 0:
        first_img = out.makeImageSnapshot()
    return out

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        frame(0)
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG); print("saved", f, flush=True)
    else:
        print("frames", TOTAL, "%.1fs" % (TOTAL / FPS), flush=True)
        tmp = "galton_tmp.mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                               "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        frame(0)
        for f in range(TOTAL):
            ff.stdin.write(frame(f).makeImageSnapshot().toarray().tobytes())
            if f % 90 == 0: print("frame", f, flush=True)
        ff.stdin.close()
        if ff.wait() == 0:
            os.replace(tmp, "galton_silent.mp4"); print("ok", flush=True)
