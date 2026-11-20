"""SOLVE IT (new format, owner 2026-11-20: "a video where we have to solve an equation or a puzzle. Stagnant one").
A still object-equation puzzle in our brass look: gear, hourglass, metronome. The puzzle itself never moves; the objects
idle softly (gear turns, sand trickles, needle ticks) so the frame is alive. 12 s seamless loop.
  gear + gear + gear = 30            -> gear = 10
  gear + hourglass + hourglass = 20  -> hourglass = 5
  hourglass + metronome x metronome = 9 -> metronome = 2
  metronome + gear x hourglass = ?   -> 2 + 10x5 = 52  (trap: left-to-right gives 60)
Usage: python solve_it.py preview <frames> OUT | render OUT"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[-1]
LOOP = 12.0
TOTAL = int(LOOP * FPS)
PCT = 3                                   # "Only 3% get this right" (hard: order-of-operations trap)
TF_XB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_B = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_XB, 84); F_EQ = font(TF_B, 92); F_OP = font(TF_B, 70)
F_PCT = font(TF_XB, 38); F_CTA = font(TF_SEMI, 42); F_LIKE = font(TF_SERIF_I, 36)
BG = background(1000)
def c4(rgb, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in rgb], a)
def col(rgb, a=1.0): return c4(rgb, a).toColor()
BR_L, BR_M, BR_D = (1, .86, .56), (.82, .6, .3), (.45, .3, .14)

def gear(c, x, y, r, t):
    n = 10; ang = t * 2 * math.pi / LOOP
    p = skia.Path()
    for k in range(n * 2):
        for j, f in enumerate((0, 1)):
            a0 = ang + (k + f * .5) * math.pi / n
            rr = r if k % 2 == 0 else r * .78
            a1 = ang + (k + .5 + f * .5) * math.pi / n
            pt = (x + rr * math.cos(a0), y + rr * math.sin(a0))
            if k == 0 and j == 0: p.moveTo(*pt)
            else: p.lineTo(*pt)
    p.close()
    c.drawPath(p.makeOffset(0, 6) if hasattr(p, "makeOffset") else p, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45),
               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - r, y - r), (x + r, y + r)], [col(BR_L), col(BR_M), col(BR_D)], [0, .5, 1])))
    c.drawCircle(x, y, r * .48, skia.Paint(AntiAlias=True, Color4f=c4((.55, .38, .18))))
    c.drawCircle(x, y, r * .4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - r, y - r), (x + r, y + r)], [col(BR_L), col(BR_M)])))
    for k in range(5):
        a = ang + k * 2 * math.pi / 5
        c.drawCircle(x + r * .26 * math.cos(a), y + r * .26 * math.sin(a), r * .06, skia.Paint(AntiAlias=True, Color4f=c4(BR_D)))
    c.drawCircle(x, y, r * .1, skia.Paint(AntiAlias=True, Color4f=c4((.12, .09, .07))))

def hourglass(c, x, y, r, t):
    w, h = r * .78, r * 1.05
    for yy in (y - h - 8, y + h):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - w - 10, yy, x + w + 10, yy + 9), 4, 4), skia.Paint(AntiAlias=True,
                    Shader=skia.GradientShader.MakeLinear([(0, yy), (0, yy + 9)], [col((.62, .4, .22)), col((.32, .2, .1))])))
    glass = skia.Path(); glass.moveTo(x - w, y - h); glass.lineTo(x + w, y - h); glass.lineTo(x + 7, y); glass.lineTo(x + w, y + h)
    glass.lineTo(x - w, y + h); glass.lineTo(x - 7, y); glass.close()
    c.drawPath(glass, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.85, .9, .95, .1)))
    u = (t % LOOP) / LOOP                     # sand runs top -> bottom over the loop, then the frame resets with the loop
    s = .25 + .5 * (.5 - .5 * math.cos(2 * math.pi * u))
    top = skia.Path(); ht = h * (1 - s) * .85
    top.moveTo(x - w * ht / h, y - ht); top.lineTo(x + w * ht / h, y - ht); top.lineTo(x + 6, y - 2); top.lineTo(x - 6, y - 2); top.close()
    sand = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - w, 0), (x + w, 0)], [col((.98, .8, .5)), col((.85, .62, .32))]))
    c.drawPath(top, sand)
    hb = h * s * .85
    bot = skia.Path(); bot.moveTo(x - w, y + h); bot.lineTo(x + w, y + h); bot.lineTo(x + w * (1 - hb / h * .6), y + h - hb); bot.lineTo(x, y + h - hb - 10)
    bot.lineTo(x - w * (1 - hb / h * .6), y + h - hb); bot.close()
    c.drawPath(bot, sand)
    c.drawLine(x, y, x, y + h - hb - 8, skia.Paint(AntiAlias=True, StrokeWidth=2.2, Color4f=c4((.95, .78, .48), .9)))
    c.drawPath(glass, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(.95, .92, .85, .55)))

def metronome(c, x, y, r, t):
    b = r * 1.1
    body = skia.Path(); body.moveTo(x - b * .55, y + b); body.lineTo(x + b * .55, y + b); body.lineTo(x + b * .22, y - b); body.lineTo(x - b * .22, y - b); body.close()
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x - b * .55, 0), (x + b * .55, 0)],
               [col((.42, .25, .14)), col((.64, .41, .23)), col((.3, .18, .1))], [0, .45, 1])))
    face = skia.Path(); face.moveTo(x - b * .3, y + b * .78); face.lineTo(x + b * .3, y + b * .78); face.lineTo(x + b * .12, y - b * .85); face.lineTo(x - b * .12, y - b * .85); face.close()
    c.drawPath(face, skia.Paint(AntiAlias=True, Color4f=c4((.93, .87, .74), .92)))
    ang = .38 * math.sin(2 * math.pi * 6 * t / LOOP)     # 6 swings per loop -> seamless
    px, py = x, y + b * .62
    L = b * 1.45
    c.drawLine(px, py, px + math.sin(ang) * L, py - math.cos(ang) * L, skia.Paint(AntiAlias=True, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap, Color4f=c4((.72, .55, .3))))
    wx, wy = px + math.sin(ang) * L * .66, py - math.cos(ang) * L * .66
    c.save(); c.translate(wx, wy); c.rotate(math.degrees(ang))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-12, -10, 12, 10), 3, 3), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(-12, 0), (12, 0)], [col(BR_L), col(BR_D)])))
    c.restore()
    c.drawCircle(px, py, 6, skia.Paint(AntiAlias=True, Color4f=c4(BR_M)))

ICON = {"G": gear, "H": hourglass, "M": metronome}
LINES = [("G", "+", "G", "+", "G", "30"), ("G", "+", "H", "+", "H", "20"), ("H", "+", "M", "×", "M", "9"), ("M", "+", "G", "×", "H", "?")]
XS = [175, 280, 385, 490, 595]           # icon, op, icon, op, icon
X_EQ, X_NUM = 700, 850
Y0, DY, R = 610, 205, 54

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "CAN YOU", W / 2, 262, F_Q, CREAM, 1.0, spacing=2)
        text(c, "SOLVE IT?", W / 2, 356, F_Q, AMBER, 1.0, spacing=2)
        # the "Only X%" badge
        s = f"ONLY {PCT}% GET THIS RIGHT"
        tw = sum(F_PCT.measureText(ch) for ch in s) + 2 * (len(s) - 1)
        pill = skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31)
        c.drawRRect(pill, skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        # equation card
        card = skia.RRect.MakeRectXY(skia.Rect(100, 500, 980, 1360), 34, 34)
        c.drawRRect(card.makeOffset(0, 12), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
        c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=c4((.09, .075, .06), .94)))
        c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, Color4f=c4(AMBER, .45)))
        for li, ln in enumerate(LINES):
            y = Y0 + li * DY
            if li == 3:
                c.drawLine(150, y - 112, 930, y - 112, skia.Paint(AntiAlias=True, StrokeWidth=2, Color4f=c4(CREAM, .18)))
            for k in range(5):
                if k % 2 == 0: ICON[ln[k]](c, XS[k], y, R, t)
                else: text(c, ln[k], XS[k], y + 24, F_OP, CREAM, .85)
            text(c, "=", X_EQ, y + 26, F_OP, CREAM, .85)
            if ln[5] == "?":
                g = .5 + .5 * math.sin(2 * math.pi * 3 * t / LOOP)
                box = skia.RRect.MakeRectXY(skia.Rect(X_NUM - 70, y - 64, X_NUM + 70, y + 64), 20, 20)
                c.drawRRect(box, skia.Paint(AntiAlias=True, Color4f=c4(AMBER, .12 + .1 * g)))
                c.drawRRect(box, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=c4(AMBER, .6 + .3 * g)))
                text(c, "?", X_NUM, y + 33, F_EQ, AMBER, 1.0)
            else:
                text(c, ln[5], X_NUM, y + 33, F_EQ, CREAM, 1.0)
        yb = 1468
        text(c, "Comment your answer", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you got it "
        fe = font(TF_EMOJI, 30); w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 54, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 52, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

def audio(path):
    from scipy.signal import butter, sosfilt
    m = Mix(LOOP + 1)
    rng = np.random.default_rng(2)
    for k in range(12):                                         # metronome ticks: 6 swings/loop -> 12 ticks
        x = XS[2] if k % 2 else XS[4]
        m.add(glass_click(1250, 240, .06, .6) + .5 * thud(150, .06), k * LOOP / 12, .5, 540)
    n = int((LOOP + 1) * SR)
    sand = sosfilt(butter(2, [2500, 8000], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    m.L += sand * .02; m.R += sand * .02
    for k in range(4):                                          # a soft gear click 4x per loop
        m.add(glass_click(2200, 300, .04, .4), k * 3 + 1.5, .25, 300)
    nL = int(LOOP * SR)
    m.L[:m.N - nL] += m.L[nL:]; m.R[:m.N - nL] += m.R[nL:]
    m.L, m.R, m.N = m.L[:nL], m.R[:nL], nL
    return m.save(path, fade_in=0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/S_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close()); print(audio(f"{OUT}/solve.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/solve.wav", f"{OUT}/solve_it.mp4"))
