"""Shared look + sound toolkit for whatiffun ASMR samples (fixed background theme)."""
import math, subprocess, os, wave
import numpy as np, skia
from scipy.signal import butter, sosfilt, fftconvolve

W, H, FPS, SR = 1080, 1920, 30, 48000
INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fonts") + "/"
TF_SERIF = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Regular.ttf")
TF_SERIF_I = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Italic.ttf")
TF_MONO = skia.Typeface.MakeFromFile(FD + "JetBrainsMono-Regular.ttf")
TF_SEMI = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
CREAM = (0.96, 0.92, 0.84)
AMBER = (0.88, 0.64, 0.30)
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)

def font(tf, s):
    f = skia.Font(tf, s); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def text(c, s, x, y, f, rgb, a=1.0, align="center", spacing=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgb, a))
    ws = [f.measureText(ch) for ch in s] if spacing else None
    w = (sum(ws) + spacing * (len(s) - 1)) if spacing else f.measureText(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    if not spacing: c.drawString(s, x, y, f, p); return
    for ch, cw in zip(s, ws): c.drawString(ch, x, y, f, p); x += cw + spacing

def background(cy=980):
    s = skia.Surface.MakeRaster(INFO)
    with s as c:
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, cy), 1250, [skia.Color(30, 25, 20), skia.Color(15, 12, 10), skia.Color(7, 6, 5)], [0, .5, 1])))
    return s.makeImageSnapshot()

def hsv(h, s=0.65, v=1.0):
    import colorsys
    return colorsys.hsv_to_rgb((h % 360) / 360, s, v)

def sprite(fn, size, S=4):
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(int(size * S), int(size * S)))
    with surf as c: c.clear(skia.Color4f(0, 0, 0, 0)); c.scale(S, S); fn(c)
    return surf.makeImageSnapshot(), size
def blit(c, spr, x, y, scale=1.0, paint=None):
    img, sz = spr; h = sz * scale / 2
    c.drawImageRect(img, skia.Rect(x - h, y - h, x + h, y + h), SAMP, paint)

def glass_ball(col, r):
    sz = r * 2 + 4
    def fn(c):
        cx = cy = sz / 2
        light = tuple(min(1, x * .45 + .55) for x in col); dark = tuple(x * .45 for x in col)
        sh = skia.GradientShader.MakeRadial((cx - r * .35, cy - r * .4), r * 1.35,
             [skia.Color4f(*light, 1).toColor(), skia.Color4f(*col, 1).toColor(), skia.Color4f(*dark, 1).toColor()], [0, .55, 1])
        c.drawCircle(cx, cy, r, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawCircle(cx + r * .28, cy + r * .3, r * .42, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .18),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(.6, r * .15))))
        c.drawCircle(cx - r * .38, cy - r * .42, r * .24, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, .9)))
    return sprite(fn, sz)
def glow(col, r, a=.8):
    sz = r * 6
    def fn(c):
        c.drawCircle(sz / 2, sz / 2, r, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*col, a),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * .9)))
    return sprite(fn, sz)

F_KICK = font(TF_SEMI, 27)
F_RULE = font(TF_SERIF, 68)
F_RULE_I = font(TF_SERIF_I, 68)
F_CNT = font(TF_SERIF, 104)
F_MONO = font(TF_MONO, 28)
F_MARK = font(TF_SERIF_I, 34)

def header(c, rule_a, rule_b=None, count=None, count_col=CREAM, count_y=452, pulse=0.0):
    text(c, "ONE RULE", W / 2, 196, F_KICK, CREAM, .5, spacing=6)
    text(c, rule_a, W / 2, 272, F_RULE, CREAM, .97)
    if rule_b: text(c, rule_b, W / 2, 336, F_RULE_I, CREAM, .9)
    if count is not None:
        s = f"{count:,}"
        c.save(); c.translate(W / 2, count_y - 40); c.scale(1 + .1 * pulse, 1 + .1 * pulse); c.translate(-W / 2, -(count_y - 40))
        text(c, s, W / 2, count_y, F_CNT, count_col)
        c.restore()
def watermark(c, y=1560):
    text(c, "@whatiffun", W / 2, y, F_MARK, CREAM, .42)
