"""SPOT IT v3 (18:00, 2026-11-28): WHICH BOX / POPS UP TWICE?
63 identical jack-in-the-boxes (cream box with an amber front panel, amber hinged lid, brass zigzag spring, amber
star, a brass crank on the right that turns all the time) on TOY-FACTORY CONVEYORS: 9 columns A-I x 7 rows, each
row standing on its own rubber belt whose dashes scroll (alternate rows run opposite ways). Letters on top,
numbers on the left.
Every box pops non-stop on a 1.9-2.7 s cycle (+-25% jitter, random phase): the lid flies open, the star shoots up
on its spring with a springy wobble, holds, sinks back in and the lid shuts. ONE box (ODD) twice per loop pops
TWICE in one go: the star shoots up, drops straight back in, the lid slams shut and it pops right out again,
all in ~0.5 s. At those moments 5 decoys' stars dip hard halfway down on their springs (lid stays open) and
~45% of the grid is launching too.
Rule type: TWICE (double vs single).  Sound: a lid click + a soft spring boing per pop (pentatonic by row, panned
by x, density-normalised), a soft thock when the lid shuts; the odd one's boing is a touch brighter (subtle).
12 s seamless loop.
Reproduce: python3 spot_jackboxes.py render x <outdir>   (preview: ... preview 0,174,330 <outdir>)"""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/jackboxes"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGHI"
NC, NR = 9, 7
CP = float(os.environ.get("CP", "94"))
RP = float(os.environ.get("RP", "140"))
Y0 = float(os.environ.get("Y0", "662"))      # belt line of row 1
X0 = 540 + 8 - 4 * CP
PCT = int(os.environ.get("PCT", "6"))
ODD = (os.environ.get("OL", "H"), int(os.environ.get("ON", "4")))
NDEC = int(os.environ.get("NDEC", "5"))
BURST = float(os.environ.get("BURST", "0.45"))
BT = [float(os.environ.get("B1", "5.8")), float(os.environ.get("B2", "11.0"))]
rng = np.random.default_rng(int(os.environ.get("SEED", "2818")))

def col_x(i): return X0 + i * CP
def row_y(r): return Y0 + r * RP
BW, BH = 62.0, 46.0     # box
TRAV = 50.0             # spring travel of the star centre above the lid line
SR_ = 20.0              # star outer radius
LID_OPEN = 118.0

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        G.append(dict(lab=lab, odd=lab == ODD, x=col_x(i), y=row_y(r), r=r, i=i, ev=[],
                      per=rng.uniform(1.9, 2.7), crk=rng.uniform(0, 2 * math.pi),
                      crate=int(rng.integers(9, 15)) / LOOP * 2 * math.pi))
ODDG = [g for g in G if g["odd"]][0]

def mk(t0, kind):
    return dict(t0=t0, kind=kind, hold=rng.uniform(.45, .85), Tr=rng.uniform(.24, .32),
                wob=rng.uniform(9, 11), dip=rng.uniform(.18, .32))
TW = 0.41     # extra time the 'twice' segment adds
def span(e): return .04 + .22 + (TW if e["kind"] == "twice" else 0) + e["hold"] + e["Tr"] + .16 + .30
def fits(g, e):
    for o in g["ev"]:
        for sh in (-LOOP, 0, LOOP):
            a0, a1 = o["t0"] + sh, o["t0"] + sh + span(o)
            if e["t0"] < a1 and a0 < e["t0"] + span(e): return False
    return True

for tb in BT:
    e = mk(0, "twice"); e["t0"] = tb - .20       # the star is back in the box at ~tb
    ODDG["ev"].append(e)
    cand = [g for g in G if not g["odd"] and not (abs(g["r"] - ODDG["r"]) <= 1 and abs(g["i"] - ODDG["i"]) <= 1)]
    perm = rng.permutation(len(cand))
    nd = 0
    for j in perm:
        if nd < NDEC:
            d = mk(0, "decoy"); d["dip"] = rng.uniform(.10, .20)
            d["t0"] = tb - .26 - d["dip"] + rng.uniform(-.08, .08)
            if fits(cand[j], d): cand[j]["ev"].append(d); nd += 1
        elif rng.random() < BURST:
            d = mk(tb - .30 + rng.uniform(-.25, .25), "pop")
            if fits(cand[j], d): cand[j]["ev"].append(d)
