"""SPOT IT v3 (10:00, 2026-11-20): 54 archery targets in ALTERNATING LANES; one arrow goes straight THROUGH its target.
Rule type: PASS-THROUGH (new). Family: archery targets + arrows (new). Arrangement: SHOOTING GALLERY
(5 columns A-E x 9 lanes, every lane shot from the left, faint lane lines, numbers on the left). Every target is hit once every 2.4 s (5 per 12 s loop, random phase): the arrow
arcs in, thunks into the bullseye, the target rocks back and the shaft quivers; then it's pulled out. The odd arrow
never stops at the face: it punches straight through with a paper puff and keeps going until
it ends lodged by its fletching with the whole shaft sticking out of the BACK of the target, pointing the wrong way.
Sound: a soft bow-string twang on each release, a wooden thock on each hit (pentatonic by row, panned by x,
density-normalised); the odd one makes a papery punch-through whff + a thin tick."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/arrows"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 5, 9
LET = "ABCDE"
SX, SY = 178, 118
X0 = 540 - (NC - 1) * SX / 2 + 8
Y0 = 496
TH = math.radians(28)                  # arrows come down at 28 deg and stick at that angle
P = 2.4
NT = int(round(LOOP / P))
TF_, TS, TW = .16, 1.74, .26          # flight, stuck until, withdraw duration (s)
AL = 96                                # arrow length
START = 54                             # tip start distance (along the shaft) before the face
RX, RY = 24, 52                        # target ellipse (3/4 view)
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "7")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))

def pos(i, r): return X0 + i * SX, Y0 + r * SY
T = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        T.append(dict(lab=lab, odd=lab == ODD, x=pos(i, r)[0], y=pos(i, r)[1], r=r, d=1,
                      ph=rng.uniform(0, 1), jit=[(rng.uniform(-6, 6), rng.uniform(-.5, .5)) for _ in range(NT)]))

def state(tg, t):
    """arrow tip offset along lane (relative to face, + = past the face), arrow y, angle(rad), alpha, rock(rad)"""
    v = t / P + tg["ph"]; n = math.floor(v); w = (v - n) * P; j = n % NT
    dy, da = tg["jit"][j]
    odd = tg["odd"]
    end = AL if odd else 0.0                  # odd: tail ends at the face, tip AL past it
    rock = 0.0
    if w < TF_:
        s = w / TF_
        tip = -START + START * s
        a = min(1, s * 5)
        return tip, dy * .3, TH, a, 0.0
    if odd and w < TF_ + .2:                  # punches on through until only the fletching is left in the face
        u = (w - TF_) / .2
        return AL * (1 - (1 - u) ** 2), dy * .3, TH, 1.0, 0.0
    ws = w - TF_ - (.2 if odd else 0)
    if ws < TS - (.2 if odd else 0):
        vib = 0.0 if odd else math.radians(5) * math.exp(-ws * 9) * math.sin(ws * 95)
        if not odd: rock = math.radians(9) * math.exp(-ws * 6) * math.sin(ws * 26 + .9)
        tip = end
        return tip, dy * .3, TH + vib + math.radians(da), 1.0, rock
    ww = ws - (TS - .2 if odd else TS)
    if ww < TW:
        s = ww / TW
        return end - 14 * ss(s), dy * .3, TH + math.radians(da), 1 - ss(s), 0.0
    return 0, 0, 0, 0.0, 0.0

def fly(tg, t):
    v = t / P + tg["ph"]; w = (v - math.floor(v)) * P
    return 1.0 if w < TF_ or (tg["odd"] and w < TF_ + .2) else 0.0

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 34)
F_PL = font(TF_SB, 21)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
F_MARK = font(TF_SERIF_I, 34)
CR = (.95, .9, .8)
AM = (.9, .62, .26)
BR = (.62, .3, .14)
WOOD = (.55, .38, .22)

def target(c, x, y, d, rock, hit):
    """face turned toward the shooter (side -d); rocks back about its foot"""
    c.save()
    c.translate(x, y + RY + 10); c.rotate(math.degrees(rock * d)); c.translate(-x, -(y + RY + 10))
    # stand legs
    lp = skia.Paint(AntiAlias=True, Color4f=c4(WOOD, .95), StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap)
    c.drawLine(x + d * 4, y + RY - 8, x + d * 14, y + RY + 12, lp)
    c.drawLine(x - d * 2, y + RY - 8, x - d * 8, y + RY + 12, lp)
    # thickness (back) + face
    c.drawOval(skia.Rect(x + d * 4 - RX, y - RY, x + d * 4 + RX, y + RY), skia.Paint(AntiAlias=True, Color4f=c4((.38, .25, .14))))
    rings = [(1.0, CR), (.8, AM), (.6, CR), (.4, AM), (.2, BR)]
    for k, (f, col) in enumerate(rings):
        c.drawOval(skia.Rect(x - RX * f, y - RY * f, x + RX * f, y + RY * f), skia.Paint(AntiAlias=True, Color4f=c4(col)))
    g = skia.GradientShader.MakeLinear([(x - RX, y - RY), (x + RX, y + RY)], [skia.Color4f(1, 1, 1, .22).toColor(),
                                        skia.Color4f(0, 0, 0, 0).toColor(), skia.Color4f(0, 0, 0, .28).toColor()], [0, .5, 1])
    c.drawOval(skia.Rect(x - RX, y - RY, x + RX, y + RY), skia.Paint(AntiAlias=True, Shader=g))
    c.drawOval(skia.Rect(x - RX, y - RY, x + RX, y + RY), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
               StrokeWidth=1.6, Color4f=c4((.3, .2, .12), .8)))
    if hit > 0:
        c.drawCircle(x, y, 26, skia.Paint(AntiAlias=True, Color4f=c4((1, .85, .55), .55 * hit),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
    c.restore()

def arrow(c, x, y, d, tip, ay, ang, a, part, streak=0.0):
    """part: 'front' draws the piece on the shooter's side of the face, 'back' the piece past it"""
    if a <= 0: return
    c.save()
    fx = x  # face plane
    if part == "front": c.clipRect(skia.Rect(0, 0, fx, H) if d > 0 else skia.Rect(fx, 0, W, H))
    else: c.clipRect(skia.Rect(fx, 0, W, H) if d > 0 else skia.Rect(0, 0, fx, H))
    tx, ty = x + d * tip * math.cos(TH), y + ay + tip * math.sin(TH)
    c.translate(tx, ty); c.rotate(math.degrees(ang) * d); c.scale(d, 1)
    if streak > 0:
        g = skia.GradientShader.MakeLinear([(-AL - 60, 0), (-AL + 10, 0)], [skia.Color4f(1, .9, .7, 0).toColor(),
                                            skia.Color4f(1, .9, .7, .55 * streak * a).toColor()], [0, 1])
        c.drawRect(skia.Rect(-AL - 60, -3.5, -AL + 10, 3.5), skia.Paint(AntiAlias=True, Shader=g))
    sh = skia.Paint(AntiAlias=True, Color4f=c4((.95, .84, .62), a), StrokeWidth=7.5, StrokeCap=skia.Paint.kRound_Cap)
    c.drawLine(-AL + 4, 0, -7, 0, sh)
    c.drawLine(-AL + 4, -1.4, -7, -1.4, skia.Paint(AntiAlias=True, Color4f=c4((1, .95, .82), .5 * a), StrokeWidth=1.5))
    hp = skia.Path(); hp.moveTo(5, 0); hp.lineTo(-17, -9.5); hp.lineTo(-17, 9.5); hp.close()
    c.drawPath(hp, skia.Paint(AntiAlias=True, Color4f=c4((.95, .8, .46), a)))
    for s in (-1, 1):
        fp = skia.Path(); fp.moveTo(-AL + 28, 0); fp.lineTo(-AL + 3, s * 14); fp.lineTo(-AL - 6, s * 14); fp.lineTo(-AL + 8, 0); fp.close()
        c.drawPath(fp, skia.Paint(AntiAlias=True, Color4f=c4(AM if s < 0 else CR, a)))
    c.drawCircle(-AL + 1, 0, 3.2, skia.Paint(AntiAlias=True, Color4f=c4(BR, a)))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ARROW", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "GOES THROUGH?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for i in range(NC):
            text(c, LET[i], pos(i, 0)[0], 412, F_LAB, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 92, Y0 + r * SY + 12, F_LAB, AMBER, .9)
        # faint lane lines
        for r in range(NR):
            y = Y0 + r * SY + RY + 13
            c.drawLine(122, y, 968, y, skia.Paint(AntiAlias=True, Color4f=c4((.5, .38, .26), .22), StrokeWidth=1.5))
        S = [state(tg, t) for tg in T]
        for tg, (tip, ay, ang, a, rock) in zip(T, S):
            arrow(c, tg["x"], tg["y"], tg["d"], tip, ay, ang, a, "back", fly(tg, t))
        for tg, (tip, ay, ang, a, rock) in zip(T, S):
            v = t / P + tg["ph"]; w = (v - math.floor(v)) * P - TF_
            hit = max(0, 1 - w / .25) if 0 <= w < .25 else 0
            if tg["odd"] and hit > 0:
                c.drawCircle(tg["x"] + 14, tg["y"] + 6, 10 + 22 * (1 - hit), skia.Paint(AntiAlias=True, Color4f=c4(CR, .5 * hit),
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
            target(c, tg["x"], tg["y"], tg["d"], rock, hit)
        for tg, (tip, ay, ang, a, rock) in zip(T, S):
            arrow(c, tg["x"], tg["y"], tg["d"], tip, ay, ang, a, "front", fly(tg, t))
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
def thock(f0, seed, dur=.35):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 26) * .7 + np.sin(2 * np.pi * f0 * 2.7 * t + 1) * np.exp(-t * 45) * .3
    s += np.sin(2 * np.pi * 70 * t) * np.exp(-t * 30) * .5
    n = rg.standard_normal(len(t)) * np.exp(-t * 700) * .35
    return (s + n) * np.minimum(1, t * 5000)
def twang(seed, dur=.22):
    t = np.arange(int(dur * SR)) / SR
    f = 180 * (1 + .04 * np.exp(-t * 30))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 60) * np.minimum(1, t * 200) * .15
    return (s * .5 + n) * np.minimum(1, t * 3000)
def whff(seed, dur=.3):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    n = sosfilt(butter(2, [1800, 6000], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t))) * np.exp(-t * 18)
    tick = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90) * .5
    return (n * 1.4 + tick) * np.minimum(1, t * 3000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, tg in enumerate(T):
        for n in range(-2, NT + 3):
            t0 = (n - tg["ph"]) * P
            for tt, kind in ((t0, "rel"), (t0 + TF_, "hit")):
                if 0 <= tt < LOOP: ev.append((tt, k, kind))
    ht = np.array([e[0] for e in ev if e[2] == "hit"])
    for tt, k, kind in ev:
        tg = T[k]
        if kind == "rel": m.add(twang(k * 13 + int(tt * 10)), tt, .07, tg["x"]); continue
        dens = max(1, (np.abs(ht - tt) < .06).sum())
        if tg["odd"]: m.add(whff(k + int(tt * 100)), tt, .5, tg["x"]); continue
        m.add(thock(note(NR - 1 - tg["r"] + 3, 130.81), k + int(tt * 100)), tt, .5 / math.sqrt(dens), tg["x"])
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
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_arrows.mp4"))
