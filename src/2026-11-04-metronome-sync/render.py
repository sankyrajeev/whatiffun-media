"""Render: '48 metronomes, random start. The only rule: the shelf can slide.' 1080x1920 @30."""
import pickle, sys, math, subprocess, os
import numpy as np, skia
from phase import analyse

d = pickle.load(open("sim.pkl", "rb"))
TH, XR = d["theta"], d["x"]; N = d["N"]
PH, RR, DEV, LOCK = analyse(d)
CNT = LOCK.sum(1)
W, H, FPS = 1080, 1920, 30
NF = len(TH)
ALL = int(np.argmax([(CNT[f:f + 45] == N).all() for f in range(NF)]))   # first frame of lasting full lock
SWAP = ALL + 12
CARD_AT = ALL + 80
TOTAL = CARD_AT + 70 + 18
XF = 18
PXM = 800.0                                  # px per metre of shelf travel
COLS, ROWS = 6, 8
XS = [540 + 150 * (i - 2.5) for i in range(COLS)]
YS = [690 + 100 * j for j in range(ROWS)]
ROD = 80.0
TICKF = np.zeros((TOTAL + 10, N), int) - 99
for t, i, sp in d["ticks"]:
    f = int(t * FPS)
    if f < len(TICKF): TICKF[f:f + 6, i] = f

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../fonts/")
tf_serif = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Regular.ttf")
tf_serif_i = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Italic.ttf")
tf_mono = skia.Typeface.MakeFromFile(FD + "JetBrainsMono-Regular.ttf")
tf_semi = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
def font(tf, s):
    f = skia.Font(tf, s); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
CREAM = (0.96, 0.92, 0.84); AMBER = (0.88, 0.64, 0.30)
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def text(c, s, x, y, f, rgb, a=1.0, align="center", spacing=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgb, a))
    ws = [f.measureText(ch) for ch in s] if spacing else None
    w = (sum(ws) + spacing * (len(s) - 1)) if spacing else f.measureText(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    if not spacing: c.drawString(s, x, y, f, p); return
    for ch, cw in zip(s, ws): c.drawString(ch, x, y, f, p); x += cw + spacing

S = 3
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
def sprite(fn, w, h):
    s = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(int(w * S), int(h * S)))
    with s as c: c.clear(skia.Color4f(0, 0, 0, 0)); c.scale(S, S); fn(c)
    return s.makeImageSnapshot(), w, h
def blit(c, spr, x, y, paint=None):     # (x, y) = sprite centre
    img, w, h = spr
    c.drawImageRect(img, skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), SAMP, paint)

# metronome body: walnut-amber pyramid with brass trim; pivot at (0, 0) = sprite point (BW/2, BH-14)
BW, BH = 84, 86
def body(locked):
    def fn(c):
        cx = BW / 2; base = BH - 6; top = 6
        p = skia.Path(); p.moveTo(cx - 34, base); p.lineTo(cx + 34, base); p.lineTo(cx + 15, top); p.lineTo(cx - 15, top); p.close()
        sh = skia.GradientShader.MakeLinear([(cx - 34, 0), (cx + 34, 0)],
             [skia.Color(70, 44, 22), skia.Color(124, 82, 40), skia.Color(58, 36, 18)], [0, .42, 1])
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3,
                   Color4f=skia.Color4f(*(AMBER if locked else (0.7, 0.55, 0.35)), .75 if locked else .45)))
        # scale window
        w = skia.Path(); w.moveTo(cx - 9, base - 22); w.lineTo(cx + 9, base - 22); w.lineTo(cx + 5, top + 12); w.lineTo(cx - 5, top + 12); w.close()
        c.drawPath(w, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.07, .05, .04, .85)))
        for k in range(6):
            yy = top + 18 + k * 9
            c.drawLine(cx - 3, yy, cx + 3, yy, skia.Paint(AntiAlias=True, StrokeWidth=1, Color4f=skia.Color4f(*AMBER, .45)))
        c.drawRect(skia.Rect(cx - 38, base - 2, cx + 38, base + 4), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.55, .38, .17, 1)))
    return sprite(fn, BW, BH)
BODY = [body(False), body(True)]
PIV_DY = -16          # pivot is 16px above row baseline
def glow_spr(r, col, a):
    sz = r * 6
    def fn(c):
        c.drawCircle(sz / 2, sz / 2, r, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*col, a),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * .8)))
    return sprite(fn, sz, sz)
