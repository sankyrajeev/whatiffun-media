"""SPOT IT v3 (15:00, 2026-11-22): WHICH SWING / NEVER STOPS? 54 identical playground swings (walnut plank seat on
two cream chains) hanging from NINE LONG SWING-SET BEAMS: 6 columns A-F x 9 rows, each row one brass-capped walnut
beam with splayed legs at both ends; column letters on top, row numbers in the left margin.
Every swing gets a push on a 4 s or 3 s cycle from a random phase: it swings ~+-32 deg (period 1 s) and dies away to
a dead stop, then hangs still for ~1-1.5 s. ONE swing (D6) never stops: it keeps swinging the whole loop (amplitude
breathes 70-100 %). Rule type: NEVER STOPS (moving vs still), the No. 43 fans rule on a new object.
Sound: a soft wooden push-thump on every push and a tiny chain clink when each swing settles (pentatonic by row,
panned by x, density-normalised); the odd swing never clinks, it gives a low chain creak at each far end. 12 s loop."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *
from scipy.signal import butter, sosfilt

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/swings"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEF"
NC, NR = 6, 9
XS = [240 + 128 * i for i in range(NC)]
BY0 = float(os.environ.get("BY0", "560"))
RP = float(os.environ.get("RP", "106"))
CHAIN = float(os.environ.get("CHAIN", "72"))
AMP = float(os.environ.get("AMP", "46"))
TP = 1.0
PCT = int(os.environ.get("PCT", "14"))
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "6")))
rng = np.random.default_rng(int(os.environ.get("SEED", "22")))

S = []
for r in range(NR):
    for i in range(NC):
        lab = (LET[i], r + 1)
        odd = lab == ODD
        P = 4.0; rest = 1.35
        # push times: a diagonal wave (1 s per column, 1.5 s per row: alternate rows swing in anti-phase) + a little noise, so a band of still swings
        # sweeps the field while neighbours in a row stay in phase (no collisions)
        t0 = (i * 1.0 + r * 1.5 + rng.uniform(-.06, .06)) % P
        S.append(dict(lab=lab, odd=odd, x=XS[i], by=BY0 + r * RP, r=r, i=i, P=P, rest=rest,
                      ph=-t0 / P, t0=t0, A=AMP * rng.uniform(.88, 1.06), sgn=1, w=rng.uniform(0, 6.28)))
print(len(S), "swings")
assert sum(s["odd"] for s in S) == 1

def cyc(s, t): return ((t / s["P"] + s["ph"]) % 1.0) * s["P"]
def angle(s, t):
    if s["odd"]:
        env = .82 + .14 * math.sin(2 * math.pi * t / 4.0 + s["w"])
        return s["A"] * env * math.sin(2 * math.pi * (t - s["t0"]) / TP)
    u = cyc(s, t); Ta = s["P"] - s["rest"]
    if u >= Ta: return 0.0
    k = u / Ta
    rise = min(1, u / .12)
    return s["sgn"] * s["A"] * rise * (1 - k) ** 1.0 * (1 - k * k) ** .5 * math.sin(2 * math.pi * u / TP)

def events(s):
    out = []
    if s["odd"]:
        for k in range(int(LOOP / TP) * 2):
            out.append(("creak", s["t0"] + TP / 4 + k * TP / 2))
        return [(e, tt % LOOP) for e, tt in out]
    for k in range(-3, int(LOOP / s["P"]) + 4):
        t0 = (k - s["ph"]) * s["P"]
        out.append(("push", t0)); out.append(("settle", t0 + s["P"] - s["rest"] - .35))
    return [(e, tt % LOOP) for e, tt in out if -1 <= tt < LOOP + 1]
EV = [events(s) for s in S]

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84); F_PCT = font(TF_BOLD, 38); F_ROW = font(TF_SB, 30)
F_CTA = font(TF_SB, 42); F_LIKE = font(TF_SERIF_I, 36)
CRM = (.96, .91, .81)
WAL = (.55, .33, .16)

def draw_beam(c, by):
    x0, x1 = 162, 958
    # legs
    for xa, xb in ((x0 + 14, x0 - 8), (x1 - 14, x1 + 8)):
        c.drawLine(xa, by, xb, by + CHAIN + 30, P_((.42, .26, .13), 1, StrokeWidth=7, StrokeCap=skia.Paint.kRound_Cap))
        c.drawLine(xa + 10 * (1 if xa < 540 else -1), by, xb + 26 * (1 if xa < 540 else -1), by + CHAIN + 30,
                   P_((.36, .22, .11), 1, StrokeWidth=6, StrokeCap=skia.Paint.kRound_Cap))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, by - 6, x1, by + 8), 5, 5),
                P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    rr = skia.RRect.MakeRectXY(skia.Rect(x0, by - 8, x1, by + 4), 5, 5)
    sh = skia.GradientShader.MakeLinear([(0, by - 8), (0, by + 4)],
        [c4((.80, .55, .30)).toColor(), c4((.55, .34, .17)).toColor(), c4((.33, .20, .10)).toColor()], [0, .5, 1])
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=sh))
    for xc in (x0, x1):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xc - 9, by - 10, xc + 9, by + 6), 3, 3), P_((.92, .74, .42), 1))

def draw_swing(c, s, t):
    x, by = s["x"], s["by"]
    a = angle(s, t)
    c.save(); c.translate(x, by); c.rotate(-a)
    L = CHAIN
    # hooks
    for hx in (-19, 19):
        c.drawCircle(hx, 0, 3.6, P_((.95, .78, .45), 1))
    # chains: dotted links
    for hx, sx in ((-19, -24), (19, 24)):
        n = 9
        for k in range(n):
            u0, u1 = k / n, (k + .78) / n
            c.drawLine(hx + (sx - hx) * u0, 3 + (L - 3) * u0, hx + (sx - hx) * u1, 3 + (L - 3) * u1,
                       P_(CRM, .92, StrokeWidth=4.2, StrokeCap=skia.Paint.kRound_Cap))
    # seat plank
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-31, L + 3, 31, L + 19), 4, 4),
                P_((0, 0, 0), .45, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    seat = skia.RRect.MakeRectXY(skia.Rect(-31, L - 4, 31, L + 12), 4, 4)
    sh = skia.GradientShader.MakeLinear([(0, L - 3), (0, L + 10)],
        [c4((1.0, .76, .38)).toColor(), c4((.88, .55, .22)).toColor(), c4((.55, .32, .12)).toColor()], [0, .55, 1])
    c.drawRRect(seat, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawLine(-28, L - 2, 28, L - 1.5, P_((1, .95, .82), .5, StrokeWidth=1.4))
    for sx in (-24, 24):
        c.drawCircle(sx, L + 3, 2.2, P_((.35, .22, .1), 1))
    c.restore()

BG = background(1000)
def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH SWING", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER STOPS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s_ = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s_) + 2 * (len(s_) - 1)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31),
                    skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s_, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        for i in range(NC):
            text(c, LET[i], XS[i], 526, F_ROW, AMBER, .9)
        for r in range(NR):
            by = BY0 + r * RP
            text(c, str(r + 1), 122, by + CHAIN + 10, F_ROW, AMBER, .9)
        for r in range(NR):
            draw_beam(c, BY0 + r * RP)
        for s in S: draw_swing(c, s, t)
        yb = 1560
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 44, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 42, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1650, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def thump(f0, seed):
    t = np.arange(int(.35 * SR)) / SR
    rg = np.random.default_rng(seed)
    nz = sosfilt(butter(2, [150, 1200], btype="band", fs=SR, output="sos"), rg.standard_normal(len(t))) * np.exp(-t * 70)
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 22)
    return nz * .4 + body * .8
def clink(f0, seed):
    t = np.arange(int(.4 * SR)) / SR
    rg = np.random.default_rng(seed)
    s = np.zeros(len(t))
    for k, d in enumerate((0, .045)):
        n0 = int(d * SR); tt = t[:len(t) - n0]
        s[n0:] += (np.sin(2 * np.pi * f0 * 4 * tt) + .5 * np.sin(2 * np.pi * f0 * 6.3 * tt)) * np.exp(-tt * 28) * (.7 if k else 1)
    s[:200] += rg.standard_normal(200) * np.exp(-np.arange(200) / 30) * .3
    return s * .5
def creak(seed):
    t = np.arange(int(.32 * SR)) / SR
    rg = np.random.default_rng(seed)
    f = 190 + 40 * np.sin(np.pi * t / .32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 6))
    am = (1 + .6 * np.sign(np.sin(2 * np.pi * 38 * t))) / 1.6
    env = np.sin(np.pi * t / .32) ** 2
    return saw * am * env * .35 + rg.standard_normal(len(t)) * env * .02

def audio(path):
    m = Mix(LOOP + 4)
    allt = np.array([tt for k in range(len(S)) for e, tt in EV[k] if e != "creak"])
    for k, s in enumerate(S):
        for e, tt in EV[k]:
            if not (0 <= tt < LOOP): continue
            if e == "creak":
                m.add(creak(k * 31 + int(tt * 50)), tt, .22, s["x"]); continue
            dens = math.sqrt(max(1, (np.abs(allt - tt) < .2).sum()))
            f0 = note(4 + (8 - s["r"]) // 2 + (s["i"] % 3), 65.41)
            if e == "push": m.add(thump(f0 * .5 + 40, k * 100 + int(tt * 50)), tt, .5 / dens, s["x"])
            else: m.add(clink(f0, k * 77 + int(tt * 40)), tt, .28 / dens, s["x"])
    n = int(LOOP * SR)
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_swings.mp4"))
