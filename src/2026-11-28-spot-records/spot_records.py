"""SPOT IT v3 (10:00, 2026-11-28): WHICH RECORD / SPINS BACKWARDS?
72 identical turntables (black vinyl, amber label with a cream wedge, a cream rim dot, brass tonearm) in DJ CONSOLES:
9 rows x 4 walnut consoles, each console holding a PAIR of decks (columns A-H); letters on top, numbers on the left.
Every record spins clockwise non-stop, 6-10 whole turns per 12 s loop (+-25% speed jitter) from a random angle.
Now and then a record is legally 'held' like a DJ hand-brake: it slows to a dead stop and starts again, forwards.
ONE record (ODD) twice per loop SPINS BACKWARDS: it slows, swings ~half a turn anticlockwise for ~0.5 s, then carries
on clockwise. At each of those moments 5 decoys do the legal hand-brake.
Rule type: WRONG WAY as a brief reversal (DJ scratch).  Sound: a soft needle tick each time a record's rim dot passes
its tonearm (panned by x, density-normalised, a quiet crackle bed), a felt rub at every brake; the odd record's rub
is a touch brighter (subtle). 12 s seamless loop.  Reproduce: python3 spot_records.py render x <outdir>"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/records"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 9
PITCH = float(os.environ.get("PITCH", "100"))     # deck pitch inside a console
PGAP = float(os.environ.get("PGAP", "14"))        # extra gap between consoles
RP = float(os.environ.get("RP", "108"))
RR = float(os.environ.get("RR", "45"))            # record radius
Y0 = 580.0
PCT = int(os.environ.get("PCT", "4"))
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "8")))
NDEC = int(os.environ.get("NDEC", "5"))
DREV = float(os.environ.get("DREV", "0.8"))       # reversal window
WR = float(os.environ.get("WR", "2.0"))          # peak backwards speed, rev/s
BT = [float(os.environ.get("B1", "5.3")), float(os.environ.get("B2", "10.5"))]
rng = np.random.default_rng(int(os.environ.get("SEED", "2811")))

X0 = 540 + 14 - (3 * (2 * PITCH + PGAP) / 2 + PITCH / 2) / 1
def col_x(i): return X0 + (i // 2) * (2 * PITCH + PGAP) + (i % 2) * PITCH
def row_y(r): return Y0 + r * RP

def W_int(u):          # integral of sin^2(pi u) du from 0..u, u in [0,1]
    u = min(1.0, max(0.0, u))
    return u / 2 - math.sin(2 * math.pi * u) / (4 * math.pi)

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i), y=row_y(r), r=r, i=i, ev=[],
                      k=int(rng.integers(6, 11)), ph=rng.uniform(0, 1)))
ODDG = [g for g in G if g["odd"]][0]
ODDG["k"] = 8
for tb in BT:
    ODDG["ev"].append(("rev", tb - DREV / 2, DREV))
    cand = [g for g in G if not g["odd"] and not (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1)]
    for j in rng.permutation(len(cand))[:NDEC]:
        d = rng.uniform(.7, 1.0)
        cand[j]["ev"].append(("brake", tb - d / 2 + rng.uniform(-.12, .12), d))
for g in G:            # background brakes so a stop is never rare
    if g["odd"]: continue
    if rng.random() < .45:
        d = rng.uniform(.6, 1.1); ts = rng.uniform(.4, LOOP - 1.6)
        if all(abs(ts - e[1]) > 1.5 for e in g["ev"]) and all(abs(ts + d / 2 - b) > .9 for b in BT):
            g["ev"].append(("brake", ts, d))
for g in G:            # solve base speed so the loop closes on whole turns
    def_ = sum(e[2] / 2 for e in g["ev"])
    extra = sum(WR * e[2] / 2 for e in g["ev"] if e[0] == "rev")
    g["w0"] = (g["k"] + extra) / (LOOP - def_)

def turns(g, t):
    th = g["ph"] + g["w0"] * t
    for kind_, ts, d in g["ev"]:
        a = g["w0"] + (WR if kind_ == "rev" else 0.0)
        th -= a * d * W_int((t - ts) / d)
    return th

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def rad(cx, cy, r, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (cx, cy), r, [c4(cc).toColor() for cc in cols], pos))
def lin(x0, y0, x1, y1, cols):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x0, y0), (x1, y1)], [c4(cc).toColor() for cc in cols]))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH RECORD", "SPINS BACKWARDS?"
def fit(s, size, maxw=860):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_Q = F_Q2 if F_Q2.getSize() < F_Q.getSize() else F_Q
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

AMB_HI, AMB, AMB_LO = (1.0, .80, .45), (.90, .58, .20), (.60, .34, .10)
CRM = (.96, .91, .82)
BRASS = (.86, .70, .40)
VINYL = (.07, .065, .06)

def static_layer():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawImage(background(1000), 0, 0)
        h = PITCH / 2 - 2
        for r in range(NR):
            y = row_y(r)
            for p in range(4):
                xa, xb = col_x(2 * p) - h - 6, col_x(2 * p + 1) + h + 6
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xa + 4, y - h - 2 + 8, xb + 4, y + h + 6 + 8), 10, 10),
                            P_((0, 0, 0), .35))                                                # shadow
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xa, y - h - 2, xb, y + h + 6), 10, 10),
                            lin(0, y - h, 0, y + h, [(.40, .27, .16), (.22, .14, .08)]))     # walnut console
                c.drawLine(xa + 8, y - h - .5, xb - 8, y - h - .5, S_((.66, .50, .32), .5, 1.4))
                for q in (0, 1):
                    x = col_x(2 * p + q)
                    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - h + 3, y - h + 1, x + h - 3, y + h + 3), 6, 6),
                                P_((.12, .10, .085)))                                          # deck top
                    c.drawCircle(x, y + 2, RR + 3, P_((.05, .045, .04)))                       # platter rim
                    c.drawCircle(x, y + 2, RR + 3, S_((.55, .48, .40), .35, 1.2))
                    c.drawCircle(x + h - 10, y + h - 7, 3.2, P_(BRASS, .7))                    # speed knob
                xm = (col_x(2 * p) + col_x(2 * p + 1)) / 2
                c.drawLine(xm, y - h + 4, xm, y + h, S_(BRASS, .55, 2))                        # brass seam
    return s.makeImageSnapshot()

def draw_record(c, g, t):
    x, y = g["x"], g["y"] + 2
    th = turns(g, t) * 360.0
    c.drawCircle(x, y, RR, rad(x, y, RR, [(.16, .15, .14), VINYL, (.10, .095, .09), (.03, .03, .03)], [0, .3, .85, 1]))
    for rr_ in (RR * .55, RR * .68, RR * .80, RR * .92):
        c.drawCircle(x, y, rr_, S_((.30, .28, .26), .35, .8))
    c.save(); c.translate(x, y); c.rotate(th)
    c.drawCircle(0, 0, RR * .38, rad(-3, -4, RR * .45, [AMB_HI, AMB, AMB_LO], [0, .5, 1]))       # label
    wedge = skia.Path(); wedge.moveTo(0, 0)
    wedge.arcTo(skia.Rect(-RR * .38, -RR * .38, RR * .38, RR * .38), -90, 110, False); wedge.close()
    c.drawPath(wedge, P_(CRM, .96))
    c.drawCircle(0, -RR * .80, 6.0, P_(CRM, .97))                                                # rim dot
    c.drawLine(0, -RR * .36, 0, -RR * .74, S_(CRM, .92, 7.0))                                    # bold stripe to the rim
    c.restore()
    # static sheen (light is fixed, the record turns under it)
    sh = skia.Path(); sh.addArc(skia.Rect(x - RR * .86, y - RR * .86, x + RR * .86, y + RR * .86), 200, 50)
    c.drawPath(sh, S_((1, 1, 1), .10, 5))
    sh2 = skia.Path(); sh2.addArc(skia.Rect(x - RR * .86, y - RR * .86, x + RR * .86, y + RR * .86), 20, 50)
    c.drawPath(sh2, S_((1, 1, 1), .06, 5))
    c.drawCircle(x, y, 2.6, P_(BRASS))
    # tonearm (static, resting on the outer groove)
    px, py = x + RR + 1, y - RR + 4
    hx, hy = x + RR * .55, y + RR * .58
    c.drawCircle(px, py, 6.5, P_((.25, .22, .19))); c.drawCircle(px, py, 4, P_(BRASS))
    c.drawLine(px, py, hx + 4, hy - 8, S_(BRASS, .95, 3.0))
    c.save(); c.translate(hx, hy); c.rotate(35)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-5, -8, 5, 6), 2, 2), P_((.75, .62, .38)))
    c.restore()

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
            text(c, LET[i], col_x(i), 514, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 110, row_y(r) + 12, F_AX, AMBER, .9)
        for g in G: draw_record(c, g, t)
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
def tick(seed, f0):
    rg = np.random.default_rng(seed)
    n = int(.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 90) * .25 + bp(rg.standard_normal(n), 1500, 5000) * np.exp(-t * 160) * .3)
def rub(seed, d, bright=False):
    rg = np.random.default_rng(seed)
    n = int(d * SR); t = np.arange(n) / SR
    lo, hi = (380, 1500) if bright else (300, 1150)
    env = np.sin(np.pi * t / d) ** 2
    return bp(rg.standard_normal(n), lo, hi) * env * .30

def audio(path):
    m = Mix(LOOP + 2)
    ev = []
    ts = np.arange(0, LOOP, 1 / 1000)
    for k, g in enumerate(G):
        th = np.array([turns(g, t) for t in ts]) - .14            # rim dot passes the tonearm
        cr = np.nonzero(np.floor(th[1:]) != np.floor(th[:-1]))[0]
        for j in cr: ev.append((k, ts[j], "tick"))
        for kd, t0, d in g["ev"]: ev.append((k, t0 % LOOP, kd, d))
    et = np.array([e[1] for e in ev if e[2] == "tick"])
    for e in ev:
        k, t0, typ = e[0], e[1], e[2]
        g = G[k]
        if typ == "tick":
            dens = math.sqrt(max(1, (np.abs(et - t0) < .1).sum()))
            s = tick(k * 131 + int(t0 * 977), note(4 + (8 - g["r"]) // 2 + (g["i"] % 3), 220.0)); a = .55 / dens
        else:
            s = rub(k * 71 + int(t0 * 31), e[3], typ == "rev"); a = .28
        m.add(s, t0, a, g["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 200, 900) * .004
        pops = rg.random(n) < 30 / SR                                  # faint vinyl crackle
        buf += sosfilt(butter(2, 2500, btype="high", fs=SR, output="sos"), pops * rg.standard_normal(n)) * .02
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "records; odd", ODD, "reverses at", BT, "w0", round(ODDG["w0"], 3))
    print("loop closes:", max(abs(turns(g, LOOP) - turns(g, 0) - g["k"]) for g in G),
          "w0 range", round(min(g["w0"] for g in G), 2), round(max(g["w0"] for g in G), 2))
    print("decoys:", sorted([(g["lab"], round(e[1] + e[2] / 2, 2)) for g in G if not g["odd"] for e in g["ev"]
                             if any(abs(e[1] + e[2] / 2 - b) < .4 for b in BT)]))
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_records.mp4"))
