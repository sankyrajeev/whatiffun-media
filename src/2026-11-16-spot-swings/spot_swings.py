"""SPOT IT v3 (18:00, 2026-11-16): 51 swings in a diamond, one goes all the way round.
Rule type: OVER THE TOP (it loops instead of swinging back). Arrangement: a DIAMOND of brass beams, rows 6/7/8/9/8/7/6,
each swing with its own label plate on the beam. Real rigid-rod pendulum physics (theta'' = -w0^2 sin theta): every
swing rises to 118 deg (above the beam) and turns back, 5 swings per 12 s loop, in a RIPPLE spreading out from the
centre of the diamond. The odd swing (F5) has a bit more energy, so it never turns back: it goes over the top, one
full revolution per 2.4 s (same rhythm as the rest), slowing as it crests like a real swing would.
Sound: a soft wooden creak-tick as each swing turns back at its right-hand peak (pentatonic by row, panned by x);
the odd swing ticks with a small brass ting each time it passes the top (audio clue)."""
import sys, os, math
import numpy as np, skia
from scipy.integrate import solve_ivp
from scipy.special import ellipk
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-05-asmr-samples"))
from kit import *

OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/swings"
LOOP = 12.0
TOTAL = int(LOOP * FPS)
WIDTHS = [7, 8, 9, 9, 8, 7]
NR = len(WIDTHS)
LET = "ABCDEFGHI"
SX, SY = 84, 180
Y0 = 446                               # first beam
ROD = 84
AMP = math.radians(float(os.environ.get("AMP", "118")))
PER = 2.4                              # swing period (5 per loop)
ODD = (os.environ.get("OL", "F"), int(os.environ.get("ON", "5")))
rng = np.random.default_rng(int(os.environ.get("SEED", "39")))

# --- physics: w0 such that a rigid pendulum of amplitude AMP has period PER
W0 = 4 * ellipk(math.sin(AMP / 2) ** 2) / PER
def traj(th0, om0, T, closed):
    ts = np.linspace(0, T, 2001)
    s = solve_ivp(lambda t, y: [y[1], -W0 * W0 * math.sin(y[0])], (0, T), [th0, om0], t_eval=ts, rtol=1e-10, atol=1e-10)
    return ts, s.y[0]
# swinger: released from rest at +AMP
TS, TH_SW = traj(AMP, 0.0, PER, True)
# rotator: speed at the bottom tuned so one revolution takes PER
def rev_time(om):
    s = solve_ivp(lambda t, y: [y[1], -W0 * W0 * math.sin(y[0])], (0, 20), [0, om],
                  events=lambda t, y: y[0] - 2 * math.pi, rtol=1e-10, atol=1e-10)
    return s.t_events[0][0]
lo, hi = 2 * W0 * 1.0001, 2 * W0 * 3
for _ in range(60):
    mid = (lo + hi) / 2
    if rev_time(mid) > PER: lo = mid
    else: hi = mid
OM_ROT = (lo + hi) / 2
TR, TH_ROT = traj(0.0, OM_ROT, PER, False)

def theta_sw(u):   # u = phase in cycles; 0 = at +AMP (right peak)
    return float(np.interp((u % 1.0) * PER, TS, TH_SW))
def theta_rot(u):  # 0 = bottom, increases through 2pi each cycle
    return float(np.interp((u % 1.0) * PER, TR, TH_ROT)) + 2 * math.pi * math.floor(u)

SW = []                                # (label, px, py, phase, odd)
CX, CY = 540, Y0 + (NR - 1) / 2 * SY
for r, n in enumerate(WIDTHS):
    for i in range(n):
        x = 540 + (i - (n - 1) / 2) * SX
        y = Y0 + r * SY
        lab = (LET[i], r + 1)
        # a chevron wave rolling down the diamond (rows nearly in step so neighbours never cross)
        ph = -float(os.environ.get("GRAD", ".11")) * r - .025 * abs(i - (n - 1) / 2) + rng.normal(0, .012)
        SW.append((lab, x, y, ph, lab == ODD))

def rgb(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a).toColor()
def c4(c, a=1.0): return skia.Color4f(*[min(1, max(0, v)) for v in c], a)
BG = background(1000)
TF_BOLD = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
TF_SB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
F_Q = font(TF_BOLD, 84)
F_PLQ = font(TF_BOLD, 24)
F_CTA = font(TF_SB, 42)
F_LIKE = font(TF_SERIF_I, 36)

SEAT_W, SEAT_H = 60, 20
def angle(sw, t):
    lab, x, y, ph, odd = sw
    u = t / PER + ph
    return -theta_rot(u) if odd else theta_sw(u)   # crests (u=.5) exactly as its row crests on the left

def draw_beam(c, r):
    n = WIDTHS[r]
    y = Y0 + r * SY
    xl = 540 - (n - 1) / 2 * SX - SX / 2 + 6
    xr = 540 + (n - 1) / 2 * SX + SX / 2 - 6
    c.drawRoundRect(skia.Rect(xl, y - 7, xr, y + 7), 7, 7, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .5),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
    c.drawRoundRect(skia.Rect(xl, y - 6, xr, y + 6), 6, 6, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, y - 6), (0, y + 6)], [rgb((.98, .86, .6)), rgb((.78, .58, .3)), rgb((.45, .3, .13))], [0, .45, 1])))
    for end in (xl, xr):    # posts
        c.drawRoundRect(skia.Rect(end - 4, y - 4, end + 4, y + 52), 3, 3, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [(end - 4, 0), (end + 4, 0)], [rgb((.7, .52, .28)), rgb((.4, .27, .12))])))

