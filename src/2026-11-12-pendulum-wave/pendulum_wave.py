"""FAMOUS DEMO: the pendulum wave. 24 pendulums on one brass rail; pendulum i swings (16 + i) times per
18 s, so their relative phase is i*t/T: one line -> a snake -> 2, 3, 4 interleaved snakes -> apparent chaos ->
all 24 back in one line at T. Seen from above the near end, in perspective. Bob colour = phase relative to the
longest one, so the row is a rainbow while they disagree and one colour when they line up."""
import sys, math, os
import numpy as np, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *

N, T, N0 = 24, 18.0, 16
T_START = 1.4                    # open mid-action (snake already formed)
ACT = T                          # T_START .. T_START+T is a perfect loop of the motion
TAIL = 2.6                       # motion continues under the end card
DUR = ACT + TAIL
TOTAL = int(round(DUR * FPS))
OUT = sys.argv[3] if len(sys.argv) > 3 else "/home/claude/pw"

# world (metres): x = swing axis, y = up, z = along the rail (0 near, far end positive)
RAIL_Y = 0.74
ZS = np.linspace(0.0, 0.92, N)                       # i = 0 (longest, slowest) nearest
LENS = np.linspace(0.62, 0.34, N)                    # display lengths (stylised, shorter = faster)
AX = 0.22                                           # equal x amplitude, like the real demo
CAM = np.array([0.0, 2.4, -1.3]); PITCH = math.radians(55); FOC = 2200; SX0, SY0 = 540, 1325; XS = 1.4

def proj(x, y, z):
    v = np.array([x, y, z]) - CAM
    zc = -v[1] * math.sin(PITCH) + v[2] * math.cos(PITCH)
    yc = v[1] * math.cos(PITCH) + v[2] * math.sin(PITCH)
    return SX0 + XS * FOC * v[0] / zc, SY0 - FOC * yc / zc, FOC / zc

def phase(i, t): return 2 * math.pi * (N0 + i) * t / T
def rel(i, t): return ((i * t / T) % 1.0)            # phase relative to pendulum 0, in turns
def bob_pos(i, t):
    x = AX * math.cos(phase(i, t)); L = LENS[i]
    return x, RAIL_Y - math.sqrt(L * L - x * x), ZS[i]

def in_step(t, tol=0.045):
    d = np.array([rel(i, t) for i in range(N)])
    best = 1
    for a in d:
        dd = np.abs(((d - a) + .5) % 1 - .5)
        best = max(best, int((dd <= tol).sum()))
    return best

HUES = 72
def hue_of(i, t): return (38 + 360 * rel(i, t)) % 360        # gold when in line
SPR = [glass_ball(hsv(h * 360 / HUES, .62, 1.0), 40) for h in range(HUES)]
GLOW = [glow(hsv(h * 360 / HUES, .7, 1.0), 26, .55) for h in range(HUES)]
BRASS = glass_ball((.93, .72, .42), 10)
BG = background(1000)
F_KICK2 = font(TF_SEMI, 30); F_SMALL = font(TF_SERIF_I, 38)

def floor_quad(c):
    pts = [proj(x, 0, z) for x, z in ((-.42, -.02), (.42, -.02), (.42, 1.05), (-.42, 1.05))]
    path = skia.Path(); path.moveTo(pts[0][0], pts[0][1])
    for p in pts[1:]: path.lineTo(p[0], p[1])
    path.close()
    sh = skia.GradientShader.MakeLinear([(0, pts[0][1]), (0, pts[2][1])],
         [skia.Color4f(.16, .11, .075, .95).toColor(), skia.Color4f(.07, .05, .04, 0.0).toColor()])
    c.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh))

def draw_frame_rail(c):
    p = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap)
    for zz in (ZS[-1] + .03, ZS[0] - .03):       # an A-frame at each end of the rail
        top = proj(0, RAIL_Y + .01, zz)
        for sx in (-.30, .30):
            a = proj(sx, 0, zz)
            sh = skia.GradientShader.MakeLinear([(top[0], top[1]), (a[0], a[1])],
                 [skia.Color4f(.80, .60, .34, 1).toColor(), skia.Color4f(.40, .28, .16, 1).toColor()])
            p.setShader(sh); p.setStrokeWidth(max(3, 8 * a[2] / 1000))
            c.drawLine(a[0], a[1], top[0], top[1], p)
    p = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap)
    a = proj(0, RAIL_Y, ZS[0] - .03); b = proj(0, RAIL_Y, ZS[-1] + .03)
    sh = skia.GradientShader.MakeLinear([(a[0], a[1]), (b[0], b[1])],
         [skia.Color4f(.95, .76, .46, 1).toColor(), skia.Color4f(.55, .40, .22, 1).toColor()])
    p.setShader(sh); p.setStrokeWidth(10)
    c.drawLine(a[0], a[1], b[0], b[1], p)

