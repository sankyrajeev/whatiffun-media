"""Film MARBLE MUSIC from the rendered wall: a 1080x1920 window follows the marble down the wall; every pad
lights up the instant it is struck; the soundtrack is synthesised from the same hit list (one note per hit).
    python3 compose.py plan/<song>.json [stills t1,t2,...]  -> out/<song>.mp4 (or stills/*.png)"""
import json, math, os, subprocess, sys, wave
import numpy as np, skia
from PIL import Image
from scipy.signal import butter, sosfilt, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
P = json.load(open(sys.argv[1])); SONG = P["song"]
RD = os.path.join(HERE, "render", SONG)
W, H, FPS, SR = 1080, 1920, 30, 48000
G = P["g"]; BR = P["ball_r"]
CREAM, AMBER = (0.96, 0.92, 0.84), (0.88, 0.64, 0.30)
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
FD = os.path.join(ROOT, "fonts") + "/"
TF_SERIF_I = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Italic.ttf")
TF_SEMI = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_XB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
def font(tf, s):
    f = skia.Font(tf, s); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def sk(arr):  # RGBA uint8 (straight alpha) -> skia image (premultiplied)
    a = arr.astype(np.float32); a[..., :3] *= a[..., 3:4] / 255.0
    return skia.Image.fromarray(a.astype(np.uint8), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)

# ---------------- motion ----------------
HITS = P["hits"]
def ball_at(t):
    if t <= HITS[0]["t"]:
        dt = HITS[0]["t"] - t; vin = np.array(HITS[0]["vin"])
        return np.array([HITS[0]["x"], HITS[0]["y"]]) - vin * dt + np.array([0, .5 * G]) * dt * dt
    for h in reversed(HITS):
        if t >= h["t"]:
            dt = t - h["t"]
            return np.array([h["x"], h["y"]]) + np.array(h["vout"]) * dt + np.array([0, .5 * G]) * dt * dt
TJ = json.load(open(os.path.join(RD, "tiles.json")))
AX, BX, AY, BY = TJ["ax"], TJ["bx"], TJ["ay"], TJ["by"]          # design (x, y) on the pad plane -> strip px
def to_px(x, y): return AX * x + BX, AY * y + BY
T_END = P["t_end"]; NF = int(round(T_END * FPS))
TS = np.arange(NF) / FPS
BXY = np.array([ball_at(t) for t in TS])
# camera: keep the marble a little above centre, smoothed both ways so it glides (and anticipates the drops)
last_y = HITS[-1]["y"]
target = AY * np.minimum(BXY[:, 1], last_y + 260) + BY - 0.52 * H
sig = 0.32 * FPS; kx = np.arange(-int(3 * sig), int(3 * sig) + 1); kern = np.exp(-0.5 * (kx / sig) ** 2); kern /= kern.sum()
pad_t = np.concatenate([np.full(len(kx), target[0]), target, np.full(len(kx), target[-1])])
CAM = np.convolve(pad_t, kern, mode="same")[len(kx):-len(kx)]
# spin: a marble rolling along the wall turns about the view axis; angle follows horizontal travel
SPIN = np.cumsum(np.r_[0, np.diff(BXY[:, 0])]) / BR

# ---------------- wall strips ----------------
def load_strip(state):
    tiles = []
    for k in range(TJ["tiles"]):
        im = Image.open(os.path.join(RD, f"{state}_{k:02d}.png")).convert("RGBA")
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        tiles.append(np.asarray(im))
    return np.concatenate(tiles, 0)