GLOW = glow_spr(10, (1, .82, .5), .9)
def weight_spr(locked):
    def fn(c):
        col = (0.95, 0.72, 0.36) if locked else (0.62, 0.55, 0.46)
        sh = skia.GradientShader.MakeLinear([(2, 0), (20, 0)], [skia.Color4f(*[min(1, x * 1.25) for x in col], 1).toColor(),
             skia.Color4f(*[x * .6 for x in col], 1).toColor()])
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(2, 2, 20, 14), 3, 3), skia.Paint(AntiAlias=True, Shader=sh))
    return sprite(fn, 22, 16)
WEIGHT = [weight_spr(False), weight_spr(True)]

def build_bg():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (540, 1000), 1250, [skia.Color(30, 25, 20), skia.Color(15, 12, 10), skia.Color(7, 6, 5)], [0, .5, 1])))
        # floor
        c.drawRect(skia.Rect(0, 1474, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, 1474), (0, 1700)],
                   [skia.Color(26, 21, 16), skia.Color(8, 7, 6)])))
        c.drawLine(40, 1474, W - 40, 1474, skia.Paint(AntiAlias=True, StrokeWidth=1.5, Color4f=skia.Color4f(*AMBER, .3)))
        text(c, "ONE RULE  ·  DAY 2", W / 2, 196, font(tf_semi, 27), CREAM, .55, spacing=4.0)
    return s.makeImageSnapshot()
BG = build_bg()

def build_rack():
    """Rack (shelves + posts) as one sprite, drawn shifted by shelf position."""
    RW, RH = 940, 860
    def fn(c):
        x0, x1 = 10, RW - 10
        rail = skia.GradientShader.MakeLinear([(0, 0), (0, 8)], [skia.Color(236, 196, 120), skia.Color(120, 80, 34)])
        for k, y in enumerate(YS):
            yy = y - 610 + 10
            c.drawRect(skia.Rect(x0, yy + 2, x1, yy + 12), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
            c.save(); c.translate(0, yy - 4)
            c.drawRect(skia.Rect(x0, 0, x1, 8), skia.Paint(AntiAlias=True, Shader=rail)); c.restore()
        post = skia.GradientShader.MakeLinear([(0, 0), (14, 0)], [skia.Color(120, 80, 34), skia.Color(236, 196, 120), skia.Color(110, 72, 30)])
        for px in (x0, x1 - 14):
            c.save(); c.translate(px, 0)
            c.drawRect(skia.Rect(0, 20, 14, RH - 44), skia.Paint(AntiAlias=True, Shader=post)); c.restore()
        c.drawRect(skia.Rect(x0, RH - 58, x1, RH - 44), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                   [(0, RH - 58), (0, RH - 44)], [skia.Color(220, 176, 104), skia.Color(100, 66, 28)])))
    return sprite(fn, RW, RH)
RACK = build_rack()   # top-left at (70, 610) when shelf at 0; centre (540, 1040)
ROLLER_Y, ROLLER_R = 1474 - 24, 24

F_H, F_HI = font(tf_serif, 64), font(tf_serif_i, 64)
F_CNT = font(tf_serif, 120)
F_MONO = font(tf_mono, 28)
F_LBL = font(tf_semi, 24)
first_img = None
rodp = [skia.Paint(AntiAlias=True, StrokeWidth=3.2, StrokeCap=skia.Paint.kRound_Cap, Color4f=skia.Color4f(.72, .64, .52, 1)),
        skia.Paint(AntiAlias=True, StrokeWidth=3.2, StrokeCap=skia.Paint.kRound_Cap, Color4f=skia.Color4f(.96, .8, .5, 1))]

def headline(c, f):
    sw = ss((f - SWAP) / 18) if f >= SWAP else 0.0
    a1, a2 = 1 - ss(sw * 2), ss(sw * 2 - 1)
    if a1 > 0:
        text(c, "48 metronomes, random start.", W / 2, 286, F_H, CREAM, a1)
        text(c, "The only rule: the shelf can slide.", W / 2, 352, F_HI, CREAM, a1)
    if a2 > 0:
        text(c, "Nobody told them", W / 2, 286 + 10 * (1 - a2), F_H, CREAM, a2)
        text(c, "to agree.", W / 2, 352 + 10 * (1 - a2), F_HI, AMBER, a2)