def scene(c, t):
    floor_quad(c)
    # bob shadows on the floor
    shp = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7))
    for i in range(N):
        x, y, z = bob_pos(i, t); s = proj(x, 0, z); r = 0.022 * s[2]
        c.drawOval(skia.Rect(s[0] - r * 1.25, s[1] - r * .45, s[0] + r * 1.25, s[1] + r * .45), shp)
    draw_frame_rail(c)
    st = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap)
    for i in reversed(range(N)):                      # far to near
        x, y, z = bob_pos(i, t)
        pv = proj(0, RAIL_Y, z); b = proj(x, y, z)
        hi = int(round(hue_of(i, t) / 360 * HUES)) % HUES
        st.setStrokeWidth(max(1.0, 1.6 * b[2] / 1000)); st.setColor4f(skia.Color4f(.92, .82, .66, .55))
        c.drawLine(pv[0], pv[1], b[0], b[1], st)
        blit(c, BRASS, pv[0], pv[1], .55 * pv[2] / 1000)
        rr = 0.021 * b[2]
        blit(c, GLOW[hi], b[0], b[1], rr / 26 * .9, skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=.45))
        blit(c, SPR[hi], b[0], b[1], rr / 40)

def frame(f):
    v = f / FPS; t = T_START + v
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        scene(c, t)
        text(c, "PENDULUM WAVE", W / 2, 196, F_KICK2, AMBER, .9, spacing=7)
        text(c, "Each one swings", W / 2, 272, F_RULE, CREAM, .97)
        text(c, "a little faster.", W / 2, 338, F_RULE_I, CREAM, .9)
        n = in_step(t)
        pulse = max(0.0, 1 - abs(v - (T - T_START)) / .35) if n == N else 0.0
        col = tuple(CREAM[k] * (1 - pulse) + AMBER[k] * pulse for k in range(3)) if n == N else CREAM
        header_count(c, n, col, pulse)
        watermark(c, 1640)
        # end card + crossfade loop
        ea = ss((v - (ACT + .25)) / .6)
        if ea > 0:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(0, 0, 0, .35 * ea)))
            end_card(c, ea)
    xf = ss((v - (DUR - .6)) / .6)
    if xf > 0:
        first = FIRST if FIRST is not None else None
        with out as c:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=xf))
    return out

def header_count(c, n, col, pulse):
    c.save(); cy = 430
    c.translate(W / 2, cy); c.scale(1 + .12 * pulse, 1 + .12 * pulse); c.translate(-W / 2, -cy)
    text(c, f"{n}", W / 2, 458, F_CNT, col)
    c.restore()
    text(c, f"of {N} in step", W / 2, 506, F_SMALL, CREAM, .55)

FIRST = None

def audio(path):
    m = Mix(DUR)
    rng = np.random.default_rng(7)
    ticks = [glass_click(note(i // 2 + 2, 220) * 2, 95, .08, .2) for i in range(N)]
    tock = mallet(110, 1.0, .5)
    dt = 1 / 2000
    ev = []
    for i in range(N):
        prev = None
        for k in range(int(DUR / dt) + 1):
            t = T_START + k * dt
            s = math.sin(phase(i, t))                  # x = AX cos -> turning point when sin crosses 0
            if prev is not None and (prev > 0) != (s > 0):
                ev.append((k * dt, i, math.cos(phase(i, t))))
            prev = s
    ev.sort()
    times = np.array([e[0] for e in ev])
    for (tv, i, side) in ev:
        dens = ((times > tv - .02) & (times < tv + .02)).sum()
        x, y, z = bob_pos(i, T_START + tv); px = proj(x, y, z)[0]
        g = .16 / math.sqrt(dens) * (1.0 if tv < ACT + .4 else max(.0, 1 - (tv - ACT - .4) / 1.4))
        m.add(ticks[i], tv + rng.uniform(0, .003), g, 540 + (px - 540) * 1.6)
        if i == 0 and side > 0 and tv < ACT + .4:
            m.add(tock, tv, .10, 540)
    # unison moment(s): when all 24 are in step
    ts = T - T_START
    for k, f0 in enumerate([note(5, 220), note(7, 220), note(9, 220), note(10, 220)]):
        m.add(mallet(f0, 2.6, .8), ts + .01 * k, .09, 540 + (k - 1.5) * 120)
    m.add(thud(55, .8), ts, .25, 540)
    # resolving chord under the end card
    te = ACT + .3
    for k, f0 in enumerate([note(0, 130.8), note(2, 130.8), note(4, 130.8), note(5, 130.8)]):
        m.add(mallet(f0, 3.0, .45), te + .06 * k, .11, 540 + (k - 1.5) * 140)
    return m.save(path, fade_in=.0, fade_out=.5)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"{OUT}/P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "counts":
        print([in_step(T_START + s) for s in np.arange(0, ACT, .5)])
    elif sys.argv[1] == "audio":
        print(audio(f"{OUT}/pw.wav"))
    else:
        FIRST = frame(0).makeImageSnapshot()
        w = Writer(f"{OUT}/pw_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close())
        print(audio(f"{OUT}/pw.wav"))
        print("mux", mux(f"{OUT}/pw_silent.mp4", f"{OUT}/pw.wav", f"{OUT}/pendulum_wave.mp4"))
