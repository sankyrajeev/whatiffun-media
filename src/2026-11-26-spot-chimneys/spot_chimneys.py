"""SPOT IT v3 (10:00, 2026-11-26): WHICH CHIMNEY / BREAKS PHYSICS? 56 identical cream cottages (amber roof,
brass chimney, warm lit window) in a SWITCHBACK VILLAGE: 7 streets of 8 houses, each street sloping the other
way, joined by hairpin bends into one serpentine road; letters A-H on top, row numbers on the left.
Every chimney puffs smoke in bursts of three on a 2.0 / 2.4 / 3.0 s cycle from a random phase: each puff leaves
the chimney small and dense, rises, swells, drifts downwind and fades. ONE chimney runs backwards in time:
faint big puffs gather out of the air, shrink, thicken and get sucked DOWN into the chimney.
Rule type: BREAKS PHYSICS (time reversal / goes down instead of up), today's one physics puzzle.
Sound: a soft 'pff' per puff (pentatonic body by row, panned by x, density-normalised); the odd one's puffs
are the same sound reversed (a swelling inhale that cuts off).
12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/chimneys"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC, NR = 8, 6
PX = 110.0
PY = float(os.environ.get("PY", "150"))
Y0 = float(os.environ.get("Y0", "692"))
X0 = 162.0
SL = float(os.environ.get("SL", "0"))     # half the street's fall across the row
PCT = int(os.environ.get("PCT", "24"))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "26")))
colx = [X0 + i * PX for i in range(NC)]
XM = (colx[0] + colx[-1]) / 2
def ground(r, x):
    sgn = 1 if r % 2 == 0 else -1
    return Y0 + r * PY + sgn * SL * (x - XM) / (colx[-1] - XM)

LIFE = float(os.environ.get("LIFE", "2.0"))
SC = 1.08
RISE = float(os.environ.get("RISE", "36"))
DRIFT = float(os.environ.get("DRIFT", "16"))
OFFS = (0.0, 0.27, 0.54, 0.81)
CHX, CHY = 18.0 * SC, -78.0 * SC     # chimney mouth relative to ground centre

G = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = 2.4 if odd else float(rng.choice([2.0, 2.4, 3.0]))
        G.append(dict(lab=lab, odd=odd, cx=colx[i], gy=ground(r, colx[i]), r=r, i=i, P=P,
                      ph=rng.uniform(0, 1), sw=rng.uniform(0, 6.28)))
print(len(G), "houses")
assert sum(g["odd"] for g in G) == 1

def sink_path(g, u, j):
    """the odd chimney's smoke falls: it slides down the roof, drops off the eave and pools on the ground"""
    x0, y0 = g["cx"] + CHX, g["gy"] + CHY - 2
    xe, ye = g["cx"] + 38 * SC, g["gy"] - 40 * SC       # eave
    xg, yg = g["cx"] + 44 * SC, g["gy"] - 8             # ground beside the wall
    w = 3 * math.sin(g["sw"] + 6 * u + j)
    if u < .3:
        v = ss(u / .3); return x0 + (xe - x0) * v, y0 + (ye - y0) * v + w * .3, 6 + 4 * v
    if u < .5:
        v = (u - .3) / .2; v = v * v
        return xe + (xg - xe) * v, ye + (yg - ye) * v, 10 + 2 * v
    v = ss((u - .5) / .5)
    side = 1 if j % 2 == 0 else -1
    return xg + side * 4 + (34 if side > 0 else 26) * v * side + w, yg - 3 * v, 12 + 8 * v

def puffs(g, t):
    """list of (x, y, radius, alpha, seedphase) for the puffs in the air at time t"""
    tt = t
    P = g["P"]; out = []
    k0 = math.floor((tt - LIFE - 1) / P - g["ph"])
    for k in range(k0, k0 + 4):
        for j, o in enumerate(OFFS):
            e = (k + g["ph"]) * P + o
            a = tt - e
            if 0 < a < LIFE:
                u = a / LIFE
                ue = 1 - (1 - u) ** 1.8
                if g["odd"]:
                    x, y, rad = sink_path(g, u, j)
                else:
                    x = g["cx"] + CHX + DRIFT * u ** 1.15 + 3 * math.sin(g["sw"] + 5 * u + j)
                    y = g["gy"] + CHY - 4 - RISE * ue + 2 * math.sin(g["sw"] + 7 * u + 2 * j)
                    rad = 6 + 9 * ue
                al = min(1, a / .06) * min(1, (1 - u) / .22) ** 1.5
                out.append((x, y, rad, al, j + k * 3))
    return out

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
QS = int(os.environ.get("QS", "84"))
F_Q = font(TF_BOLD, QS); F_PCT = font(TF_BOLD, 38); F_AX = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
CR = (.95, .90, .80); CR_D = (.74, .67, .56); ROOF = (.80, .50, .22); ROOF_D = (.58, .33, .13)
BRASS = (.62, .47, .30); WIN = (1.0, .78, .38)
STROKE = dict(Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)

