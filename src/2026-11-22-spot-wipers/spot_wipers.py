"""SPOT IT v3 (18:00, 2026-11-22): WHICH WIPER / NEVER TURNS BACK? 59 identical rain-spotted windscreens in a
CAR-PARK BRICK layout (9 rows alternating 7 and 6 screens, the short rows offset half a bay; each screen's
label "C7" is printed on its bonnet strip). Rain keeps landing on every screen; every wiper sweeps back and
forth across 164 degrees non-stop (2.0 / 2.4 / 3.0 s per cycle, random phase), clearing the drops it passes.
ONE wiper never turns back: it keeps going round the same way, down through the bonnet and up the other side.
Rule type: wrong way / never turns back. (v1 "WIPES TWICE?" with rests failed review 5 vs 7: half the grid
still at any moment, the double wipe too subtle.)
Sound: a soft rubber swish per stroke + a light rain bed (pentatonic by row, panned by x, density-normalised);
the odd wiper's strokes end in a small rubber squeak. 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/wipers"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFG"
NR = 9
PX = float(os.environ.get("PX", "126"))      # bay pitch
PY = float(os.environ.get("PY", "108"))      # row pitch
Y0 = float(os.environ.get("Y0", "508"))      # top of row 1 glass
GW, GH = 112.0, 70.0                         # glass size
ARM = 60.0
A_REST, A_FAR = 172.0, 8.0
PCT = int(os.environ.get("PCT", "9"))
ODD = (os.environ.get("OL", "C"), int(os.environ.get("ON", "7")))
RAIN = float(os.environ.get("RAIN", "7"))    # drops per second per screen
rng = np.random.default_rng(int(os.environ.get("SEED", "22")))

G = []
for r in range(NR):
    n = 7 if r % 2 == 0 else 6
    for i in range(n):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        cx = W / 2 + (i - (n - 1) / 2) * PX
        P = 2.4 if odd else float(rng.choice([2.0, 2.4, 3.0]))
        G.append(dict(lab=lab, odd=odd, cx=cx, y=Y0 + r * PY, r=r, i=i, P=P,
                      ph=float(os.environ.get("OPH", ".55")) if odd else rng.uniform(0, 1)))
print(len(G), "wipers")
assert sum(g["odd"] for g in G) == 1

def ease(u): return .5 - .5 * math.cos(math.pi * min(1, max(0, u)))
def angle(g, t):
    """normal: sweeps back and forth across the glass all the time (cosine, dwell at the ends).
    odd: never turns back - keeps going round in one direction, passing down through the bonnet."""
    u = (t / g["P"] + g["ph"]) % 1.0
    if g["odd"]:
        # sweeps over the glass like the others (72% of the turn), then dives quickly through the bonnet
        TOP = float(os.environ.get("TOP", ".72")); span = A_REST - A_FAR
        if u < TOP: return A_REST - span * u / TOP, True
        return A_FAR - (360 - span) * (u - TOP) / (1 - TOP), True
    return 90 + (A_REST - 90) * math.cos(2 * math.pi * u), True

# ---- rain: periodic drops, each cleared the first time the blade passes it after landing ----
DT = 1 / 600
TS = np.arange(0, 2 * LOOP, DT)
for k, g in enumerate(G):
    th = np.array([angle(g, t)[0] for t in TS[:int(LOOP / DT)]])
    th = np.concatenate([th, th])
    nd = int(RAIN * LOOP)
    b = np.sort(rng.uniform(0, LOOP, nd))
    phi = rng.uniform(14, 166, nd); rad = np.sqrt(rng.uniform(.06, 1, nd)) * (ARM - 3)
    sz = rng.uniform(1.8, 4.6, nd)
    clr = np.empty(nd)
    for j in range(nd):
        i0 = int(b[j] / DT) + 1
        d = ((th[i0:i0 + int(4 / DT)] - phi[j] + 180) % 360) - 180
        seg = d > 0
        ch = np.nonzero((seg[1:] != seg[:-1]) & (np.abs(d[1:]) < 40))[0]
        clr[j] = b[j] + (ch[0] + 1) * DT if len(ch) else b[j] + 4
    g["drops"] = (b, clr, phi, rad, sz)

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_Q2 = font(TF_BOLD, float(os.environ.get('Q2', '80'))); F_LAB = font(TF_SB, 17); F_PCT = font(TF_BOLD, 38)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
CRM = (.96, .91, .81)

def glass_path(cx, y):
    p = skia.Path()
    x0, x1, yb = cx - GW / 2, cx + GW / 2, y + GH
    ins = 11
    p.moveTo(x0 + ins + 8, y); p.lineTo(x1 - ins - 8, y)
    p.quadTo(x1 - ins, y, x1 - ins + 1.5, y + 7)
    p.lineTo(x1 - 1, yb - 8); p.quadTo(x1, yb, x1 - 8, yb)
    p.lineTo(x0 + 8, yb); p.quadTo(x0, yb, x0 + 1, yb - 8)
    p.lineTo(x0 + ins - 1.5, y + 7); p.quadTo(x0 + ins, y, x0 + ins + 8, y)
    p.close(); return p

def draw_wiper(c, g, t):
    cx, y = g["cx"], g["y"]
    yb = y + GH
    gp = glass_path(cx, y)
    # car body: a bonnet strip under the glass + a roof hint above
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - GW / 2 - 4, yb - 2, cx + GW / 2 + 4, yb + 22), 7, 7),
                skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, yb), (0, yb + 22)],
                    [c4((.55, .38, .18)).toColor(), c4((.30, .19, .09)).toColor()])))
    text(c, f"{g['lab'][0]}{g['lab'][1]}", cx, yb + 17, F_LAB, (1, .88, .62), .95)
    # glass
    c.drawPath(gp, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y), (0, yb)],
        [c4((.24, .22, .21)).toColor(), c4((.10, .09, .085)).toColor()])))
    c.save(); c.clipPath(gp, doAntiAlias=True)
    px, py = cx, yb - 4
    # reflection streak
    c.drawLine(cx - 30, y + 6, cx - 48, yb - 6, P_((1, 1, 1), .05, StrokeWidth=8))
    # drops
    b, clr, phi, rad, sz = g["drops"]
    for sh in (0, -LOOP):
        bb = b + sh; cc = clr + sh
        m = (bb <= t) & (cc > t)
        for j in np.nonzero(m)[0]:
            age = t - bb[j]
            s = sz[j] * min(1, .4 + age / .12)
            a = math.radians(phi[j])
            dx, dy = px + rad[j] * math.cos(a), py - rad[j] * math.sin(a)
            c.drawCircle(dx + .6, dy + .8, s, P_((0, 0, 0), .35))
            c.drawCircle(dx, dy, s, P_((.80, .82, .84), .30))
            c.drawCircle(dx - s * .35, dy - s * .35, max(.7, s * .38), P_((1, 1, 1), .75))
    ang, moving = angle(g, t)
    if g["odd"]:
        c.restore(); c.save()
        uni = skia.Path(gp); uni.addRRect(skia.RRect.MakeRectXY(skia.Rect(cx - GW / 2 - 4, yb - 4, cx + GW / 2 + 4, yb + 22), 7, 7))
        c.clipPath(uni, doAntiAlias=True)
    # motion ghosts
    if moving:
        for k, dt in enumerate((.05, .033, .016)):
            a2, _ = angle(g, t - dt)
            c.save(); c.translate(px, py); c.rotate(-a2)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(12, -3, ARM, 3), 3, 3), P_(AMBER, .10 + .06 * k))
            c.restore()
    c.save(); c.translate(px, py); c.rotate(-ang)
    c.drawLine(0, 0, ARM - 4, 0, P_((.25, .17, .08), 1, StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(12, -3.6, ARM, 3.6), 3.6, 3.6), P_((.98, .78, .42), 1))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(12, 1, ARM, 3.6), 2, 2), P_((.25, .13, .05), .55))
    c.restore()
    c.restore()
    c.drawPath(gp, P_(CRM, .85, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
    c.drawCircle(px, py, 5, P_((.95, .78, .45), 1)); c.drawCircle(px, py, 2, P_((.35, .24, .1), 1))

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH WIPER", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER TURNS BACK?", W / 2, 356, F_Q2, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for g in G: draw_wiper(c, g, t)
        yb = 1528
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
BP = butter(2, [700, 5000], btype="band", fs=SR, output="sos")
def swish(f0, dur, seed, odd=False):
    t = np.arange(int((dur + .15) * SR)) / SR
    rg = np.random.default_rng(seed)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    nz = sosfilt(BP, rg.standard_normal(len(t))) * env * .5
    thup = np.sin(2 * np.pi * f0 * (t - dur)) * np.exp(-np.clip(t - dur, 0, None) * 40) * (t >= dur) * .6
    out = nz + thup
    if odd:
        tt = np.clip(t - dur + .09, 0, None)
        f = 1150 - 500 * np.clip(tt / .1, 0, 1)
        sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 28) * (t >= dur - .09) * .35
        out = out + sq
    return out
def rain_bed(n, seed=5):
    rg = np.random.default_rng(seed)
    x = np.zeros(n)
    idx = rg.integers(0, n, int(n / SR * 260))
    x[idx] = rg.uniform(-1, 1, len(idx))
    x = sosfilt(butter(2, [1500, 7000], btype="band", fs=SR, output="sos"), x)
    return x / (np.abs(x).max() + 1e-9) * .05

def audio(path):
    m = Mix(LOOP + 4)
    ev = []
    for k, g in enumerate(G):
        n, s = 2, g["P"] / 2
        for c_ in range(-2, int(LOOP / g["P"]) + 3):
            t0 = (c_ - g["ph"]) * g["P"]
            for j in range(n):
                ev.append((k, t0 + j * s, s))
    allt = np.array([e[1] % LOOP for e in ev])
    for k, ts, s in ev:
        tt = ts % LOOP
        g = G[k]
        if not (0 <= ts < LOOP): continue
        dens = math.sqrt(max(1, (np.abs(allt - tt) < .25).sum()))
        f0 = note(3 + (8 - g["r"]) // 2 + (g["i"] % 3), 65.41)
        gain = .55 / dens * (2.0 if g["odd"] else 1)
        m.add(swish(f0, s, k * 131 + int(tt * 70), g["odd"]), tt, gain, g["cx"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rb = rain_bed(n); rb2 = rain_bed(n, 9)
    m.L += rb; m.R += rb2
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot_wipers.mp4".replace("spot_wipers.mp4", "spot.wav"), f"{OUT}/spot_wipers.mp4"))
