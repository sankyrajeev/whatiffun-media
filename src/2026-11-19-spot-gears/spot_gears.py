"""SPOT IT v3 (10:00, 2026-11-19): 72 meshed brass gears in four concentric rings, one breaks physics.
Rule type: BREAKS PHYSICS (meshed gears must counter-rotate): every ring is a closed train of identical 12-tooth
gears, so neighbours always turn opposite ways and their teeth interleave. Each ring rocks back and forth (big
swings, reversing every 1.2-2 s, each ring on its own rhythm). On the odd gear the direction is the SAME as both
neighbours, so its teeth grind straight through theirs. Arrangement: CONCENTRIC RINGS (new): rings A-D from the centre
out (6 / 14 / 22 / 30 gears), numbered clockwise from the top; the label sits on each stationary hub ("C17").
Sound: soft brass tooth ticks (one per tooth pitch, pitched by ring, panned along the ring), a low clunk at each
reversal; the odd gear adds a faint gritty scrape (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/gears"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
CX, CY = 540, 900
NS = [8, 16, 24]
RINGS = "ABC"
RP = 49.0                      # pitch radius
T = 14                         # teeth
ADD, DED = 7.5, 7.0
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "15")))
# ring motion: angular speed is a smoothed square wave (steady big turning, a quick reversal), each ring its own rhythm
RMOT = [(4, 0.15), (3, 0.55), (4, 0.62)]   # reversals per half-loop pair, phase (fraction)
WMAX = float(os.environ.get("WMAX", "3.8"))           # rad/s (~6.5 deg per frame: no wagon-wheel aliasing)

GEARS = []                     # dict(label, ring, x, y, theta0, sign)
for k, N in enumerate(NS):
    R = RP / math.sin(math.pi / N)
    pos = [(CX + R * math.sin(2 * math.pi * i / N), CY - R * math.cos(2 * math.pi * i / N)) for i in range(N)]
    th = [0.0] * N
    psi = [math.atan2(pos[(i + 1) % N][1] - pos[i][1], pos[(i + 1) % N][0] - pos[i][0]) for i in range(N)]
    th[0] = psi[0] + 0.07 * k
    for i in range(N - 1):
        th[i + 1] = 2 * psi[i] + math.pi + math.pi / T - th[i]
    for i in range(N):
        lab = (RINGS[k], i + 1)
        s = 1 if i % 2 == 0 else -1
        GEARS.append(dict(label=lab, ring=k, x=pos[i][0], y=pos[i][1], th0=th[i], s=s))
_rs = np.random.default_rng(int(os.environ.get("SEED", "19")))
for g in GEARS: g["mark"] = int(_rs.integers(T)) * 360 / T     # which tooth carries the painted stripe
for g in GEARS:                # the odd one turns the same way as its neighbours
    if g["label"] == ODD: g["s"] = -g["s"]

_TG = np.arange(0, LOOP, 1 / 1200)
_PHI = []
for n, p in RMOT:
    w = WMAX * np.tanh(3.0 * np.sin(2 * np.pi * (n * _TG / LOOP + p))) / np.tanh(3.0)
    ph = np.cumsum(w) / 1200
    _PHI.append(ph - ph.mean())
def phi(t, k):
    return float(np.interp(t % LOOP, _TG, _PHI[k], period=LOOP))

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(900)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_BLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Bold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_HUB = font(TF_BLD, 25)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
BLUR = lambda s: skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, s)

def gear_path():
    p = skia.Path()
    ro, rr = RP + ADD, RP - DED
    pts = []
    for j in range(T):
        a = 2 * math.pi * j / T
        w = 2 * math.pi / T
        for frac, r in ((-.5, rr), (-.27, rr), (-.15, ro), (.15, ro), (.27, rr)):
            pts.append((r * math.cos(a + frac * w), r * math.sin(a + frac * w)))
    p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close()
    # lightening holes so the rotation reads
    for j in range(5):
        a = 2 * math.pi * j / 5 + math.pi / 5
        p.addCircle(26.5 * math.cos(a), 26.5 * math.sin(a), 8.6)
    p.setFillType(skia.PathFillType.kEvenOdd)
    return p
GEAR = gear_path()

def plate(c):
    Rm = RP / math.sin(math.pi / NS[-1]) + RP + ADD + 14
    c.drawCircle(CX + 4, CY + 10, Rm, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .7), MaskFilter=BLUR(16)))
    c.drawCircle(CX, CY, Rm, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (CX - 120, CY - 160), Rm * 1.5, [rgb((.17, .12, .085)), rgb((.11, .08, .055)), rgb((.06, .045, .03))], [0, .55, 1])))
    c.drawCircle(CX, CY, Rm, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                 Color4f=c4((.62, .46, .26), .55)))
    for k, N in enumerate(NS):     # engraved track per ring
        R = RP / math.sin(math.pi / N)
        c.drawCircle(CX, CY, R, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2,
                     Color4f=c4((.0, .0, .0), .45)))
    # centre boss
    c.drawCircle(CX, CY, 24, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (CX - 7, CY - 8), 30, [rgb((1, .88, .6)), rgb((.72, .52, .26)), rgb((.32, .21, .1))], [0, .5, 1])))

def gear(c, g, ang):
    x, y = g["x"], g["y"]
    deg = math.degrees(ang)
    # shadow
    c.save(); c.translate(x + 3, y + 6); c.rotate(deg)
    c.drawPath(GEAR, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .55), MaskFilter=BLUR(4)))
    c.restore()
    c.save(); c.translate(x, y); c.rotate(deg)
    lm = skia.Matrix.RotateDeg(-deg)
    sh = skia.GradientShader.MakeLinear([(-52, -56), (52, 56)],
         [rgb((1, .9, .62)), rgb((.86, .64, .32)), rgb((.55, .37, .16)), rgb((.4, .26, .11))], [0, .35, .75, 1],
         skia.TileMode.kClamp, 0, lm)
    c.drawPath(GEAR, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawPath(GEAR, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4,
               Color4f=c4((.22, .13, .05), .9)))
    # painted index stripe (makes every turn readable, even in a still)
    c.save(); c.rotate(g["mark"])
    c.drawRoundRect(skia.Rect(19, -6.5, RP + ADD - 1, 6.5), 4, 4, skia.Paint(AntiAlias=True, Color4f=c4((.99, .95, .84))))
    c.drawRoundRect(skia.Rect(19, -6.5, RP + ADD - 1, 6.5), 4, 4, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                    StrokeWidth=1, Color4f=c4((.3, .18, .07), .8)))
    c.restore()
    # rim groove
    c.drawCircle(0, 0, RP - DED - 3.5, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3,
                 Color4f=c4((.35, .22, .09), .6)))
    c.restore()

def hub(c, g):
    x, y = g["x"], g["y"]
    c.drawCircle(x, y, 21, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (x - 5, y - 6), 27, [rgb((.2, .15, .11)), rgb((.08, .06, .045))])))
    c.drawCircle(x, y, 21, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                 Color4f=c4((.95, .78, .5), .8)))
    s = f"{g['label'][0]}{g['label'][1]}"
    text(c, s, x, y + 9, F_HUB, CREAM, .97)

_ODDI = [i for i, g in enumerate(GEARS) if g["label"] == ODD][0]
def sparks(c, f, ph):
    g = GEARS[_ODDI]; k = g["ring"]
    t = f / FPS
    w = abs(phi(t + .5 / FPS, k) - phi(t - .5 / FPS, k)) * FPS / WMAX
    if w < .35: return
    ring = [h for h in GEARS if h["ring"] == k]
    j = ring.index(g)
    rs = np.random.default_rng(f * 7 + 3)
    for h in (ring[j - 1], ring[(j + 1) % len(ring)]):
        mx, my = (g["x"] + h["x"]) / 2, (g["y"] + h["y"]) / 2
        for _ in range(int(rs.integers(1, 4))):
            a = rs.uniform(0, 2 * math.pi); d = rs.uniform(0, 7)
            c.drawCircle(mx + d * math.cos(a), my + d * math.sin(a), rs.uniform(1.2, 2.4),
                         skia.Paint(AntiAlias=True, Color4f=c4((1, .86, .5), .55 * w)))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        plate(c)
        ph = [phi(t, k) for k in range(len(NS))]
        for g in GEARS:
            gear(c, g, g["th0"] + g["s"] * ph[g["ring"]])
        for g in GEARS:
            hub(c, g)
        sparks(c, f, ph)
        yb = 1452
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 52, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 50, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def tick(f0, seed=0, dur=.09):
    t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 60) + .4 * np.sin(2 * np.pi * f0 * 2.4 * t) * np.exp(-t * 110)
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 2500) * .5
    return (body + np.diff(n, prepend=0)) * np.minimum(1, t * 8000)
def scrape(seed=0, dur=.07):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = sosfilt(butter(2, [1800, 5200], btype="band", fs=SR, output="sos"), n)
    return n * np.exp(-t * 45) * np.minimum(1, t * 3000) * 1.6

def audio(path):
    m = Mix(LOOP + 1.0)
    dt = 1 / 600
    ts = np.arange(0, LOOP, dt)
    pitch = 2 * math.pi / T
    rng = np.random.default_rng(4)
    odd = [g for g in GEARS if g["label"] == ODD][0]
    for k, N in enumerate(NS):
        ring = [g for g in GEARS if g["ring"] == k]
        p = np.array([phi(t, k) for t in ts])
        q = np.floor(p / pitch)
        ev = np.nonzero(np.diff(q) != 0)[0]
        v = np.abs(np.gradient(p, dt))
        f0 = note(3 + 2 * k, 392.0)
        for n, i in enumerate(ev):
            g = ring[rng.integers(len(ring))]
            m.add(tick(f0 * (1 + .01 * rng.standard_normal()), seed=n + 1000 * k), ts[i], .13, g["x"])
            if k == odd["ring"] and n % 2 == 0:
                m.add(scrape(seed=n), ts[i] + .004, .07, odd["x"])
        # reversal clunks
        sv = np.sign(np.gradient(p))
        for i in np.nonzero(np.diff(sv) != 0)[0]:
            m.add(thud(70 + 12 * k, .35), ts[i], .22, CX)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    tt = np.arange(n) / SR
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 280) / 230) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    hum = (np.sin(2 * np.pi * 98 * tt) + .4 * np.sin(2 * np.pi * 196 * tt)) * .015
    m.L += bed * .035 + hum; m.R += np.roll(bed, 5000) * .035 + hum
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/G_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_gears.mp4"))
