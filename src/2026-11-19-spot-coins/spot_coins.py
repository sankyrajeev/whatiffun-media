"""SPOT IT v3 (15:00, 2026-11-19): 48 brass coins tossed on felt pads, one always lands standing on its edge.
Rule type: LANDING (new: it never lands flat). Arrangement: SLANTED GRID (a parallelogram: 8 columns A-H x 6 rows,
each row shifted right, letters on top, numbers on the left of each row).
Every coin is flicked up once every 2.4 s (5 tosses per 12 s loop, random phase), spins 2.5-3.5 flips in the air and
comes down. The others land flat (heads or tails), some first hitting at a steep angle and toppling over (decoy);
the odd one comes down on its EDGE and stands there, every time.
Sound: a soft thumb flick on each toss, a bright brass clink on each landing (pentatonic by row, panned by x,
density-normalised), a second softer clink when a decoy topples; the odd coin lands with a dull wooden tok."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/coins"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 8, 6
LET = "ABCDEFGH"
SX, SY, SHIFT = 98, 166, 12
X0 = 540 + 5 - ((NC - 1) * SX + (NR - 1) * SHIFT) / 2
Y0 = 620                                   # pad centre of row 1
P = 2.4
NT = int(round(LOOP / P))                  # 5 tosses per loop
UF = 1.08 / P                              # flight fraction
R, TK, TILT = 45, 8, math.radians(30)
HMAX = 64
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))

def pos(i, r): return X0 + i * SX + r * SHIFT, Y0 + r * SY

C = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        ks = list(rng.integers(5, 8, NT))
        if sum(ks) % 2: ks[rng.integers(0, NT)] += 1 if rng.uniform() < .5 else -1
        base = 90.0 if odd else (0.0 if rng.uniform() < .5 else 180.0)
        Phi = [base]
        for k in ks: Phi.append(Phi[-1] + 180 * k)
        dec = [rng.uniform() < .35 for _ in range(NT)]
        dl = [rng.choice([-1, 1]) * (rng.uniform(48, 68) if d else rng.uniform(8, 18)) for d in dec]
        if odd: dl = [rng.choice([-1, 1]) * rng.uniform(10, 16) for _ in range(NT)]
        C.append(dict(lab=lab, odd=odd, x=pos(i, r)[0], y=pos(i, r)[1], r=r, ph=rng.uniform(0, 1), Phi=Phi, dec=dec,
                      dl=dl, spin=rng.choice([-1, 1])))

def state(cn, t):
    """returns (phi deg, height px, event marks)"""
    v = t / P + cn["ph"]
    n = math.floor(v); u = v - n; j = n % NT
    Phi = cn["Phi"]; p0, p1 = Phi[j] % 360.0, None
    # Phi accumulates; use relative turn so the loop closes (sum of ks even -> same face)
    p0 = Phi[j] - Phi[0] + Phi[0]
    p1 = Phi[j + 1]
    dl = cn["dl"][j]
    if u < UF:
        s = u / UF
        land = p1 + dl
        ph = p0 + (land - p0) * (s * .85 + .15 * ss(s))
        h = HMAX * 4 * s * (1 - s)
        return ph, h
    w = (u - UF) * P                         # seconds since landing
    if cn["dec"][j] and not cn["odd"]:
        tt = .26
        if w < tt:                           # topple over: gravity, accelerating
            q = (w / tt) ** 2
            return p1 + dl * (1 - q), 0.0
        w2 = w - tt
        return p1 + dl * .10 * math.exp(-w2 * 9) * math.sin(w2 * 40), 3 * abs(math.sin(w2 * 22)) * math.exp(-w2 * 14)
    # small bounce + damped wobble to rest
    h = 9 * abs(math.sin(min(w, .14) / .14 * math.pi)) * (w < .14)
    k = 7 if cn["odd"] else 9
    return p1 + dl * math.exp(-w * k) * math.cos(w * 34), h

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 34)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
GOLD = (.93, .74, .38)
GOLD_D = (.52, .34, .13)
GOLD_L = (1.0, .92, .68)

def star_path(rr, n=5):
    p = skia.Path()
    for k in range(2 * n):
        a = -math.pi / 2 + k * math.pi / n
        rad = rr if k % 2 == 0 else rr * .42
        (p.moveTo if k == 0 else p.lineTo)(rad * math.cos(a), rad * math.sin(a))
    p.close(); return p
STAR = star_path(R * .44)

def pad(c, x, y, h):
    c.drawOval(skia.Rect(x - R * 1.1, y - R * .5, x + R * 1.1, y + R * .62), skia.Paint(AntiAlias=True, Color4f=c4((.16, .1, .07))))
    c.drawOval(skia.Rect(x - R * 1.1, y - R * .5, x + R * 1.1, y + R * .62), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
               StrokeWidth=2, Color4f=c4((.42, .3, .2), .55)))
    sc = max(.45, 1 - h / 160); al = .55 * sc
    c.drawOval(skia.Rect(x - R * sc, y - R * .4 * sc + 6, x + R * sc, y + R * .4 * sc + 6), skia.Paint(AntiAlias=True,
               Color4f=c4((0, 0, 0), al), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))

def coin(c, x, y, phi):
    a = math.radians(phi) + TILT
    s, co = math.sin(a), math.cos(a)
    sy = max(.03, abs(s))
    heads = s > 0
    lit = .62 + .38 * sy
    glint = math.exp(-((math.degrees(a) % 180 - 70) / 14) ** 2)
    d = TK * abs(co)
    # rim (edge band)
    c.save(); c.translate(x, y + d * .5); c.scale(1, sy)
    c.drawCircle(0, 0, R, skia.Paint(AntiAlias=True, Color4f=c4([v * .75 for v in GOLD_D])))
    c.restore()
    c.drawRect(skia.Rect(x - R, y - d * .5, x + R, y + d * .5), skia.Paint(AntiAlias=True, Color4f=c4([v * .9 for v in GOLD_D])))
    # face
    c.save(); c.translate(x, y - d * .5); c.scale(1, sy)
    g = skia.GradientShader.MakeLinear([(-R, -R), (R, R)], [c4([min(1, v * lit * 1.08) for v in GOLD_L]).toColor(),
                                        c4([v * lit for v in GOLD]).toColor(), c4([v * lit for v in GOLD_D]).toColor()], [0, .5, 1])
    c.drawCircle(0, 0, R, skia.Paint(AntiAlias=True, Shader=g))
    c.drawCircle(0, 0, R * .82, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                 Color4f=c4([v * lit * .7 for v in GOLD_D], .9)))
    c.drawCircle(0, 0, R * .86, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4,
                 Color4f=c4(GOLD_L, .5 * lit)))
    emb = skia.Paint(AntiAlias=True, Color4f=c4([v * lit * .62 for v in GOLD_D], .95))
    if heads:
        c.save(); c.translate(1.5, 1.5); c.drawPath(STAR, skia.Paint(AntiAlias=True, Color4f=c4(GOLD_L, .35 * lit))); c.restore()
        c.drawPath(STAR, emb)
    else:
        for k in range(8):
            aa = k * math.pi / 4
            c.drawCircle(R * .5 * math.cos(aa), R * .5 * math.sin(aa), R * .085, emb)
        c.drawCircle(0, 0, R * .16, emb)
    if glint > .02:
        c.drawCircle(-R * .25, -R * .3, R * .9, skia.Paint(AntiAlias=True, Color4f=c4((1, .97, .85), .45 * glint),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, R * .35)))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH COIN", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "LANDS ON ITS EDGE?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for i in range(NC):
            text(c, LET[i], pos(i, 0)[0], 440, F_LAB, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), pos(0, r)[0] - 70, Y0 + r * SY + 12, F_LAB, AMBER, .9)
        for cn in C: pad(c, cn["x"], cn["y"], state(cn, t)[1])
        for cn in C:
            phi, h = state(cn, t)
            lift = R * abs(math.sin(math.radians(phi))) * math.cos(TILT)
            coin(c, cn["x"], cn["y"] - h - lift, phi)
        yb = 1548
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 50, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 48, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1642, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def clink(f0, seed, dur=.5, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = np.zeros(len(t))
    for m, dec, a in ((1.0, 9, .6), (2.32, 14, .45 * bright), (4.1, 22, .3 * bright), (6.7, 35, .18 * bright)):
        s += a * np.sin(2 * np.pi * f0 * m * rg.uniform(.995, 1.005) * t + rg.uniform(0, 6)) * np.exp(-t * dec)
    n = rg.standard_normal(len(t)) * np.exp(-t * 1500) * .25
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 5000)
def tok(seed, dur=.25):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = np.sin(2 * np.pi * 330 * t) * np.exp(-t * 40) * .8 + np.sin(2 * np.pi * 760 * t) * np.exp(-t * 60) * .3
    n = rg.standard_normal(len(t)) * np.exp(-t * 600) * .3
    return (s + n) * np.minimum(1, t * 4000)
def flick(seed, dur=.08):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 250)
    return np.diff(n, prepend=0) * .5 + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 200) * .3

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, cn in enumerate(C):
        for n in range(-2, NT + 3):
            j = n % NT
            t0 = (n - cn["ph"]) * P
            tl = t0 + UF * P
            for tt, kind in ((t0, "flick"), (tl, "land")) + (((tl + .26, "topple"),) if cn["dec"][j] and not cn["odd"] else ()):
                if 0 <= tt < LOOP: ev.append((tt, k, kind))
    lt = np.array([e[0] for e in ev if e[2] == "land"])
    for tt, k, kind in ev:
        cn = C[k]
        if kind == "flick": m.add(flick(k * 7 + int(tt * 10)), tt, .10, cn["x"]); continue
        dens = max(1, (np.abs(lt - tt) < .06).sum())
        if kind == "topple": m.add(clink(note(NR - 1 - cn["r"] + 7, 196.0), k + 999, .35, .6), tt, .26 / math.sqrt(dens), cn["x"]); continue
        if cn["odd"]: m.add(tok(k + int(tt * 100)), tt, .5, cn["x"]); continue
        m.add(clink(note(NR - 1 - cn["r"] + 7, 196.0), k + int(tt * 100)), tt, .42 / math.sqrt(dens), cn["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    for ch, seed in ((m.L, 3), (m.R, 4)):    # faint room tone, seamless
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
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_coins.mp4"))
