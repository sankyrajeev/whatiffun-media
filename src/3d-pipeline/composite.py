"""Upscale the Cycles frames to 1080x1920 and overlay the fixed whatiffun look (rule, count, mark, end card)."""
import sys, pickle, numpy as np, skia
sys.path.insert(0, "/home/claude/notes")
from kit import *

d = pickle.load(open("/home/claude/notes/split.pkl", "rb"))
CNT = d["counts"]; NF = len(CNT)
HOLD, CARD, XF = 18, 66, 18
TOTAL = NF + HOLD + CARD + XF
first = None
def load(f):
    img = skia.Image.open(f"/home/claude/b3d/frames/f_{min(f, NF - 1):04d}.png")
    return img
def frame(f):
    global first
    out = skia.Surface.MakeRaster(INFO)
    with out as c:
        img = load(f)
        c.drawImageRect(img, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.CubicResampler.Mitchell()))
        # darken the top so the text sits on our warm black
        c.drawRect(skia.Rect(0, 0, W, 620), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, 620)], [skia.Color4f(.03, .025, .02, .75).toColor(), skia.Color4f(.03, .025, .02, 0).toColor()])))
        k = min(f, NF - 1)
        header(c, "Every bounce", "splits it in two.", count=int(CNT[k]))
        watermark(c, 1640)
        if f >= NF + HOLD:
            a = ss((f - NF - HOLD) / 14)
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
            frame(f).makeImageSnapshot().save(f"/home/claude/b3d/C_{f:04d}.png", skia.kPNG)
    else:
        w = Writer("/home/claude/b3d/split3d_silent.mp4")
        for f in range(TOTAL): w.write(frame(f))
        print("video", w.close(), TOTAL)
        print("mux", mux("/home/claude/b3d/split3d_silent.mp4", "/home/claude/notes/B.wav", "/home/claude/b3d/split3d.mp4"))
