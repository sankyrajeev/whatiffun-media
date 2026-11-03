"""Render: 'Every time a marble hits something moving, it doubles.' 1080x1920 @30."""
import pickle, sys, math, subprocess, os
import numpy as np, skia

d = pickle.load(open("sim.pkl", "rb"))
FR, OM, CNT, BORN, GEN = d["frames"], d["omegas"], d["counts"], d["born"], d["gen"]
G, PEGS, JAM = d["geom"], d["pegs"], d["jam"]
W, H, FPS = 1080, 1920, 30
CX, CY, RB, BR = G["CX"], G["CY"], G["R_BOWL"], G["BR"]
R_ORB, R_DISC, R_PEG = G["R_ORB"], G["R_DISC"], G["R_PEG"]
NF = len(FR)
CARD_AT = JAM + 40
TOTAL = CARD_AT + 70 + 18
XF = 18
OMEGA0 = abs(OM[5, 0])
TS = 1.3
RPM0 = OMEGA0 / TS * 60 / (2 * math.pi)      # sim runs 1.3x real time; show real-time rpm

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
FD = "/home/claude/pend/fonts/"
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

S = 4
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
def sprite(fn, size):
    s = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(int(size * S), int(size * S)))
    with s as c: c.clear(skia.Color4f(0, 0, 0, 0)); c.scale(S, S); fn(c)
    return s.makeImageSnapshot(), size
def blit(c, spr, x, y, scale=1.0, paint=None):
    img, sz = spr; h = sz * scale / 2
    c.drawImageRect(img, skia.Rect(x - h, y - h, x + h, y + h), SAMP, paint)

def hexc(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
SHADES = [hexc(h) for h in ("#F2CE86", "#E8B45A", "#DDA049", "#D08C3A", "#C27A2E", "#B86E28")]
def marble(col):
    sz = BR * 2 + 4
    def fn(c):
        cx = cy = sz / 2
        light = tuple(min(1, x * 0.5 + 0.5) for x in col); dark = tuple(x * 0.55 for x in col)
        sh = skia.GradientShader.MakeRadial((cx - BR * .35, cy - BR * .4), BR * 1.35,
             [skia.Color4f(*light, 1).toColor(), skia.Color4f(*col, 1).toColor(), skia.Color4f(*dark, 1).toColor()], [0, .55, 1])
        c.drawCircle(cx, cy, BR, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawCircle(cx + BR * .28, cy + BR * .3, BR * .42, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .9, .7, .22),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.2)))
        c.drawCircle(cx - BR * .38, cy - BR * .42, BR * .24, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .9)))
    return sprite(fn, sz)
MARB = [marble(cl) for cl in SHADES]
def glow_spr(r, a):
    sz = r * 6
    def fn(c):
        c.drawCircle(sz / 2, sz / 2, r, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, .85, .55, a),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * .8)))
    return sprite(fn, sz)
POP = glow_spr(BR * 1.4, 0.9)
def brass(r, engraved=True):
    sz = r * 2 + 6
    def fn(c):
        cx = cy = sz / 2
        sh = skia.GradientShader.MakeRadial((cx - r * .35, cy - r * .45), r * 1.5,
             [skia.Color(246, 214, 150), skia.Color(190, 140, 70), skia.Color(98, 66, 30)], [0, .5, 1])
        c.drawCircle(cx, cy, r, skia.Paint(AntiAlias=True, Shader=sh))
        if engraved:
            for rr, a in ((r * .78, .35), (r * .5, .25)):
                c.drawCircle(cx, cy, rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4,
                             Color4f=skia.Color4f(.25, .16, .06, a)))
            c.drawCircle(cx, cy, r * .16, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.22, .14, .06, .85)))
        c.drawCircle(cx, cy, r - .6, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                     Color4f=skia.Color4f(1, .92, .7, .5)))
    return sprite(fn, sz)
DISC, PEG, HUB = brass(R_DISC), brass(R_PEG, False), brass(34)

