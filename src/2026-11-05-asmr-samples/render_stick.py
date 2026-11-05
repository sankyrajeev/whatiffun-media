import pickle, sys, math
import numpy as np, skia
from kit import *
from scipy.signal import butter, sosfilt

d = pickle.load(open("stick.pkl", "rb"))
ST, FALL, NN, EV, G = d["stuck"], d["falling"], d["n"], d["events"], d["geom"]
BR, TOP, SEED_Y, CX = G["BR"], G["TOP"], G["SEED_Y"], G["CX"]
NF = len(FALL)
HOLD, CARD, XF = 20, 66, 18
TOTAL = NF + HOLD + CARD + XF

ymin, ymax = TOP, SEED_Y
def hcol(y):
    u = min(1, max(0, (ymax - y) / (ymax - ymin)))
    return hsv(195 - 15 * u, .62 - .5 * u, .62 + .38 * u)
LEVELS = 24
SPR = [glass_ball(hcol(ymax - (ymax - ymin) * i / (LEVELS - 1)), BR) for i in range(LEVELS)]
def lvl(y): return int(min(LEVELS - 1, max(0, round((ymax - y) / (ymax - ymin) * (LEVELS - 1)))))
FALLS = glass_ball((1.0, .96, .9), BR * .8)
FLASH = glow((.85, .97, 1.0), BR * 1.6, .9)
BG = background(1100)
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .35))
stuck_frame = (ST[:, 2]).astype(int)
order = np.argsort(stuck_frame, kind="stable")
first = None

def frame(f):
    global first
    k = min(f, NF - 1)
    upto = int(np.searchsorted(stuck_frame[order], k, side="right"))
    idx = order[:upto]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BG, 0, 0)
        # brass pin
        c.drawRect(skia.Rect(CX - 3, SEED_Y, CX + 3, SEED_Y + 70), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.75, .58, .32, 1)))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(CX - 70, SEED_Y + 68, CX + 70, SEED_Y + 80), 6, 6),
                    skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.55, .42, .24, 1)))
        for i in idx:
            c.drawCircle(float(ST[i, 0]) + 1.2, float(ST[i, 1]) + 2.0, BR, SH)
        for i in idx:
            blit(c, SPR[lvl(ST[i, 1])], float(ST[i, 0]), float(ST[i, 1]))
        for i in idx[-200:]:
            age = k - stuck_frame[i]
            if age < 8:
                blit(c, FLASH, float(ST[i, 0]), float(ST[i, 1]), 1.0, skia.Paint(Alphaf=.8 * (1 - age / 8), BlendMode=skia.BlendMode.kPlus))
        for x, y in (FALL[k] if f < NF else []):
            if y < 1700: blit(c, FALLS, float(x), float(y))
        header(c, "Touch it", "and you stick.", count=int(NN[k]))
        watermark(c, 1620)
        if f >= NF + HOLD:
            a = ss((f - NF - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

def audio(path):
    m = Mix(TOTAL / FPS + .5)
    rng = np.random.default_rng(2)
    cache = {}
    def tink(step):
        if step not in cache:
            f0 = note(step, 220.0)
            t = np.arange(int(.9 * SR)) / SR
            s = (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 5) + .4 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 11)
                 + .15 * np.sin(2 * np.pi * f0 * 5.4 * t) * np.exp(-t * 25))
            n = rng.standard_normal(len(t)) * np.exp(-t * 1500) * .25
            cache[step] = (s + np.diff(n, prepend=0)) * np.minimum(1, t * 6000)
        return cache[step]
    byf = {}
    for e in EV: byf.setdefault(int(e[0] * FPS), []).append(e)
    for f, es in byf.items():
        rng.shuffle(es)
        for e in es[:9]:
            u = (ymax - e[2]) / (ymax - ymin)
            step = int(min(14, max(0, round(u * 14))))
            g = .3 / (1 + .08 * max(0, len(es) - 3))
            m.add(tink(step), e[0] + rng.uniform(0, .01), g, e[1])
    # soft rain air under the falling beads
    nfall = np.array([len(x) for x in FALL] + [0] * (TOTAL - NF), float)
    env = np.interp(np.arange(m.N) / SR, (np.arange(TOTAL) + .5) / FPS, np.clip(nfall / 120, 0, 1))
    air = sosfilt(butter(2, [2500, 8000], btype="bandpass", fs=SR, output="sos"), rng.standard_normal((2, m.N)), axis=1)
    m.L += air[0] * env * .03; m.R += air[1] * env * .03
    tc = (d["done"] or NF) / FPS + .2
    for i, nn in enumerate([10, 12, 14]):
        m.add(mallet(note(nn - 10, 523.25), 3.2, .4), tc + i * .09, .16, 540 + (i - 1) * 120)
    return m.save(path)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for f in [int(x) for x in sys.argv[2].split(",")]:
            if f > 0: frame(0)
            frame(f).makeImageSnapshot().save(f"C_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("C_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), "frames", TOTAL)
        print(audio("C.wav"))
        print("mux", mux("C_silent.mp4", "C.wav", "sample_C_stick.mp4"))
