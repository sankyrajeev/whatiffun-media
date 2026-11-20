"""SPOT IT v3 (15:00, 2026-11-20): 45 hot-air balloons in a PYRAMID (rows 5/6/7/8/9/10, rows 1-6 top to bottom,
letters A.. from the left of each row; the label is painted on each balloon's belly band "C6").
BREAKS PHYSICS (hot air rises): every balloon fires its burner every 3 s from a random phase; the flame lights the
envelope from inside and the balloon SHOOTS UP ~70 px, then slowly sinks back while the burner is off.
The odd balloon does the opposite: every time its burner fires it DROPS, and it floats up while the burner is off.
Sound: soft burner whoosh per burn (panned by x, density-normalised) + a tiny wicker creak tick; the odd one's burner
gives a lower, hollow falling 'fwump'."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/balloons"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
P = 3.0
ROWS = [5, 6, 7, 8, 9, 10]
LET = "ABCDEFGHIJ"
SX = 88.0
Y1, SY = 642.0, 166.0
HT = float(os.environ.get("HT", "80"))     # vertical travel
T_UP = 0.95
SC = 1.2
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))

C = []
for r, n in enumerate(ROWS):
    for i in range(n):
        lab = (LET[i], r + 1)
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y1 + r * SY
        C.append(dict(lab=lab, odd=lab == ODD, x=x, y=y, r=r, i=i,
                      ph=rng.uniform(0, 1), ph2=rng.uniform(0, 1), ph3=rng.uniform(0, 1), amp=rng.uniform(.93, 1.05)))
print(len(C), "balloons")

def flame(cn, t):
    u = ((t / P + cn["ph"]) % 1.0) * P
    return ss(u / .07) * (1 - ss((u - .5) / .22)) * (.85 + .15 * math.sin(2 * math.pi * 23 * t / LOOP * 4 + cn["i"]))

def lift(cn, t):
    u = ((t / P + cn["ph"]) % 1.0) * P
    if u < T_UP: a = ss(u / T_UP) ** .8                                  # fast up while burning
    else: a = 1 - ss((u - T_UP) / (P - T_UP))                           # slow sink
    if cn["odd"]: a = 1 - a                                             # odd: drops while burning
    return HT * cn["amp"] * a

def place(cn, t):
    sx = 4.0 * math.sin(2 * math.pi * (2 * t / LOOP + cn["ph2"]))
    rot = 3.2 * math.sin(2 * math.pi * (3 * t / LOOP + cn["ph3"]))
    return cn["x"] + sx, cn["y"] - lift(cn, t), rot

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 23)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
CR = (.95, .90, .80); AM = (.86, .58, .26); AM_D = (.55, .33, .12)
WICK = (.50, .33, .17); FL1 = (1.0, .93, .62); FL2 = (1.0, .55, .16)

# envelope profile (local: origin = basket top centre, y down). top at -112, widest at -74 (r=36), mouth -18 (hw 10)
RT, CY, MY, MW = 37.0, -80.0, -24.0, 9.0
def hw(y):
    if y <= CY: return math.sqrt(max(0, RT * RT - (y - CY) ** 2))
    v = (y - CY) / (MY - CY)
    return MW + (RT - MW) * (1 - v) ** 1.25 * (1 + .55 * v)
YS = np.linspace(CY - RT, MY, 60)
HWS = np.array([hw(y) for y in YS]); HWS[-1] = MW
def env_path(u0=-1.0, u1=1.0):
    p = skia.Path()
    p.moveTo(u0 * HWS[0], YS[0])
    for y, w in zip(YS, HWS): p.lineTo(u0 * w, y)
    for y, w in zip(YS[::-1], HWS[::-1]): p.lineTo(u1 * w, y)
    p.close(); return p
ENV = env_path()
GORES = [env_path(-1 + 2 * k / 6, -1 + 2 * (k + 1) / 6) for k in range(6)]
SHADE = skia.GradientShader.MakeRadial((-12, -96), 70, [c4((1, 1, 1), .28).toColor(), c4((1, 1, 1), 0).toColor(),
                                        c4((0, 0, 0), .34).toColor()], [0, .45, 1])
FLAME = skia.Path(); FLAME.moveTo(-5, 0); FLAME.cubicTo(-7, -9, -2, -18, 0, -26); FLAME.cubicTo(2, -18, 7, -9, 5, 0); FLAME.close()

def draw_balloon(c, cn, t):
    x, y, rot = place(cn, t)
    fl = flame(cn, t)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(SC, SC)
    if fl > .01:   # warm halo around a burning balloon
        hg = skia.GradientShader.MakeRadial((0, -40), 70, [c4((1, .62, .25), .45 * fl).toColor(), c4((1, .5, .2), 0).toColor()], [0, 1])
        c.drawCircle(0, -40, 70, skia.Paint(Shader=hg, BlendMode=skia.BlendMode.kScreen))
    # envelope
    for k, g in enumerate(GORES):
        c.drawPath(g, P_(CR if k % 2 == 0 else AM))
    c.drawPath(ENV, skia.Paint(AntiAlias=True, Shader=SHADE))
    if fl > .01:   # inside glow from the burner
        gl = skia.GradientShader.MakeRadial((0, -26), 62, [c4((1, .74, .32), .95 * fl).toColor(), c4((1, .6, .2), 0).toColor()], [0, 1])
        c.save(); c.clipPath(ENV, doAntiAlias=True); c.drawRect(skia.Rect(-40, -119, 40, -20), skia.Paint(Shader=gl, BlendMode=skia.BlendMode.kScreen)); c.restore()
    c.drawPath(ENV, P_(AM_D, .7, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3))
    # belly band with the label
    c.drawRoundRect(skia.Rect(-31, -90, 31, -66), 6, 6, P_((.20, .12, .06), .92))
    text(c, f"{cn['lab'][0]}{cn['lab'][1]}", 0, -70.5, F_LAB, CR, .97)
    # mouth ring, ropes, basket
    c.drawLine(-MW, MY, MW, MY, P_(AM_D, 1, StrokeWidth=3))
    for sx0, sx1 in ((-MW, -8), (MW, 8)):
        c.drawLine(sx0, MY, sx1, 0, P_((.85, .72, .52), .95, StrokeWidth=1.5))
    if fl > .01:
        c.save(); c.translate(0, -1); c.scale(1.7, (.5 + .9 * fl) * 1.45)
        c.drawPath(FLAME, P_(FL2, .95 * fl, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.2)))
        c.scale(.55, .7); c.drawPath(FLAME, P_(FL1, fl))
        c.restore()
    c.drawRoundRect(skia.Rect(-9, 0, 9, 14), 2.5, 2.5, P_(WICK))
    for yy in (4.5, 9):
        c.drawLine(-9, yy, 9, yy, P_((.32, .2, .1), .8, StrokeWidth=1))
    c.drawRect(skia.Rect(-10, -1, 10, 2), P_((.36, .23, .11)))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for cn in C:
            draw_balloon(c, cn, t)
        yb = 1556
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 46, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 44, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1642, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def whoosh(seed, dur=.7, odd=False):
    n = int(dur * SR); t = np.arange(n) / SR
    rg = np.random.default_rng(seed)
    x = rg.standard_normal(n)
    sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    fc, bw = (380, 260) if odd else (1300, 900)
    sp *= np.exp(-((fr - fc) / bw) ** 2); x = np.fft.irfft(sp, n); x /= np.abs(x).max() + 1e-9
    env = np.minimum(1, t / .05) * np.exp(-np.maximum(0, t - .35) * 9)
    s = x * env
    if odd:   # hollow falling tone
        f = 240 * np.exp(-t * 1.6)
        s = .55 * s + .6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env
    else:     # gentle rising flutter
        s = s * (.8 + .2 * np.sin(2 * np.pi * 31 * t))
    return s
def creak(f0, seed, dur=.18):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + rg.uniform(0, 6)) * np.exp(-t * d) for m, d, a in ((1, 26, .6), (2.3, 40, .25)))
    return s * np.minimum(1, t * 3000)

def audio(path):
    m = Mix(LOOP + 1.8)
    ev = []
    for k, cn in enumerate(C):
        for n in range(-2, 7):
            t0 = (n - cn["ph"]) * P
            ev.append((t0, k, "burn")); ev.append((t0 + T_UP, k, "creak"))
    bt = np.array([e[0] for e in ev if e[1] != -1 and e[2] == "burn"])
    for tt, k, kind in ev:
        if not (0 <= tt < LOOP): continue
        cn = C[k]
        dens = max(1, (np.abs(bt - tt) < .6).sum())
        if kind == "burn":
            snd = whoosh(k * 31 + int(tt * 10), odd=cn["odd"])
            m.add(snd, tt, (.42 if cn["odd"] else .5) / math.sqrt(dens), cn["x"])
        else:
            m.add(creak(note(6 - cn["r"] + 5, 220.0), k * 100 + int(tt * 50)), tt, .22, cn["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    for ch, seed in ((m.L, 3), (m.R, 4)):
        x = np.random.default_rng(seed).standard_normal(n)
        sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
        sp *= np.exp(-((fr - 300) / 400) ** 2)
        bed = np.fft.irfft(sp, n); bed /= np.abs(bed).max(); ch += bed * .03
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        print(audio(f"{OUT}/spot.wav"))
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_balloons.mp4"))