def draw_house(c, g):
    x, y = g["cx"], g["gy"]
    c.save(); c.translate(x, y); c.scale(SC, SC)
    c.drawOval(skia.Rect(-34, -4, 34, 5), P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    # chimney (behind roof)
    cx_, cy_ = CHX / SC, CHY / SC
    c.drawRect(skia.Rect(cx_ - 7, cy_ + 2, cx_ + 7, -44), P_(BRASS))
    c.drawRect(skia.Rect(cx_ - 9, cy_ - 1, cx_ + 9, cy_ + 5), P_((.75, .60, .40)))
    # body
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-27, -40, 27, 0), 2, 2), P_(CR))
    c.drawRect(skia.Rect(-27, -40, 27, -36), P_(CR_D, .8))
    # roof
    p = skia.Path(); p.moveTo(-35, -38); p.lineTo(0, -70); p.lineTo(35, -38); p.close()
    c.drawPath(p, P_(ROOF))
    c.drawPath(p, P_(ROOF_D, 1, StrokeWidth=2.5, **STROKE))
    # lit window + door
    c.drawRect(skia.Rect(-19, -30, -6, -17), P_(WIN, .95, MaskFilter=skia.MaskFilter.MakeBlur(skia.kSolid_BlurStyle, 4)))
    c.drawLine(-12.5, -30, -12.5, -17, P_(ROOF_D, .9, StrokeWidth=1.6))
    c.drawLine(-19, -23.5, -6, -23.5, P_(ROOF_D, .9, StrokeWidth=1.6))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(5, -24, 17, 0), 5, 5), P_(ROOF_D))
    c.restore()

def draw_puff(c, x, y, rad, al, s):
    """flat cartoon puff (matches the flat houses), drawn as one translucent layer"""
    if al < .01: return
    o = (s * 1.7) % 6.28
    sh = skia.Paint(AntiAlias=True, Color4f=c4((.78, .74, .68)))
    hi = skia.Paint(AntiAlias=True, Color4f=c4((.97, .94, .88)))
    c.save(); c.translate(x, y)
    c.saveLayer(skia.Rect(-3 * rad, -3 * rad, 3 * rad, 3 * rad), skia.Paint(Alphaf=al * .92))
    c.drawCircle(-rad * .5, rad * .18, rad * .68, sh)
    c.drawCircle(rad * .5, rad * .2, rad * .62, sh)
    c.drawCircle(rad * .06 * math.cos(o), -rad * .12, rad * .8, hi)
    c.drawCircle(-rad * .42, rad * .02, rad * .5, hi)
    c.restore(); c.restore()

def road(c):
    pa = P_(AMBER, .30, StrokeWidth=5, **STROKE)
    xl, xr = colx[0] - 44, colx[-1] + 44
    pth = skia.Path()
    for r in range(NR):
        a, b = (xl, xr) if r % 2 == 0 else (xr, xl)
        ya, yb = ground(r, a) + 3, ground(r, b) + 3
        if r == 0: pth.moveTo(a, ya)
        pth.lineTo(b, yb)
        if r < NR - 1:
            y2 = ground(r + 1, b) + 3
            bulge = 30 if b == xr else -30
            pth.cubicTo(b + bulge, yb, b + bulge, y2, b, y2)
    c.drawPath(pth, pa)

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH CHIMNEY", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "BREAKS PHYSICS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], colx[i], 520, F_AX, AMBER, .9)
        for r in range(NR):
            text(c, str(r + 1), 106, ground(r, colx[0]) - 30, F_AX, AMBER, .9)
        for g in G: draw_house(c, g)
        for g in G:
            for (x, y, rad, al, s) in puffs(g, t): draw_puff(c, x, y, rad, al, s)
        yb = 1546
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 42, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 40, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
def pff(f0, seed):
    rg = np.random.default_rng(seed)
    t = np.arange(int(.42 * SR)) / SR
    env = np.minimum(1, t * 250) * np.exp(-t * 11)
    s = bp(rg.standard_normal(len(t)), 250, 1800) * env * .9
    s += np.sin(2 * np.pi * f0 * t) * np.minimum(1, t * 400) * np.exp(-t * 16) * .35   # soft chimney 'chuff' body
    return s

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        n = int(LOOP / g["P"])
        for c_ in range(n):
            for o in OFFS:
                e = (c_ + g["ph"]) * g["P"] + o
                ts = e
                ev.append((k, ts % LOOP))
    allt = np.array([e[1] for e in ev])
    for k, ts in ev:
        g = G[k]
        d = np.abs(allt - ts); d = np.minimum(d, LOOP - d)
        dens = math.sqrt(max(1, (d < .12).sum() / 3))
        f0 = note(1 + (6 - g["r"]) // 2 + (g["i"] % 3), 110.0)
        s = pff(f0, k * 31 + int(ts * 89))
        if g["odd"]: s = s[::-1] * 1.15   # a reversed, inhaled 'pff' as the audio clue
        m.add(s, ts, .34 / dens, g["cx"])
    n = int(LOOP * SR)
    rg = np.random.default_rng(3)
    room = bp(rg.standard_normal(n), 120, 700) * .007
    m.L[:n] += room; m.R[:n] += room
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_chimneys.mp4"))
