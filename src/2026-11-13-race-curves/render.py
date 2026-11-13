"""No. 27 RACE — three frictionless sleds, same start, same finish: A straight ramp, B steep drop, C cycloid.
python3 render.py preview <outdir> f1,f2,...   |   python3 render.py full <outdir>"""
import sys, os, math
import numpy as np, skia
from kit import *
import sim

OUTD = sys.argv[2] if len(sys.argv) > 2 else "."
KINDS = ["straight", "steep", "cycloid"]
NAMES = ["A", "B", "C"]
DESC = ["straight ramp", "steep drop", "deep curve"]
HUES = [188, 8, 268]
COLS = [hsv(h, .55, 1) for h in HUES]
LANES = [sim.lane(k) for k in KINDS]
T0 = 1.0                                   # release
FIN = [T0 + d["T"] for d in LANES]
ORDER = np.argsort(FIN); WIN = int(ORDER[0]); SECOND = int(ORDER[1])
MARGIN = FIN[SECOND] - FIN[WIN]
T_LAST = max(FIN)
CARD = T_LAST + 1.5
XF = 18
TOTAL = int((CARD + 2.6) * FPS) + XF

X0 = 200.0
ROW_TOP = [440, 785, 1130]
SY = 70.0                                  # start y inside a row
def to_px(i, x, y): return X0 + x, ROW_TOP[i] + SY + y

def state(i, t):
    """position along the lane at time t (s after start of the video)"""
    d = LANES[i]; tt = min(max(t - T0, 0), d["T"])
    s = np.interp(tt, d["t"], d["s"])
    x = np.interp(s, d["s"], d["x"]); y = np.interp(s, d["s"], d["y"])
    s2 = min(s + 2.0, d["s"][-1]); s1 = s2 - 4.0
    x1, y1 = np.interp(s1, d["s"], d["x"]), np.interp(s1, d["s"], d["y"])
    x2, y2 = np.interp(s2, d["s"], d["x"]), np.interp(s2, d["s"], d["y"])
    v = math.sqrt(2 * sim.G * max(y, 0))
    return x, y, math.atan2(y2 - y1, x2 - x1), v, tt

def leader(t):
    if t <= T0 + .25: return -1
    xs = [state(i, t)[0] for i in range(3)]
    done = [t >= FIN[i] for i in range(3)]
    if any(done): return WIN
    return int(np.argmax(xs))

BG = background(980)
ADD = skia.BlendMode.kPlus
def pa(a): return skia.Paint(Alphaf=max(0., min(1., a)), BlendMode=ADD)

# ---------- static board (tracks, sleepers, flags) ----------
def track_path(i, step=8):
    d = LANES[i]; p = skia.Path()
    idx = np.linspace(0, len(d["x"]) - 1, 400).astype(int)
    for k, j in enumerate(idx):
        X, Y = to_px(i, d["x"][j], d["y"][j])
        (p.moveTo if k == 0 else p.lineTo)(X, Y)
    return p
PATHS = [track_path(i) for i in range(3)]
SLEEP_X = np.linspace(0, sim.L, 21)[1:-1]          # 19 sleepers, every 37 px of x
def sleepers(i):
    d = LANES[i]; out = []
    for sx in SLEEP_X:
        # first crossing of that x (all three tracks are monotone in x)
        y = np.interp(sx, d["x"], d["y"]); j = np.searchsorted(d["x"], sx)
        j = min(max(j, 1), len(d["x"]) - 2)
        ang = math.atan2(d["y"][j + 1] - d["y"][j - 1], d["x"][j + 1] - d["x"][j - 1])
        out.append((sx, y, ang))
    return out
SLEEPERS = [sleepers(i) for i in range(3)]

def draw_board(c):
    for i in range(3):
        col = COLS[i]; top = ROW_TOP[i]
        # faint lane band
        band = skia.RRect.MakeRectXY(skia.Rect(108, top - 8, 972, top + 337), 26, 26)
        c.drawRRect(band, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*col, .028)))
        c.drawRRect(band, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                                     Color4f=skia.Color4f(*col, .10)))
        # start + finish posts
        sx, sy = to_px(i, 0, 0); fx, fy = to_px(i, sim.L, sim.HD)
        for (px, py) in ((sx, sy), (fx, fy)):
            c.drawLine(px, py - 46, px, py + 22, skia.Paint(AntiAlias=True, StrokeWidth=3, Color4f=skia.Color4f(.75, .62, .42, .55)))
        # checkered finish flag
        for r in range(3):
            for q in range(4):
                if (r + q) % 2 == 0:
                    c.drawRect(skia.Rect.MakeXYWH(fx + 2 + q * 7, fy - 46 + r * 7, 7, 7),
                               skia.Paint(Color4f=skia.Color4f(*CREAM, .75)))
        # sleepers
        for (x, y, ang) in SLEEPERS[i]:
            X, Y = to_px(i, x, y); nx, ny = -math.sin(ang), math.cos(ang)
            c.drawLine(X - nx * 3, Y - ny * 3, X + nx * 13, Y + ny * 13,
                       skia.Paint(AntiAlias=True, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap,
                                  Color4f=skia.Color4f(.42, .30, .20, .9)))
        # rail: shadow, body, highlight
        c.drawPath(PATHS[i], skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9,
                   Color4f=skia.Color4f(0, 0, 0, .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        c.drawPath(PATHS[i], skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                   Color4f=skia.Color4f(.80, .64, .40, 1)))
        c.drawPath(PATHS[i], skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6,
                   Color4f=skia.Color4f(1, .93, .78, .85)))
        # lane letter + description
        text(c, NAMES[i], 136, top + 64, font(TF_SERIF, 64), col, .95)
        text(c, DESC[i], 128, top + 302, font(TF_SERIF_I, 32), CREAM, .5, align="left")
