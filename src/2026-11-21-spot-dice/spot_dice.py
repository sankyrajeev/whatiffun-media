"""SPOT IT v3 (10:00, 2026-11-21): 48 cream dice in 8 walnut FELT TRAYS (blocks of 3 x 2), columns A-F, rows 1-8.
Rule type IMPOSSIBLE OUTCOME (new): every die hops, tumbles a whole turn and lands showing a random face 1-6, on a 2 s
or 3 s cycle (random phase). The odd die tumbles like the rest but every time it lands it shows SEVEN pips
(two columns of three + a centre pip) - a face no die has. Sound: a soft rattle on each throw + a bone-on-felt
double clack on each landing (pentatonic by row, panned by x, density-normalised); the odd die lands with a duller,
lower clunk (audio clue). 12 s seamless loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/dice"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
NC, NR = 6, 8
LET = "ABCDEF"
SX, SY = 128.0, 120.0
X0 = 540 - (NC - 1) / 2 * SX + 22       # shift right a touch to make room for row numbers
Y0 = 612.0
S = 98.0                                  # die side
T_ROLL, T_SET = .62, .16
HOP = 62.0
PCT = int(os.environ.get("PCT", "14"))
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "5")))

D = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        Pc = 2.0 if odd else (2.0 if rng.uniform() < .7 else 3.0)
        ncy = int(round(LOOP / Pc))
        faces = []
        for k in range(ncy):
            f = int(rng.integers(1, 7))
            while faces and f == faces[-1]: f = int(rng.integers(1, 7))
            faces.append(f)
        if faces[0] == faces[-1] and ncy > 1: faces[0] = faces[0] % 6 + 1
        flick = [[int(rng.integers(1, 7)) for _ in range(4)] for _ in range(ncy)]
        D.append(dict(lab=lab, odd=odd, x=X0 + i * SX, y=Y0 + r * SY, r=r, i=i, P=Pc, ncy=ncy, ph=rng.uniform(0, 1),
                      faces=faces, flick=flick, spin=(1 if rng.uniform() < .5 else -1), jit=rng.uniform(-4, 4, 2)))
print(len(D), "dice")
assert sum(d["odd"] for d in D) == 1

def state(d, t):
    """-> (face, angle deg, hop px, scale, squash)"""
    Pc = d["P"]
    v = (t / Pc + d["ph"])
    k = int(math.floor(v)) % d["ncy"]
    u = (v - math.floor(v)) * Pc
    land_face = 7 if d["odd"] else d["faces"][k]
    prev_face = 7 if d["odd"] else d["faces"][(k - 1) % d["ncy"]]
    if u < T_ROLL:
        w = u / T_ROLL
        e = ss(w) * .7 + w * .3
        ang = d["spin"] * 360 * e
        hop = HOP * 4 * w * (1 - w)
        q = int(e * 4)                              # four quarter-turns: a new face every quarter
        if q == 0: face = prev_face
        elif q >= 4: face = land_face
        else: face = d["flick"][k][q] if not (d["flick"][k][q] == 7) else 1
        if d["odd"] and 0 < q < 4: face = d["flick"][k][q]
        sc = 1 + .12 * 4 * w * (1 - w)
        sq = 0.0
    else:
        w = (u - T_ROLL) / T_SET
        face, ang, hop = land_face, 0.0, 0.0
        sc = 1.0
        sq = .10 * math.exp(-w * 2.2) * math.cos(min(w, 3) * 4.0) if w < 3 else 0.0
        if u - T_ROLL < .12: hop = 9 * math.sin(math.pi * (u - T_ROLL) / .12)   # little second bounce
    return face, ang, hop, sc, sq

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_PCT = font(TF_BOLD, 38)
F_LAB = font(TF_SB, 30)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
CR = (.96, .92, .83); PIP = (.16, .10, .06)
BR = (.80, .62, .34); BR_D = (.42, .30, .14)
FELT = (.20, .12, .07)

PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)],
        7: [(-1, -1), (-1, 0), (-1, 1), (0, 0), (1, -1), (1, 0), (1, 1)]}
FACE_SH = skia.GradientShader.MakeLinear([(-S / 2, -S / 2), (S / 2, S / 2)],
                                         [c4((1, .99, .95)).toColor(), c4((.90, .84, .72)).toColor()])

def draw_die(c, d, t):
    face, ang, hop, sc, sq = state(d, t)
    x, y = d["x"] + d["jit"][0] * 0, d["y"]
    # shadow on felt (shrinks as the die rises)
    sh = 1 - .35 * hop / HOP
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - S / 2 * sh + 6, y - S / 2 * sh + 10, x + S / 2 * sh + 6, y + S / 2 * sh + 10), 16, 16),
                P_((0, 0, 0), .45 * sh, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7 + 8 * (1 - sh))))
    c.save()
    c.translate(x, y - hop)
    c.rotate(ang)
    c.scale(sc * (1 + sq), sc * (1 - sq))
    h = S / 2
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-h, -h + 5, h, h + 5), 18, 18), P_((.62, .52, .38)))   # side edge
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-h, -h, h, h), 18, 18), skia.Paint(AntiAlias=True, Shader=FACE_SH))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-h + 1, -h + 1, h - 1, h - 1), 17, 17),
                P_((1, 1, 1), .35, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5))
    g = 26.0
    for px, py in PIPS[face]:
        c.drawCircle(px * g, py * g + 1.2, 9.6, P_((1, 1, 1), .5))
        c.drawCircle(px * g, py * g, 9.6, P_(PIP))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH DIE", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "ROLLS A 7?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s) + 2 * (len(s) - 1)
        pill = skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31)
        c.drawRRect(pill, skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        # felt trays: 2 x 4 blocks of 3 x 2 dice
        for bi in range(2):
            for bj in range(4):
                xa = X0 + bi * 3 * SX - SX / 2 + 8; xb = xa + 3 * SX - 16
                ya = Y0 + bj * 2 * SY - SY / 2 + 6; yb = ya + 2 * SY - 12
                rr = skia.RRect.MakeRectXY(skia.Rect(xa, ya, xb, yb), 20, 20)
                c.drawRRect(rr, P_(FELT, .95))
                c.drawRRect(rr, P_(BR, .55, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        for i in range(NC):
            text(c, LET[i], X0 + i * SX, Y0 - SY / 2 - 14, F_LAB, CREAM, .85)
        for r in range(NR):
            text(c, str(r + 1), X0 - SX / 2 - 24, Y0 + r * SY + 11, F_LAB, CREAM, .85)
        # draw resting dice first, airborne on top
        order = sorted(D, key=lambda d: state(d, t)[2])
        for d in order:
            draw_die(c, d, t)
        yb = 1566
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1648, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def rattle(seed, dur=.35):
    n = int(dur * SR); t = np.arange(n) / SR
    rg = np.random.default_rng(seed)
    s = np.zeros(n)
    for k in range(6):
        t0 = rg.uniform(0, .25); i0 = int(t0 * SR); m = n - i0
        tt = np.arange(m) / SR
        s[i0:] += rg.uniform(.4, 1) * np.sin(2 * np.pi * rg.uniform(2600, 4200) * tt) * np.exp(-tt * 160)
    return s
def clack(f0, seed, dur=.25, dull=False):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    parts = ((1, 40, .6), (2.3, 60, .3), (4.1, 90, .18)) if not dull else ((1, 22, .8), (1.9, 40, .2))
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + rg.uniform(0, 6)) * np.exp(-t * dd) for m, dd, a in parts)
    nz = rg.standard_normal(len(t)) * np.exp(-t * 300) * (.25 if not dull else .1)
    return (s + nz) * np.minimum(1, t * 4000)

def audio(path):
    m = Mix(LOOP + 1.8)
    ev = []
    for k, d in enumerate(D):
        for n in range(-2, 9):
            t0 = (n - d["ph"]) * d["P"]
            ev.append((t0 + .01, k, "rat"))
            ev.append((t0 + T_ROLL, k, "land"))
    lt = np.array([e[0] for e in ev if e[2] == "land"])
    rt = np.array([e[0] for e in ev if e[2] == "rat"])
    for tt, k, kind in ev:
        if not (0 <= tt < LOOP): continue
        d = D[k]
        if kind == "rat":
            m.add(rattle(k * 31 + int(tt * 10)), tt, .10 / math.sqrt(max(1, (np.abs(rt - tt) < .4).sum())), d["x"])
            continue
        dens = math.sqrt(max(1, (np.abs(lt - tt) < .4).sum()))
        if d["odd"]:
            m.add(clack(note(2, 110.0), k * 100 + int(tt * 50), .4, dull=True), tt, .55 / dens, d["x"])
            m.add(clack(note(2, 110.0), k * 100 + int(tt * 50) + 1, .3, dull=True), tt + .12, .25 / dens, d["x"])
        else:
            f0 = note(8 - d["r"] + 6, 220.0)
            m.add(clack(f0, k * 100 + int(tt * 50)), tt, .42 / dens, d["x"])
            m.add(clack(f0, k * 100 + int(tt * 50) + 1, .18), tt + .12, .18 / dens, d["x"])
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    for ch, seed in ((m.L, 3), (m.R, 4)):
        x = np.random.default_rng(seed).standard_normal(n)
        sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
        sp *= np.exp(-((fr - 300) / 400) ** 2)
        bed = np.fft.irfft(sp, n); bed /= np.abs(bed).max(); ch += bed * .03
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_dice.mp4"))
