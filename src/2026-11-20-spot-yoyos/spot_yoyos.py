"""SPOT IT v3 (18:00, 2026-11-20): 46 yo-yos in an OVAL / LENS of 5 GARLAND ROWS of 9 sagging between brass posts (rows 1-6 top to bottom,
letters A.. from the left of each row; the label is printed on each yo-yo's stationary hub cap "D4").
Rule type RETURN (it never comes back up): every yo-yo hangs from a brass finger peg; every 3 s or 4 s (random phase, so the field never repeats inside the loop) the peg
flicks, the yo-yo shoots down its string spinning hard, sleeps a moment at the bottom, then climbs back and is caught
with a soft wooden tock. The odd yo-yo goes down and NEVER climbs back: it sleeps at the bottom of its string, spinning,
for the whole loop, while its peg keeps flicking. Sound: string zip per throw + wooden catch tock (pentatonic by row,
panned by x, density-normalised); the odd yo-yo gives a low sleepy buzz instead of a catch."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/yoyos"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
P = 3.0
ROWS = [9, 9, 9, 9, 9]
SAG = 30.0
LET = "ABCDEFGHI"
SX = 98.0
Y1, SY = 518.0, 196.0          # peg y of row 1, row pitch
R = 44.0                       # yo-yo radius (88 px across)
S0, TRAV = 4.0, 90.0          # string length at rest, extra drop
T_DN, T_SL, T_UP = .28, .17, .45
PCT = int(os.environ.get("PCT", "21"))
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "4")))
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))

C = []
for r, n in enumerate(ROWS):
    for i in range(n):
        lab = (LET[i], r + 1)
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y1 + r * SY + SAG * (1 - ((i - (n - 1) / 2) / ((n - 1) / 2)) ** 2)
        C.append(dict(lab=lab, odd=lab == ODD, x=x, y=y, r=r, i=i,
                      P=(3.0 if rng.uniform() < .5 else 4.0), ph=rng.uniform(0, 1), a0=rng.uniform(0, 2 * math.pi), sw=rng.uniform(0, 1)))
print(len(C), "yo-yos")
assert any(cn["odd"] for cn in C)

def state(cn, t):
    """returns (drop 0..1, spin angle, peg flick 0..1)"""
    Pc = cn["P"]
    u = ((t / Pc + cn["ph"]) % 1.0) * Pc
    flick = math.exp(-((u - .04) / .07) ** 2)
    if cn["odd"]:
        d = 1.0 + .06 * math.sin(2 * math.pi * 4 * t / LOOP) + .05 * flick
        ang = cn["a0"] + 2 * math.pi * 3.0 * t          # 36 turns per loop, seamless
        return d, ang, flick
    if u < T_DN:
        v = u / T_DN; d = v ** 1.6                       # accelerating fall
    elif u < T_DN + T_SL:
        v = (u - T_DN) / T_SL; d = 1 + .05 * math.sin(math.pi * v)
    elif u < T_DN + T_SL + T_UP:
        v = (u - T_DN - T_SL) / T_UP; d = 1 - ss(v) ** .85
    else:
        v = (u - T_DN - T_SL - T_UP) / (Pc - T_DN - T_SL - T_UP)
        d = .03 * math.sin(math.pi * v) * math.exp(-v * 2)   # little settle bob
    # spin: whole cycle = exactly 4/3 turn (seamless for 3 s and 4 s cycles), fast while moving, stopped when resting
    act = T_DN + T_SL + T_UP
    g = 1.0 if u >= act else (u / act - math.sin(2 * math.pi * u / act) / (2 * math.pi))
    ang = cn["a0"] + 2 * math.pi * (4 / 3) * g
    return d, ang, flick

def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
def P_(col, a=1.0, **kw): return skia.Paint(AntiAlias=True, Color4f=c4(col, a), **kw)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_PCT = font(TF_BOLD, 38)
F_LAB = font(TF_SB, 21)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)
CR = (.95, .90, .80); AM = (.86, .58, .26); AM_D = (.50, .30, .11)
BR = (.80, .62, .34); BR_D = (.42, .30, .14)

# one blade of the pinwheel print on the yo-yo face (3 swooshes)
BLADE = skia.Path()
BLADE.moveTo(0, 0); BLADE.cubicTo(10, -14, 30, -22, 40, -12); BLADE.cubicTo(30, -30, 6, -34, -6, -20); BLADE.close()
RIMSH = skia.GradientShader.MakeRadial((-14, -16), R * 1.5, [c4((1, 1, 1), .30).toColor(), c4((1, 1, 1), 0).toColor(),
                                        c4((0, 0, 0), .22).toColor()], [0, .45, 1])

def draw_yoyo(c, cn, t):
    d, ang, fl = state(cn, t)
    px, py = cn["x"], cn["y"] - 6 * fl                 # peg flicks up
    L = S0 + TRAV * d
    sway = math.radians(2.5 * math.sin(2 * math.pi * (2 * t / LOOP + cn["sw"])) * (.3 + d))
    yx, yy = px + (L + R) * math.sin(sway), py + (L + R) * math.cos(sway)
    # string
    c.drawLine(px, py, yx - R * math.sin(sway) * 0 , yy - 2, P_(CR, .75, StrokeWidth=1.6))
    # peg: small brass finger ring
    c.drawCircle(px, py - 4, 7, P_(BR, 1, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2))
    c.drawCircle(px, py - 4, 7, P_(BR_D, .5, Style=skia.Paint.kStroke_Style, StrokeWidth=1))
    # shadow
    c.drawCircle(yx + 4, yy + 7, R, P_((0, 0, 0), .35, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
    # body
    c.drawCircle(yx, yy, R, P_(AM_D))
    c.drawCircle(yx, yy, R - 4, P_(CR))
    c.save(); c.translate(yx, yy); c.rotate(math.degrees(ang))
    for k in range(3):
        c.save(); c.rotate(120 * k); c.drawPath(BLADE, P_(AM)); c.restore()
    c.restore()
    c.drawCircle(yx, yy, R - 4, skia.Paint(AntiAlias=True, Shader=RIMSH))
    c.drawCircle(yx, yy, R - 2, P_(AM_D, .9, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
    # stationary hub cap with the label
    c.drawCircle(yx, yy, 21, P_((.17, .11, .06), .94))
    c.drawCircle(yx, yy, 21, P_(BR, .8, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6))
    text(c, f"{cn['lab'][0]}{cn['lab'][1]}", yx, yy + 7.5, F_LAB, CR, .97)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH YO-YO", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER COMES BACK?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        s = f"ONLY {PCT}% CAN FIND IT"
        tw = sum(F_PCT.measureText(ch) for ch in s) + 2 * (len(s) - 1)
        pill = skia.RRect.MakeRectXY(skia.Rect(W / 2 - tw / 2 - 30, 400, W / 2 + tw / 2 + 30, 462), 31, 31)
        c.drawRRect(pill, skia.Paint(AntiAlias=True, Color4f=c4((.75, .2, .14), .92)))
        text(c, s, W / 2, 445, F_PCT, (1, .96, .9), 1.0, spacing=2)
        # brass rails for each row
        for r, n in enumerate(ROWS):   # garland rails sagging between two brass posts
            h = (n - 1) / 2 * SX + 46
            pa = skia.Path(); pb = skia.Path()
            for k in range(41):
                xx = -h + 2 * h * k / 40
                yy = Y1 + r * SY - 13 + SAG * 1.1 * (1 - (xx / h) ** 2) - 6
                (pa.moveTo if k == 0 else pa.lineTo)(540 + xx, yy)
            c.drawPath(pa, P_(BR_D, .95, Style=skia.Paint.kStroke_Style, StrokeWidth=5, StrokeCap=skia.Paint.kRound_Cap))
            c.drawPath(pa, P_(BR, .5, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5))
            for sx in (-1, 1):
                c.drawCircle(540 + sx * h, Y1 + r * SY - 19, 7, P_(BR))
        for cn in C:
            draw_yoyo(c, cn, t)
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
def zip_(seed, dur=.42):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.random.default_rng(seed).standard_normal(n)
    sp = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    sp *= np.exp(-((fr - 2400) / 1500) ** 2); x = np.fft.irfft(sp, n); x /= np.abs(x).max() + 1e-9
    env = np.minimum(1, t / .02) * np.exp(-t * 7)
    return x * env * (.7 + .3 * np.sin(2 * np.pi * (40 + 120 * t) * t))
def tock(f0, seed, dur=.22):
    t = np.arange(int(dur * SR)) / SR
    rg = np.random.default_rng(seed)
    s = sum(a * np.sin(2 * np.pi * f0 * m * t + rg.uniform(0, 6)) * np.exp(-t * dd) for m, dd, a in ((1, 30, .7), (2.76, 48, .28), (5.4, 70, .1)))
    return s * np.minimum(1, t * 4000)
def buzz(seed, dur=.6):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / .05) * np.exp(-t * 4)
    f = 118 + 6 * np.sin(2 * np.pi * 9 * t)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + .4 * np.sin(2 * np.pi * 2 * np.cumsum(f) / SR)
    return s * env

def audio(path):
    m = Mix(LOOP + 1.8)
    ev = []
    for k, cn in enumerate(C):
        for n in range(-2, 8):
            t0 = (n - cn["ph"]) * cn["P"]
            ev.append((t0 + .02, k, "zip"))
            ev.append((t0 + T_DN + T_SL + T_UP, k, "catch"))
    zt = np.array([e[0] for e in ev if e[2] == "zip"])
    ct = np.array([e[0] for e in ev if e[2] == "catch"])
    for tt, k, kind in ev:
        if not (0 <= tt < LOOP): continue
        cn = C[k]
        dens = max(1, (np.abs(zt - tt) < .5).sum())
        if kind == "zip":
            m.add(zip_(k * 31 + int(tt * 10)), tt, .30 / math.sqrt(dens), cn["x"])
        elif cn["odd"]:
            m.add(buzz(k * 7 + int(tt * 10)), tt, .09, cn["x"])
        else:
            m.add(tock(note(6 - cn["r"] + 5, 220.0), k * 100 + int(tt * 50)), tt, .40 / math.sqrt(max(1, (np.abs(ct - tt) < .5).sum())), cn["x"])
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
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_yoyos.mp4"))