for g in G:
    t = rng.uniform(0, g["per"])
    while t < LOOP:
        e = mk(t, "decoy" if (not g["odd"] and rng.random() < .08) else "pop")
        if fits(g, e): g["ev"].append(e)
        t += g["per"] * rng.uniform(.75, 1.25)
for g in G:
    g["all"] = sorted([dict(e, t0=e["t0"] + sh) for e in g["ev"] for sh in (-LOOP, 0, LOOP)], key=lambda e: e["t0"])

def ss_(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def spring_up(tau, wob):   # 0 -> 1 with one springy overshoot (~1.08) and a damped wobble
    if tau <= 0: return 0.0
    return 1 - math.exp(-11 * tau) * math.cos(wob * 1.35 * tau)
def lid_open(dt):  return LID_OPEN * ss_(dt / .10)
def lid_close(dt): return LID_OPEN * (1 - ss_(dt / .12)) + (6 * math.exp(-dt * 30) * abs(math.sin(dt * 40)) if dt > .12 else 0)

def state(g, t):
    """returns (lid angle deg, star extension 0..~1.08, shake px)"""
    last = None
    for e in g["all"]:
        if e["t0"] <= t: last = e
        else: break
    shake = 0.0
    # anticipation shake just before the next pop
    for e in g["all"]:
        if 0 < e["t0"] - t < .16:
            shake = 1.6 * math.sin((e["t0"] - t) * 90); break
    if last is None: return 0.0, 0.0, shake
    dt = t - last["t0"]
    wob = last["wob"]
    if last["kind"] == "twice":
        if dt < .04: return lid_open(dt), 0.0, shake
        tau = dt - .04
        if tau < .14: return LID_OPEN, ss_(tau / .14), shake                 # first pop (fast)
        tau -= .14
        if tau < .11: return LID_OPEN * (1 - ss_((tau - .03) / .08)), 1 - ss_(tau / .10), shake   # straight back in, lid slams
        tau -= .11
        if tau < .07: return 2.0 * math.exp(-tau * 20), 0.0, shake            # shut for a beat
        tau -= .07
        if tau < .07: return LID_OPEN * ss_(tau / .07), 0.0, shake        # lid flies open again
        tau -= .07
        dt = .04 + tau                                                     # and the normal pop continues
    if dt < .04: return lid_open(dt), 0.0, shake
    tau = dt - .04
    if tau < .22 + last["hold"]:
        e_ = spring_up(tau, wob)
        if last["kind"] == "decoy":
            u = (tau - .22 - last["dip"]) / .34
            if 0 <= u <= 1: e_ -= .56 * math.sin(math.pi * u) ** 1.4
        return LID_OPEN, e_, shake
    tau -= .22 + last["hold"]
    e_end = spring_up(.22 + last["hold"], wob)
    if tau < last["Tr"]: return LID_OPEN, e_end * (1 - ss_(tau / last["Tr"])), shake
    tau -= last["Tr"]
    return lid_close(tau), 0.0, shake

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                             StrokeJoin=skia.Paint.kRound_Join)
def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(x0, y0), (x1, y1)], [c4(cc).toColor() for cc in cols], pos))
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH BOX", "POPS UP TWICE?"
F_Q = font(TF_BOLD, 84)
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

CRM = (.96, .91, .82); CRM_LO = (.78, .71, .60)
BRASS = (.86, .70, .40); BRASS_LO = (.55, .42, .22)
AMB = (.93, .60, .20); AMB_LO = (.70, .40, .12)
BELT = 12.0

def static_layer():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawImage(background(1000), 0, 0)
        xl, xr = col_x(0) - CP / 2 + 2, col_x(NC - 1) + CP / 2 + 2
        for r in range(NR):
            y = row_y(r)
            # warm glow behind the row
            c.drawRect(skia.Rect(xl, y - 92, xr, y), lin(0, y - 92, 0, y, [(.10, .07, .05), (.24, .15, .08)]))
            # rollers at the belt ends
            for xx in (xl + 2, xr - 2):
                c.drawCircle(xx, y + BELT / 2, BELT / 2 + 3, P_((.30, .25, .20)))
                c.drawCircle(xx, y + BELT / 2, 3, P_(BRASS))
            # legs
            for xx in np.linspace(xl + 40, xr - 40, 4):
                c.drawRect(skia.Rect(xx - 3, y + BELT, xx + 3, y + BELT + 10), P_((.22, .18, .15)))
    return s.makeImageSnapshot()

