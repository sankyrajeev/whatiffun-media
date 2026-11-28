"""SPOT IT v3 (13:00, 2026-11-28): WHICH TOASTER / FLIPS ITS TOAST?
64 identical cream pop-up toasters (brass lever + amber dial), one slice of toast each, on a CHECKERBOARD of kitchen
tiles (8 columns A-H x 8 rows); letters on top, numbers on the left.
Every toaster pops its slice up at random times (every ~1.5-2.4 s, +-25% jitter, random phase): the lever snaps up,
the toast flies straight up with a little wobble, lands, sits high for a beat, then the lever is pressed down again.
ONE toaster (ODD) twice per loop launches its toast into a full 360-degree SOMERSAULT (~0.6 s airtime), then it
lands upright as if nothing happened. At those moments ~40% of the grid pops too and 5 decoys pop high with a big
legal tilt (22-30 deg and back) that never goes over.
Rule type: FLIPS WHEN NONE SHOULD (a somersault among straight pops).  Sound: a soft spring 'ting' on every pop,
a light toast thud on landing, a lever click on every press (pentatonic by row, panned by x, density-normalised);
the odd flip's ting is a touch brighter (subtle). 12 s seamless loop.
Reproduce: python3 spot_toasters.py render x <outdir>   (preview: ... preview 0,90,168 <outdir>)"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/toasters"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 8
CP = float(os.environ.get("CP", "106"))       # column pitch
RP = float(os.environ.get("RP", "118"))       # row pitch
Y0 = float(os.environ.get("Y0", "640"))       # first toaster centre
X0 = 540 + 16 - 3.5 * CP
PCT = int(os.environ.get("PCT", "3"))
ODD = (os.environ.get("OL", "G"), int(os.environ.get("ON", "3")))
NDEC = int(os.environ.get("NDEC", "5"))
BURST = float(os.environ.get("BURST", "0.40"))
BT = [float(os.environ.get("B1", "5.6")), float(os.environ.get("B2", "10.9"))]
TFLIP = float(os.environ.get("TFLIP", "0.62"))
GRAV = 1250.0                                  # px/s^2: peak = g T^2 / 8
rng = np.random.default_rng(int(os.environ.get("SEED", "2813")))

def col_x(i): return X0 + i * CP
def row_y(r): return Y0 + r * RP
BW, BH = 88.0, 50.0                            # toaster body
TW, TH = 54.0, 58.0                            # toast
SUNK = 7.0; HIGH = 26.0                        # how much toast peeks out of the slot
REST_SINK = 0.16

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i), y=row_y(r), r=r, i=i, ev=[],
                      per=rng.uniform(1.5, 2.4)))
ODDG = [g for g in G if g["odd"]][0]

def mk(t0, kind, T=None, rest=None, amp=None):
    T = T if T is not None else rng.uniform(.46, .60)
    return dict(t0=t0, kind=kind, T=T, rest=rest if rest is not None else rng.uniform(.45, .85),
                amp=amp if amp is not None else rng.uniform(5, 12) * rng.choice([-1, 1]))
def span(e): return e["T"] + e["rest"] + REST_SINK + .35
def fits(g, e):
    for o in g["ev"]:
        for sh in (-LOOP, 0, LOOP):
            a0, a1 = o["t0"] + sh, o["t0"] + sh + span(o)
            if e["t0"] < a1 and a0 < e["t0"] + span(e): return False
    return True

for tb in BT:   # the odd flip, its decoys and a burst of ordinary pops at the same moment
    ODDG["ev"].append(mk(tb - TFLIP / 2, "flip", T=TFLIP, amp=360.0 * rng.choice([-1, 1])))
    cand = [g for g in G if not g["odd"] and not (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1)]
    perm = rng.permutation(len(cand))
    for j in perm[:NDEC]:
        e = mk(tb - TFLIP / 2 + rng.uniform(-.12, .12), "decoy", T=rng.uniform(.58, .66),
               amp=rng.uniform(22, 30) * rng.choice([-1, 1]))
        if fits(cand[j], e): cand[j]["ev"].append(e)
    for j in perm[NDEC:]:
        if rng.random() < BURST:
            e = mk(tb - .3 + rng.uniform(-.25, .25), "pop")
            if fits(cand[j], e): cand[j]["ev"].append(e)
for g in G:     # fill the loop with ordinary pops
    t = rng.uniform(0, g["per"])
    while t < LOOP:
        e = mk(t, "pop")
        if fits(g, e): g["ev"].append(e)
        t += g["per"] * rng.uniform(.75, 1.25)
for g in G:
    g["all"] = sorted([dict(e, t0=e["t0"] + sh) for e in g["ev"] for sh in (-LOOP, 0, LOOP)], key=lambda e: e["t0"])

def ss_(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def state(g, t):
    """-> (toast lift above body top, rotation deg, lever 0=down 1=up, glow)"""
    last = None
    for e in g["all"]:
        if e["t0"] <= t: last = e
        else: break
    if last is None: return SUNK, 0.0, 0.0, 1.0
    dt = t - last["t0"]; T = last["T"]
    if dt < T:
        u = dt / T
        h = GRAV * T * T / 8
        lift = SUNK + (HIGH - SUNK) * u + h * 4 * u * (1 - u)
        if last["kind"] == "flip": rot = last["amp"] * ss_(u)
        elif last["kind"] == "decoy": rot = last["amp"] * math.sin(math.pi * u) ** 1.2
        else: rot = last["amp"] * math.sin(math.pi * u)
        return lift, rot, 1.0, 0.0
    dt -= T
    if dt < last["rest"]:
        bounce = 3.0 * math.exp(-dt * 14) * abs(math.sin(dt * 30))
        return HIGH + bounce, 0.0, 1.0, 0.0
    dt -= last["rest"]
    if dt < REST_SINK:
        u = ss_(dt / REST_SINK)
        return HIGH + (SUNK - HIGH) * u, 0.0, 1 - u, u
    return SUNK, 0.0, 0.0, 1.0

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x0, y0), (x1, y1)], [c4(cc).toColor() for cc in cols], pos))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH TOASTER", "FLIPS ITS TOAST?"
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
CRUST, CRUST_LO = (.66, .38, .14), (.48, .25, .08)
BREAD = (.97, .78, .46)

def static_layer():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawImage(background(1000), 0, 0)
        # checkerboard kitchen tiles
        for r in range(NR):
            for i in range(NC):
                x, y = col_x(i), row_y(r)
                rect = skia.Rect(x - CP / 2 + 2, y - RP / 2 - 18, x + CP / 2 - 2, y + RP / 2 - 22)
                dark = (r + i) % 2 == 0
                cols = [(.21, .15, .10), (.16, .11, .07)] if dark else [(.30, .22, .15), (.24, .17, .11)]
                c.drawRRect(skia.RRect.MakeRectXY(rect, 7, 7), lin(0, rect.top(), 0, rect.bottom(), cols))
                c.drawRRect(skia.RRect.MakeRectXY(rect, 7, 7), S_((.55, .42, .28), .25, 1))
            # counter edge under each row
            yb = row_y(r) + BH / 2 + 4
            c.drawLine(col_x(0) - CP / 2 + 6, yb + 4, col_x(NC - 1) + CP / 2 - 6, yb + 4, S_(BRASS, .22, 1.5))
    return s.makeImageSnapshot()

def toast_path():
    p = skia.Path()
    w, h = TW, TH
    # loaf-shaped slice: two round lobes on top, straight sides, rounded bottom
    p.moveTo(-w / 2, h / 2 - 6)
    p.lineTo(-w / 2, -h / 2 + 14)
    p.cubicTo(-w / 2 - 3, -h / 2 - 2, -2, -h / 2 - 6, 0, -h / 2 + 3)
    p.cubicTo(2, -h / 2 - 6, w / 2 + 3, -h / 2 - 2, w / 2, -h / 2 + 14)
    p.lineTo(w / 2, h / 2 - 6)
    p.quadTo(w / 2, h / 2, w / 2 - 6, h / 2)
    p.lineTo(-w / 2 + 6, h / 2)
    p.quadTo(-w / 2, h / 2, -w / 2, h / 2 - 6)
    p.close()
    return p
TOAST = toast_path()
INNER = skia.Path(TOAST); m = skia.Matrix(); m.setScale(.80, .80); INNER.transform(m)

def draw_toast(c, x, cy, rot):
    c.save(); c.translate(x, cy); c.rotate(rot)
    c.drawPath(TOAST, lin(0, -TH / 2, 0, TH / 2, [CRUST, CRUST_LO]))
    c.save(); c.translate(0, 1.5)
    c.drawPath(INNER, lin(-TW / 2, -TH / 2, TW / 2, TH / 2, [BREAD, (.92, .66, .32)]))
    c.restore()
    c.drawCircle(-8, -2, 2.2, P_((.80, .52, .22), .55)); c.drawCircle(7, 7, 1.8, P_((.80, .52, .22), .55))
    c.drawCircle(4, -9, 1.6, P_((.80, .52, .22), .5))
    c.restore()

def draw_toaster(c, g, t):
    x, y = g["x"], g["y"]
    lift, rot, lev, glow = state(g, t)
    top = y - BH / 2
    # shadow
    c.drawOval(skia.Rect(x - BW / 2 - 2, y + BH / 2 - 3, x + BW / 2 + 6, y + BH / 2 + 9), P_((0, 0, 0), .35))
    # toast (behind the body); centre = slot top - lift + TH/2
    draw_toast(c, x, top - lift + TH / 2, rot)
    # body
    body = skia.RRect.MakeRectXY(skia.Rect(x - BW / 2, top, x + BW / 2, y + BH / 2), 15, 15)
    c.drawRRect(body, lin(0, top, 0, y + BH / 2, [(1, .97, .90), CRM, CRM_LO], [0, .35, 1]))
    c.drawRRect(body, S_((.55, .47, .36), .6, 1.2))
    # slot lip + heat glow
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - TW / 2 - 4, top - 2, x + TW / 2 + 4, top + 5), 3, 3),
                P_((.20, .15, .11)))
    if glow > 0:
        c.drawLine(x - TW / 2, top + 1.5, x + TW / 2, top + 1.5, S_((1, .55, .18), .55 * glow, 2.5))
    # chrome highlight band
    c.drawLine(x - BW / 2 + 12, top + 11, x + BW / 2 - 12, top + 11, S_((1, 1, 1), .55, 2))
    c.drawLine(x - BW / 2 + 8, y + 12, x + BW / 2 - 8, y + 12, S_(BRASS, .65, 2))
    # dial
    c.drawCircle(x - BW / 2 + 18, y + 2, 6.5, P_((.90, .58, .20)))
    c.drawLine(x - BW / 2 + 18, y + 2, x - BW / 2 + 18, y - 3, S_(CRM, .9, 1.6))
    # lever track + knob
    tx = x + BW / 2 - 13
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(tx - 2.5, top + 16, tx + 2.5, y + 8), 2, 2), P_((.30, .24, .18), .8))
    ky = (y + 6) + (top + 18 - (y + 6)) * lev
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(tx - 9, ky - 4, tx + 9, ky + 4), 3, 3), P_(BRASS))
    c.drawLine(tx - 7, ky - 2, tx + 7, ky - 2, S_((1, .93, .75), .7, 1.2))
    # feet
    for fx in (x - BW / 2 + 14, x + BW / 2 - 14):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(fx - 7, y + BH / 2 - 1, fx + 7, y + BH / 2 + 4), 2, 2),
                    P_((.18, .14, .10)))

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
            text(c, str(r + 1), 116, row_y(r) + 4, F_AX, AMBER, .9)
        for g in G: draw_toaster(c, g, t)
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
def ting(seed, f0, bright=False):
    rg = np.random.default_rng(seed)
    n = int(.22 * SR); t = np.arange(n) / SR
    f = f0 * (1.035 if bright else 1.0)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 26) * .22 + np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 60) * .05
    s += bp(rg.standard_normal(n), 2200, 6000) * np.exp(-t * 220) * (.30 if bright else .25)
    return s
def thud(seed):
    rg = np.random.default_rng(seed)
    n = int(.09 * SR); t = np.arange(n) / SR
    return bp(rg.standard_normal(n), 250, 1400) * np.exp(-t * 70) * .35 + np.sin(2 * np.pi * 150 * t) * np.exp(-t * 50) * .2
def click(seed):
    rg = np.random.default_rng(seed)
    n = int(.04 * SR); t = np.arange(n) / SR
    return bp(rg.standard_normal(n), 1200, 4500) * np.exp(-t * 200) * .3

def audio(path):
    m = Mix(LOOP + 2)
    ev = []
    for k, g in enumerate(G):
        for e in g["ev"]:
            t0 = e["t0"] % LOOP
            ev.append((k, t0, "ting", e["kind"] == "flip"))
            ev.append((k, (t0 + e["T"]) % LOOP, "thud", False))
            ev.append((k, (t0 + e["T"] + e["rest"]) % LOOP, "click", False))
    tt = np.array([e[1] for e in ev])
    for k, t0, typ, odd in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(tt - t0) < .12).sum()))
        if typ == "ting":
            s = ting(k * 131 + int(t0 * 977), note(6 + (7 - g["r"]) // 2 + (g["i"] % 3), 220.0), odd); a = .75 / dens
        elif typ == "thud":
            s = thud(k * 71 + int(t0 * 31)); a = .55 / dens
        else:
            s = click(k * 17 + int(t0 * 53)); a = .45 / dens
        m.add(s, t0, a, g["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 120, 600) * .006            # faint kitchen hum
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "toasters; odd", ODD, "flips at", BT)
    print("pops/toaster", min(len(g["ev"]) for g in G), max(len(g["ev"]) for g in G),
          "odd events", [(round(e["t0"], 2), e["kind"]) for e in ODDG["ev"]])
    print("decoys:", sorted([(g["lab"], round(e["t0"], 2)) for g in G for e in g["ev"] if e["kind"] == "decoy"]))
    for tb in BT:
        air = sum(1 for g in G if state(g, tb)[2] > .5 and state(g, tb)[0] > HIGH + 2)
        print("in the air at", tb, ":", air)
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_toasters.mp4"))