def frame(f):
    global first_img
    k = min(f, NF - 1)
    th = TH[k]; dx = float(XR[k] * PXM); lk = LOCK[k]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        # rollers (roll without slipping under the rack): angle = travel / r
        for rx in (240, 840):
            x = rx + dx / 2      # roller centre moves half as far as the rack on top of it
            c.drawCircle(x, ROLLER_Y + 4, ROLLER_R, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
            c.drawCircle(x, ROLLER_Y, ROLLER_R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                (x - 8, ROLLER_Y - 9), ROLLER_R * 1.5, [skia.Color(246, 214, 150), skia.Color(170, 120, 56), skia.Color(80, 52, 22)], [0, .5, 1])))
            a = (dx / 2) / ROLLER_R
            for q in range(3):
                aa = a + q * 2 * math.pi / 3
                c.drawLine(x, ROLLER_Y, x + 17 * math.cos(aa), ROLLER_Y + 17 * math.sin(aa),
                           skia.Paint(AntiAlias=True, StrokeWidth=2, Color4f=skia.Color4f(.25, .16, .06, .6)))
        blit(c, RACK, 540 + dx, 1040)
        for j in range(ROWS):
            for i in range(COLS):
                m = j * COLS + i
                bx, by = XS[i] + dx, YS[j]
                L = int(lk[m])
                blit(c, BODY[L], bx, by - BH / 2 + 8)
                px, py = bx, by + PIV_DY
                a = float(th[m])
                tx, ty = px + ROD * math.sin(a), py - ROD * math.cos(a)
                c.drawLine(px, py, tx, ty, rodp[L])
                wx, wy = px + ROD * .74 * math.sin(a), py - ROD * .74 * math.cos(a)
                c.save(); c.translate(wx, wy); c.rotate(math.degrees(a)); blit(c, WEIGHT[L], 0, 0); c.restore()
                c.drawCircle(px, py, 3.2, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.95, .82, .55, 1)))
                tf = TICKF[f, m] if f < len(TICKF) else -99
                if f - tf < 6:
                    blit(c, GLOW, px, py, skia.Paint(Alphaf=(1 - (f - tf) / 6) * (.9 if L else .5), BlendMode=skia.BlendMode.kPlus))
        headline(c, f)
        # counter
        n = int(CNT[k]); full = f >= ALL
        pulse = math.exp(-max(0, f - ALL) / 8) if full else 0
        cs = f"{n} / {N}"
        c.save(); c.translate(W / 2, 470); s_ = 1 + .1 * pulse; c.scale(s_, s_); c.translate(-W / 2, -470)
        if full:
            g = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*AMBER, .45 * min(1, (f - ALL) / 6)),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
            c.drawString(cs, W / 2 - F_CNT.measureText(cs) / 2, 500, F_CNT, g)
        col = tuple(CREAM[q] + (AMBER[q] - CREAM[q]) * min(1, max(0, (f - ALL) / 8)) for q in range(3)) if full else CREAM
        text(c, cs, W / 2, 500, F_CNT, col)
        c.restore()
        text(c, "IN STEP", W / 2, 540, F_LBL, AMBER, .85, spacing=5)
        mm = XR[k] * 1000
        text(c, "SHELF %+d mm" % int(round(mm)) if abs(mm) >= .5 else "SHELF  0 mm", 110, 590, F_MONO, CREAM, .7, align="left")
        text(c, "t %4.1f s" % (k / FPS), 970, 590, F_MONO, CREAM, .7, align="right")
        # end card
        if f >= CARD_AT:
            a = ss((f - CARD_AT) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            card = skia.RRect.MakeRectXY(skia.Rect(150, 840, W - 150, 1160), 34, 34)
            c.drawRRect(card.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6 * a),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
            c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.09, .075, .06, .94 * a)))
            c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                        Color4f=skia.Color4f(*AMBER, .45 * a)))
            dy = 12 * (1 - a)
            text(c, "ONE RULE  ·  A NEW ONE EVERY DAY", W / 2, 905 + dy, font(tf_semi, 22), AMBER, .8 * a, spacing=3.5)
            text(c, "Follow", W / 2, 995 + dy, font(tf_serif, 76), CREAM, a)
            text(c, "@whatiffun", W / 2, 1077 + dy, font(tf_serif_i, 76), AMBER, a)
            text(c, "for more", W / 2, 1127 + dy, font(tf_serif_i, 40), CREAM, .6 * a)
        if f >= TOTAL - XF:
            c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0:
        first_img = out.makeImageSnapshot()
    return out

if __name__ == "__main__":
    frame(0)
    print("ALL", ALL, "SWAP", SWAP, "TOTAL", TOTAL, flush=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG); print("saved", f, flush=True)
    else:
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                               "-pix_fmt", "yuv420p", "-movflags", "+faststart", "tmp.mp4"], stdin=subprocess.PIPE)
        for f in range(TOTAL):
            ff.stdin.write(frame(f).makeImageSnapshot().toarray().tobytes())
            if f % 90 == 0: print("frame", f, flush=True)
        ff.stdin.close()
        if ff.wait() == 0: os.replace("tmp.mp4", "silent.mp4"); print("ok", flush=True)