IDLE = load_strip("idle"); LIT = load_strip("lit")
# one lit sprite per pad: the lit wall around the pad, feathered so only the pad and its glow light up
SPR = []
for k, pd in enumerate(P["pads"]):
    rad = pd["len"] / 2 + 46
    cxp, cyp = to_px(pd["x"], pd["y"])
    x0, x1 = int(cxp - rad * AX), int(cxp + rad * AX); y0, y1 = int(cyp - rad * AX), int(cyp + rad * AX)
    x0c, x1c = max(0, x0), min(W, x1); y0c, y1c = max(0, y0), min(len(LIT), y1)
    crop = LIT[y0c:y1c, x0c:x1c].copy()
    yy, xx = np.mgrid[y0c:y1c, x0c:x1c].astype(np.float32)
    dxd, dyd = (xx - cxp) / AX, (yy - cyp) / AY                   # back to design units
    ux, uy = math.cos(pd["ang"]), math.sin(pd["ang"])
    along = dxd * ux + dyd * uy; perp = -dxd * uy + dyd * ux
    m = np.clip(1.0 - np.maximum(np.abs(along) - pd["len"] / 2, 0) / 40.0, 0, 1) * np.clip(1.0 - np.maximum(np.abs(perp) - pd["half"] - 14, 0) / 40.0, 0, 1)
    crop[..., 3] = (m ** 1.5 * 255).astype(np.uint8)
    SPR.append((sk(crop), x0c, y0c))
BALL = [sk(np.asarray(Image.open(os.path.join(RD, f"ball_{k:02d}.png")).convert("RGBA"))) for k in range(36)]
BALL_SPAN = 2.6 * BR * AX

# ---------------- overlay ----------------
def overlay(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (W / 2, H * 0.5), 1150, [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.0), skia.Color4f(0.01, 0.008, 0.006, 0.7)], [0, .45, 1])))
    # soft dark bands so the text reads over the wall
    c.drawRect(skia.Rect(0, 0, W, 470), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (0, 470)], [skia.Color4f(0.02, 0.016, 0.012, 0.92), skia.Color4f(0.02, 0.016, 0.012, 0.0)])))
    c.drawRect(skia.Rect(0, 1380, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [(0, 1380), (0, H)], [skia.Color4f(0.02, 0.016, 0.012, 0.0), skia.Color4f(0.02, 0.016, 0.012, 0.95)])))
    def ctext(s, y, f, rgb, a=1.0):
        w = f.measureText(s); c.drawString(s, W / 2 - w / 2, y, f, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgb, a)))
    ctext("GUESS", 268, font(TF_XB, 96), CREAM)
    ctext("THE SONG", 370, font(TF_XB, 96), AMBER)
    ctext("Comment the song", 1534, font(TF_SEMI, 44), CREAM)
    ctext("Like it if you got it", 1590, font(TF_SERIF_I, 36), CREAM, 0.6)
    ctext("@whatiffun", 1640, font(TF_SERIF_I, 32), CREAM, 0.42)

surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
IDLE_SK = None
def frame(fi):
    global IDLE_SK
    t = TS[fi]; top = int(round(CAM[fi]))
    with surf as c:
        top = max(0, min(top, len(IDLE) - H))
        c.drawImage(sk(IDLE[top:top + H]), 0, 0)
        # lit pads (struck in the last 0.7 s)
        for k, h in enumerate(HITS):
            dt = t - h["t"]
            if 0 <= dt < 0.7:
                img, sx, sy = SPR[k]
                if sy + img.height() < top or sy > top + H: continue
                a = math.exp(-dt / 0.2) * min(1, dt / 0.02 + 0.6)
                p = skia.Paint(); p.setAlphaf(min(1, a))
                c.drawImage(img, sx, sy - top, SAMP, p)
        # marble shadow on the wall, then the marble
        bx, by = to_px(BXY[fi][0], BXY[fi][1]); by -= top
        r = BR * AX
        c.drawOval(skia.Rect(bx + 10 - r, by + 16 - r * 0.9, bx + 10 + r, by + 16 + r * 0.9),
                   skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
        k = int(round((SPIN[fi] % (2 * math.pi)) / (2 * math.pi) * 36)) % 36
        c.drawImageRect(BALL[k], skia.Rect(bx - BALL_SPAN / 2, by - BALL_SPAN / 2, bx + BALL_SPAN / 2, by + BALL_SPAN / 2), SAMP, skia.Paint(AntiAlias=True))
        # impact sparkle at the contact point
        for h in HITS:
            dt = t - h["t"]
            if 0 <= dt < 0.35:
                n = np.array(h["nrm"]); cx, cy = to_px(h["x"] - n[0] * BR, h["y"] - n[1] * BR); cy -= top
                u = dt / 0.35
                glow = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus, Shader=skia.GradientShader.MakeRadial(
                    (cx, cy), 70, [skia.Color4f(1, .8, .45, .55 * (1 - u)), skia.Color4f(1, .6, .2, 0)]))
                c.drawCircle(cx, cy, 70, glow)
                c.drawCircle(cx, cy, 18 + 70 * ss(u), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                             Color4f=skia.Color4f(1, .85, .55, .5 * (1 - u))))
        overlay(c, t)
    return surf

