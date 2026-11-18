"""SPOT IT v3 (18:00, 2026-11-18): 52 padlocks on a bridge railing, every key turns, ONE lock springs open.
Rule type: UNLOCK (new: every key turns, every lock stays shut, except one). Arrangement: BRIDGE RAILING,
8 steel cables with offset rows 7/6/7/6/7/6/7/6 (each lock has its label engraved on its brass body, "D5").
Every lock swings on its cable (big pendulum arcs, a soft diagonal wave + noise so you must check each) and its
key gives a full half-turn every 3 s (4 per 12 s loop) with a clack and a tug; on the odd lock the turn pops the
shackle: the body drops off the short leg, the shackle swings out, then it snaps shut as the key turns back.
Sound: a metallic key clack per turn (pentatonic by row, panned by x, density-normalised), a softer click on the
way back, a faint cable creak bed; the odd lock adds a springy brass 'ping-clunk' when it pops (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/locks"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
WIDTHS = [7, 6, 7, 6, 7, 6, 7, 6]
NR = len(WIDTHS)
LET = "ABCDEFG"
SX, SY = 122, 128
Y0 = 408                       # cable of row 1
P = 3.0                        # key cycle
PSW = 2.0                      # swing period (6 swings per loop)
AMP = math.radians(float(os.environ.get("AMP", "16")))
ODD = (os.environ.get("OL", "E"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "47")))

LOCKS = []                     # (label, x, y, key phase, swing phase, row)
for r, n in enumerate(WIDTHS):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y0 + r * SY
        ph = (.11 * i + .19 * r + rng.uniform(0, .55)) % 1.0
        sp = (.09 * i + .12 * r + rng.uniform(0, .12)) % 1.0
        LOCKS.append(((LET[i], r + 1), x, y, ph, sp, r))

def sm(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
K0, K1, K2, K3 = .00, .14, .40, .54     # key: turn out (K0-K1), hold, turn back (K2-K3)
def state(t, ph, sp, odd):
    """(swing angle rad, key turn 0..1, body drop px, shackle swing 0..1, tug px)"""
    u = (t / P + ph) % 1.0
    if u < K1: kt = sm(u / K1)
    elif u < K2: kt = 1.0
    elif u < K3: kt = 1 - sm((u - K2) / (K3 - K2))
    else: kt = 0.0
    sw = AMP * math.sin(2 * math.pi * (t / PSW + sp))
    tug = 0.0
    for ue in (K1, K3):          # a small tug at each clack
        d = (u - ue) % 1.0
        if d < .08: tug += 7 * math.sin(math.pi * d / .08)
    drop, sh = 0.0, 0.0
    if odd:
        if K1 <= u < K2 + .04:
            v = (u - K1) * P            # seconds since pop
            drop = 19 * (1 - math.exp(-v * 30) * math.cos(v * 34))   # springs down with a bounce
            sh = sm(v / .35)
        elif K2 + .04 <= u < K3:
            v = (u - K2 - .04) / (K3 - K2 - .04)
            sh = 1 - sm(v / .7)
            drop = 19 * (1 - sm((v - .55) / .45))
        tug *= .3
    return sw, kt, drop, sh, tug
def events(ph):
    out = []
    for k in range(-2, int(LOOP / P) + 3):
        for du, kind in ((K1, "turn"), (K3, "back")):
            tt = (k + du - ph) * P
            if 0 <= tt < LOOP: out.append((tt, kind))
    return out

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_ENG = font(TF_BOLD, 28)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

BW, BH = 64, 54                 # body
SH_W, SH_H, SH_T = 40, 40, 9    # shackle outer width, height above body, thickness
LEG = 12                        # how deep the legs go into the body
BRASS = [rgb((1, .9, .62)), rgb((.92, .7, .34)), rgb((.58, .38, .14))]
STEEL = [rgb((.95, .94, .92)), rgb((.66, .66, .66)), rgb((.32, .32, .33))]

def shackle(c, sh):
    """shackle hooked at (0,0); legs end at y = SH_H + LEG. Swings out around its left (long) leg."""
    L = -SH_W / 2 + SH_T / 2
    R = SH_W / 2 - SH_T / 2
    cs = 1 - .45 * sh
    rx = L + (R - L) * cs            # projected x of the short leg
    p = skia.Path()
    rr = (rx - L) / 2
    cy = SH_T / 2 + abs(rr)
    p.moveTo(L, SH_H + LEG + 26)
    p.lineTo(L, cy)
    if abs(rr) > .5:
        p.arcTo(skia.Rect(min(L, rx), cy - abs(rr), max(L, rx), cy + abs(rr)), 180 if rr > 0 else 0, 180 if rr > 0 else -180, False)
    p.lineTo(rx, SH_H + LEG)
    pt = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=SH_T + 2.5, StrokeCap=skia.Paint.kRound_Cap,
                    Color4f=c4((.08, .08, .09), .85))
    c.drawPath(p, pt)
    pt = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=SH_T, StrokeCap=skia.Paint.kRound_Cap,
                    Shader=skia.GradientShader.MakeLinear([(-SH_W / 2, 0), (SH_W / 2, 0)], STEEL, [0, .35, 1]))
    c.drawPath(p, pt)
    hl = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, StrokeCap=skia.Paint.kRound_Cap,
                    Color4f=c4((1, 1, 1), .5))
    c.drawLine(L - 2, cy, L - 2, SH_H + 4, hl)

def body(c, lab, y0):
    r = skia.Rect(-BW / 2, y0, BW / 2, y0 + BH)
    c.drawRoundRect(r.makeOffset(0, 3), 10, 10, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .5),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    c.drawRoundRect(r, 10, 10, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(-BW / 2, y0), (BW / 2, y0 + BH)], BRASS, [0, .45, 1])))
    c.drawRoundRect(r.makeInset(2, 2), 8, 8, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6,
                    Color4f=c4((1, .96, .8), .35)))
    c.drawRect(skia.Rect(-BW / 2 + 3, y0 + 2, BW / 2 - 3, y0 + 7), skia.Paint(AntiAlias=True, Color4f=c4((1, .97, .85), .28)))
    # engraved label
    s = f"{lab[0]}{lab[1]}"
    text(c, s, 0, y0 + 37.5, F_ENG, (1, .93, .7), .45)
    text(c, s, 0, y0 + 36, F_ENG, (.24, .14, .04), .92)
    # keyhole on the underside
    c.drawRoundRect(skia.Rect(-7, y0 + BH - 4, 7, y0 + BH + 1), 2, 2, skia.Paint(AntiAlias=True, Color4f=c4((.12, .08, .03))))

def key(c, y0, kt):
    """key hanging from the keyhole at y0; turning = rotation about the vertical axis (bow width ~ |cos|)."""
    a = math.pi * kt
    s = math.cos(a)
    w = max(2.2, 15 * abs(s))
    side = s >= 0
    sh = skia.GradientShader.MakeLinear([(-w, 0), (w, 0)], STEEL if side else [STEEL[2], STEEL[1], STEEL[0]], [0, .4, 1])
    # shank
    c.drawRect(skia.Rect(-max(1.6, 3.2 * abs(s)) , y0, max(1.6, 3.2 * abs(s)), y0 + 16), skia.Paint(AntiAlias=True, Shader=sh))
    # bow (ring) — an ellipse squashed by the turn
    ob = skia.Rect(-w, y0 + 14, w, y0 + 44)
    c.drawOval(ob, skia.Paint(AntiAlias=True, Shader=sh))
    if w > 6:
        c.drawOval(skia.Rect(-w * .45, y0 + 22, w * .45, y0 + 36), skia.Paint(AntiAlias=True, Color4f=c4((.05, .045, .04))))
    c.drawOval(ob, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=c4((0, 0, 0), .5)))

def lock(c, lab, x, y, st):
    sw, kt, drop, sh, tug = st
    c.save(); c.translate(x, y); c.rotate(math.degrees(sw))
    # body hangs from the shackle; on the open lock it drops off the short leg
    by = SH_H + tug + drop
    shackle(c, sh)
    if drop > 0:      # hanging from the long leg only: the body tips away from it
        c.translate(-SH_W / 2 + SH_T / 2, SH_H); c.rotate(15 * drop / 19); c.translate(SH_W / 2 - SH_T / 2, -SH_H)
    body(c, lab, by)
    key(c, by + BH, kt)
    c.restore()

def cables(c, t):
    for r in range(NR):
        y = Y0 + r * SY
        p = skia.Path(); p.moveTo(70, y - 6)
        p.quadTo(540, y + 10, 1010, y - 6)
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color4f=c4((0, 0, 0), .55)))
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4.5, Shader=skia.GradientShader.MakeLinear(
            [(0, y - 3), (0, y + 3)], [rgb((.75, .73, .7)), rgb((.36, .35, .34))])))
    # two railing posts
    for x in (78, 1002):
        c.drawRoundRect(skia.Rect(x - 7, Y0 - 22, x + 7, Y0 + (NR - 1) * SY + 30), 6, 6, skia.Paint(AntiAlias=True,
                        Shader=skia.GradientShader.MakeLinear([(x - 7, 0), (x + 7, 0)], [rgb((.5, .48, .45)), rgb((.25, .24, .23))])))

def cable_y(x, r):
    y = Y0 + r * SY
    u = (x - 70) / 940
    return y - 6 + 16 * u * (1 - u) * 2 * .5 * 2

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH LOCK", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "POPS OPEN?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        cables(c, t)
        for lab, x, y, ph, sp, r in LOCKS:
            lock(c, lab, x, cable_y(x, r) - 3, state(t, ph, sp, lab == ODD))
        yb = 1512
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 50, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 48, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def clack(f0, dur=.16, seed=0, soft=False):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    n = rg.standard_normal(len(t))
    hp = np.diff(n, prepend=0)
    tick = hp * np.exp(-t * (260 if soft else 180)) * (.25 if soft else .45)
    ring = (np.sin(2 * np.pi * f0 * 2 * t) + .4 * np.sin(2 * np.pi * f0 * 5.4 * t)) * np.exp(-t * (60 if soft else 38))
    low = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 50) * .4
    return (tick + ring * (.35 if soft else .55) + low * (0 if soft else 1)) * np.minimum(1, t * 6000)
def ping(f0, dur=.6):
    t = np.arange(int(dur * SR)) / SR
    spring = np.sin(2 * np.pi * (f0 * 3 + 160 * np.exp(-t * 9)) * t) * np.exp(-t * 7) * .55
    clunk = np.sin(2 * np.pi * 95 * t) * np.exp(-t * 26) * .9
    return (spring + clunk) * np.minimum(1, t * 5000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, sp, r) in enumerate(LOCKS):
        for tt, kind in events(ph): ev.append((tt, k, kind))
    allt = np.array([e[0] for e in ev])
    for tt, k, kind in ev:
        lab, x, y, ph, sp, r = LOCKS[k]
        odd = lab == ODD
        dens = (np.abs(allt - tt) < .06).sum()
        f0 = note(NR - 1 - r + 4, 220.0) * (1 + .003 * (x - 540) / SX)
        m.add(clack(f0, seed=k * 3 + (kind == "back"), soft=kind == "back"), tt, (.72 if kind == "turn" else .45) / math.sqrt(dens), x)
        if odd and kind == "turn":
            m.add(ping(f0), tt + .01, .55, x)
        if odd and kind == "back":
            m.add(clack(f0 * .75, seed=999), tt - .05, .35, x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)          # soft breezy bed over the river
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 500) / 400) ** 2) + .25 * np.exp(-((fr - 2500) / 1500) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .045; m.R += np.roll(bed, 7000) * .045
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_locks.mp4"))