def draw_plate(c, lab, x, y):
    R = 24
    c.drawCircle(x, y + 2, R + 1, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    c.drawCircle(x, y, R, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - 5, y - 6), R * 1.6,
                 [rgb((.99, .93, .78)), rgb((.85, .7, .45)), rgb((.55, .38, .17))], [0, .55, 1])))
    c.drawCircle(x, y, R - 2.5, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Color4f=c4((.45, .3, .12), .6)))
    text(c, f"{lab[0]}{lab[1]}", x, y + 8.5, F_PLQ, (.2, .12, .05), .95)

def draw_swing(c, sw, th):
    lab, x, y, ph, odd = sw
    sx, sy = x + ROD * math.sin(th), y + ROD * math.cos(th)
    # rod (two chains seen side-on read as one brass rod)
    nx, ny = math.cos(th) * 0, 0
    c.drawLine(x, y, sx, sy, skia.Paint(AntiAlias=True, StrokeWidth=7, StrokeCap=skia.Paint.kRound_Cap,
               Color4f=c4((0, 0, 0), .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2)))
    c.drawLine(x, y, sx, sy, skia.Paint(AntiAlias=True, StrokeWidth=5.6, StrokeCap=skia.Paint.kRound_Cap,
               Shader=skia.GradientShader.MakeLinear([(x, y), (sx, sy)], [rgb((.98, .86, .6)), rgb((.72, .52, .26))])))
    # seat: a glossy amber plank perpendicular to the rod
    c.save(); c.translate(sx, sy); c.rotate(-math.degrees(th))
    c.drawRoundRect(skia.Rect(-SEAT_W / 2, 1, SEAT_W / 2, 1 + SEAT_H), 4, 4, skia.Paint(AntiAlias=True, Color4f=c4((0, 0, 0), .45),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    c.drawRoundRect(skia.Rect(-SEAT_W / 2, -2, SEAT_W / 2, -2 + SEAT_H), 4, 4, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, -2), (0, SEAT_H - 2)], [rgb((1, .82, .48)), rgb((.92, .58, .22)), rgb((.6, .32, .1))], [0, .4, 1])))
    c.drawRoundRect(skia.Rect(-SEAT_W / 2 + 4, -1, SEAT_W / 2 - 4, 1.5), 1, 1, skia.Paint(AntiAlias=True, Color4f=c4((1, .95, .8), .55)))
    c.restore()

def frame(f):
    t = f / FPS
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        text(c, "WHICH SWING", W / 2, 262, F_Q, CREAM, 1.0, spacing=1)
        text(c, "LOOPS THE LOOP?", W / 2, 356, F_Q, AMBER, 1.0, spacing=1)
        for r in range(NR): draw_beam(c, r)
        for sw in SW:
            for k, a in ((3, .07), (2, .12), (1, .2)):
                th = angle(sw, t - k / FPS * 1.5)
                gx, gy = sw[1] + ROD * math.sin(th), sw[2] + ROD * math.cos(th)
                c.drawCircle(gx, gy + 6, 16, skia.Paint(AntiAlias=True, Color4f=c4((.95, .6, .2), a),
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
        for sw in SW: draw_swing(c, sw, angle(sw, t))
        for sw in SW: draw_plate(c, sw[0], sw[1], sw[2])
        yb = 1528
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
def creak(f0, dur=.14, seed=0):
    t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 40) + .3 * np.sin(2 * np.pi * f0 * 2.4 * t) * np.exp(-t * 70)
    n = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 700) * .4
    return (body + np.diff(n, prepend=0) * .6) * np.minimum(1, t * 5000)
def ting(f0, dur=.5):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 8) + .35 * np.sin(2 * np.pi * f0 * 2.76 * t + 1) * np.exp(-t * 14)
    return s * np.minimum(1, t * 6000)

def audio(path):
    m = Mix(LOOP + 1.0)
    ev = []
    for k, (lab, x, y, ph, odd) in enumerate(SW):
        # right peak at u integer (swinger); top at u = k + .5 (rotator)
        off = .5 if odd else 0.0
        for j in range(-2, 8):
            tt = (j + off - ph) * PER
            if 0 <= tt < LOOP: ev.append((tt, k))
    times = np.array([e[0] for e in ev])
    for tt, k in ev:
        lab, x, y, ph, odd = SW[k]
        r = lab[1] - 1
        dens = (np.abs(times - tt) < .05).sum()
        if odd:
            m.add(creak(note(NR - 1 - r + 3, 196.0), seed=k), tt, .45 / math.sqrt(dens), x)
            m.add(ting(note(r + 11, 261.63)), tt + .01, .2, x)
        else:
            m.add(creak(note(NR - 1 - r + 3, 196.0) * (1 + .004 * (x - 540) / 94), seed=k), tt, .5 / math.sqrt(dens), x)
    n = int(LOOP * SR)
    m.L[:m.N - n] += m.L[n:]; m.R[:m.N - n] += m.R[n:]
    m.L, m.R, m.N = m.L[:n], m.R[:n], n
    rg = np.random.default_rng(2)
    spec = np.fft.rfft(rg.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR)
    spec *= np.exp(-((fr - 300) / 260) ** 2)       # soft air bed
    bed = np.fft.irfft(spec, n); bed /= np.abs(bed).max()
    m.L += bed * .05; m.R += np.roll(bed, 5000) * .05
    return m.save(path, fade_in=.0, fade_out=.01)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/S_{f:04d}.png", skia.kPNG)
    else:
        w = Writer(f"{OUT}/silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/spot.wav"))
        print("mux", mux(f"{OUT}/silent.mp4", f"{OUT}/spot.wav", f"{OUT}/spot_swings.mp4"))
