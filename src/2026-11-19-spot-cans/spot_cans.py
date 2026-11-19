"""SPOT IT v3 (18:00, 2026-11-19): 50 brass watering cans in a CHECKERBOARD (9 columns A-I x 11 rows, cans only on
alternate squares). BREAKS PHYSICS: every can tips forward on its front edge every 3 s and pours a stream that falls
in a parabola into the brass bowl below it; on the odd can the water falls UP (gravity reversed): the stream curls
up into the air and breaks into rising droplets, and its bowl never ripples.
Sound: soft water trickle per pour (panned by x, density-normalised), a brass tap as each can sets down; the odd can's
stream gives a rising bubbly whistle instead of a trickle."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/cans"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 9, 10
LET = "ABCDEFGHI"
SX, SY = 94, 102
X0 = 540 - (NC - 1) * SX / 2 - 14
Y0 = 512
P = 3.0
TH = math.radians(47)
G = 1100.0
V0 = 85.0
SC = float(os.environ.get("SC", "0.86"))
ODD = (os.environ.get("OL", "G"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))

def pos(i, r): return X0 + i * SX, Y0 + r * SY

C = []
for r in range(NR):
    for i in range(NC):
        if (i + r) % 2: continue
        lab = (LET[i], r + 1)
        C.append(dict(lab=lab, odd=lab == ODD, x=pos(i, r)[0], y=pos(i, r)[1], r=r, i=i,
                      ph=(rng.uniform(0, 1) * .8 + .2 * ((i + r) / 18.0)) % 1.0, amp=rng.uniform(.92, 1.06)))
print(len(C), "cans")

# timeline within one period (seconds): rest, tip up, pour, tip back
T_UP0, T_UP1, T_DN0, T_DN1 = 0.0, 0.45, 1.75, 2.2
def tilt(cn, t):
    u = ((t / P + cn["ph"]) % 1.0) * P
    if u < T_UP1: a = ss(u / T_UP1)
    elif u < T_DN0: a = 1 + .05 * math.sin((u - T_UP1) * 9) * math.exp(-(u - T_UP1) * 2.5)
    elif u < T_DN1: a = 1 - ss((u - T_DN0) / (T_DN1 - T_DN0))
    else:
        w = u - T_DN1; a = -.035 * math.exp(-w * 7) * math.sin(w * 30)  # little rock on landing
    return TH * cn["amp"] * a

# can geometry (local, pivot = front-bottom edge at origin, y down)
TIP = np.array([40.0, -50.0]) * SC
TIPDIR = np.array([0.78, -0.62])
def rot(v, a):
    c, s = math.cos(a), math.sin(a); return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])
def pivot(cn): return np.array([cn["x"] + 10, cn["y"]])
def bowl(cn): return np.array([cn["x"] + 84 * SC, cn["y"] + 26 * SC])

def flow(a): return min(1.0, max(0.0, (a - math.radians(30)) / math.radians(12)))  # 0..1 when tilted enough

def particles(cn, t):
    """sample emitted water particles; returns list of (x, y, age, alive)"""
    pts = []
    bw = bowl(cn)
    life = .55 if cn["odd"] else .5
    for k in range(60):
        age = k / 120.0
        tau = t - age
        a = tilt(cn, tau)
        if flow(a) <= 0.02: pts.append(None); continue
        p0 = pivot(cn) + rot(TIP, a)
        d = rot(TIPDIR, a)
        v = d * V0
        g = -G * .55 if cn["odd"] else G
        x = p0[0] + v[0] * age
        y = p0[1] + v[1] * age + .5 * g * age * age
        if not cn["odd"] and y > bw[1] - 4: pts.append(("hit", x, bw[1] - 4, age)); break
        if age > life: break
        pts.append((x, y, age, flow(a)))
    return pts

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 34)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
BR = (.90, .70, .36); BR_D = (.48, .31, .12); BR_L = (1.0, .9, .64)
WATER = (.72, .90, 1.0)

def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)

def can_paths():
    s = SC
    body = skia.Path()
    body.moveTo(-50 * s, 0); body.lineTo(0, 0); body.lineTo(-3 * s, -46 * s); body.lineTo(-47 * s, -46 * s); body.close()
    spout = skia.Path()
    spout.moveTo(-4 * s, -16 * s); spout.lineTo(TIP[0] - 4 * s, TIP[1] - 4 * s); spout.lineTo(TIP[0] + 4 * s, TIP[1] + 5 * s)
    spout.lineTo(-2 * s, -3 * s); spout.close()
    return body, spout
BODY, SPOUT = can_paths()

def draw_can(c, cn, a):
    pv = pivot(cn)
    c.save(); c.translate(pv[0], pv[1]); c.rotate(math.degrees(a))
    s = SC
    lit = 1.0
    g = skia.GradientShader.MakeLinear([(-50 * s, 0), (0, 0)], [c4(BR_D).toColor(), c4(BR_L).toColor(), c4(BR).toColor(),
                                        c4([v * .8 for v in BR_D]).toColor()], [0, .35, .6, 1])
    c.drawPath(SPOUT, P_(BR))
    c.drawPath(SPOUT, P_(BR_L, .6, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2))
    # rose (sprinkler head) at spout tip
    c.save(); c.translate(TIP[0], TIP[1]); c.rotate(math.degrees(math.atan2(TIPDIR[1], TIPDIR[0])))
    c.drawRoundRect(skia.Rect(-2 * s, -8 * s, 6 * s, 8 * s), 3 * s, 3 * s, P_(BR_L))
    c.restore()
    # handle
    c.drawArc(skia.Rect(-46 * s, -70 * s, -8 * s, -30 * s), 180, 180, False,
              P_(BR_D, 1, Style=skia.Paint.kStroke_Style, StrokeWidth=6 * s, StrokeCap=skia.Paint.kRound_Cap))
    c.drawArc(skia.Rect(-46 * s, -70 * s, -8 * s, -30 * s), 200, 140, False,
              P_(BR_L, .5, Style=skia.Paint.kStroke_Style, StrokeWidth=2 * s))
    c.drawPath(BODY, skia.Paint(AntiAlias=True, Shader=g))
    # cream band
    c.drawRect(skia.Rect(-48.6 * s, -30 * s, -1.4 * s, -22 * s), P_(CREAM, .92))
    c.drawRect(skia.Rect(-47 * s, -46 * s, -3 * s, -43 * s), P_(BR_L, .8))
    c.restore()

def draw_bowl_back(c, cn, rip):
    b = bowl(cn); s = SC
    c.drawOval(skia.Rect(b[0] - 26 * s, b[1] - 6 * s, b[0] + 26 * s, b[1] + 6 * s), P_((.14, .09, .05)))
    c.drawOval(skia.Rect(b[0] - 22 * s, b[1] - 4 * s, b[0] + 22 * s, b[1] + 4 * s), P_(WATER, .28))
    for (rr, al) in rip:
        c.drawOval(skia.Rect(b[0] - rr, b[1] - rr * .22, b[0] + rr, b[1] + rr * .22),
                   P_(WATER, al, Style=skia.Paint.kStroke_Style, StrokeWidth=2))
def draw_bowl_front(c, cn):
    b = bowl(cn); s = SC
    p = skia.Path(); p.moveTo(b[0] - 26 * s, b[1]); p.cubicTo(b[0] - 24 * s, b[1] + 22 * s, b[0] + 24 * s, b[1] + 22 * s, b[0] + 26 * s, b[1])
    p.cubicTo(b[0] + 20 * s, b[1] + 6 * s, b[0] - 20 * s, b[1] + 6 * s, b[0] - 26 * s, b[1]); p.close()
    g = skia.GradientShader.MakeLinear([(b[0] - 26 * s, 0), (b[0] + 26 * s, 0)], [c4(BR_D).toColor(), c4(BR_L).toColor(),
                                        c4(BR_D).toColor()], [0, .4, 1])
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=g))

def ripples(cn, t):
    if cn["odd"]: return []
    out = []
    for k in range(4):
        tau = t - k * .16 - .12
        if flow(tilt(cn, tau)) > .3:
            w = (t - tau) % .16 + k * .16
            out.append((6 + w * 60, .5 * (1 - w / .64)))
    return out

def draw_water(c, cn, t):
    pts = particles(cn, t)
    seg = []
    segs = []
    hit = None
    for q in pts:
        if q is None:
            if seg: segs.append(seg); seg = []
            continue
        if q[0] == "hit": hit = q; seg.append((q[1], q[2], q[3], 1.0)); break
        seg.append(q)
    if seg: segs.append(seg)
    for sg in segs:
        if len(sg) < 2: continue
        for k in range(len(sg) - 1):
            x0, y0, a0, f0 = sg[k]; x1, y1, a1, f1 = sg[k + 1]
            if cn["odd"]:
                al = max(0, 1 - a0 / .55) ** .7
                wdt = 6.0 * SC * (1 - .5 * a0 / .55)
            else:
                al, wdt = .95, 6.0 * SC
            c.drawLine(x0, y0, x1, y1, P_(WATER, al * min(1, f0 * 1.5), StrokeWidth=max(1.2, wdt), StrokeCap=skia.Paint.kRound_Cap))
        # glints / droplets
        x, y, a, f = sg[-1]
        if cn["odd"]:
            for d in range(5):
                rr = np.random.default_rng(int(t * 30) * 7 + d)
                dx, dy = rr.uniform(-10, 10), rr.uniform(-16, 4)
                c.drawCircle(x + dx, y + dy, 2.4, P_(WATER, .7 * f))
    if hit is not None:
        x, y = hit[1], hit[2]
        for d in range(3):
            ph = (t * 7 + d / 3) % 1
            c.drawCircle(x + (d - 1) * 7 * ph, y - 9 * math.sin(ph * math.pi), 1.8, P_(WATER, .7 * (1 - ph)))

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH ONE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        # checkerboard squares (faint)
        for r in range(NR):
            for i in range(NC):
                if (i + r) % 2: continue
                x, y = pos(i, r)
                c.drawRoundRect(skia.Rect(x - 44, y - 66, x + 78, y + 44), 10, 10, P_((1, .9, .7), .035))
        for i in range(NC):
            text(c, LET[i], pos(i, 0)[0] + 10, 430, F_LAB, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 92 if r % 2 == 0 else 92, Y0 + r * SY - 8, F_LAB, AMBER, .9)
        for cn in C:
            a = tilt(cn, t)
            draw_bowl_back(c, cn, ripples(cn, t))
            # ground shadow + plinth
            pv = pivot(cn)
            c.drawOval(skia.Rect(pv[0] - 52 * SC, pv[1] - 3, pv[0] + 4, pv[1] + 5), P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
            draw_can(c, cn, a)
            draw_water(c, cn, t)
            draw_bowl_front(c, cn)
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
def trickle(seed, dur, rise=False):
    n = int(dur * SR); t = np.arange(n) / SR
    rg = np.random.default_rng(seed)
    x = rg.standard_normal(n)
    sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    sp *= np.exp(-((fr - 2400) / 1400) ** 2); x = np.fft.irfft(sp, n); x /= np.abs(x).max() + 1e-9
    # bubbly droplets
    s = x * .5
    for k in range(int(dur * 18)):
        t0 = rg.uniform(0, dur - .05); f0 = rg.uniform(700, 1400)
        i0 = int(t0 * SR); m = int(.04 * SR); tt = np.arange(m) / SR
        s[i0:i0 + m] += .35 * np.sin(2 * np.pi * (f0 + 9000 * tt) * tt) * np.exp(-tt * 90)
    if rise:
        f = 500 + 900 * (t / dur) ** 1.4
        s = .25 * s + .8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (.6 + .4 * np.sin(2 * np.pi * 14 * t))
    env = np.minimum(1, t / .06) * np.minimum(1, (dur - t) / .12)
    return s * env
def tap(f0, seed, dur=.3):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + rg.uniform(0, 6)) * np.exp(-t * d) for m, d, a in ((1, 18, .6), (2.7, 30, .3), (5.1, 50, .15)))
    return s * np.minimum(1, t * 4000)

def audio(path):
    m = Mix(LOOP + 1.8)
    ev = []
    for k, cn in enumerate(C):
        for n in range(-2, 7):
            t0 = (n - cn["ph"]) * P
            ev.append((t0 + .3, k, "pour")); ev.append((t0 + T_DN1, k, "tap"))
    pt = np.array([e[0] for e in ev if e[2] == "pour"])
    for tt, k, kind in ev:
        if not (0 <= tt < LOOP): continue
        cn = C[k]; tt2 = tt
        dens = max(1, (np.abs(pt - tt) < 1.2).sum())
        if kind == "pour":
            snd = trickle(k * 31 + int(tt * 10), 1.5, rise=cn["odd"])
            m.add(snd, tt2, (.16 if cn["odd"] else .5 / math.sqrt(dens)), cn["x"])
        else:
            m.add(tap(note(NR - 1 - cn["r"] + 5, 196.0), k * 100 + int(tt * 50)), tt2, .32 / math.sqrt(max(1, dens / 4)), cn["x"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_cans.mp4"))