def star_path(R, r_in):
    p = skia.Path()
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = R if k % 2 == 0 else r_in
        (p.moveTo if k == 0 else p.lineTo)(rr * math.cos(a), rr * math.sin(a))
    p.close(); return p
STAR = star_path(SR_, SR_ * .48)
SMALL_STAR = star_path(9, 4.3)

def draw_belts(c, t):
    xl, xr = col_x(0) - CP / 2 + 2, col_x(NC - 1) + CP / 2 + 2
    for r in range(NR):
        y = row_y(r)
        rect = skia.Rect(xl, y, xr, y + BELT)
        c.drawRRect(skia.RRect.MakeRectXY(rect, BELT / 2, BELT / 2), lin(0, y, 0, y + BELT, [(.26, .22, .19), (.13, .11, .09)]))
        sp = 22.0
        off = ((t * sp * 4 / LOOP * 6) % sp) * (1 if r % 2 == 0 else -1)   # 2 dash periods / s, seamless over 12 s
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(rect, BELT / 2, BELT / 2), doAntiAlias=True)
        x = xl - sp + off
        while x < xr + sp:
            c.drawLine(x, y + 3, x + 8, y + 3, S_((.70, .60, .46), .35, 2))
            x += sp
        c.restore()
        c.drawLine(xl + 6, y + .5, xr - 6, y + .5, S_((.85, .70, .48), .35, 1.2))

def draw_box(c, g, t):
    lid, ext, shake = state(g, t)
    x, y = g["x"] + shake, g["y"]
    top = y - BH
    # shadow on the belt
    c.drawOval(skia.Rect(x - BW / 2 - 2, y - 3, x + BW / 2 + 8, y + 5), P_((0, 0, 0), .40))
    # spring + star (behind the box front)
    sc = top - 6 - ext * TRAV          # star centre
    if ext > .01 or lid > 5:
        base = top + 8
        n = 7; L = base - (sc + SR_ * .45)
        pts = []
        for k in range(n + 1):
            yy = base - L * k / n
            xx = x + (9 if k % 2 else -9) * (0 if k in (0, n) else 1)
            pts.append((xx, yy))
        p = skia.Path(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        c.drawPath(p, S_(BRASS_LO, 1, 5.5)); c.drawPath(p, S_(BRASS, 1, 3))
        c.save(); c.translate(x, sc); c.rotate(math.sin(t * 7 + g["crk"]) * 6 * min(1, ext))
        c.drawPath(STAR, lin(0, -SR_, 0, SR_, [(1, .78, .38), AMB, AMB_LO]))
        c.drawPath(STAR, S_((1, .90, .70), .8, 1.6))
        c.drawCircle(0, 0, 4.5, P_(CRM, .95))
        c.restore()
    # box body
    body = skia.Rect(x - BW / 2, top, x + BW / 2, y)
    c.drawRRect(skia.RRect.MakeRectXY(body, 5, 5), lin(x - BW / 2, 0, x + BW / 2, 0, [CRM, (1, .97, .90), CRM_LO]))
    panel = skia.Rect(x - BW / 2 + 7, top + 8, x + BW / 2 - 7, y - 7)
    c.drawRRect(skia.RRect.MakeRectXY(panel, 3, 3), lin(0, top + 8, 0, y - 7, [(.95, .63, .24), AMB_LO]))
    c.save(); c.translate(x, (top + y) / 2 + 1); c.drawPath(SMALL_STAR, P_(CRM, .85)); c.restore()
    c.drawRRect(skia.RRect.MakeRectXY(body, 5, 5), S_((.45, .36, .26), .6, 1))
    # crank on the right side (turns all the time)
    cx, cy = x + BW / 2 + 2, (top + y) / 2
    a = g["crk"] + g["crate"] * t
    hx, hy = cx + 11 * math.cos(a), cy + 11 * math.sin(a) * .55
    c.drawCircle(cx, cy, 4, P_(BRASS_LO))
    c.drawLine(cx, cy, hx, hy, S_(BRASS, 1, 3.5))
    c.drawLine(hx, hy, hx + 6, hy, S_(BRASS_LO, 1, 5))
    c.drawLine(hx + 1, hy, hx + 6, hy, S_((1, .85, .55), 1, 2.4))
    # lid, hinged at the back-left top corner, opens up and over to the left
    c.save(); c.translate(x - BW / 2, top); c.rotate(-lid)
    lr = skia.Rect(0, -9, BW + 2, 1)
    c.drawRRect(skia.RRect.MakeRectXY(lr, 3, 3), lin(0, -9, 0, 1, [(1, .74, .34), AMB, AMB_LO]))
    c.drawRRect(skia.RRect.MakeRectXY(lr, 3, 3), S_((.45, .30, .15), .6, 1))
    c.restore()
    c.drawCircle(x - BW / 2, top, 2.6, P_(BRASS))

BASE = None
def frame(f):
    global BASE
    if BASE is None: BASE = static_layer()
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BASE, 0, 0)
        text(c, L1, W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, L2, W / 2, 354, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], col_x(i), 524, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 116, row_y(r) - 14, F_AX, AMBER, .9)
        draw_belts(c, t)
        for g in G: draw_box(c, g, t)
        yb = 1566
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
def click(seed):
    rg = np.random.default_rng(seed)
    n = int(.05 * SR); t = np.arange(n) / SR
    return bp(rg.standard_normal(n), 1500, 5000) * np.exp(-t * 300) * .30
