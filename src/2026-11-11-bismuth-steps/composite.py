"""Upscale the Cycles frames to 1080x1920 and overlay the whatiffun look: ONE RULE, the rule, the live step count,
the mark, the end card and the crossfade loop."""
import sys, os, json, numpy as np, skia
sys.path.insert(0, "/home/claude/whatiffun-media/src/2026-11-05-asmr-samples")
from kit import *
from motion import NFR, count

FR = os.environ.get("FR", "/home/claude/bi/frames")
HOLD, CARD, XF = 24, 84, 18
TOTAL = NFR + HOLD + CARD + XF
MS = json.load(open("/home/claude/bi/milestones.json"))
CNT = [count(f) for f in range(NFR)]
F_LBL = font(TF_SERIF_I, 40)

def pulse(f):
    p = 0.0
    for m in MS:
        if m <= f: p = max(p, np.exp(-(f - m) / 5.0))
    return p
def load(f): return skia.Image.open(f"{FR}/f_{min(f, NFR - 1):04d}.png")

first = None
def frame(f):
    global first
    out = skia.Surface.MakeRaster(INFO)
    k = min(f, NFR - 1)
    with out as c:
        c.drawImageRect(load(f), skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.CubicResampler.Mitchell()))
        c.drawRect(skia.Rect(0, 0, W, 640), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, 640)], [skia.Color4f(.03, .025, .02, .84).toColor(), skia.Color4f(.03, .025, .02, 0).toColor()])))
        c.drawRect(skia.Rect(0, 1480, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 1480), (0, H)], [skia.Color4f(.03, .025, .02, 0).toColor(), skia.Color4f(.03, .025, .02, .6).toColor()])))
        n = CNT[k]
        header(c, "Every step", "grows a smaller crystal.", count=n, pulse=pulse(k))
        text(c, "step" if n == 1 else "steps", W / 2, 452 + 48, F_LBL, AMBER, .85)
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
            frame(f).makeImageSnapshot().save(f"/home/claude/bi/C_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("/home/claude/bi/bi_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), TOTAL)
        print("mux", mux("/home/claude/bi/bi_silent.mp4", "/home/claude/bi/bi.wav", "/home/claude/bi/bi.mp4"))
