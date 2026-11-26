"""SPOT IT v3 (18:00, 2026-11-26): WHICH WIPER / GOES TOO FAR?
66 identical amber taxis queued in a RAINY MOTORWAY IN PERSPECTIVE (6 lanes A-F x 11 rows; far rows smaller and
higher, dashed lane lines converging; letters on top, numbers on the left).
Every taxi's single centre wiper sweeps non-stop across its rainy windscreen between two stops (+-72 deg), on a
1.5 / 1.71 / 2.0 / 2.4 s cycle from a random phase, clearing the raindrops; now and then one bounces a little at
its stop (still on the glass, legal decoys). ONE wiper (ODD) twice per loop swings PAST its stop, right off the
glass and down over the bonnet (~125 deg), for ~0.55 s, then carries on as if nothing happened.
Rule type: goes past its stop / passes through the frame. HARDER: two short breaks per 12 s loop, 5 decoy bounces
timed with each break, heavy random phase + speed jitter.
Sound: a soft rubber 'thwick' at each stop (pitch by row, panned by x, density-normalised) over a light rain bed;
the odd one's overshoot is a slightly lower, longer thwick (subtle). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/wipers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEF"
NC, NR = 6, 11
CX = 562.0
LW = float(os.environ.get("LW", "136"))
PITCH = float(os.environ.get("PITCH", "91"))
S0 = float(os.environ.get("S0", "0.87"))
A0 = 72.0                                   # normal stop angle (deg from vertical)
OVER = float(os.environ.get("OVER", "134"))  # the odd one's overshoot
BOUNCE = 12.0
PCT = int(os.environ.get("PCT", "5"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "3")))
rng = np.random.default_rng(int(os.environ.get("SEED", "2618")))

SC = [S0 + (1 - S0) * r / (NR - 1) for r in range(NR)]
ROWY = [560 + 62 * SC[0]]
for r in range(1, NR): ROWY.append(ROWY[-1] + PITCH * (SC[r - 1] + SC[r]) / 2)
def lane_x(i, r): return CX + (i - (NC - 1) / 2) * LW * SC[r]

def ease(x): return .5 - .5 * math.cos(math.pi * min(1, max(0, x)))
def bump(x): return math.sin(math.pi * x) ** 2 if 0 <= x <= 1 else 0.0

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([12 / 8, 12 / 7, 12 / 6, 12 / 5]))
        G.append(dict(lab=lab, odd=lab == ODD, cx=lane_x(i, r), y=ROWY[r], s=SC[r], r=r, i=i, P=P,
                      ph=rng.uniform(0, P), A=A0 + rng.uniform(-3, 3), ev=[]))
ODDG = [g for g in G if g["odd"]][0]
ODDG["P"] = 2.0; ODDG["A"] = A0

def ends(g):
    """times (within the loop, plus wrap copies) at which the wiper arrives at a stop, and which side"""
    out = []
    n = int(round(LOOP / g["P"]))
    for j in range(-1, n + 1):
        b = g["ph"] + j * g["P"]
        out.append((b + .42 * g["P"], +1)); out.append((b + .92 * g["P"], -1))
    return out

# the odd one's two breaks: one at a right stop around t~3.5, one at a left stop around t~9.3
def pick(g, want, side):
    c = [(abs(t - want), t, s) for t, s in ends(g) if s == side and 0.5 < t < LOOP - .5]
    return min(c)[1:]
for want, side in ((3.5, +1), (9.3, -1)):
    te, s = pick(ODDG, want, side)
    ODDG["ev"].append((te, s, OVER - ODDG["A"], .56))
    # 5 decoys: other wipers whose stop falls near te bounce a little, legally, at the same moment
    cand = []
    for g in G:
        if g["odd"] or g["r"] == ODDG["r"] and abs(g["i"] - ODDG["i"]) <= 1: continue
        for t2, s2 in ends(g):
            if abs(t2 - te) < .3: cand.append((abs(t2 - te) + rng.uniform(0, .2), id(g), g, t2, s2))
    cand.sort(key=lambda x: x[0])
    used = set()
    for _, gid, g, t2, s2 in cand:
        if gid in used or len(used) >= 5: continue
        used.add(gid); g["ev"].append((t2, s2, BOUNCE + rng.uniform(-2, 3), .36))
# a few random legal bounces elsewhere so a bounce means nothing
for g in G:
    if g["odd"]: continue
    for t2, s2 in ends(g):
        if 0 <= t2 < LOOP and rng.random() < .07: g["ev"].append((t2, s2, BOUNCE + rng.uniform(-3, 2), .36))

def angle(g, t):
    u = ((t - g["ph"]) % g["P"]) / g["P"]
    A = g["A"]
    if u < .42: a = -A + 2 * A * ease(u / .42)
    elif u < .5: a = A
    elif u < .92: a = A - 2 * A * ease((u - .5) / .42)
    else: a = -A
    for te, s, amp, dur in g["ev"]:
        for k in (-1, 0, 1):
            x = (t - (te + k * LOOP) + dur * .42) / dur
            a += s * amp * bump(x)
    return a

# raindrops on each windscreen: spawn at random, cleared when the blade passes over them
GW_T, GW_B, GH = 88.0, 112.0, 54.0       # glass top width, bottom width, height (local units)
ARM = 50.0
for k, g in enumerate(G):
    ts_grid = np.arange(0, 2 * LOOP, 1 / 60)
    ang = np.array([angle(g, t) for t in ts_grid])
    drops = []
    for _ in range(14):
        while True:
            x, y = rng.uniform(-GW_T / 2, GW_T / 2), rng.uniform(-GH + 4, -6)
            hw = GW_B / 2 - (GW_B - GW_T) / 2 * (-y / GH)
            if abs(x) < hw - 4: break
        da = math.degrees(math.atan2(x, -y)); rr = math.hypot(x, y)
        ts = rng.uniform(0, LOOP)
        if rr < ARM + 1 and abs(da) < g["A"] + 1:
            i0 = int(ts * 60); seg = ang[i0:i0 + int(LOOP * 60)] - da
            cr = np.where(np.sign(seg[1:]) != np.sign(seg[:-1]))[0]
            life = (cr[0] + 1) / 60 if len(cr) else LOOP
        else:
            life = LOOP + 1      # outside the swept arc: always there
        drops.append((x, y, ts, life, rng.uniform(1.6, 2.6)))
    g["drops"] = drops

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                            StrokeJoin=skia.Paint.kRound_Join)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH WIPER", "GOES TOO FAR?"
def fit(s, size, maxw=830):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BODY, BODY_HI, BODY_LO = (.86, .60, .26), (.95, .73, .38), (.62, .40, .16)
GLASS_T, GLASS_B = (.16, .17, .19), (.07, .075, .08)
BLADE = (.97, .94, .86)
ARMC = (.10, .09, .08)

def trap(tw, bw, h, y0=0.0):
    p = skia.Path()
    p.moveTo(-tw / 2, y0 - h); p.lineTo(tw / 2, y0 - h); p.lineTo(bw / 2, y0); p.lineTo(-bw / 2, y0); p.close()
    return p
GLASS = trap(GW_T, GW_B, GH)
ROOF = skia.Path(); ROOF.addRRect(skia.RRect.MakeRectXY(skia.Rect(-GW_T / 2 - 6, -GH - 14, GW_T / 2 + 6, -GH + 4), 9, 9))
CAB = trap(GW_T + 12, GW_B + 12, GH + 8, 4)
HOOD = skia.Path(); HOOD.addRRect(skia.RRect.MakeRectXY(skia.Rect(-62, -2, 62, 26), 9, 9))

def draw_car(c, g, t, part="body"):
    c.save(); c.translate(g["cx"], g["y"]); c.scale(g["s"], g["s"])
    if part == "wiper":
        draw_wiper(c, g, t); c.restore(); return
    # shadow on the road
    c.drawOval(skia.Rect(-66, 18, 66, 36), P_((0, 0, 0), .35))
    # body
    bodysh = skia.GradientShader.MakeLinear([(0, -GH - 14), (0, 26)], [c4(BODY_HI).toColor(), c4(BODY).toColor(), c4(BODY_LO).toColor()], [0, .55, 1])
    bp_ = skia.Paint(AntiAlias=True, Shader=bodysh)
    c.drawPath(ROOF, bp_); c.drawPath(CAB, bp_); c.drawPath(HOOD, bp_)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-12, -GH - 22, 12, -GH - 13), 3, 3), P_(BLADE, .9))   # taxi sign
    # headlights + grille
    for s in (-1, 1):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(s * 50 - 9, 8, s * 50 + 9, 18), 4, 4), P_(BLADE, .95))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-24, 10, 24, 17), 3, 3), P_(BODY_LO, .9))
    # glass
    gsh = skia.GradientShader.MakeLinear([(0, -GH), (0, 0)], [c4(GLASS_T).toColor(), c4(GLASS_B).toColor()])
    c.drawPath(GLASS, skia.Paint(AntiAlias=True, Shader=gsh))
    c.save(); c.clipPath(GLASS, doAntiAlias=True)
    a = angle(g, t)
    # wiped (clean) arc: a touch clearer than the rainy rest
    arc = skia.Path(); arc.moveTo(0, -2)
    arc.arcTo(skia.Rect(-ARM, -ARM - 2, ARM, ARM - 2), -90 - g["A"], 2 * g["A"], False); arc.close()
    c.drawPath(arc, P_((.36, .38, .42), .42))
    # reflection streak
    rp = skia.Path(); rp.moveTo(-GW_T / 2 + 6, -GH); rp.lineTo(-GW_T / 2 + 22, -GH); rp.lineTo(-GW_B / 2 + 40, 0); rp.lineTo(-GW_B / 2 + 24, 0); rp.close()
    c.drawPath(rp, P_((1, 1, 1), .05))
    for (x, y, ts, life, rad) in g["drops"]:
        age = (t - ts) % LOOP
        if age < life:
            al = min(1, age / .25) * .55
            c.drawCircle(x, y, rad, P_((.85, .88, .92), al))
            c.drawCircle(x - rad * .3, y - rad * .3, rad * .35, P_((1, 1, 1), al))
    c.restore()
    c.drawPath(GLASS, S_(BODY_LO, .8, 2))
    c.restore()

def draw_wiper(c, g, t):
    a = angle(g, t)
    # wiper arm + blade (drawn on top, so it can swing off the glass onto the bonnet)
    c.save(); c.translate(0, -2); c.rotate(a)
    c.drawLine(0, 0, 0, -ARM * .32, S_(ARMC, 1, 5.5))
    c.drawLine(0, -ARM * .2, 0, -ARM, S_(ARMC, 1, 9.5))
    c.drawLine(0, -ARM * .24, 0, -ARM + 1, S_(BLADE, 1, 5.6))
    c.restore()
    c.drawCircle(0, -2, 5, P_(ARMC)); c.drawCircle(0, -2, 2.4, P_(BODY_HI))

def draw_road(c):
    top, bot = ROWY[0] - 80 * SC[0], ROWY[-1] + 38
    xl0, xr0 = lane_x(0, 0) - LW * SC[0] / 2, lane_x(NC - 1, 0) + LW * SC[0] / 2
    xl1, xr1 = lane_x(0, NR - 1) - LW / 2, lane_x(NC - 1, NR - 1) + LW / 2
    road = skia.Path(); road.moveTo(xl0, top); road.lineTo(xr0, top); road.lineTo(xr1, bot); road.lineTo(xl1, bot); road.close()
    c.drawPath(road, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, top), (0, bot)], [c4((.11, .10, .095)).toColor(), c4((.16, .145, .13)).toColor()])))
    def lx(k, y):
        u = (y - top) / (bot - top)
        sl = S0 + (1 - S0) * u
        return CX + (k - NC / 2) * LW * sl
    for k in range(NC + 1):
        solid = k in (0, NC)
        y = top
        while y < bot:
            y2 = min(bot, y + (bot - top) if solid else y + 26)
            c.drawLine(lx(k, y), y, lx(k, y2), y2, S_(CREAM, .22 if solid else .16, 3))
            y = y2 + (0 if solid else 22)

# falling rain over everything (seamless: each streak falls a whole number of screens per loop)
RAIN = [(rng.uniform(80, 1000), rng.uniform(0, 1), int(rng.integers(3, 6)), rng.uniform(.05, .11)) for _ in range(90)]
def draw_rain(c, t):
    y0, y1 = 480, 1520
    for x, ph, k, al in RAIN:
        y = y0 + ((ph + k * t / LOOP) % 1) * (y1 - y0)
        c.drawLine(x - (y - y0) * .06, y, x - (y - y0) * .06 - 3, y + 22, S_((.8, .85, .9), al, 1.6))

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
        draw_road(c)
        for i in range(NC):
            text(c, LET[i], lane_x(i, 0), 516, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), lane_x(0, r) - LW * SC[r] / 2 - 26, ROWY[r] - 14 * SC[r], F_AX, AMBER, .9)
        for g in G: draw_car(c, g, t)
        for g in G: draw_car(c, g, t, "wiper")
        draw_rain(c, t)
        yb = 1562
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 40, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 38, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def thwick(seed, f0, odd=False):
    """soft rubber blade reaching its stop: a short squeegee swish + a muted low tick"""
    rg = np.random.default_rng(seed)
    d = .26 if not odd else .34
    n = int(d * SR); t = np.arange(n) / SR; x = t / d
    sw = bp(rg.standard_normal(n), 1400 if not odd else 1100, 4200 if not odd else 3400) * np.sin(np.pi * x) ** 3 * .22
    tk_t = np.arange(int(.12 * SR)) / SR
    f = f0 * (.89 if odd else 1.0)
    tk = (np.sin(2 * np.pi * f * tk_t) * .8 + np.sin(2 * np.pi * f * 2.02 * tk_t) * .12) * np.exp(-tk_t * 38)
    s = sw.copy(); k = int(d * .62 * SR)
    s[k:k + len(tk)] += tk[:n - k]
    return s

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        for te, s in ends(g):
            if 0 <= te < LOOP: ev.append((k, te, False))
    for te, s, amp, dur in ODDG["ev"]:
        ev.append((G.index(ODDG), te + dur * .1, True))
    et = np.array([e[1] for e in ev])
    for k, ts, special in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .25).sum())) * 1.15
        f0 = note(2 + (10 - g["r"]) // 2 + (g["i"] % 3), 220.0)
        s = thwick(k * 131 + int(ts * 977), f0, special)
        m.add(s, ts, (.36 if special else .30) / dens, g["cx"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    for buf in (m.L, m.R):
        buf += bp(rg.standard_normal(n), 2500, 9000) * .010 + bp(rg.standard_normal(n), 300, 1500) * .006
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(len(G), "taxis; odd", ODD, "breaks at", [(round(e[0], 2), e[1]) for e in ODDG["ev"]])
    print("decoys:", sorted([(g["lab"], round(e[0], 2)) for g in G if not g["odd"] for e in g["ev"] if any(abs(e[0] - o[0]) < .4 for o in ODDG["ev"])]))
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_wipers.mp4"))
