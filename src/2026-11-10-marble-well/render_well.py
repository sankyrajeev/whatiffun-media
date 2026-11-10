"""No. 15 render — 'Everything rolls / toward the middle.'
usage: python render_well.py preview 0,240,360   |   python render_well.py audio   |   python render_well.py full"""
import pickle, sys, math, os
import numpy as np, skia
from kit import *

E = lambda k, d: float(os.environ.get(k, d))
d = pickle.load(open("well.pkl", "rb"))
POS, R, BIRTH, EV, RB = d["POS"], d["R"], d["birth"], d["events"], d["RB"]
KT, KN = d["KT"], d["KN"]
NM = len(R)
CX, CY = 540.0, E("CY", 1010)
NS = POS.shape[0]
# settle time: when nothing moves any more
SPD = np.zeros(NS)
for f in range(1, NS):
    v = np.linalg.norm(POS[f] - POS[f - 1], axis=1) * FPS
    SPD[f] = np.nanmax(v) if np.any(~np.isnan(v)) else 0
T_SET = next(f for f in range(int(KT[-1] * FPS), NS) if SPD[f] < 6) / FPS
GL0, GL1 = T_SET + .25, T_SET + 1.9      # glint ripples out across the finished mosaic
NF = int((GL1 + .5) * FPS)
HOLD, CARD, XF = 15, 60, 18
TOTAL = NF + HOLD + CARD + XF
MILE_T = [KT[1], KT[2], KT[3]]
print("settle", round(T_SET, 2), "NF", NF, "TOTAL", TOTAL, round(TOTAL / FPS, 2))

def count_at(t):
    if t <= KT[1]: return 1 + 9 * max(t, 0) / KT[1]
    return min(KN[-1], 10 ** np.interp(t, KT, np.log10(KN)))
def shown_count(t):
    return int(min(NM, np.sum(BIRTH <= t)))

# colour by birth time: a rainbow that turns as the marbles keep coming
LV = 64
HUE0, HSPAN = E("HUE0", 196), E("HSPAN", 212)
HUE = HUE0 + HSPAN * np.log10(np.arange(1, NM + 1)) / 3       # one colour band per rung of the ladder
HI = ((HUE - HUE0) / HSPAN * (LV - 1)).round().astype(int)
COLS = [hsv(HUE0 + HSPAN * k / (LV - 1), .6, 1.0) for k in range(LV)]
SPR = [glass_ball(c, 30) for c in COLS]
GLW = glow((1, .96, .86), 20, .9)
BG = background(CY)

def basin_layer():
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawImage(BG, 0, 0)
        # the basin: a dark glass dish that sinks toward the middle
        c.drawCircle(CX, CY + 16, RB + 26, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
        c.drawCircle(CX, CY, RB + 12, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (CX, CY), RB + 12, [skia.Color(10, 8, 7), skia.Color(19, 16, 14), skia.Color(34, 29, 25), skia.Color(52, 45, 38)],
            [0, .45, .9, 1])))
        # depth contours (equal steps down the well -> they crowd toward the middle)
        for k in range(1, 12):
            z = k / 12
            r = (1 / (z * (1 / math.sqrt(90) - 1 / math.sqrt(RB + 90)) + 1 / math.sqrt(RB + 90))) ** 2 - 90
            if r < 12: continue
            c.drawCircle(CX, CY, r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                         Color4f=skia.Color4f(*CREAM, .035 + .02 * (1 - z))))
        # glossy rim
        rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                         Shader=skia.GradientShader.MakeSweep(CX, CY,
                         [skia.Color(70, 60, 50), skia.Color(150, 130, 105), skia.Color(240, 225, 200), skia.Color(150, 130, 105),
                          skia.Color(60, 52, 44), skia.Color(90, 78, 64), skia.Color(70, 60, 50)], [0, .3, .62, .72, .85, .95, 1]))
        c.drawCircle(CX, CY, RB + 9, rim)
        c.drawCircle(CX, CY, RB + 3, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                     Color4f=skia.Color4f(0, 0, 0, .5)))
    return s.makeImageSnapshot()
BASIN = basin_layer()
SH = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .42), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3))
TRAIL = int(E("TRAIL", 14))