def end_card(c, a):
    if a <= 0: return
    card = skia.RRect.MakeRectXY(skia.Rect(150, 820, W - 150, 1100), 34, 34)
    c.drawRRect(card.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6 * a),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
    c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.09, .075, .06, .94 * a)))
    c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                Color4f=skia.Color4f(*AMBER, .45 * a)))
    dy = 12 * (1 - a)
    text(c, "Follow", W / 2, 940 + dy, font(TF_SERIF, 76), CREAM, a)
    text(c, "@whatiffun", W / 2, 1022 + dy, font(TF_SERIF_I, 76), AMBER, a)
    text(c, "for more", W / 2, 1072 + dy, font(TF_SERIF_I, 40), CREAM, .6 * a)

class Writer:
    def __init__(self, path):
        self.path, self.tmp = path, path.replace(".mp4", "_tmp.mp4")
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                                   "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", self.tmp], stdin=subprocess.PIPE)
    def write(self, surf): self.p.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
    def close(self):
        self.p.stdin.close()
        if self.p.wait() == 0: os.replace(self.tmp, self.path); return True
        return False

# ---------------- audio ----------------
class Mix:
    def __init__(self, seconds):
        self.N = int(seconds * SR); self.L = np.zeros(self.N); self.R = np.zeros(self.N)
    def add(self, sig, t0, g, x=540):
        p = max(-.92, min(.92, (x - 540) / 440))
        gl, gr = math.cos((p + 1) * math.pi / 4), math.sin((p + 1) * math.pi / 4)
        d = int(abs(p) * .00045 * SR); i = int(t0 * SR)
        il, ir = (i + d, i) if p > 0 else (i, i + d)
        for buf, j, gg in ((self.L, il, gl), (self.R, ir, gr)):
            if 0 <= j < self.N:
                s = sig[:self.N - j]; buf[j:j + len(s)] += s * g * gg
    def save(self, path, room=.15, fade_in=.03, fade_out=.4):
        rng = np.random.default_rng(1)
        n = int(.45 * SR); t = np.arange(n) / SR
        irs = [sosfilt(butter(1, 4500, fs=SR, output="sos"), rng.standard_normal(n) * np.exp(-t * 10)) for _ in range(2)]
        irs = [x / np.sqrt((x ** 2).sum()) for x in irs]
        L = self.L + room * fftconvolve(self.L, irs[0])[:self.N]; R = self.R + room * fftconvolve(self.R, irs[1])[:self.N]
        out = np.stack([L, R], 1)
        fi, fo = int(fade_in * SR), int(fade_out * SR)
        out[:fi] *= np.linspace(0, 1, fi)[:, None]; out[-fo:] *= np.linspace(1, .15, fo)[:, None]
        out = np.tanh(out / (np.percentile(np.abs(out), 99.95) + 1e-9) * .95)
        out = out / np.max(np.abs(out)) * .89
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((out * 32767).astype(np.int16).tobytes())
        return [round(float(np.sqrt((out[s * SR:(s + 1) * SR] ** 2).mean())), 3) for s in range(int(self.N / SR))]

_rng = np.random.default_rng(5)
def glass_click(f0, dec, dur=.07, noise=.3):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) + .5 * np.sin(2 * np.pi * f0 * 2.76 * t + 1) * np.exp(-t * dec * .6)) * np.exp(-t * dec)
    n = _rng.standard_normal(len(t)) * np.exp(-t * 1800) * noise
    return (s + np.diff(n, prepend=0)) * np.minimum(1, t * 6000)
def mallet(f0, dur=1.2, bright=1.0):
    """glass/marimba-like struck bar"""
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 3.2)
         + .45 * bright * np.sin(2 * np.pi * f0 * 3.93 * t) * np.exp(-t * 9)
         + .2 * bright * np.sin(2 * np.pi * f0 * 9.2 * t) * np.exp(-t * 22))
    n = _rng.standard_normal(len(t)) * np.exp(-t * 900) * .15 * bright
    return (s + n) * np.minimum(1, t * 3000)
def thud(f0=60, dur=.5):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * (f0 * t + 30 * (1 - np.exp(-t * 18)) / 18)) * np.exp(-t * 9) * np.minimum(1, t * 4000)
def mux(video, audio, out):
    tmp = out.replace(".mp4", "_mux.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", tmp])
    if r.returncode == 0: os.replace(tmp, out); return True
    return False
PENTA = [0, 2, 4, 7, 9]   # major pentatonic — calm
def note(i, base=261.63):
    o, d = divmod(i, 5); return base * 2 ** ((PENTA[d] + 12 * o) / 12)