def build_bg():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (CX, CY), 1250, [skia.Color(30, 25, 20), skia.Color(15, 12, 10), skia.Color(7, 6, 5)], [0, .5, 1])))
        c.drawCircle(CX, CY + 18, RB + 10, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
        c.drawCircle(CX, CY, RB, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX - 120, CY - 160), RB * 1.4, [skia.Color(36, 30, 24), skia.Color(20, 17, 14)])))
        # orbit track
        c.drawCircle(CX, CY, R_ORB, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                     PathEffect=skia.DashPathEffect.Make([3, 9], 0), Color4f=skia.Color4f(*AMBER, .22)))
        for p in PEGS:
            c.drawCircle(p[0] + 2, p[1] + 4, R_PEG, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
            blit(c, PEG, p[0], p[1])
        text(c, "ZERO GRAVITY  ·  ONE MOTOR  ·  ONE RULE", W / 2, 196, font(tf_semi, 27), CREAM, .5, spacing=3.4)
    return s.makeImageSnapshot()
BG = build_bg()

def glass_rim(c):
    c.drawCircle(CX, CY, RB + 2, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                 Color4f=skia.Color4f(1, .9, .7, .07)))
    c.drawCircle(CX, CY, RB + 2, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2,
                 Color4f=skia.Color4f(*AMBER, .55)))
    arc = skia.Path(); arc.addArc(skia.Rect(CX - RB + 8, CY - RB + 8, CX + RB - 8, CY + RB - 8), 200, 55)
    c.drawPath(arc, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=skia.Color4f(1, .95, .85, .16)))

F_H, F_HI = font(tf_serif, 66), font(tf_serif_i, 66)
F_CNT = font(tf_serif, 132)
F_MONO = font(tf_mono, 30)
first_img = None
streak = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=BR * 1.3, StrokeCap=skia.Paint.kRound_Cap)
shadow = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35))

def headline(c, f):
    swap = ss((f - JAM - 6) / 16) if f >= JAM else 0.0
    a1, a2 = 1 - ss(swap * 2), ss(swap * 2 - 1)
    if a1 > 0:
        text(c, "Every time a marble hits", W / 2, 290, F_H, CREAM, a1)
        text(c, "something moving, it doubles.", W / 2, 358, F_HI, CREAM, a1)
    if a2 > 0:
        text(c, "Until there were", W / 2, 290 + 10 * (1 - a2), F_H, CREAM, a2)
        text(c, "too many to move.", W / 2, 358 + 10 * (1 - a2), F_HI, AMBER, a2)

