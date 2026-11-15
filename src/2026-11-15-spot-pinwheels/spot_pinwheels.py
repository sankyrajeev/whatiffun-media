"""SPOT IT (BIG FIELD, DIAMOND): 169 paper pinwheels on a diamond lattice (letters A-M run down-right along the
upper-right edge, numbers 1-13 run down-left along the upper-left edge; A1 is the top corner).
Three breezes per 12 s loop sweep across the field from the left (visible wind streaks); each pinwheel spins up
as the front passes and coasts to a stop (linear model: w' = a*wind - b*w).
The odd one has a looser axle (smaller drag b): it spins up a bit faster and keeps turning after its
neighbours have stopped. Seamless: steady-state is periodic and each pinwheel's total turn per loop is a whole
number of quarter turns (normal 16, odd 24; blades are 4-fold symmetric).
Sound: soft paper tick per pinwheel per full turn (pentatonic by number, panned by x, density-normalised), a
breeze whoosh following each front, faint air bed; the odd one gives a low wooden tock every half turn."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/spotp"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
N = 11
LET = "ABCDEFGHIJK"
CX, Y0 = 540, 566
DX, DY = 38.0, 48.0
PR = 30.0                                   # pinwheel radius
ODD_CELL = (LET.index(os.environ.get("OL", "H")), int(os.environ.get("ON", "4")) - 1)
GUSTS = [(3.3, 1.0), (7.3, 1.22), (11.3, 0.78)]   # (start, strength); the last wraps into the loop start
WDIR = math.radians(18)                     # wind heading (from the left, slightly downward)
VFRONT = float(os.environ.get("VF", "480"))                              # px/s
GW = 1.05                                   # gust duration at a point
BN = float(os.environ.get("BN", "3.2"))
Q_N, Q_O = int(os.environ.get("QN", "12")), int(os.environ.get("QO", "23"))   # quarter turns per loop

CELLS = []
for i in range(N):
    for j in range(N):
        x = CX + (i - j) * DX; y = Y0 + (i + j) * DY
        CELLS.append(dict(i=i, j=j, x=x, y=y))
NC = len(CELLS)
ODD = [k for k, c in enumerate(CELLS) if (c["i"], c["j"]) == ODD_CELL][0]
X = np.array([c["x"] for c in CELLS]); Y = np.array([c["y"] for c in CELLS])
UX, UY = math.cos(WDIR), math.sin(WDIR)
PROJ = X * UX + Y * UY
P0 = PROJ.min() - 60

def wind(t, proj):
    out = np.zeros_like(proj)
    for k in range(-1, 2):
        for (t0, s) in GUSTS:
            tau = ((t % LOOP) - (t0 + k * LOOP)) - (proj - P0) / VFRONT
            u = np.clip(tau / GW, 0, 1)
            out += s * np.sin(np.pi * u) ** 2 * ((tau > 0) & (tau < GW))
    return out

def simulate():
    dt = 1 / 600; sub = 20
    b = np.full(NC, BN); b[ODD] = BN * Q_N / Q_O
    # integral of wind over a loop = sum(strength) * GW/2 for every pinwheel
    I = sum(s for _, s in GUSTS) * GW / 2
    a = (Q_N * math.pi / 2) * BN / I          # normal: a/b*I = Q_N quarter turns
    w = np.zeros(NC); th = np.random.default_rng(21).uniform(0, math.pi / 2, NC)   # each pinwheel rests at its own angle
    loops = 4; steps = int(loops * LOOP / dt); start = (loops - 1) * int(LOOP / dt)
    TH = np.zeros((NC, TOTAL + 1)); OM = np.zeros((NC, TOTAL + 1))
    for s in range(steps + 1):
        t = s * dt
        if s >= start and (s - start) % sub == 0:
            f = (s - start) // sub
            if f <= TOTAL: TH[:, f] = th; OM[:, f] = w
        w += (a * wind(t, PROJ) - b * w) * dt
        th += w * dt
    return TH, OM
TH, OM = simulate()

# ---------------- look ----------------
BG = background(1000)
F_LBL = font(TF_SEMI, 33)
F_SPOT = font(TF_SEMI, 30)
F_Q = font(TF_SERIF, 64); F_QI = font(TF_SERIF_I, 64)
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()

def cell_hue(c):
    u = (c["i"] + c["j"]) / (2 * (N - 1)); v = (c["i"] - c["j"]) / (2 * (N - 1))
    return 28 + 300 * u + 30 * v      # amber at the top -> coral -> magenta -> violet -> blue at the bottom

def pinwheel_sprite(hue):
    sz = PR * 2 + 10
    def fn(c):
        x = y = sz / 2
        lite = hsv(hue, .55, 1.0); mid = hsv(hue, .75, .9); dark = hsv(hue, .85, .55)
        for k in range(4):
            a = k * math.pi / 2
            # blade: from centre to tip (corner), curling back to the half-edge point
            tip = (x + PR * math.cos(a), y + PR * math.sin(a))
            fold = (x + PR * .72 * math.cos(a + math.radians(62)), y + PR * .72 * math.sin(a + math.radians(62)))
            mid_pt = (x + PR * .30 * math.cos(a + math.radians(40)), y + PR * .30 * math.sin(a + math.radians(40)))
            p1 = skia.Path(); p1.moveTo(x, y); p1.lineTo(*tip); p1.lineTo(*mid_pt); p1.close()
            p2 = skia.Path(); p2.moveTo(*mid_pt); p2.lineTo(*tip); p2.quadTo(fold[0] + 2 * math.cos(a), fold[1] + 2 * math.sin(a), *fold); p2.close()
            p3 = skia.Path(); p3.moveTo(x, y); p3.lineTo(*mid_pt); p3.lineTo(*fold); p3.close()
            c.drawPath(p1, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x, y), tip], [rgb(mid), rgb(lite)])))
            c.drawPath(p3, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*dark, 1)))
            c.drawPath(p2, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([mid_pt, fold], [rgb(lite), rgb(mid)])))
            c.drawLine(x, y, *tip, skia.Paint(AntiAlias=True, StrokeWidth=.7, Color4f=skia.Color4f(1, 1, 1, .45)))
        c.drawCircle(x, y, 3.3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (x - 1, y - 1), 4, [rgb((1, .92, .7)), rgb((.72, .52, .26))])))
        c.drawCircle(x - .9, y - .9, 1.1, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .85)))
    return sprite(fn, sz)
SPR = [pinwheel_sprite(cell_hue(c)) for c in CELLS]
GLOWS = [glow(hsv(cell_hue(c), .45, 1.0), PR * .95, .9) for c in CELLS]
SHADOW = sprite(lambda c: c.drawCircle(PR + 8, PR + 8, PR * .92, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4))), PR * 2 + 16)

def diamond_path():
    m = 46
    top = (CX, Y0 - m * 1.15); right = (CX + (N - 1) * DX + m, Y0 + (N - 1) * DY)
    bot = (CX, Y0 + 2 * (N - 1) * DY + m * 1.15); left = (CX - (N - 1) * DX - m, Y0 + (N - 1) * DY)
    p = skia.Path(); p.moveTo(*top); p.lineTo(*right); p.lineTo(*bot); p.lineTo(*left); p.close()
    return p

def board_img():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.clear(skia.Color4f(0, 0, 0, 0))
        p = diamond_path()
        c.save(); c.translate(0, 14)
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
        c.restore()
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX - 80, Y0 + 300), 700, [rgb((.16, .115, .08)), rgb((.10, .075, .055)), rgb((.06, .047, .037))], [0, .6, 1])))
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0, Color4f=skia.Color4f(.86, .62, .34, .42)))
        # letters along the upper-right edge (j = 0), numbers along the upper-left edge (i = 0)
        # faint guide grooves along every letter line and number line
        for k in range(N):
            for (a0, a1) in (((k, 0), (k, N - 1)), ((0, k), (N - 1, k))):
                x0 = CX + (a0[0] - a0[1]) * DX; y0 = Y0 + (a0[0] + a0[1]) * DY
                x1 = CX + (a1[0] - a1[1]) * DX; y1 = Y0 + (a1[0] + a1[1]) * DY
                c.drawLine(x0, y0, x1, y1, skia.Paint(AntiAlias=True, StrokeWidth=1.6, Color4f=skia.Color4f(.96, .85, .6, .12)))
        off = 54
        for k in range(N):
            x = CX + k * DX + off * .74; y = Y0 + k * DY - off * .67
            text(c, LET[k], x, y + 11, F_LBL, CREAM, .95)
            x = CX - k * DX - off * .74; y = Y0 + k * DY - off * .67
            text(c, str(k + 1), x, y + 11, F_LBL, AMBER, 1.0)
    return s.makeImageSnapshot()
BOARD = board_img()

def streaks(c, t):
    """wind streaks travelling with each front, kept on the board"""
    c.save(); c.clipPath(diamond_path(), skia.ClipOp.kIntersect, True)
    rg = np.random.default_rng(11)
    pts = rg.uniform(0, 1, (46, 2))
    for k in range(-1, 2):
        for gi, (t0, s) in enumerate(GUSTS):
            d = (t - (t0 + k * LOOP)) * VFRONT + P0     # projection of the front
            if d < P0 - 300 or d > PROJ.max() + 420: continue
            for (u, v) in pts:
                along = d - u * 260            # streaks spread behind the front
                across = 805 + (v - .5) * 1150
                x = along * UX - across * UY; y = along * UY + across * UX
                # map back to screen: projection coordinates are absolute (origin 0,0)
                if not (60 < x < 1020 and 480 < y < 1640): continue
                a = .30 * s * (1 - u) ** .7 * min(1, (d - P0 + 100) / 200)
                L = 60 + 70 * (1 - u)
                c.drawLine(x - UX * L, y - UY * L, x, y, skia.Paint(AntiAlias=True, StrokeWidth=3.0, StrokeCap=skia.Paint.kRound_Cap,
                           Shader=skia.GradientShader.MakeLinear([(x - UX * L, y - UY * L), (x, y)],
                           [skia.Color4f(1, .97, .9, 0).toColor(), skia.Color4f(1, .97, .9, max(0, a)).toColor()])))
    c.restore()

def header(c):
    text(c, "SPOT IT", W / 2, 200, F_SPOT, AMBER, .9, spacing=8)
    text(c, "One pinwheel keeps", W / 2, 278, F_Q, CREAM, .97)
    text(c, "spinning longer.", W / 2, 346, F_QI, CREAM, .9)
    text(c, "Comment its letter + number", W / 2, 420, font(TF_SERIF_I, 40), CREAM, .7)
    fi = font(TF_SERIF_I, 32); fe = font(TF_EMOJI, 26)
    s1 = "Like it if you found it "
    w1 = fi.measureText(s1); w2 = fe.measureText("👍")
    x0 = W / 2 - (w1 + w2) / 2
    text(c, s1, x0, 466, fi, CREAM, .62, align="left")
    c.drawString("👍", x0 + w1, 465, fe, skia.Paint(AntiAlias=True, Alphaf=.75))

def frame(f, mark_odd=False):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        header(c)
        c.drawImage(BOARD, 0, 0)
        for k, cc in enumerate(CELLS):
            blit(c, SHADOW, cc["x"] + 3, cc["y"] + 5)
        for k, cc in enumerate(CELLS):
            x, y = cc["x"], cc["y"]
            th = TH[k, f]; om = OM[k, f]
            stepdeg = abs(om) / FPS * 180 / math.pi       # degrees per frame
            ga = min(1.0, max(0.0, (stepdeg - 3) / 14))
            if ga > 0: blit(c, GLOWS[k], x, y, 1.0, skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=.45 * ga))
            nsub = 1 if stepdeg < 6 else 3
            for s in range(nsub):
                a = th - (om / FPS) * (s / max(1, nsub)) * 1.2
                c.save(); c.translate(x, y); c.rotate(math.degrees(a)); c.translate(-x, -y)
                blit(c, SPR[k], x, y, 1.0 + .10 * ga, None if s == 0 else skia.Paint(Alphaf=.45 / s))
                c.restore()
            if mark_odd and k == ODD:
                c.drawCircle(x, y, PR + 5, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3, Color4f=skia.Color4f(0, 1, 0, 1)))
        streaks(c, t)
        text(c, "@whatiffun", W / 2, 1640, F_MARK, CREAM, .45)
    return out

# ---------------- sound ----------------
def paper_tick(f0, dur=.06):
    t = np.arange(int(dur * SR)) / SR
    n = np.random.default_rng(int(f0 * 10)).standard_normal(len(t))
    n = sosfilt(butter(2, [f0 * 1.5, f0 * 5], btype="band", fs=SR, output="sos"), n) * np.exp(-t * 120)
    tone = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 70)
    return (n * .8 + tone * .7) * np.minimum(1, t * 8000)

def wood_tock(f0, dur=.16):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .45 * np.sin(2 * np.pi * f0 * 2.4 * t + .5) * np.exp(-t * 40)) * np.exp(-t * 26)
    n = np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t * 700) * .25
    return (s + n) * np.minimum(1, t * 5000)

def whoosh(dur, seed):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.random.default_rng(seed).standard_normal(n)
    lo = sosfilt(butter(2, [250, 1400], btype="band", fs=SR, output="sos"), x)
    hi = sosfilt(butter(2, [1800, 5000], btype="band", fs=SR, output="sos"), x)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    return (lo + .25 * hi) * env

def events():
    """(time, cell, kind) — normal: every full turn; odd: every half turn"""
    ev = []
    for k in range(NC):
        per = math.pi if k == ODD else 2 * math.pi
        a = TH[k] - TH[k, 0]
        for f in range(1, TOTAL + 1):
            n0, n1 = math.floor(a[f - 1] / per + 1e-9), math.floor(a[f] / per + 1e-9)
            if n1 > n0:
                frac = (n1 * per - a[f - 1]) / max(1e-9, a[f] - a[f - 1])
                ev.append(((f - 1 + frac) / FPS % LOOP, k))
    return ev

def audio(path):
    m = Mix(LOOP)
    def addw(sig, t0, g, x):
        t0 %= LOOP
        m.add(sig, t0, g, x)
        over = t0 + len(sig) / SR - LOOP
        if over > 0:
            k = int(round((LOOP - t0) * SR)); m.add(sig[k:], 0.0, g, x)
    ev = events()
    times = np.array([e[0] for e in ev])
    rg = np.random.default_rng(2)
    for tt, k in ev:
        cc = CELLS[k]
        if k == ODD:
            addw(wood_tock(note(cc["j"] // 3, 130.81) * .98), tt, .30, cc["x"])
            continue
        dens = np.sum(np.abs(((times - tt + LOOP / 2) % LOOP) - LOOP / 2) < .15)   # events within ±0.15 s
        g = .10 / math.sqrt(max(1, dens / 2))
        f0 = note(12 - cc["j"] + 2, 261.63) * (1 + rg.uniform(-.008, .008))
        addw(paper_tick(f0), tt + rg.uniform(0, .006), g, cc["x"])
    span = (PROJ.max() - P0) / VFRONT + GW
    for gi, (t0, s) in enumerate(GUSTS):
        # whoosh split in pieces panned left -> right as the front crosses
        pieces = 8
        for p in range(pieces):
            tp = t0 + span * p / pieces
            xs = 140 + 800 * p / (pieces - 1)
            addw(whoosh(span / pieces * 2.2, gi * 31 + p), tp - span / pieces * .6, .05 * s, xs)
    n = m.N; rg = np.random.default_rng(4)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 500) / 400) ** 2) + .1 * np.exp(-((fr - 2800) / 1400) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .07; m.R += np.roll(bed, 5000) * .07
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    c = CELLS[ODD]
    print("pinwheels", NC, "odd", LET[c["i"]] + str(c["j"] + 1), round(c["x"]), round(c["y"]))
    seam = np.angle(np.exp(4j * (TH[:, TOTAL] - TH[:, 0]))) / 4
    print("seam err deg", float(np.degrees(np.abs(seam)).max()), "omega seam", float(np.abs(OM[:, TOTAL] - OM[:, 0]).max()))
    print("max deg/frame normal", float(np.degrees(np.abs(np.delete(OM, ODD, 0)).max()) / FPS), "odd", float(np.degrees(np.abs(OM[ODD]).max()) / FPS))
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f, mark_odd=os.environ.get("MARK") == "1").makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "stats":
        # how long the odd keeps spinning after its neighbours stop
        nb = [k for k, cc in enumerate(CELLS) if abs(cc["i"] - c["i"]) <= 1 and abs(cc["j"] - c["j"]) <= 1 and k != ODD]
        for f in range(0, TOTAL, 6):
            print(f"{f/FPS:5.1f}s  odd {np.degrees(OM[ODD,f])/FPS:6.2f}  nb {np.degrees(OM[nb,f].mean())/FPS:6.2f} deg/frame")
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_pinwheels.mp4"))