s0 = skia.Surface.MakeRaster(INFO)
with s0 as c:
    c.drawImage(BG, 0, 0); draw_board(c)
BOARD = s0.makeImageSnapshot()

# ---------- sleds ----------
def sled_sprite(col):
    w, h = 50, 26; sz = 64
    def fn(c):
        cx, cy = sz / 2, sz / 2
        r = skia.Rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        light = tuple(min(1, x * .45 + .55) for x in col); dark = tuple(x * .4 for x in col)
        sh = skia.GradientShader.MakeLinear([(cx, cy - h / 2), (cx, cy + h / 2)],
             [skia.Color4f(*light, 1).toColor(), skia.Color4f(*col, 1).toColor(), skia.Color4f(*dark, 1).toColor()], [0, .45, 1])
        c.drawRRect(skia.RRect.MakeRectXY(r, 12, 12), skia.Paint(AntiAlias=True, Shader=sh))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - w / 2 + 7, cy - h / 2 + 4, cx + w / 2 - 9, cy - h / 2 + 9), 3, 3),
                    skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .55)))
        c.drawCircle(cx + w / 2 - 12, cy - 1, 3.2, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .9)))
        # brass runner
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - w / 2 + 4, cy + h / 2 - 3, cx + w / 2 - 4, cy + h / 2 + 2), 2, 2),
                    skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.85, .68, .42, 1)))
    return sprite(fn, sz)
SLEDS = [sled_sprite(cl) for cl in COLS]
GLOWS = [glow(cl, 16, .7) for cl in COLS]
GL_W = glow((1, .85, .55), 40, .5)

F_LANE_T = font(TF_MONO, 30)
F_STAT = font(TF_SERIF_I, 44)
F_TAG = font(TF_SEMI, 20)

def head(c, t):
    text(c, "RACE", W / 2, 196, F_KICK, AMBER, .9, spacing=7)
    text(c, "Same start, same finish.", W / 2, 272, F_RULE, CREAM, .97)
    text(c, "First to the flag wins.", W / 2, 336, F_RULE_I, CREAM, .9)
    if t >= FIN[WIN]:
        a = ss((t - FIN[WIN]) / .35)
        text(c, f"{NAMES[WIN]} wins by {MARGIN:.2f} s", W / 2, 408, F_STAT, COLS[WIN], a)
    elif t < T0:
        text(c, "ready", W / 2, 408, F_STAT, CREAM, .45)

def frame(f, trails):
    t = f / FPS
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawImage(BOARD, 0, 0)
        lead = leader(t)
        for i in range(3):
            x, y, ang, v, tt = state(i, t)
            X, Y = to_px(i, x, y)
            nx, ny = math.sin(ang), -math.cos(ang)       # normal pointing "up" off the rail
            PX, PY = X + nx * 15, Y + ny * 15
            trails[i].append((PX, PY, v))
            tr = trails[i][-14:]
            for k in range(1, len(tr)):
                a = k / len(tr) * min(1, tr[k][2] / 260) * .55
                c.drawLine(tr[k - 1][0], tr[k - 1][1], tr[k][0], tr[k][1],
                           skia.Paint(AntiAlias=True, StrokeWidth=3 + 9 * k / len(tr), StrokeCap=skia.Paint.kRound_Cap,
                                      Color4f=skia.Color4f(*COLS[i], a), BlendMode=ADD))
            done = t >= FIN[i]
            if t < T0:   # gate pulse before release
                blit(c, GLOWS[i], PX, PY, 1.0, pa(.25 + .2 * math.sin(t * 9 + i)))
            if done:
                blit(c, GLOWS[i], PX, PY, 1.3, pa(.8 * math.exp(-(t - FIN[i]) * 1.4) + .15))
            c.save(); c.translate(PX, PY); c.rotate(math.degrees(ang)); c.translate(-PX, -PY)
            blit(c, SLEDS[i], PX, PY)
            c.restore()
            # live time, top-right of the lane
            top = ROW_TOP[i]
            tshow = min(max(t - T0, 0), LANES[i]["T"])
            text(c, f"{tshow:5.2f} s", 958, top + 46, F_LANE_T, COLS[i] if done else CREAM,
                 .95 if done else .7, align="right")
            if done:
                place = int(np.where(ORDER == i)[0][0]) + 1
                text(c, ["1st", "2nd", "3rd"][place - 1], 958, top + 80, F_TAG, COLS[i], .9, align="right", spacing=2)
            if lead == i and not any(t >= FIN[k] for k in range(3)):
                text(c, "LEADING", 958, top + 80, F_TAG, AMBER, .85, align="right", spacing=3)
        if t >= FIN[WIN]:
            X, Y = to_px(WIN, sim.L, sim.HD)
            blit(c, GL_W, X, Y - 14, 1.6, pa(.9 * math.exp(-(t - FIN[WIN]) * 1.6)))
        head(c, t)
        watermark(c)
        end_card(c, ss((t - CARD) / .5))
    return s

