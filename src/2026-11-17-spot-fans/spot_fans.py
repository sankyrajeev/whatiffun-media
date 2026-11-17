"""SPOT IT v3 (18:00, 2026-11-17): 68 ceiling fans in STAGGERED COLUMNS, one never stops.
Rule type: STOP (it never comes to rest). Arrangement: 8 columns A-H, alternate columns shifted down half a step
(9/8/9/8/... fans), each fan's brass hub carries its own label "C4" (columns are offset, rows aren't straight).
Every fan runs a 4 s cycle: rest 1.0 s (blades crisp and still), spin up, cruise at ~1.7 turns/s (blades blur into a
soft disc), spin down to a dead stop. Phases follow a soft diagonal wave + noise, so waves of stopping fans sweep the
field. The odd fan keeps turning the whole loop (its speed breathes 50-100 %, but it never stops).
Sound: a soft wooden tock when each fan comes to rest (pentatonic by row, panned by x, density-normalised) over a
low air/whir bed; the odd fan gives a small brass ting once per cycle at its slowest moment (audio clue)."""
import sys, os, math
import numpy as np, skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/fans"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
LET = "ABCDEFGH"
NC = 8
SX, SY = 110, 112
Y0 = 476
R = 48                          # blade tip radius
P = 4.0
REST, UPT, DOWNT = float(os.environ.get("REST", "1.0")), .7, 1.0
CRUISE = P - REST - UPT - DOWNT
ODD = (os.environ.get("OL", "D"), int(os.environ.get("ON", "7")))
rng = np.random.default_rng(int(os.environ.get("SEED", "43")))

def sm(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def shape(s):
    """normalised speed at time s into the cycle (0 = start of rest)"""
    if s < REST: return 0.0
    s -= REST
    if s < UPT: return sm(s / UPT)
    s -= UPT
    if s < CRUISE: return 1.0
    s -= CRUISE
    return 1 - sm(s / DOWNT)
# integrate the shape once -> angle table (turns), scale so one cycle = whole quarter turns
NS = 4000
ss_ = np.linspace(0, P, NS + 1)
sp = np.array([shape(s) for s in ss_])
cum = np.concatenate([[0], np.cumsum((sp[1:] + sp[:-1]) / 2 * (P / NS))])
AREA = cum[-1]
TURNS_CYCLE = round(1.7 * AREA * 4) / 4         # turns per cycle, multiple of 1/4 (4 blades)
WMAX = TURNS_CYCLE / AREA                       # turns/s at cruise
def turns_normal(t, ph):
    s = (t + ph * P) % P
    k = math.floor((t + ph * P) / P)
    return k * TURNS_CYCLE + np.interp(s, ss_, cum) * WMAX
def speed_normal(t, ph):
    return shape((t + ph * P) % P) * WMAX
# odd: w = WO * (0.75 + 0.25 cos) -> 12 s gives 0.75*WO*12 turns, quarter-turn multiple
WO = round(WMAX * .78 * .75 * LOOP * 4) / 4 / (.75 * LOOP)
def turns_odd(t, ph):
    return WO * (.75 * t + .25 * P / (2 * math.pi) * math.sin(2 * math.pi * (t / P + ph)))
def speed_odd(t, ph):
    return WO * (.75 + .25 * math.cos(2 * math.pi * (t / P + ph)))

FANS = []                       # (label, x, y, phase, row, a0, spin dir)
for i in range(NC):
    n = 9 if i % 2 == 0 else 8
    for j in range(n):
        x = 540 + (i - (NC - 1) / 2) * SX
        y = Y0 + j * SY + (0 if i % 2 == 0 else SY / 2)
        ph = (.06 * i + .09 * j + rng.uniform(0, .45)) % 1.0
        FANS.append(((LET[i], j + 1), x, y, ph, j, rng.uniform(0, .25), 1))
assert any(f[0] == ODD for f in FANS)

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_LAB = font(TF_SB, 21)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

S = 3
BS = 2 * R + 8
def blades_image(alpha_scale=1.0):
    """4 cream paddle blades pointing up/right/down/left, centred"""
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(BS * S, BS * S))
    with surf as c:
        c.scale(S, S); c.translate(BS / 2, BS / 2)
        p = skia.Path()
        p.moveTo(-6, -15); p.lineTo(6, -15); p.lineTo(14, -R + 12)
        p.quadTo(14, -R, 0, -R); p.quadTo(-14, -R, -14, -R + 12); p.close()
        for k in range(4):
            c.save(); c.rotate(90 * k)
            cols = [rgb((.99, .95, .86)), rgb((.93, .84, .68)), rgb((.72, .6, .44))] if k else \
                   [rgb((1, .78, .42)), rgb((.92, .58, .22)), rgb((.62, .36, .12))]   # one amber blade to track the turn
            c.drawPath(p, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
                [(-14, 0), (14, 0)], cols, [0, .45, 1])))
            c.drawLine(0, -18, 0, -R + 6, skia.Paint(AntiAlias=True, StrokeWidth=1.4, Color4f=c4((.6, .46, .3), .45)))
            c.restore()
    return surf.makeImageSnapshot()
BLADES = blades_image()
def shadow_image():
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(BS * S, BS * S))
    with surf as c:
        c.scale(S, S); c.translate(BS / 2, BS / 2)
        p = skia.Path()
        p.moveTo(-6, -15); p.lineTo(6, -15); p.lineTo(14, -R + 12)
        p.quadTo(14, -R, 0, -R); p.quadTo(-14, -R, -14, -R + 12); p.close()
        for k in range(4):
            c.save(); c.rotate(90 * k)
            c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
            c.restore()
    return surf.makeImageSnapshot()
