"""Render the simulation to a 1080x1920 30fps video (or preview PNGs)."""
import pickle, sys, math, colorsys, subprocess, os
import numpy as np, skia

d = pickle.load(open("sim.pkl", "rb"))
FR, DONE, C, R, W, H, FPS = d["frames"], d["done"], d["C"], d["R"], d["W"], d["H"], d["FPS"]
CX, CY = float(C[0]), float(C[1])
TARGET = 1000

# end sequence timing (frames after DONE)
FREEZE = 15        # flash + hold
BURST = 36         # balls fly out
HOLD = 24          # big number on clean bg
XFADE = 15         # crossfade back to frame 0 (loop)
TOTAL = DONE + 1 + FREEZE + BURST + HOLD + XFADE

FONT_DIR = "/usr/share/fonts/opentype/inter/"
tf_black = skia.Typeface.MakeFromFile(FONT_DIR + "InterDisplay-Black.otf")
tf_semi = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-SemiBold.otf")
tf_med = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-Medium.otf")

INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)

def radius(n):
    return 30.0 * n ** -0.22

def hsv(h, s=0.72, v=1.0):
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, s, v)
    return r, g, b

# --- background image (static) ---
bg_surf = skia.Surface.MakeRaster(INFO)
with bg_surf as c:
    c.clear(skia.Color(7, 7, 14))
    p = skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (CX, CY), 1100, [skia.Color(26, 20, 52), skia.Color(10, 9, 22), skia.Color(5, 5, 11)], [0, 0.55, 1]))
    c.drawRect(skia.Rect(0, 0, W, H), p)
    # faint inner disc
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(1, 1, 1, 0.025))
    c.drawCircle(CX, CY, R, p)
BG = bg_surf.makeImageSnapshot()

trail = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_F16_ColorType, skia.kPremul_AlphaType))
with trail as c:
    c.drawImage(BG, 0, 0)

def text_center(c, s, y, size, tf, color, spacing=0.0):
    font = skia.Font(tf, size)
    font.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    w = font.measureText(s)
    if spacing:
        # manual letter spacing
        glyph_w = [font.measureText(ch) for ch in s]
        w = sum(glyph_w) + spacing * (len(s) - 1)
        x = W / 2 - w / 2
        p = skia.Paint(AntiAlias=True, Color4f=color)
        for ch, gw in zip(s, glyph_w):
            c.drawString(ch, x, y, font, p)
            x += gw + spacing
        return
    c.drawString(s, W / 2 - w / 2, y, font, skia.Paint(AntiAlias=True, Color4f=color))

ring_glow = 0.0
def draw_ring(c, n, glow, rad=R, alpha=1.0, gold=0.0):
    # base ring
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                   Color4f=skia.Color4f(1, 1, 1, (0.22 + 0.5 * glow) * alpha))
    c.drawCircle(CX, CY, rad + 6, p)
    # progress arc to 1,000 (log scale feels steadier; use linear on log)
    prog = min(1.0, math.log(max(n, 1)) / math.log(TARGET))
    if prog > 0:
        cols = [skia.Color4f(0.35, 0.85, 1, 1), skia.Color4f(0.75, 0.45, 1, 1),
                skia.Color4f(1, 0.4, 0.75, 1), skia.Color4f(1, 0.8, 0.35, 1), skia.Color4f(0.35, 0.85, 1, 1)]
        if gold > 0:
            g = skia.Color4f(1, 0.82, 0.38, 1)
            cols = [skia.Color4f(a.fR + (g.fR - a.fR) * gold, a.fG + (g.fG - a.fG) * gold,
                                 a.fB + (g.fB - a.fB) * gold, 1) for a in cols]
        sh = skia.GradientShader.MakeSweep(CX, CY, [skia.Color4f(x.fR, x.fG, x.fB, alpha).toColor() for x in cols])
        mat = skia.Matrix().setRotate(-90, CX, CY)
        sh = sh.makeWithLocalMatrix(mat)
        rect = skia.Rect(CX - rad - 6, CY - rad - 6, CX + rad + 6, CY + rad + 6)
        # soft glow under
        pg = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=22, Shader=sh,
                        StrokeCap=skia.Paint.kRound_Cap, Alphaf=0.22 * alpha,
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
        c.drawArc(rect, -90, 360 * prog, False, pg)
        pa = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Shader=sh,
                        StrokeCap=skia.Paint.kRound_Cap)
        c.drawArc(rect, -90, 360 * prog, False, pa)

def draw_balls(c, pos, hues, n, white=0.0, alpha=1.0, born=None, f=0):
    r = radius(n)
    halo = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kPlus)
    core = skia.Paint(AntiAlias=True)
    hr = r * 2.6
    for i in range(len(pos)):
        x, y = float(pos[i, 0]), float(pos[i, 1])
        cr, cg, cb = hsv(hues[i])
        if white > 0:
            gr, gg, gb = 1.0, 0.88, 0.55
            cr, cg, cb = cr + (gr - cr) * white, cg + (gg - cg) * white, cb + (gb - cb) * white
        pop = 1.0
        if born is not None:
            age = f - born[i]
            if age < 6:
                pop = 1.0 + 0.6 * (1 - age / 6)
        halo.setColor4f(skia.Color4f(cr, cg, cb, 0.07 * alpha))
        c.drawCircle(x, y, hr * pop, halo)
        halo.setColor4f(skia.Color4f(cr, cg, cb, 0.12 * alpha))
        c.drawCircle(x, y, r * 1.7 * pop, halo)
        core.setColor4f(skia.Color4f(cr, cg, cb, alpha))
        c.drawCircle(x, y, r * pop, core)
        # highlight
        core.setColor4f(skia.Color4f(1, 1, 1, 0.55 * alpha))
        c.drawCircle(x - r * 0.3, y - r * 0.3, r * 0.35, core)

