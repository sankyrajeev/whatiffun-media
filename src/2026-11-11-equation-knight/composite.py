"""Upscale the Cycles frames to 1080x1920 and overlay the whatiffun look: ONE EQUATION kicker, the series as the rule
line, the live arm count, the mark, the end card and the crossfade loop."""
import sys, os, numpy as np, skia
sys.path.insert(0, "/home/claude/whatiffun-media/src/2026-11-05-asmr-samples")
from kit import *
from motion import state, NFR, STARTS, STAGES, DRAW_END

FR = os.environ.get("FR", "/home/claude/eq/frames")
HOLD, CARD, XF = 24, 84, 18
TOTAL = NFR + HOLD + CARD + XF
TF_DV = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
FI = font(TF_SERIF_I, 60); FR_ = font(TF_SERIF, 60); FS = font(TF_SERIF_I, 36); FSIG = font(TF_DV, 54)
F_ARMS = font(TF_SERIF_I, 40)

def formula(c, y, a=.95):
    # x(t) + i·y(t) = Σ cₖ e^{ikt}
    parts = [("x(t) + i·y(t) = ", FI, 0), ("Σ", FSIG, 2), (" c", FI, 0), ("k", FS, 14), (" e", FI, 0), ("ikt", FS, -26)]
    widths = [f.measureText(s) for s, f, _ in parts]
    x = W / 2 - sum(widths) / 2
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*CREAM, a))
    for (s, f, dy), w in zip(parts, widths):
        c.drawString(s, x, y + dy, f, p); x += w

def stage_pulse(f):
    best = 0.0
    for s in STARTS:
        if s <= f: best = max(best, np.exp(-(f - s) / 5.0))
    if f >= DRAW_END: best = max(best, np.exp(-(f - DRAW_END) / 6.0))
    return best

def load(f):
    return skia.Image.open(f"{FR}/f_{min(f, NFR - 1):04d}.png")

first = None
def frame(f):
    global first
    out = skia.Surface.MakeRaster(INFO)
    k = min(f, NFR - 1); st = state(k)
    with out as c:
        c.drawImageRect(load(f), skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.CubicResampler.Mitchell()))
        c.drawRect(skia.Rect(0, 0, W, 640), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, 640)], [skia.Color4f(.03, .025, .02, .82).toColor(), skia.Color4f(.03, .025, .02, 0).toColor()])))
        text(c, "ONE EQUATION", W / 2, 196, F_KICK, CREAM, .5, spacing=6)
        formula(c, 290)
        n = st["label"]; pu = stage_pulse(k)
        cy = 430
        c.save(); c.translate(W / 2, cy - 40); c.scale(1 + .1 * pu, 1 + .1 * pu); c.translate(-W / 2, -(cy - 40))
        text(c, f"{n:,}", W / 2, cy, F_CNT, CREAM)
        c.restore()
        text(c, "arm" if n == 1 else "arms", W / 2, cy + 48, F_ARMS, AMBER, .85)
        watermark(c, 1640)
        if f >= NFR + HOLD:
            a = ss((f - NFR - HOLD) / 14)
            if f >= TOTAL - XF: a *= 1 - ss((f - (TOTAL - XF)) / XF)
            end_card(c, a)
        if f >= TOTAL - XF:
            c.drawImage(first, 0, 0, SAMP, skia.Paint(Alphaf=ss((f - (TOTAL - XF) + 1) / XF)))
    if f == 0: first = out.makeImageSnapshot()
    return out

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        frame(0)
        for f in [int(x) for x in sys.argv[2].split(",")]:
            frame(f).makeImageSnapshot().save(f"/home/claude/eq/C_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("/home/claude/eq/eq_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), TOTAL)
        print("mux", mux("/home/claude/eq/eq_silent.mp4", "/home/claude/eq/eq.wav", "/home/claude/eq/eq.mp4"))