def run(fs=None, writer=None):
    trails = [[], [], []]; first = None
    for f in range(TOTAL):
        s = frame(f, trails)
        if f == 0: first = s.makeImageSnapshot()
        if f >= TOTAL - XF:
            with s as c: c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
        if fs is not None and f in fs: s.makeImageSnapshot().save(f"{OUTD}/P_{f:04d}.png", skia.kPNG)
        if writer: writer.write(s)
        if fs is not None and f >= max(fs): break

# ---------- audio ----------
PAN = [140, 540, 940]
def audio(path):
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(27)
    m = Mix(TOTAL / FPS)
    # pre-roll: three soft gate ticks, then the release clack
    for k, tk in enumerate((.1, .4, .7)):
        m.add(glass_click(1400, 220, .05, .4), tk, .6, 540)
    for i in range(3):
        m.add(glass_click(note(5 + i * 2, 196), 120, .1, .4), T0, .5, PAN[i])
    m.add(thud(70, .4), T0, .5, 540)
    # tension bed: a soft clock tick that speeds up toward the photo finish (2 -> 5 Hz), then relaxes while A crawls home
    tk = glass_click(950, 260, .05, .5); t = T0
    while t < T_LAST:
        u = min(1, (t - T0) / (FIN[WIN] - T0))
        if t < FIN[WIN]: m.add(tk, t, .2 + .14 * u, 540); t += 1 / (2 + 3 * u ** 1.4)
        else: m.add(tk, t, .14, 540); t += .5
    sw = sosfilt(butter(2, [400, 3000], btype="band", fs=SR, output="sos"), rng.standard_normal(int(2.5 * SR)))
    m.add(sw * np.linspace(0, 1, len(sw)) ** 2 * .08, FIN[WIN] - 2.5, 1, 540)
    for i in range(3):
        d = LANES[i]
        # sleeper clicks: a soft wooden tick each time the sled passes a sleeper (pitch per lane, pentatonic)
        for k, sx in enumerate(SLEEP_X):
            tk = T0 + np.interp(sx, d["x"], d["t"])
            m.add(glass_click(note(7 + 2 * i + (k % 3 == 0), 196), 200, .06, .45), tk, .30, PAN[i])
        # rolling hiss tied to speed (band-passed noise, level + brightness follow v)
        n = int((FIN[i] - T0) * SR); tt = np.arange(n) / SR
        v = np.sqrt(2 * sim.G * np.maximum(np.interp(np.interp(tt, d["t"], d["s"]), d["s"], d["y"]), 0))
        vn = v / 320.0
        noise = sosfilt(butter(2, [300 + 200 * i, 1800 + 300 * i], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
        hum = np.sin(2 * np.pi * np.cumsum(80 + 90 * vn + 25 * i) / SR)
        sig = (noise * .5 + hum * .5) * (.25 + vn) ** 1.3 * np.minimum(1, tt * 8)
        sig[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))
        m.add(sig * .16, T0, 1, PAN[i])
        # finish: struck note per lane
        place = int(np.where(ORDER == i)[0][0])
        m.add(mallet(note([9, 7, 4][place], 261.63), 1.6, .8), FIN[i], .28 if place == 0 else .2, PAN[i])
    # winner chord + low thump
    m.add(thud(58, .8), FIN[WIN], .4, PAN[WIN])
    for j, n_ in enumerate((0, 4, 7, 9)):
        m.add(mallet(note(n_, 261.63), 2.4, .5), FIN[WIN] + .05 + j * .07, .15, 380 + j * 100)
    # a gentle sleeper-tick bed while only A is left, so it never goes dead
    for j, n_ in enumerate((0, 4, 7)):
        m.add(mallet(note(n_, 196), 2.4, .4), CARD + .1 + j * .06, .25, 450 + j * 90)
    return m.save(path, fade_in=.0, fade_out=.3)

if __name__ == "__main__":
    print("finish", [round(x - T0, 3) for x in FIN], "win", NAMES[WIN], "margin", round(MARGIN, 3), "total s", TOTAL / FPS)
    if sys.argv[1] == "preview":
        run([int(x) for x in sys.argv[3].split(",")])
    elif sys.argv[1] == "audio":
        print("rms", audio(f"{OUTD}/a.wav"))
    else:
        w = Writer(f"{OUTD}/silent.mp4"); run(writer=w); print("video", w.close())
        print("rms", audio(f"{OUTD}/a.wav"))
        print("mux", mux(f"{OUTD}/silent.mp4", f"{OUTD}/a.wav", f"{OUTD}/out.mp4"))