def fmt(n):
    return f"{n:,}"

def draw_hud(c, n, gold=0.0, pop=1.0, alpha=1.0):
    text_center(c, "EVERY BOUNCE = +1 BALL", 262, 40, tf_semi, skia.Color4f(1, 1, 1, 0.62 * alpha), spacing=4)
    s = fmt(n)
    col = skia.Color4f(1, 1 - 0.18 * gold, 1 - 0.62 * gold, alpha)
    c.save()
    c.translate(W / 2, 400)
    c.scale(pop, pop)
    c.translate(-W / 2, -400)
    if gold > 0:
        font = skia.Font(tf_black, 168)
        w = font.measureText(s)
        gp = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 0.75, 0.3, 0.55 * gold * alpha),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 28))
        c.drawString(s, W / 2 - w / 2, 450, font, gp)
    text_center(c, s, 450, 168, tf_black, col)
    c.restore()
    text_center(c, "of 1,000", 520, 38, tf_med, skia.Color4f(1, 1, 1, 0.4 * alpha))

def fade_alpha(n):
    # long trails early (draws the star pattern), shorter as it fills
    return min(0.4, 0.035 + 0.06 * math.log(n))

first_img = None

def frame(f):
    """Returns RGBA bytes for frame f."""
    global ring_glow, first_img
    out = skia.Surface.MakeRaster(INFO)
    if f <= DONE:
        st = FR[f]
        n = st["n"]
        nprev = FR[f - 1]["n"] if f > 0 else 1
        ring_glow = ring_glow * 0.8 + min(0.6, (n - nprev) * 0.12)
        cur = st["pos"]
        prev = cur.copy()
        if f > 0:
            pp = FR[f - 1]["pos"]
            prev[:len(pp)] = pp
        with trail as c:
            c.drawImage(BG, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=fade_alpha(n)))
            r = radius(n)
            sp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kButt_Cap,
                            StrokeWidth=r * 1.1)
            a = 0.7 if n < 50 else 0.4
            for i in range(n):
                cr, cg, cb = hsv(st["hue"][i])
                sp.setColor4f(skia.Color4f(cr, cg, cb, a))
                c.drawLine(float(prev[i, 0]), float(prev[i, 1]), float(cur[i, 0]), float(cur[i, 1]), sp)
        with out as c:
            c.drawImage(trail.makeImageSnapshot(), 0, 0)
            draw_balls(c, cur, st["hue"], n, born=st["born"], f=f)
            draw_ring(c, n, ring_glow)
            draw_hud(c, n)
        if f == 0:
            first_img = out.makeImageSnapshot()
    else:
        st = FR[DONE]
        n = st["n"]
        k = f - DONE - 1
        pos0 = st["pos"]
        if k < FREEZE:
            u = k / FREEZE
            white = min(1.0, u * 3)
            with trail as c:
                c.drawImage(BG, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.5))
                draw_balls(c, pos0, st["hue"], n, white=white)
            pop = 1.0 + 0.28 * math.exp(-k / 4.0) * (1 if k > 0 else 0.5)
            with out as c:
                c.drawImage(trail.makeImageSnapshot(), 0, 0)
                draw_ring(c, n, 1.0 - 0.6 * u, gold=min(1, u * 3))
                draw_hud(c, n, gold=min(1, u * 3), pop=pop)
                # white flash
                c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(1, 0.95, 0.85, 0.55 * math.exp(-k / 2.5))))
        elif k < FREEZE + BURST:
            u = (k - FREEZE) / BURST
            e = u * u
            d = pos0 - np.array([CX, CY], dtype=np.float32)
            dist = np.linalg.norm(d, axis=1, keepdims=True) + 1e-3
            p = np.array([CX, CY]) + d * (1 + 3.2 * e) + d / dist * 600 * e
            with trail as c:
                c.drawImage(BG, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.35))
                draw_balls(c, p, st["hue"], n, white=1.0, alpha=max(0.0, 1 - u * 1.1))
            with out as c:
                c.drawImage(trail.makeImageSnapshot(), 0, 0)
                draw_ring(c, n, 0.4 * (1 - u), rad=R + 260 * e, alpha=max(0.0, 1 - u * 1.3), gold=1)
                draw_hud(c, n, gold=1, pop=1.1 - 0.05 * u)
        elif k < FREEZE + BURST + HOLD:
            with trail as c:
                c.drawImage(BG, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=0.35))
            with out as c:
                c.drawImage(trail.makeImageSnapshot(), 0, 0)
                draw_hud(c, n, gold=1, pop=1.05)
        else:
            u = (k - FREEZE - BURST - HOLD + 1) / XFADE
            u = u * u * (3 - 2 * u)
            with out as c:
                c.drawImage(BG, 0, 0)
                draw_hud(c, n, gold=1, pop=1.05, alpha=1 - u)
                c.drawImage(first_img, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=u))
    return out

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        want = set(int(x) for x in sys.argv[2].split(","))
        for f in range(max(want) + 1):
            s = frame(f)
            if f in want:
                s.makeImageSnapshot().save(f"prev_{f:04d}.png", skia.kPNG)
                print("saved", f)
    else:
        print("total frames", TOTAL, "=", TOTAL / FPS, "s")
        tmp = "video_tmp.mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
                               "-profile:v", "high", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        for f in range(TOTAL):
            arr = frame(f).makeImageSnapshot().toarray()
            ff.stdin.write(arr.tobytes())
            if f % 60 == 0:
                print("frame", f, flush=True)
        ff.stdin.close()
        if ff.wait() == 0:
            os.replace(tmp, "video_silent.mp4")
            print("ok")