def boing(f0, bright=False):
    n = int(.35 * SR); t = np.arange(n) / SR
    f0 = f0 * (1.04 if bright else 1.0)
    f = f0 * (1 + .35 * np.exp(-t * 40)) * (1 + .05 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 6))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * .14 + np.sin(2 * ph) * (.045 if bright else .035)) * np.exp(-t * 11) * np.minimum(1, t / .004)
def thock(seed):
    rg = np.random.default_rng(seed)
    n = int(.12 * SR); t = np.arange(n) / SR
    return bp(rg.standard_normal(n), 250, 1300) * np.exp(-t * 70) * .30 + np.sin(2 * np.pi * 150 * t) * np.exp(-t * 45) * .18

def audio(path):
    m = Mix(LOOP + 2)
    ev = []
    for k, g in enumerate(G):
        for e in g["ev"]:
            t0 = e["t0"]
            odd = e["kind"] == "twice"
            ev.append((k, t0 % LOOP, "click", False))
            ev.append((k, (t0 + .04) % LOOP, "boing", odd))
            ex = 0
            if odd:
                ev.append((k, (t0 + .04 + .14 + .10) % LOOP, "thock", False))
                ev.append((k, (t0 + .04 + .14 + .11 + .07 + .07) % LOOP, "boing", True))
                ex = TW
            ev.append((k, (t0 + .04 + ex + .22 + e["hold"] + e["Tr"] + .10) % LOOP, "thock", False))
    tt = np.array([e[1] for e in ev])
    for k, t0, typ, odd in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(tt - t0) < .12).sum()))
        if typ == "boing":
            s = boing(note(5 + (6 - g["r"]) // 2 + (g["i"] % 3), 220.0), odd); a = .85 / dens
        elif typ == "thock":
            s = thock(k * 71 + int(t0 * 31)); a = .5 / dens
        else:
            s = click(k * 17 + int(t0 * 53)); a = .45 / dens
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
    print(len(G), "boxes; odd", ODD, "pops twice at", BT)
    print("pops/box", min(len(g["ev"]) for g in G), max(len(g["ev"]) for g in G),
          "odd events", [(round(e["t0"], 2), e["kind"]) for e in ODDG["ev"]])
    print("decoys:", sorted([(g["lab"], round(e["t0"], 2)) for g in G for e in g["ev"] if e["kind"] == "decoy"]))
    for tb in BT:
        mov = sum(1 for g in G if abs(state(g, tb)[1] - state(g, tb - .1)[1]) > .05 or abs(state(g, tb)[0] - state(g, tb - .1)[0]) > 5)
        print("moving at", tb, ":", mov, " odd state", [round(v, 2) for v in state(ODDG, tb)])
    ts = np.arange(0, LOOP, 1 / FPS)
    mx = max(state(g, t)[1] for g in G[:9] for t in ts[::3])
    print("max ext", round(mx, 3))
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_jackboxes.mp4"))