SHADOW = shadow_image()

def mount(c, x, y):
    # recessed dark plate + thin brass ring around each fan
    c.drawCircle(x, y, R + 4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y - 10), R + 8,
                 [rgb((.16, .11, .07)), rgb((.09, .06, .04))])))
    c.drawCircle(x, y, R + 4, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                 Color4f=c4((.78, .58, .3), .55)))

def fan(c, lab, x, y, turns, speed):
    v = min(1.0, speed / WMAX)             # 0 = still, 1 = cruise
    deg = 360 * turns
    # swept disc (blur) grows with speed
    if v > .05:
        c.drawCircle(x, y, R - 1, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), R,
                     [c4((.95, .86, .7), .0).toColor(), rgb((.95, .86, .7), .10 * v), rgb((.95, .86, .7), .08 * v), rgb((.95, .86, .7), 0)],
                     [0, .35, .9, 1.0])))
    # shadow
    c.save(); c.translate(x + 3, y + 5); c.rotate(deg)
    c.drawImageRect(SHADOW, skia.Rect(-BS / 2, -BS / 2, BS / 2, BS / 2), SAMP, skia.Paint(Alphaf=.8 * (1 - .6 * v)))
    c.restore()
    # motion ghosts trailing behind
    trail = speed * 360 / FPS               # degrees per frame
    ng = 4
    for g in range(ng, 0, -1):
        if v < .05: break
        c.save(); c.translate(x, y); c.rotate(deg - trail * g / ng * .8)
        c.drawImageRect(BLADES, skia.Rect(-BS / 2, -BS / 2, BS / 2, BS / 2), SAMP, skia.Paint(Alphaf=.22 * v * (1 - g / (ng + 1))))
        c.restore()
    c.save(); c.translate(x, y); c.rotate(deg)
    c.drawImageRect(BLADES, skia.Rect(-BS / 2, -BS / 2, BS / 2, BS / 2), SAMP, skia.Paint(Alphaf=1 - .15 * v))
    c.restore()
    # brass hub with label (stationary text)
    c.drawCircle(x + 1, y + 2, 19, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
    c.drawCircle(x, y, 18.5, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - 5, y - 6), 26,
                 [rgb((1, .9, .62)), rgb((.88, .66, .34)), rgb((.55, .37, .15))], [0, .5, 1])))
    text(c, f"{lab[0]}{lab[1]}", x, y + 7.5, F_LAB, (.16, .1, .05), .95)

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH FAN", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "NEVER STOPS?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for lab, x, y, ph, j, a0, d in FANS: mount(c, x, y)
        for lab, x, y, ph, j, a0, d in FANS:
            if lab == ODD: tu, spd = turns_odd(t, ph), speed_odd(t, ph)
            else: tu, spd = turns_normal(t, ph), speed_normal(t, ph)
            fan(c, lab, x, y, a0 + tu, spd)
        yb = 1500
        text(c, "Comment its letter + number", W / 2, yb, F_CTA, CREAM, .95)
        s1 = "Like it if you found it "
        fe = font(TF_EMOJI, 30)
        w1, w2 = F_LIKE.measureText(s1), fe.measureText("👍")
        x0 = W / 2 - (w1 + w2) / 2
        text(c, s1, x0, yb + 54, F_LIKE, CREAM, .6, align="left")
        c.drawString("👍", x0 + w1, yb + 52, fe, skia.Paint(AntiAlias=True, Alphaf=.8))
        text(c, "@whatiffun", W / 2, 1636, F_MARK, CREAM, .42)
    return out

# ---------------- sound ----------------
def tock(f0, dur=.22, seed=0):
    t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * f0 * .7 * t) * np.exp(-t * 55) + .3 * np.sin(2 * np.pi * f0 * 1.6 * t) * np.exp(-t * 90)
    low = np.sin(2 * np.pi * 75 * t) * np.exp(-t * 35) * .5
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 1100) * .45
    return (body + low + np.diff(n, prepend=0) * .6) * np.minimum(1, t * 6000)
def ting(f0, dur=.6):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 7) + .35 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 14)) * np.minimum(1, t * 3000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, j, a0, d) in enumerate(FANS):
        if lab == ODD:
            for q in range(-1, 5):
                tt = (q + .5 - ph) * P          # slowest moment: cos = -1
                if 0 <= tt < LOOP: ev.append((tt, k, True))
        else:
            for q in range(-1, 5):
                tt = (q - ph) * P               # comes to rest at cycle start
                if 0 <= tt < LOOP: ev.append((tt, k, False))
    times = np.array([e[0] for e in ev])
    for tt, k, odd in ev:
        lab, x, y, ph, j, a0, d = FANS[k]
        dens = (np.abs(times - tt) < .05).sum()
        if odd:
            m.add(ting(note(9, 261.63)), tt, .26, x)
        else:
            m.add(tock(note(8 - j + 3, 196.0) * (1 + .004 * (x - 540) / 110), seed=k), tt, .5 / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 300) / 260) ** 2)
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    # whir swells with how many fans are spinning (periodic -> seamless)
    tt = np.arange(n) / SR
    act = np.zeros(n)
    for ts in np.linspace(0, LOOP, 97)[:-1]:
        pass
    grid = np.linspace(0, LOOP, 241)
    a = np.array([np.mean([speed_normal(g, f[3]) / WMAX for f in FANS if f[0] != ODD]) for g in grid])
    act = np.interp(tt, grid, a)
    m.L += bed * (.035 + .03 * act); m.R += np.roll(bed, 5000) * (.035 + .03 * act)
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("turns/cycle", TURNS_CYCLE, "wmax", WMAX, "wodd", WO)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/F_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_fans.mp4"))
