"""Code-drawn cut-outs for flannan-keepers (no credits): wave, stopped clock, smashed crate."""
import math, os, random, skia
OUT = os.path.join(os.path.dirname(__file__), "..", "art", "raw")
INK = skia.Color4f(0.10, 0.08, 0.07, 1)
def P(c): return skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*c, 1))
def stroke(w, c=None):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                   StrokeJoin=skia.Paint.kRound_Join); p.setColor4f(c or INK); return p
def save(surf, name): surf.makeImageSnapshot().save(os.path.join(OUT, name), skia.kPNG)

def wave():
    W, H = 1400, 1100; s = skia.Surface(W, H); c = s.getCanvas(); c.clear(0)
    body = skia.Path(); body.moveTo(60, 1050)
    body.cubicTo(120, 700, 330, 330, 700, 180)            # rising back of the wave
    body.cubicTo(980, 70, 1290, 160, 1330, 420)            # crest
    body.cubicTo(1350, 560, 1210, 640, 1110, 560)          # curl tip coming down
    body.cubicTo(1040, 500, 1080, 400, 1160, 420)          # inner curl
    body.cubicTo(1060, 330, 900, 380, 860, 520)
    body.cubicTo(800, 720, 900, 900, 1340, 1050); body.close()
    g = skia.GradientShader.MakeLinear([(700, 150), (700, 1050)], [skia.Color(70, 120, 130), skia.Color(30, 62, 74)])
    p = skia.Paint(AntiAlias=True); p.setShader(g); c.drawPath(body, p)
    c.save(); c.clipPath(body, doAntiAlias=True)
    for k in range(7):    # inner streaks
        q = skia.Path(); y = 420 + k * 85; q.moveTo(260 + k * 40, y + 300); q.cubicTo(420 + k * 30, y, 650, y - 120, 820, y - 60)
        c.drawPath(q, stroke(7, skia.Color4f(0.62, 0.80, 0.80, 0.55)))
    c.restore()
    foam = skia.Path(); foam.moveTo(560, 240); foam.cubicTo(800, 90, 1180, 90, 1310, 330)
    foam.cubicTo(1330, 420, 1260, 480, 1200, 440); foam.cubicTo(1150, 300, 900, 230, 700, 290); foam.close()
    c.drawPath(foam, P((0.96, 0.93, 0.86)))
    random.seed(4)
    for _ in range(26):   # spray
        x = random.uniform(620, 1360); y = random.uniform(40, 260) - (x - 620) * 0.05; r = random.uniform(10, 28)
        c.drawCircle(x, y, r, P((0.96, 0.93, 0.86))); c.drawCircle(x, y, r, stroke(5))
    c.drawPath(body, stroke(12)); c.drawPath(foam, stroke(9))
    save(s, "wave.png")

def clock():
    W = 900; s = skia.Surface(W, W); c = s.getCanvas(); c.clear(0); cx = cy = W / 2
    c.drawCircle(cx, cy, 400, P((0.45, 0.28, 0.16))); c.drawCircle(cx, cy, 400, stroke(14))
    c.drawCircle(cx, cy, 330, P((0.96, 0.92, 0.82))); c.drawCircle(cx, cy, 330, stroke(9))
    for k in range(60):
        a = k / 60 * 2 * math.pi; r0 = 290 if k % 5 else 255
        c.drawLine(cx + r0 * math.sin(a), cy - r0 * math.cos(a), cx + 310 * math.sin(a), cy - 310 * math.cos(a), stroke(12 if k % 5 == 0 else 4))
    def hand(frac, L, w):
        a = frac * 2 * math.pi; c.drawLine(cx, cy, cx + L * math.sin(a), cy - L * math.cos(a), stroke(w))
    hand((4 + 52 / 60) / 12, 170, 22); hand(52 / 60, 250, 13)
    c.drawCircle(cx, cy, 24, P((0.85, 0.62, 0.28))); c.drawCircle(cx, cy, 24, stroke(6))
    save(s, "clock-stopped.png")

def crate():
    W, H = 1300, 800; s = skia.Surface(W, H); c = s.getCanvas(); c.clear(0)
    random.seed(7)
    planks = [(330, 560, -14, 520), (720, 610, 9, 560), (1010, 470, 38, 420), (420, 380, 62, 380), (820, 330, -30, 470), (210, 690, 4, 360)]
    for x, y, ang, L in planks:
        c.save(); c.translate(x, y); c.rotate(ang)
        r = skia.Rect.MakeXYWH(-L / 2, -45, L, 90)
        tone = random.uniform(0.85, 1.0)
        c.drawRect(r, P((0.62 * tone, 0.42 * tone, 0.24 * tone)))
        for gy in (-20, 4, 24): c.drawLine(-L / 2 + 20, gy, L / 2 - 30, gy + random.uniform(-6, 6), stroke(4, skia.Color4f(0.35, 0.22, 0.12, 0.8)))
        jag = skia.Path(); jag.moveTo(L / 2, -45)       # splintered end
        for k in range(1, 6): jag.lineTo(L / 2 + (28 if k % 2 else 0), -45 + k * 18)
        c.drawPath(jag, P((0.70 * tone, 0.50 * tone, 0.30 * tone))); c.drawPath(jag, stroke(6))
        c.drawRect(r, stroke(9))
        for nx in (-L / 2 + 30, L / 2 - 60): c.drawCircle(nx, 0, 8, P((0.3, 0.3, 0.32)))
        c.restore()
    rope = skia.Path(); rope.moveTo(150, 330)          # a loose rope
    rope.cubicTo(300, 180, 420, 260, 520, 200); rope.cubicTo(640, 130, 700, 240, 900, 160); rope.cubicTo(1050, 100, 1150, 200, 1230, 140)
    c.drawPath(rope, stroke(26)); c.drawPath(rope, stroke(16, skia.Color4f(0.86, 0.74, 0.52, 1)))
    save(s, "crate-smashed.png")

wave(); clock(); crate(); print("drawn")