def frame(f, first=[None]):
    fs = min(f, NF - 1); t = fs / FPS
    P = POS[min(fs, NS - 1)]
    alive = np.nonzero(~np.isnan(P[:, 0]))[0]
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        c.drawImage(BASIN, 0, 0)
        # glowing trails: the rosette loops each marble is rolling
        for i in alive:
            TL = 80 if i < 10 else 34 if i < 100 else TRAIL      # the first marbles leave long rosette ribbons
            n0 = max(0, fs - TL, int(math.ceil((BIRTH[i]) * FPS)))
            pts = POS[n0:fs + 1, i]
            if len(pts) < 3: continue
            pts = pts[~np.isnan(pts[:, 0])]
            if len(pts) < 3: continue
            v = np.linalg.norm(pts[-1] - pts[-2]) * FPS
            if v < 25: continue
            col = COLS[HI[i]]
            a0 = min(1, v / 200) * (.5 if i < 10 else .36 if i < 100 else .24)
            if i < 10: a0 = .5 * min(1, v / 120)
            for k in range(1, len(pts)):
                u = k / (len(pts) - 1)
                if i < 10: u = u ** .5
                c.drawLine(CX + pts[k - 1][0], CY + pts[k - 1][1], CX + pts[k][0], CY + pts[k][1],
                           skia.Paint(AntiAlias=True, StrokeWidth=float(R[i]) * (.25 + .5 * u), StrokeCap=skia.Paint.kRound_Cap,
                                      Color4f=skia.Color4f(*col, a0 * u * u), BlendMode=skia.BlendMode.kPlus))
        for i in alive:
            x, y = CX + P[i, 0], CY + P[i, 1]; r = float(R[i])
            c.drawCircle(x + r * .22, y + r * .38, r * .96, SH)
        for i in alive:
            x, y = CX + P[i, 0], CY + P[i, 1]; r = float(R[i])
            age = t - BIRTH[i]
            sc = 1 + .45 * (1 - ss(age / .28)) if age < .28 else 1.0      # dropping in from just above
            blit(c, SPR[HI[i]], float(x), float(y), r * sc / 30)
            if age < .3:
                blit(c, GLW, float(x), float(y), r / 16, skia.Paint(Alphaf=.5 * (1 - age / .3), BlendMode=skia.BlendMode.kPlus))
        # soft sparks on the harder clicks this frame
        if len(EV):
            sel = EV[(EV[:, 0] >= t - 1 / FPS) & (EV[:, 0] < t)]
            sel = sel[sel[:, 3] > 70][:40]
            for e in sel:
                blit(c, GLW, CX + float(e[1]), CY + float(e[2]), .45, skia.Paint(Alphaf=float(min(.5, e[3] / 500)), BlendMode=skia.BlendMode.kPlus))
        # rung glint + final glint: a soft ring of light gliding out over the marbles
        rings = [(mt, .9, .45) for mt in MILE_T] + [(GL0, GL1 - GL0, .6)]
        for mt, dur, amp in rings:
            u = (t - mt) / dur
            if 0 <= u <= 1:
                rr = np.hypot(P[alive, 0], P[alive, 1])
                front = u * (RB + 20)
                g = amp * np.exp(-((rr - front) / 24) ** 2) * (1 - u) ** .4
                for k in np.nonzero(g > .04)[0]:
                    i = alive[k]
                    blit(c, GLW, CX + float(P[i, 0]), CY + float(P[i, 1]), float(R[i]) / 22, skia.Paint(Alphaf=float(.55 * g[k]), BlendMode=skia.BlendMode.kPlus))
        pulse = 0.0
        for mt in MILE_T:
            if 0 <= t - mt < .5: pulse = max(pulse, (1 - (t - mt) / .5) ** 2)
        header(c, "Everything rolls", "toward the middle.", count=shown_count(t), count_col=CREAM, pulse=pulse)
        watermark(c, 1585)
        if f >= NF + HOLD:
            a = ss((f - NF - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF and first[0] is not None:
            c.drawImage(first[0], 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first[0] = out.makeImageSnapshot()
    return out

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        frame(0).makeImageSnapshot().save("P_0000.png", skia.kPNG)
        for f in [int(v) for v in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"P_{f:04d}.png", skia.kPNG)
    elif sys.argv[1] == "audio":
        from audio_well import audio
        print(audio("A.wav", sys.modules[__name__]))
    else:
        import time; t0 = time.time()
        w = Writer("A_silent.mp4")
        for f in range(TOTAL):
            w.write(frame(f))
            if f % 60 == 0: print(f, round(time.time() - t0), flush=True)
        print("video", w.close(), "frames", TOTAL)
        from audio_well import audio
        print(audio("A.wav", sys.modules[__name__]))
        print("mux", mux("A_silent.mp4", "A.wav", "well.mp4"))
