"""SPOT IT v3 (13:00, 2026-11-27): WHICH STAPLER / STAPLES TWICE?
64 identical desk staplers (amber arm, cream base, brass hinge) in a HERRINGBONE PARQUET: 8 columns A-H x 8 rows,
alternate columns tilted +-11 deg on walnut parquet planks; letters on top, numbers on the left.
Every stapler opens its arm wide (38 deg) and SLAMS it shut, non-stop, on a 1.5 / 1.71 / 2.0 / 2.4 s cycle from a
random phase (+-23% speed jitter); each slam fires a staple (a small brass flash at the jaw). Now and then a slam
rebounds legally (the arm bounces up ~30% and settles, no staple).
ONE stapler (ODD) twice per loop staples TWICE: right after its slam the arm flies back fully open and slams again
(a second flash) within ~0.55 s, then carries on as normal. At each of those moments 5 decoys rebound.
Rule type: TWICE (double vs single). Sound: a crisp metal 'chk' per slam + a soft spring creak per opening (pitch by
row, panned by x, density-normalised); the odd one's second chk is a touch lower (subtle).
12 s seamless loop.  Reproduce: python3 spot_staplers.py render x <outdir>"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/staplers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFG"
NC, NR = 7, 9
CW = float(os.environ.get("CW", "122"))
RP = float(os.environ.get("RP", "102"))
X0 = 540 - 3 * CW + 14
Y0 = 636.0                                   # base line of row 1
TILT = 8.0
OPEN = 34.0                                  # degrees
SC = float(os.environ.get("SC", "1.0"))
PCT = int(os.environ.get("PCT", "3"))
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "7")))
NDEC = int(os.environ.get("NDEC", "5"))
rng = np.random.default_rng(int(os.environ.get("SEED", "2713")))

def col_x(i): return X0 + i * CW
def row_y(r): return Y0 + r * RP
def ease(x): x = min(1, max(0, x)); return .5 - .5 * math.cos(math.pi * x)
def easein(x): x = min(1, max(0, x)); return x * x

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([12 / 8, 12 / 7, 12 / 6, 12 / 5]))
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i), y=row_y(r), r=r, i=i, P=P,
                      tilt=TILT * (1 if i % 2 == 0 else -1), ph=rng.uniform(0, P), ev={}))
ODDG = [g for g in G if g["odd"]][0]
ODDG["P"] = 2.0

# cycle (fractions of P), t0 = the SLAM moment: closed .00-.22, opening .22-.62, hover .62-.78, slam-down .78-1.0
SLAM = .22   # fraction of P spent closed after a slam (min .5 s window for the special events)
def slams(g):
    n = int(round(LOOP / g["P"]))
    return [g["ph"] + j * g["P"] for j in range(-1, n + 2)]

BREAK = .55
def pick(g, want):
    c = [(abs(t - want), t) for t in slams(g) if .8 < t < LOOP - 1.0]
    return min(c)[1]
BREAKS = [pick(ODDG, float(os.environ.get("B1", "3.9"))), pick(ODDG, float(os.environ.get("B2", "9.6")))]
for tb in BREAKS:
    ODDG["ev"][round(tb % LOOP, 4)] = "twice"
    cand = []
    for g in G:
        if g["odd"] or (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1): continue
        for t2 in slams(g):
            if abs(t2 - tb) < .3: cand.append((abs(t2 - tb) + rng.uniform(0, .2), id(g), g, t2))
    cand.sort(key=lambda x: x[0]); used = set()
    for _, gid, g, t2 in cand:
        if gid in used or len(used) >= NDEC: continue
        used.add(gid); g["ev"][round(t2 % LOOP, 4)] = "bounce"
for g in G:
    if g["odd"]: continue
    for t2 in slams(g):
        if 0 <= t2 < LOOP and rng.random() < .08: g["ev"].setdefault(round(t2 % LOOP, 4), "bounce")

def kind(g, t0): return g["ev"].get(round(t0 % LOOP, 4))

def arm(g, t):
    """returns (angle in degrees, flash strength 0..1)"""
    P = g["P"]
    j = math.floor((t - g["ph"]) / P); t0 = g["ph"] + j * P
    dt = t - t0; u = dt / P
    k = kind(g, t0)
    fl = max(0, 1 - dt / .18)
    if k == "twice":
        # fly back fully open, hold a hair, slam again at +0.40 s
        if dt < .22: return OPEN * ease(dt / .22), fl
        if dt < .30: return OPEN, 0
        if dt < .40: return OPEN * (1 - easein((dt - .30) / .10)), 0
        if dt < BREAK: return 0.0, max(0, 1 - (dt - .40) / .18)
        return OPEN * ease((u - BREAK / P) / (.62 - BREAK / P)), 0
    if k == "bounce" and dt < .24:
        return .3 * OPEN * math.sin(math.pi * dt / .24), fl
    if u < SLAM: return 0.0, fl
    if u < .62: return OPEN * ease((u - SLAM) / (.62 - SLAM)), 0
    if u < .78: return OPEN, 0
    return OPEN * (1 - easein((u - .78) / .22)), 0

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
def lin(y0, y1, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y0), (0, y1)], [c4(cc).toColor() for cc in cols], pos))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH STAPLER", "STAPLES TWICE?"
def fit(s, size, maxw=850):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_Q = F_Q2 if F_Q2.getSize() < F_Q.getSize() else F_Q
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

ARM_T, ARM_B = (.97, .72, .36), (.78, .48, .17)
BASE_T, BASE_B = (.95, .91, .83), (.78, .72, .62)
BRASS = (.86, .70, .40)
DARK = (.16, .14, .12)
PLANK = [(.25, .17, .11), (.21, .145, .095)]

def draw_floor(c):
    # walnut parquet planks under each column (herringbone: alternate columns lean opposite ways)
    for i in range(NC):
        x = col_x(i); tl = TILT * (1 if i % 2 == 0 else -1)
        for r in range(NR):
            y = row_y(r)
            c.save(); c.translate(x, y - 24)
            R = skia.RRect.MakeRectXY(skia.Rect(-CW / 2 + 6, -RP / 2 + 4, CW / 2 - 6, RP / 2 - 4), 10, 10)
            c.drawRRect(R, P_(PLANK[(i + r) % 2], .9))
            c.drawRRect(R, S_((.36, .26, .17), .55, 1.2))
            c.restore()

def arm_path():
    p = skia.Path()
    # arm in local coords, hinge at (0,0); arm extends to the left (front) along -x, top surface curved
    L = 88 * SC
    p.moveTo(9, -2)
    p.cubicTo(8, -26, -24, -27, -L + 12, -21)
    p.quadTo(-L - 3, -19, -L - 1, -6)
    p.lineTo(-L + 1, 4)
    p.lineTo(6, 5)
    p.close()
    return p
ARM = arm_path()
def base_path():
    L = 92 * SC
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-L / 2, -16, L / 2, 0), 7, 7))
    return p
BASE = base_path()

def draw_stapler(c, g, t):
    x, y = g["x"], g["y"]
    a, fl = arm(g, t)
    c.save(); c.translate(x + 3, y); c.rotate(g["tilt"])
    # shadow
    c.drawOval(skia.Rect(-50 * SC, -4, 50 * SC, 6), P_((0, 0, 0), .35))
    # base
    c.save(); c.translate(0, 3 * fl)
    c.drawPath(BASE, lin(-16, 0, [BASE_T, BASE_B]))
    # paper sheet under the jaw
    for kk in range(3):
        c.drawRect(skia.Rect(-52 * SC + kk, -19 + kk * 1.5, -14 * SC, -17 + kk * 1.5), P_((.98, .97, .93) if kk % 2 == 0 else (.80, .78, .72), .95))
    # anvil plate
    c.drawRect(skia.Rect(-46 * SC, -20, -30 * SC, -16), P_(DARK, .9))
    hx, hy = 40 * SC, -26
    # arm
    c.save(); c.translate(hx, hy); c.rotate(a)
    c.drawPath(ARM, lin(-22, 4, [ARM_T, ARM_B]))
    c.drawPath(ARM, S_((.55, .33, .10), .6, 1.4))
    c.drawLine(-80 * SC, -17, -6, -21, S_((1, .9, .7), .4, 2.6))   # highlight
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-88 * SC - 1, -14, -76 * SC, 5), 3, 3), P_(DARK, .85))   # nose
    c.restore()
    # brass hinge
    c.drawCircle(hx, hy, 7.5, P_(BRASS))
    c.drawCircle(hx, hy, 3, P_((.55, .42, .2)))
    c.restore()
    # staple flash at the jaw
    if fl > 0:
        fx, fy = -32 * SC, -30
        c.drawCircle(fx, fy, 38 * fl + 4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (fx, fy), 38 * fl + 4, [c4((1, .9, .55), .85 * fl).toColor(), c4((1, .8, .4), 0).toColor()])))
        for k in range(7):
            th = math.radians(-180 + k * 30)
            r0, r1 = 10, 10 + 26 * fl
            c.drawLine(fx + r0 * math.cos(th), fy + r0 * math.sin(th), fx + r1 * math.cos(th), fy + r1 * math.sin(th),
                       S_((1, .93, .7), .9 * fl, 2.2))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, L1, W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, L2, W / 2, 354, F_Q2, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], col_x(i), 528, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), col_x(0) - CW / 2 - 14, row_y(r) - 12, F_AX, AMBER, .9)
        draw_floor(c)
        for g in G: draw_stapler(c, g, t)
        yb = 1560
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 40, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 38, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def chk(seed, f0, low=False):
    rg = np.random.default_rng(seed)
    n = int(.12 * SR); t = np.arange(n) / SR
    k = .88 if low else 1.0
    s = bp(rg.standard_normal(n), 1800 * k, 5200 * k) * np.exp(-t * 70) * .5
    s += np.sin(2 * np.pi * f0 * 2 * k * t) * np.exp(-t * 45) * .35
    s += np.sin(2 * np.pi * f0 * .5 * k * t) * np.exp(-t * 35) * .25
    return s
def creak(seed, f0, dur):
    rg = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR; x = t / dur
    s = bp(rg.standard_normal(n), 500, 1400) * np.sin(np.pi * x) ** 2 * .05
    s += np.sin(2 * np.pi * (f0 * 1.5 + 30 * x) * t) * np.sin(np.pi * x) ** 2 * .02
    return s
def tick(f0):
    tt = np.arange(int(.06 * SR)) / SR
    return np.sin(2 * np.pi * f0 * 3 * tt) * np.exp(-tt * 80) * .25

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        P = g["P"]
        for t0 in slams(g):
            if not (0 <= t0 < LOOP): continue
            kd = kind(g, t0)
            ev.append((k, t0, "chk"))
            if kd == "twice": ev.append((k, t0 + .40, "chk2"))
            if kd == "bounce": ev.append((k, t0 + .24, "tick"))
            ev.append((k, t0 + SLAM * P, "creak"))
    et = np.array([e[1] for e in ev if e[2] != "creak"])
    for k, ts, typ in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .25).sum())) * 1.1
        f0 = note(2 + (7 - g["r"]) // 2 + (g["i"] % 3), 220.0)
        sd = k * 131 + int(ts * 977)
        if typ == "creak": s = creak(sd, f0, .4 * g["P"]); a = .5
        elif typ == "tick": s = tick(f0); a = .3
        else: s = chk(sd, f0, typ == "chk2"); a = .45
        m.add(s, ts % LOOP, a / dens, g["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 200, 900) * .005
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "staplers; odd", ODD, "breaks at", [round(b, 2) for b in BREAKS])
    print("decoys:", sorted([(g["lab"], t) for g in G if not g["odd"] for t, k in g["ev"].items()
                             if any(abs(t - b % LOOP) < .4 for b in BREAKS)]))
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_staplers.mp4"))
