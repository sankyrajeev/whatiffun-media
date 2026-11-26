"""SPOT IT v3 (13:00, 2026-11-26): WHICH BOOK / FLIPS BACKWARDS?
45 identical open books (walnut covers, cream pages with amber text lines) lying on four long walnut reading
desks (LIBRARY DESKS: 5 columns A-E x 9 rows, three rows per desk; letters on top, numbers on the left).
Every book turns a page non-stop, right -> left, two pages per 1.2 / 1.5 / 2.0 s period, half a period apart (random phase), so every book riffles non-stop: each page lifts, sweeps
over the spine in a big arc and lands. ONE book (ODD) turns its pages LEFT -> RIGHT (backwards).
A turning page shows its bright front over its start side and its warmer back over the far side, so the flow direction reads; the odd book shows them mirrored.
Rule type: wrong way (linear sweep direction).
Sound: a papery 'fwip' per page turn + a soft landing tap (pitch by row, panned by x, density-normalised); the
odd one's fwip is played REVERSED (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/books"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDE"
NC, NR = 5, 9
PX = float(os.environ.get("PX", "160"))
RP = float(os.environ.get("RP", "100"))      # row pitch inside a desk
DG = float(os.environ.get("DG", "18"))       # extra gap between desks
Y0 = float(os.environ.get("Y0", "560"))      # page top of row 1
WP = float(os.environ.get("WP", "64"))       # page width
HP = float(os.environ.get("HP", "66"))       # page height
LIFT = float(os.environ.get("LIFT", "40"))
FDF = float(os.environ.get("FDF", "0.9"))    # flip duration as a fraction of the period
PCT = int(os.environ.get("PCT", "21"))
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "7")))
rng = np.random.default_rng(int(os.environ.get("SEED", "1126")))
colx = [W / 2 + 20 + (i - (NC - 1) / 2) * PX for i in range(NC)]
def rowy(r): return Y0 + r * RP + (r // 3) * DG

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        P = float(rng.choice([1.2, 1.5, 2.0]))
        G.append(dict(lab=lab, odd=lab == ODD, cx=colx[i], y=rowy(r), r=r, i=i, P=P, ph=rng.uniform(0, P),
                      tilt=rng.uniform(-3, 3)))
for g in G:
    if g["odd"]: g["P"] = 1.5
print(len(G), "books")
assert sum(g["odd"] for g in G) == 1

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
def S_(col, a, w): return P_(col, a, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
                            StrokeJoin=skia.Paint.kRound_Join)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
L1, L2 = "WHICH BOOK", "FLIPS BACKWARDS?"
def fit(s, size, maxw=830):
    f = font(TF_BOLD, size)
    while sum(f.measureText(ch) for ch in s) + (len(s) - 1) > maxw: size -= 2; f = font(TF_BOLD, size)
    return f
F_Q = fit(L1, 84); F_Q2 = fit(L2, 84)
F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)

BRASS = (.86, .66, .34)
WOOD, WOOD_HI, WOOD_LO = (.36, .20, .10), (.50, .29, .14), (.20, .11, .05)
COVER = (.55, .16, .10)                       # deep red-brown leather
COVER_LO = (.34, .09, .05)
PAPER, PAPER_LO = (.97, .93, .85), (.86, .80, .70)
INK = (.62, .42, .22)
BACK = (.90, .78, .60)                        # back of a turning page: warmer, a touch darker

def flip_starts(g):
    """two pages per period, half a period apart: every book riffles non-stop"""
    return [0.0, g["P"] / 2]
def flips(g, t):
    """thetas in [0, pi] of the pages in the air (0 = lying on the start side), oldest first"""
    D = FDF * g["P"]; out = []
    for o in flip_starts(g):
        u = (t - g["ph"] - o) % g["P"]
        if u < D:
            x = u / D
            out.append(math.pi * (.5 - .5 * math.cos(math.pi * x)) * .97 + math.pi * .03 * x)
    return sorted(out, reverse=True)

def page_lines(c, x0, x1, top, lift0, lift1, a=1.0):
    """amber text lines on a page between spine x0 and edge x1 (lift interpolated along x)"""
    n = 6
    for k in range(n):
        yy = top + 11 + k * (HP - 20) / (n - 1)
        if k == n - 1: xa, xb = .12, .55
        else: xa, xb = .12, .86
        pa = x0 + (x1 - x0) * xa; pb = x0 + (x1 - x0) * xb
        la = lift0 + (lift1 - lift0) * xa; lb = lift0 + (lift1 - lift0) * xb
        c.drawLine(pa, yy - la, pb, yy - lb, S_(INK, .55 * a, 3.0))

def draw_book(c, g, t):
    ths = flips(g, t)
    sgn = -1.0 if g["odd"] else 1.0           # start side of the turning page: +1 right, -1 left
    c.save(); c.translate(g["cx"], g["y"]); c.rotate(g["tilt"])
    # shadow + cover
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-WP - 9, 6, WP + 9, HP + 12), 6, 6), P_((0, 0, 0), .35))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-WP - 7, -4, WP + 7, HP + 7), 5, 5),
                skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                    [(0, -4), (0, HP + 7)], [c4(COVER).toColor(), c4(COVER_LO).toColor()])))
    # page stacks (edges)
    for k in range(3, 0, -1):
        c.drawRect(skia.Rect(-WP - .5, k * 1.4, WP + .5, HP + k * 1.4), P_(PAPER_LO, 1))
        c.drawLine(-WP, HP + k * 1.4, WP, HP + k * 1.4, S_((.6, .52, .42), .6, .8))
    # flat pages
    for s in (-1, 1):
        r = skia.Rect(min(0, s * WP), 0, max(0, s * WP), HP)
        c.drawRect(r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (s * WP, 0)], [c4(PAPER_LO).toColor(), c4(PAPER).toColor(), c4(PAPER).toColor()], [0, .25, 1])))
        page_lines(c, s * 3, s * WP, 0, 0, 0)
    # gutter
    c.drawLine(0, 0, 0, HP, S_((.55, .45, .35), .8, 1.6))
    for th in ths:
        ct = math.cos(th); st = math.sin(th)
        xe = sgn * WP * ct                    # free edge x
        lift = LIFT * st                      # free edge rises towards the viewer
        bend = sgn * WP * .55 * math.cos(th * .85)
        c.drawRect(skia.Rect(min(0, xe), 0, max(0, xe), HP), P_((.25, .15, .05), .18 * st))
        pth = skia.Path()
        pth.moveTo(0, 0); pth.quadTo(bend, -lift * .55, xe, -lift)
        pth.lineTo(xe, HP - lift * .55)
        pth.quadTo(bend, HP - lift * .2, 0, HP); pth.close()
        front = ct > 0                        # front face up while still over its start side
        base = PAPER if front else BACK
        shade = .84 + .16 * abs(ct)
        c.drawPath(pth, P_(tuple(v * shade for v in base)))
        if abs(ct) > .12:
            page_lines(c, math.copysign(3, xe), xe, 0, lift * .1, lift * .95, a=abs(ct) * (1 if front else .7))
        c.drawPath(pth, S_((.6, .5, .38), .8, 1.3))
    c.restore()

def draw_desks(c):
    for d in range(3):
        y0 = rowy(3 * d) - 20; y1 = rowy(3 * d + 2) + HP + 22
        r = skia.Rect(colx[0] - 100, y0, colx[-1] + 80, y1)
        c.drawRRect(skia.RRect.MakeRectXY(r, 14, 14), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(0, y0), (0, y1)], [c4(WOOD_HI).toColor(), c4(WOOD).toColor(), c4(WOOD_LO).toColor()], [0, .45, 1])))
        for k in range(5):  # wood grain
            yy = y0 + 18 + k * (y1 - y0 - 30) / 4
            c.drawLine(r.left() + 20, yy, r.right() - 20, yy + 3, S_(WOOD_LO, .35, 1.2))
        c.drawLine(r.left() + 10, y1 - 2, r.right() - 10, y1 - 2, S_(BRASS, .35, 2))

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
            text(c, LET[i], colx[i], 516, F_AX, AMBER, .9)
        draw_desks(c)
        for r in range(NR):
            text(c, str(r + 1), colx[0] - 90, rowy(r) + HP / 2 + 11, F_AX, AMBER, .9)
        for g in G: draw_book(c, g, t)
        yb = 1556
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 46, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 44, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def fwip(seed, f0, FD):
    """papery swoosh with a rising band + a soft landing tap"""
    rg = np.random.default_rng(seed)
    n = int(FD * SR); t = np.arange(n) / SR
    noise = rg.standard_normal(n)
    lo = bp(noise, 500, 2500); hi = bp(noise, 2500, 7500)
    x = t / FD
    env = np.sin(np.pi * np.clip(x, 0, 1)) ** 2
    s = (lo * (1 - x) + hi * x) * env * .6
    # crinkle grains
    for k in range(6):
        p = int(rg.uniform(.1, .8) * n); m = int(.006 * SR)
        s[p:p + m] += bp(rg.standard_normal(m), 3000, 8000)[:len(s[p:p + m])] * np.exp(-np.arange(min(m, n - p)) / SR * 600) * .5
    tap_t = np.arange(int(.08 * SR)) / SR
    tap = (np.sin(2 * np.pi * f0 * tap_t) * .5 + bp(rg.standard_normal(len(tap_t)), 300, 1500) * .6) * np.exp(-tap_t * 70)
    return s, tap

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        n = int(round(LOOP / g["P"]))
        for j in range(-1, n + 1):
            for o in flip_starts(g):
                ts = g["ph"] + j * g["P"] + o
                if 0 <= ts < LOOP: ev.append((k, ts))
    et = np.array([e[1] for e in ev])
    for k, ts in ev:
        g = G[k]
        dens = math.sqrt(max(1, (np.abs(et - ts) < .3).sum())) * 1.2
        f0 = note(2 + (8 - g["r"]) + (g["i"] % 2), 196.0)
        FD = FDF * g["P"]
        s, tap = fwip(k * 131 + int(ts * 977), f0, FD)
        if g["odd"]:
            m.add(s[::-1] * 1.15, ts, .55 / max(1, dens * .6), g["cx"])
            m.add(tap * 1.3, ts + FD * .92, .5 / max(1, dens * .6), g["cx"])
        else:
            m.add(s, ts, .30 / dens, g["cx"])
            m.add(tap, ts + FD * .92, .22 / dens, g["cx"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(3)
    m.L += bp(rg.standard_normal(n), 200, 1200) * .006; m.R += bp(rg.standard_normal(n), 200, 1200) * .006
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_books.mp4"))
