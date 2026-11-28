"""SPOT IT v3 (15:00, 2026-11-28): WHICH BARRIER / SWINGS OVER THE TOP?
64 identical car-park boom barriers (cream arm with amber stripes, amber tip lamp, cream post housing with a brass
cap) on a PARKING DECK: 8 columns A-H x 8 rows, each row its own concrete deck strip with painted bay lines; the
rows are MIRRORED (odd rows hinge on the left, even rows on the right), so the arms of neighbouring rows sweep in
opposite directions. Letters on top, numbers on the left.
Every arm lifts ~85 deg and drops back down non-stop on a 1.5-2.4 s cycle (+-25% jitter, random phase), with a
rubbery bounce when it lands. ~8% of lifts are legal 'bounce-backs' (overshoot to 100-108 deg and settle back).
ONE barrier (ODD) twice per loop keeps going right over the top (to ~165 deg, over its own post) for ~0.45 s, then
swings back up to 85 deg and carries on as if nothing happened. At those moments 5 decoys overshoot to 100-110 deg
and ~45% of the grid is lifting too.
Rule type: GOES PAST ITS STOP (over the top).  Sound: a soft latch tick when an arm reaches the top, a rubber thock
on landing (pentatonic by row, panned by x, density-normalised); the odd one's tick is a touch brighter (subtle).
12 s seamless loop.
Reproduce: python3 spot_barriers.py render x <outdir>   (preview: ... preview 0,174,330 <outdir>)"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/barriers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 8
CP = float(os.environ.get("CP", "106"))
RP = float(os.environ.get("RP", "116"))
Y0 = float(os.environ.get("Y0", "640"))       # ground line of row 1
X0 = 540 + 16 - 3.5 * CP
PCT = int(os.environ.get("PCT", "5"))
ODD = (os.environ.get("OL", "B"), int(os.environ.get("ON", "6")))
NDEC = int(os.environ.get("NDEC", "5"))
BURST = float(os.environ.get("BURST", "0.45"))
BT = [float(os.environ.get("B1", "5.8")), float(os.environ.get("B2", "10.6"))]
OVER = float(os.environ.get("OVER", "165"))
rng = np.random.default_rng(int(os.environ.get("SEED", "2815")))

def col_x(i): return X0 + i * CP
def row_y(r): return Y0 + r * RP
ARM = 88.0          # arm length from pivot
AW = 16.0           # arm thickness
UP = 85.0

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        left = (r % 2 == 0)                       # hinge side
        x = col_x(i); y = row_y(r)
        px = x - 40 if left else x + 40
        G.append(dict(lab=lab, odd=lab == ODD, x=x, y=y, r=r, i=i, left=left, px=px, py=y - 30, ev=[],
                      per=rng.uniform(1.5, 2.4)))
ODDG = [g for g in G if g["odd"]][0]

def mk(t0, kind, peak=None):
    if peak is None:
        peak = UP + rng.uniform(2, 5) if kind == "lift" else rng.uniform(100, 110)
    return dict(t0=t0, kind=kind, Tu=rng.uniform(.38, .50), hold=rng.uniform(.18, .55),
                Td=rng.uniform(.30, .40), peak=peak, wob=rng.uniform(2, 4))
def span(e): return e["Tu"] + (.30 if e["kind"] == "over" else 0) + e["hold"] + e["Td"] + .35
def fits(g, e):
    for o in g["ev"]:
        for sh in (-LOOP, 0, LOOP):
            a0, a1 = o["t0"] + sh, o["t0"] + sh + span(o)
            if e["t0"] < a1 and a0 < e["t0"] + span(e): return False
    return True

for tb in BT:
    e = mk(0, "over", peak=OVER); e["t0"] = tb - e["Tu"] * .75
    ODDG["ev"].append(e)
    cand = [g for g in G if not g["odd"] and not (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1)]
    perm = rng.permutation(len(cand))
    nd = 0
    for j in perm:
        if nd < NDEC:
            d = mk(0, "decoy"); d["t0"] = tb - d["Tu"] * .8 + rng.uniform(-.12, .12)
            if fits(cand[j], d): cand[j]["ev"].append(d); nd += 1
        elif rng.random() < BURST:
            d = mk(tb - .35 + rng.uniform(-.3, .2), "lift")
            if fits(cand[j], d): cand[j]["ev"].append(d)
for g in G:
    t = rng.uniform(0, g["per"])
    while t < LOOP:
        e = mk(t, "decoy" if (not g["odd"] and rng.random() < .08) else "lift")
        if fits(g, e): g["ev"].append(e)
        t += g["per"] * rng.uniform(.75, 1.25)
for g in G:
    g["all"] = sorted([dict(e, t0=e["t0"] + sh) for e in g["ev"] for sh in (-LOOP, 0, LOOP)], key=lambda e: e["t0"])

def ss_(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def eob(u, s=1.6):  # ease-out-back
    u = min(1, max(0, u)) - 1; return 1 + (s + 1) * u ** 3 + s * u ** 2
def angle(g, t):
    last = None
    for e in g["all"]:
        if e["t0"] <= t: last = e
        else: break
    if last is None: return 0.0
    dt = t - last["t0"]
    if last["kind"] == "over":
        if dt < last["Tu"]: return OVER * ss_(dt / last["Tu"])
        dt -= last["Tu"]
        if dt < .30: return OVER + (UP - OVER) * ss_(dt / .30)
        dt -= .30
        top = UP
    elif dt < last["Tu"]:
        u = dt / last["Tu"]
        if last["kind"] == "decoy":   # overshoot past 100 then settle to UP
            k = ss_(u); return last["peak"] * k if u < .7 else last["peak"] + (UP - last["peak"]) * ss_((u - .7) / .3)
        return UP * eob(u, 1.2) if u < 1 else UP
    else:
        dt -= last["Tu"]; top = UP
    if dt < last["hold"]:
        return top + last["wob"] * math.exp(-dt * 8) * math.sin(dt * 22)
    dt -= last["hold"]
    if dt < last["Td"]:
        u = dt / last["Td"]; return top * (1 - u * u)
    dt -= last["Td"]
    return 9.0 * math.exp(-dt * 7) * abs(math.sin(dt * 17))

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x0, y0), (x1, y1)], [c4(cc).toColor() for cc in cols], pos))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH BARRIER", "SWINGS OVER THE TOP?"
def fit(s, size, maxw=860):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_Q = F_Q2 if F_Q2.getSize() < F_Q.getSize() else F_Q
F_Q2 = F_Q
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

CRM = (.96, .91, .82); CRM_LO = (.78, .71, .60)
BRASS = (.86, .70, .40)
AMB = (.93, .60, .20)

def static_layer():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawImage(background(1000), 0, 0)
        xl, xr = col_x(0) - CP / 2 + 4, col_x(NC - 1) + CP / 2 - 4
        for r in range(NR):
            y = row_y(r)
            # concrete deck strip
            rect = skia.Rect(xl, y - 4, xr, y + 26)
            c.drawRRect(skia.RRect.MakeRectXY(rect, 6, 6), lin(0, y - 4, 0, y + 26, [(.30, .25, .20), (.18, .14, .11)]))
            c.drawLine(xl + 6, y - 3, xr - 6, y - 3, S_((.70, .60, .46), .30, 1.2))
            # painted bay lines between barriers
            for i in range(1, NC):
                bx = col_x(0) - CP / 2 + i * CP
                c.drawLine(bx, y + 4, bx + (6 if r % 2 == 0 else -6), y + 22, S_(AMB, .30, 3))
            # warm lit back wall behind each row + a pool of lamp light under every barrier
            c.drawRect(skia.Rect(xl, y - 100, xr, y - 4), lin(0, y - 100, 0, y - 4, [(.12, .08, .05), (.30, .19, .10)]))
            for i in range(NC):
                cx = col_x(i)
                c.drawOval(skia.Rect(cx - 50, y - 70, cx + 50, y + 10),
                           skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
                               (cx, y - 18), 56, [c4((1, .62, .25), .26).toColor(), c4((1, .62, .25), 0).toColor()])))
            c.drawRRect(skia.RRect.MakeRectXY(rect, 6, 6), lin(0, y - 4, 0, y + 26, [(.36, .29, .22), (.20, .15, .11)]))
            c.drawLine(xl + 6, y - 3, xr - 6, y - 3, S_((.85, .70, .48), .45, 1.5))
            for i in range(1, NC):
                bx = col_x(0) - CP / 2 + i * CP
                c.drawLine(bx, y + 4, bx + (6 if r % 2 == 0 else -6), y + 22, S_(AMB, .45, 3))
    return s.makeImageSnapshot()

def arm_path():
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-14, -AW / 2, ARM, AW / 2), AW / 2, AW / 2)); return p
ARMP = arm_path()

def draw_barrier(c, g, t):
    a = angle(g, t)
    px, py = g["px"], g["py"]
    sgn = 1 if g["left"] else -1
    # shadow on deck
    c.drawOval(skia.Rect(px - 18, g["y"] - 2, px + 18, g["y"] + 6), P_((0, 0, 0), .35))
    # arm (drawn in a local frame pointing along +x, mirrored for right-hinged)
    c.save(); c.translate(px, py)
    if not g["left"]: c.scale(-1, 1)
    c.rotate(-a)
    c.drawPath(ARMP, lin(0, -AW / 2, 0, AW / 2, [(1, .97, .90), CRM, CRM_LO], [0, .4, 1]))
    c.save(); c.clipPath(ARMP, doAntiAlias=True)
    for k in range(5):
        x0 = 8 + k * 16
        p = skia.Path(); p.moveTo(x0, AW / 2 + 1); p.lineTo(x0 + 7, AW / 2 + 1); p.lineTo(x0 + 13, -AW / 2 - 1); p.lineTo(x0 + 6, -AW / 2 - 1); p.close()
        c.drawPath(p, P_(AMB, .95))
    c.restore()
    c.drawPath(ARMP, S_((.45, .36, .26), .6, 1))
    # counterweight + tip lamp
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-22, -10, -8, 10), 3, 3), P_((.32, .26, .20)))
    c.drawCircle(ARM - 4, 0, 5.2, P_((1, .55, .18)))
    c.drawCircle(ARM - 4, 0, 15, P_((1, .55, .18), .16)); c.drawCircle(ARM - 4, 0, 9, P_((1, .62, .25), .3))
    c.restore()
    # post housing (in front of the arm root)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(px - 13, py - 6, px + 13, g["y"] + 2), 5, 5),
                lin(px - 13, 0, px + 13, 0, [CRM, (1, .97, .90), CRM_LO]))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(px - 13, py - 6, px + 13, g["y"] + 2), 5, 5), S_((.45, .36, .26), .6, 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(px - 15, py - 10, px + 15, py - 3), 3, 3), P_(BRASS))
    c.drawCircle(px, py, 4.5, P_((.30, .24, .18)))
    c.drawCircle(px, py, 2.0, P_(BRASS))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(px - 6, py + 10, px + 6, py + 16), 2, 2), P_(AMB, .85))

BASE = None
def frame(f):
    global BASE
    if BASE is None: BASE = static_layer()
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BASE, 0, 0)
        text(c, L1, W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, L2, W / 2, 354, F_Q2, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], col_x(i), 520, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 116, row_y(r) - 22, F_AX, AMBER, .9)
        for g in G: draw_barrier(c, g, t)
        yb = 1560
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 38, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 36, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1646, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def tick(seed, f0, bright=False):
    rg = np.random.default_rng(seed)
    n = int(.16 * SR); t = np.arange(n) / SR
    f = f0 * (1.04 if bright else 1.0)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 34) * .16 + np.sin(2 * np.pi * f * 2.4 * t) * np.exp(-t * 70) * .04
    s += bp(rg.standard_normal(n), 1800, 5500) * np.exp(-t * 260) * (.32 if bright else .26)
    return s
def thock(seed):
    rg = np.random.default_rng(seed)
    n = int(.12 * SR); t = np.arange(n) / SR
    return bp(rg.standard_normal(n), 200, 1100) * np.exp(-t * 60) * .35 + np.sin(2 * np.pi * 120 * t) * np.exp(-t * 40) * .22
def whirr(seed, dur):
    rg = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur) ** 2
    return bp(rg.standard_normal(n), 300, 900) * env * .05

def audio(path):
    m = Mix(LOOP + 2)
    ev = []
    for k, g in enumerate(G):
        for e in g["ev"]:
            t0 = e["t0"]
            ex = .30 if e["kind"] == "over" else 0
            ev.append((k, (t0 + e["Tu"] * .9) % LOOP, "tick", e["kind"] == "over", 0))
            ev.append((k, t0 % LOOP, "whirr", False, e["Tu"]))
            ev.append((k, (t0 + e["Tu"] + ex + e["hold"] + e["Td"]) % LOOP, "thock", False, 0))
    tt = np.array([e[1] for e in ev])
    for k, t0, typ, odd, d in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(tt - t0) < .12).sum()))
        if typ == "tick":
            s = tick(k * 131 + int(t0 * 977), note(6 + (7 - g["r"]) // 2 + (g["i"] % 3), 220.0), odd); a = .75 / dens
        elif typ == "thock":
            s = thock(k * 71 + int(t0 * 31)); a = .55 / dens
        else:
            s = whirr(k * 17 + int(t0 * 53), max(.2, d)); a = .5 / dens
        m.add(s, t0, a, g["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 90, 400) * .006
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "barriers; odd", ODD, "over the top at", BT)
    print("lifts/barrier", min(len(g["ev"]) for g in G), max(len(g["ev"]) for g in G),
          "odd events", [(round(e["t0"], 2), e["kind"]) for e in ODDG["ev"]])
    print("decoys:", sorted([(g["lab"], round(e["t0"], 2)) for g in G for e in g["ev"] if e["kind"] == "decoy"]))
    for tb in BT:
        mov = sum(1 for g in G if abs(angle(g, tb) - angle(g, tb - .1)) > 2)
        print("moving at", tb, ":", mov, " odd angle", round(angle(ODDG, tb), 1))
    ts = np.arange(0, LOOP, 1 / FPS)
    above = [t for t in ts if angle(ODDG, t) > 100]
    print("odd >100deg frames", len(above), "≈", round(len(above) / FPS, 2), "s")
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_barriers.mp4"))