def frame(f):
    global first_img
    k = min(f, NF - 1)
    pos = FR[k]; prev = FR[k - 1] if k > 0 else pos
    n = len(pos)
    w, ang = OM[k]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        c.save(); c.clipPath(skia.Path().addCircle(CX, CY, RB), skia.ClipOp.kIntersect, True)
        # shadows
        for i in range(n):
            c.drawCircle(float(pos[i, 0]) + 1.6, float(pos[i, 1]) + 2.6, BR, shadow)
        # motion streaks
        if k > 0:
            pv = prev
            for i in range(min(n, len(pv))):
                dx, dy = float(pos[i, 0] - pv[i, 0]), float(pos[i, 1] - pv[i, 1])
                v2 = dx * dx + dy * dy
                if v2 > 36:
                    streak.setColor4f(skia.Color4f(*SHADES[min(5, GEN[i] // 2)], min(.32, v2 / 2500)))
                    c.drawLine(float(pv[i, 0]) + dx * .45, float(pv[i, 1]) + dy * .45, float(pos[i, 0]), float(pos[i, 1]), streak)
        # discs + hub (rotating)
        for j in range(3):
            a = ang + 2 * math.pi * j / 3
            x, y = CX + R_ORB * math.cos(a), CY + R_ORB * math.sin(a)
            c.drawCircle(x + 3, y + 6, R_DISC, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5),
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
            c.save(); c.translate(x, y); c.rotate(math.degrees(ang)); blit(c, DISC, 0, 0)
            c.drawLine(R_DISC * .2, 0, R_DISC * .74, 0, skia.Paint(AntiAlias=True, StrokeWidth=2.2,
                       Color4f=skia.Color4f(.22, .14, .06, .55))); c.restore()
        blit(c, HUB, CX, CY)
        # marbles
        for i in range(n):
            x, y = float(pos[i, 0]), float(pos[i, 1])
            age = k - BORN[i]
            sc = 1.0 + (0.5 * (1 - age / 5) if age < 5 else 0)
            blit(c, MARB[min(5, GEN[i] // 2)], x, y, sc)
        for i in range(n):
            age = k - BORN[i]
            if 0 < BORN[i] and age < 6:
                blit(c, POP, float(pos[i, 0]), float(pos[i, 1]), 1.0, skia.Paint(Alphaf=1 - age / 6, BlendMode=skia.BlendMode.kPlus))
        c.restore()
        glass_rim(c)
        headline(c, f)
        # counter
        jam_pulse = math.exp(-max(0, f - JAM) / 8) if f >= JAM else 0
        cs = f"{n:,}"
        c.save(); c.translate(W / 2, 490); s_ = 1 + .12 * jam_pulse; c.scale(s_, s_); c.translate(-W / 2, -490)
        if f >= JAM:
            g = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*AMBER, .45 * min(1, (f - JAM) / 6)),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
            c.drawString(cs, W / 2 - F_CNT.measureText(cs) / 2, 520, F_CNT, g)
        col = tuple(CREAM[i] + (AMBER[i] - CREAM[i]) * min(1, max(0, (f - JAM) / 8)) for i in range(3)) if f >= JAM else CREAM
        text(c, cs, W / 2, 520, F_CNT, col)
        c.restore()
        # motor gauge
        rpm = abs(w) / TS * 60 / (2 * math.pi)
        gy = CY + RB + 78
        jammed = f >= JAM
        text(c, ("MOTOR  %4.1f rpm" % rpm), CX - RB + 6, gy, F_MONO, CREAM, .8, align="left")
        if jammed:
            text(c, "JAMMED", CX + RB - 6, gy, F_MONO, AMBER, .95 * min(1, (f - JAM) / 4), align="right")
        bw = 2 * RB - 12
        c.drawRect(skia.Rect(CX - RB + 6, gy + 24, CX - RB + 6 + bw, gy + 27), skia.Paint(Color4f=skia.Color4f(*CREAM, .12)))
        c.drawRect(skia.Rect(CX - RB + 6, gy + 24, CX - RB + 6 + bw * min(1, rpm / RPM0), gy + 27),
                   skia.Paint(Color4f=skia.Color4f(*AMBER, .9)))
        # end card
        if f >= CARD_AT:
            a = ss((f - CARD_AT) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            card = skia.RRect.MakeRectXY(skia.Rect(150, 870, W - 150, 1150), 34, 34)
            c.drawRRect(card.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6 * a),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
            c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.09, .075, .06, .94 * a)))
            c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                        Color4f=skia.Color4f(*AMBER, .45 * a)))
            dy = 12 * (1 - a)
            text(c, "Follow", W / 2, 990 + dy, font(tf_serif, 76), CREAM, a)
            text(c, "@whatiffun", W / 2, 1072 + dy, font(tf_serif_i, 76), AMBER, a)
            text(c, "for more", W / 2, 1122 + dy, font(tf_serif_i, 40), CREAM, .6 * a)
        if f >= TOTAL - XF:
            c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0:
        first_img = out.makeImageSnapshot()
    return out

if __name__ == "__main__":
    frame(0)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG); print("saved", f, flush=True)
    else:
        print("frames", TOTAL, "%.1fs" % (TOTAL / FPS), "jam", JAM, flush=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                               "-pix_fmt", "yuv420p", "-movflags", "+faststart", "jam_tmp.mp4"], stdin=subprocess.PIPE)
        for f in range(TOTAL):
            ff.stdin.write(frame(f).makeImageSnapshot().toarray().tobytes())
            if f % 90 == 0: print("frame", f, flush=True)
        ff.stdin.close()
        if ff.wait() == 0: os.replace("jam_tmp.mp4", "jam_silent.mp4"); print("ok", flush=True)