# ---------------- sound ----------------
def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def voice(fam, f0, dur=2.6):
    t = np.arange(int(dur * SR)) / SR; att = np.minimum(1, t * 900)
    if fam == "wood":     # marimba
        s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 5) + .35 * np.sin(2 * np.pi * f0 * 3.93 * t) * np.exp(-t * 16) \
            + .12 * np.sin(2 * np.pi * f0 * 9.2 * t) * np.exp(-t * 40)
    elif fam == "tube":   # tubular chime
        s = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in
                [(1, 1, 1.3), (2.76, .5, 2.2), (5.40, .25, 3.5), (8.93, .12, 6), (1.003, .4, 1.4)])
    elif fam == "glass":
        s = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 2.2) + .3 * np.sin(2 * np.pi * f0 * 2 * t) * np.exp(-t * 4) \
            + .15 * np.sin(2 * np.pi * f0 * 4.1 * t) * np.exp(-t * 9)
    else:                 # saucer: steel-pan-ish
        s = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in
                [(1, 1, 3.0), (2, .45, 4.5), (3, .22, 6), (4.2, .1, 9)])
    return s * att
def soundtrack(path):
    n = int((T_END + 0.5) * SR); L = np.zeros(n); R = np.zeros(n)
    rng = np.random.default_rng(5)
    for h in HITS:
        f0 = mtof(h["midi"]); gain = {"wood": .5, "tube": .32, "glass": .38, "saucer": .4}[h["fam"]]
        if h is HITS[-1]: gain *= 1.6
        s = voice(h["fam"], f0) * gain
        click = sosfilt(butter(2, [2500, 9000], "bandpass", fs=SR, output="sos"), rng.standard_normal(int(.006 * SR))) * .25
        s[:len(click)] += click
        pan = (h["x"] - 540) / 540 * 0.6
        i = int(h["t"] * SR); m = min(len(s), n - i)
        L[i:i + m] += s[:m] * math.sqrt(0.5 * (1 - pan)); R[i:i + m] += s[:m] * math.sqrt(0.5 * (1 + pan))
    # small warm room
    ir_t = np.arange(int(1.6 * SR)) / SR
    irL = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2); irR = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2)
    lp = butter(2, 5000, "lowpass", fs=SR, output="sos"); irL = sosfilt(lp, irL); irR = sosfilt(lp, irR)
    irL /= np.abs(irL).sum() ** .5 * 6; irR /= np.abs(irR).sum() ** .5 * 6
    L = L + fftconvolve(L, irL)[:n] * .9; R = R + fftconvolve(R, irR)[:n] * .9
    st = np.stack([L, R], 1); st /= max(1e-9, np.abs(st).max()) / 0.8
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for tt in [float(x) for x in sys.argv[3].split(",")]:
            fi = min(NF - 1, int(tt * FPS))
            frame(fi).makeImageSnapshot().save(os.path.join(HERE, "stills", f"{SONG}-{tt:05.2f}.png"), skia.kPNG)
        print("stills ok"); sys.exit()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    base = os.path.join(HERE, "out", SONG); tmp = base + "_v.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(NF): p.stdin.write(frame(fi).makeImageSnapshot().toarray().tobytes())
    p.stdin.close(); assert p.wait() == 0
    wav = base + "_a.wav"; soundtrack(wav)
    out = base + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.5dB", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    os.replace(out, base + ".mp4"); os.remove(tmp); os.remove(wav)
    print("wrote", base + ".mp4", f"{T_END:.1f}s")
