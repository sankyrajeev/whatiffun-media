"""'What if the Eiffel Tower was made of human bones?' in the whatiffun look.
One script, two native layouts from the same drawings:
    python3 render.py 16x9   -> 1920x1080 (YouTube main)
    python3 render.py 9x16   -> 1080x1920 (Shorts / Reels)
Voice = one continuous George take; captions/cues come from its word timings (whisper, align-words workflow)."""
import json, math, os, subprocess, sys, wave
import numpy as np, skia
from PIL import Image

FMT = sys.argv[1] if len(sys.argv) > 1 else "16x9"
ONLY = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None   # preview stills at these times
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LAND = FMT == "16x9"
W, H = (1920, 1080) if LAND else (1080, 1920)
FPS, SR = 30, 48000
CREAM, AMBER = (0.96, 0.92, 0.84), (0.88, 0.64, 0.30)
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
FD = os.path.join(ROOT, "fonts") + "/"
TF_SERIF = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Regular.ttf")
TF_SERIF_I = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Italic.ttf")
TF_SEMI = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
def font(tf, s):
    f = skia.Font(tf, s); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def eob(u):  # ease-out-back, small overshoot
    u = min(1, max(0, u)); c = 1.4; return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2

# ---------------- timing from the aligned voice ----------------
LEAD = 0.30
WORDS = json.load(open(os.path.join(HERE, "..", "narration-george-continuous.words.json")))["words"]
VOICE = 42.27
def ws(i): return LEAD + WORDS[i]["start"]
def we(i): return LEAD + WORDS[i]["end"]
CAPS = [(0, 4, "What if the Eiffel Tower"), (5, 9, "was made of human bones?"),
        (10, 13, "The real tower is"), (14, 18, "7,300 tonnes of iron."),
        (19, 24, "Bone is about four times lighter."),
        (25, 33, "So if you built the same shape from bone,"), (34, 40, "it would weigh about 1,800 tonnes."),
        (41, 45, "That's about 250,000 skeletons."),
        (46, 50, "Where would Paris get them?"), (51, 54, "Right under its streets."),
        (55, 59, "The Catacombs hold the bones"), (60, 63, "of six million people."),
        (64, 68, "That's enough for 24 towers."), (69, 72, "So, would it stand?"),
        (73, 78, "Pound for pound, bone is nearly"), (79, 84, "as strong as the tower's iron."),
        (85, 88, "But it's much bendier,"), (89, 95, "so it would sway in the wind."),
        (96, 103, "And the rain would slowly rot it away."), (104, 108, "Subscribe for more what-ifs.")]
CAPT = []
START_FIX = {69: LEAD + 28.38}
for k, (a, b, txt) in enumerate(CAPS):
    st = START_FIX.get(a, ws(a) - 0.08); nx = START_FIX.get(CAPS[k + 1][0], ws(CAPS[k + 1][0]) - 0.08) - 0.06 if k + 1 < len(CAPS) else 99
    CAPT.append((st, min(we(b) + 0.45, nx), txt))
CUT = [0.0] + [ws(i) - 0.22 for i in (10, 19, 25, 41, 46, 55)] + [LEAD + 28.15] + [ws(i) - 0.22 for i in (85, 96, 104)]
CARD = LEAD + VOICE + 0.25
END = round(CARD + 2.6, 2)
XF = 0.40   # crossfade between shots

# ---------------- art ----------------
ART = {}
def art(name):
    if name not in ART:
        im = Image.open(os.path.join(HERE, "art", name)).convert("RGBA")
        a = np.asarray(im).astype(np.float32) / 255; a[..., :3] *= a[..., 3:4]   # premultiply
        ART[name] = skia.Image.fromarray((a * 255).astype(np.uint8), colorType=skia.kRGBA_8888_ColorType,
                                          alphaType=skia.kPremul_AlphaType)
    return ART[name]

# stage box: where the picture lives (centre x, floor y, height)
BOX = (1370, 935, 800) if LAND else (540, 1450, 860)
def draw_art(c, name, hf, ox=0.0, oy=0.0, ang=0.0, alpha=1.0, sc=1.0, pivot="bottom"):
    if alpha <= 0.003: return
    img = art(name); bx, by, bh = BOX
    h = bh * hf * sc; w = h * img.width() / img.height()
    x = bx + ox * bh; y = by + oy * bh
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang))
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    c.drawImageRect(img, skia.Rect(-w / 2, -h, w / 2, 0), SAMP, p); c.restore()
def floor_shadow(c, w_frac, alpha=1.0, ox=0.0):
    bx, by, bh = BOX
    c.drawOval(skia.Rect(bx + ox * bh - bh * w_frac / 2, by - 22, bx + ox * bh + bh * w_frac / 2, by + 22),
               skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .55 * alpha),
                          MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))

def sway(t, amp, per, ph=0.0): return amp * math.sin(2 * math.pi * (t / per) + ph)
def rise(t, t0=0.0, d=0.6): u = ss((t - t0) / d); return (1 - u) * 0.08, u   # (oy, alpha)

# ---------------- text ----------------
if LAND:
    TX, TALIGN = 150, "left"
    KICK_Y, L1_Y, L2_Y, N_Y = 330, 455, 575, 720
    F_KICK, F_HEAD, F_HEAD_I, F_NUM = font(TF_SEMI, 30), font(TF_SERIF, 118), font(TF_SERIF_I, 118), font(TF_SERIF, 150)
    F_CAP, CAP_Y = font(TF_SEMI, 44), 1022
else:
    TX, TALIGN = 540, "center"
    KICK_Y, L1_Y, L2_Y, N_Y = 250, 355, 455, 575
    F_KICK, F_HEAD, F_HEAD_I, F_NUM = font(TF_SEMI, 30), font(TF_SERIF, 104), font(TF_SERIF_I, 104), font(TF_SERIF, 124)
    F_CAP, CAP_Y = font(TF_SEMI, 50), 1540
F_MARK = font(TF_SERIF_I, 34)
def text(c, s, x, y, f, rgb, a=1.0, align="center", spacing=0.0):
    if a <= 0.003: return
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgb, a))
    ws_ = [f.measureText(ch) for ch in s] if spacing else None
    w = (sum(ws_) + spacing * (len(s) - 1)) if spacing else f.measureText(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    if not spacing: c.drawString(s, x, y, f, p); return
    for ch, cw in zip(s, ws_): c.drawString(ch, x, y, f, p); x += cw + spacing
def line(c, s, y, f, rgb, t, t0, pop=False, spacing=0.0, a=1.0):
    u = ss((t - t0) / 0.35)
    if u <= 0: return
    dy = 18 * (1 - u)
    if pop:
        k = 0.85 + 0.15 * eob((t - t0) / 0.45)
        w = f.measureText(s); ax = TX + (w / 2 if TALIGN == "left" else 0)
        c.save(); c.translate(ax, y - f.getSize() * .35); c.scale(k, k); c.translate(-ax, -(y - f.getSize() * .35))
        text(c, s, TX, y + dy, f, rgb, u * a, TALIGN, spacing); c.restore()
    else:
        text(c, s, TX, y + dy, f, rgb, u * a, TALIGN, spacing)
def head(c, t, kick, l1, l2=None, num=None, t_l2=0.0, t_num=None, l2_italic=True, num_col=AMBER):
    line(c, kick, KICK_Y, F_KICK, AMBER, t, 0.0, spacing=7)
    line(c, l1, L1_Y, F_HEAD, CREAM, t, 0.08)
    if l2: line(c, l2, L2_Y, F_HEAD_I if l2_italic else F_HEAD, CREAM, t, t_l2 or 0.16, a=.92)
    if num: line(c, num, N_Y, F_NUM, num_col, t, t_num, pop=True)

# ---------------- shots ----------------
def s1(c, t):  # hook
    head(c, t, "WHAT IF", "The Eiffel Tower", "was made of bones?", t_l2=ws(5) - CUT[0])
    oy, a = rise(t, 0.0, 0.8)
    floor_shadow(c, .55, a); draw_art(c, "tower-bones.png", .98, 0, oy, sway(t, .012, 3.2), a)
def s2(c, t):
    t0 = CUT[1]
    head(c, t, "THE REAL ONE", "7,300 tonnes", "of iron.", t_l2=ws(17) - t0)
    oy, a = rise(t)
    floor_shadow(c, .5, a); draw_art(c, "tower-iron.png", .98, 0, oy, sway(t, .006, 3.0), a)
def s3(c, t):
    t0 = CUT[2]
    head(c, t, "BONE IS", "four times", "lighter.", t_l2=ws(24) - t0)
    oy, a = rise(t)
    bob = 0.012 * math.sin(t * 5.5)
    floor_shadow(c, .8, a); draw_art(c, "lift-iron-vs-bone.png", .9, 0, oy + bob * .3, sway(t, .01, 1.1), a)
def s4(c, t):
    t0 = CUT[3]; tn = ws(38) - t0
    head(c, t, "SAME SHAPE, IN BONE", "It would weigh", None, num="1,800 tonnes", t_num=tn)
    oy, a = rise(t)
    fade = 1 - .7 * ss((t - (ws(33) - t0)) / 0.8)
    floor_shadow(c, .3, a, -.33); draw_art(c, "tower-iron.png", .82, -.33, oy, 0, a * fade)
    ub = ss((t - 0.7) / 0.9)
    floor_shadow(c, .35, ub, .27); draw_art(c, "tower-bones.png", .95, .27, (1 - ub) * .08, sway(t, .012, 2.6), ub)
def s5(c, t):
    t0 = CUT[4]
    head(c, t, "THAT'S ABOUT", "250,000", "skeletons.", t_l2=ws(45) - t0, l2_italic=True)
    oy, a = rise(t)
    k = 1 + .015 * math.sin(t * 3)
    floor_shadow(c, .5, a); draw_art(c, "skeleton-queue.png", .98 * k, 0, oy, sway(t, .008, 1.4), a)
def s6(c, t):
    t0 = CUT[5]; ta = ws(51) - t0
    head(c, t, "WHERE FROM?", "Right under", "the streets.", t_l2=ta + 0.3)
    bx, by, bh = BOX
    # street line draws across, then the tunnel rises from beneath it
    u = ss(t / 0.9); y0 = by - bh * 1.0
    x0, x1 = bx - bh * .55, bx + bh * .55
    c.drawLine(x0, y0, x0 + (x1 - x0) * u, y0, skia.Paint(AntiAlias=True, StrokeWidth=4, Color4f=skia.Color4f(*CREAM, .7)))
    text(c, "PARIS", bx - bh * .5, y0 - 18, F_KICK, CREAM, .5 * u, "left", 6)
    ub = ss((t - ta + 0.2) / 0.8)
    floor_shadow(c, .55, ub); draw_art(c, "catacombs.png", .9, 0, (1 - ub) * .12, 0, ub)
def s7(c, t):
    t0 = CUT[6]; t24 = ws(67) - t0
    head(c, t, "THE CATACOMBS", "6,000,000", "people", t_l2=ws(63) - t0)
    line(c, "= 24 towers", N_Y, F_NUM, AMBER, t, t24 - 0.1, pop=True)
    out = ss((t - t24 + 0.6) / 0.5)
    draw_art(c, "catacombs.png", .9, 0, 0, sway(t, .006, 2.4), 1 - out)
    if t > t24 - 0.6:
        bx, by, bh = BOX
        for k in range(24):
            r, col = divmod(k, 8)
            tk = t24 - 0.35 + k * 0.06; u = ss((t - tk) / 0.25)
            if u <= 0: continue
            ox = (col - 3.5) * .135 * (1 if LAND else .9); oy = -(2 - r) * .33
            draw_art(c, "tower-bones.png", .3, ox, oy + (1 - u) * .04, sway(t, .02, 1.8, k), u)
def s8(c, t):
    t0 = CUT[7]
    head(c, t, "WOULD IT STAND?", "Nearly as strong", "as iron.", t_l2=ws(79) - t0)
    oy, a = rise(t)
    sc = 1 if LAND else .84
    floor_shadow(c, .45, a, -.27 * sc); draw_art(c, "lift-iron-vs-bone.png", .72 * sc, -.27 * sc, oy, sway(t, .01, 1.2), a)
    ub = ss((t - 0.5) / 0.8)
    floor_shadow(c, .3, ub, .33 * sc); draw_art(c, "tower-bones.png", .95 * sc, .33 * sc, (1 - ub) * .08, sway(t, .02, 1.6), ub)
def s9(c, t):
    head(c, t, "BUT", "It bends.", "The wind would sway it.", t_l2=ws(92) - CUT[8])
    oy, a = rise(t, 0, .4)
    floor_shadow(c, .5, a); draw_art(c, "tower-sway.png", .98, 0, oy, sway(t, .055, 0.95), a)
def s10(c, t):
    head(c, t, "AND THE RAIN", "would slowly", "rot it away.", t_l2=ws(101) - CUT[9])
    oy, a = rise(t, 0, .4)
    sink = .02 * ss(t / 2.6)
    floor_shadow(c, .45, a); draw_art(c, "tower-rain.png", .98, 0, oy + sink, sway(t, .008, 1.3), a)
def s11(c, t):
    head(c, t, "SUBSCRIBE", "for more", "what-ifs.", t_l2=0.2)
    oy, a = rise(t, 0, .5)
    floor_shadow(c, .5, a); draw_art(c, "tower-bones.png", .98, 0, oy, sway(t, .03, 1.0), a)
SHOTS = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11]

# ---------------- frame ----------------
def background():
    s = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(W, H))
    with s as c:
        cx, cy = (BOX[0], BOX[1] - BOX[2] * .45)
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (cx, cy), max(W, H) * .95, [skia.Color(34, 27, 20), skia.Color(15, 12, 10), skia.Color(7, 6, 5)], [0, .5, 1])))
        # soft amber light pool on the floor, like the channel banner
        c.drawOval(skia.Rect(BOX[0] - BOX[2] * .75, BOX[1] - 70, BOX[0] + BOX[2] * .75, BOX[1] + 70),
                   skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*AMBER, .10),
                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
    return s.makeImageSnapshot()
BG = background()

def caption(c, t):
    for st, en, txt in CAPT:
        if st <= t <= en:
            a = ss((t - st) / 0.12) * ss((en - t) / 0.12)
            sh = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .75 * a),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7))
            w = F_CAP.measureText(txt)
            c.drawString(txt, W / 2 - w / 2, CAP_Y + 3, F_CAP, sh)
            text(c, txt, W / 2, CAP_Y, F_CAP, CREAM, a)

def end_card(c, a):
    if a <= 0: return
    cw, ch = (900, 330) if LAND else (780, 300)
    cy0 = H / 2 - ch / 2 - (40 if LAND else 60)
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(0.03, 0.025, 0.02, .85 * a)))
    card = skia.RRect.MakeRectXY(skia.Rect(W / 2 - cw / 2, cy0, W / 2 + cw / 2, cy0 + ch), 34, 34)
    c.drawRRect(card.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6 * a),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
    c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.09, .075, .06, .95 * a)))
    c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                Color4f=skia.Color4f(*AMBER, .45 * a)))
    dy = 12 * (1 - a)
    text(c, "Subscribe", W / 2, cy0 + 118 + dy, font(TF_SERIF, 80), CREAM, a)
    text(c, "@whatiffun", W / 2, cy0 + 205 + dy, font(TF_SERIF_I, 80), AMBER, a)
    text(c, "for more what-ifs", W / 2, cy0 + 262 + dy, font(TF_SERIF_I, 42), CREAM, .6 * a)

def shot_at(t):
    k = max(i for i, s in enumerate(CUT) if s <= t + 1e-9); return k

surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
def frame(t):
    with surf as c:
        c.drawImage(BG, 0, 0)
        k = shot_at(t)
        u = ss((t - CUT[k]) / XF) if k > 0 else 1
        if u < 1:   # crossfade from the previous shot
            c.saveLayerAlpha(None, int(255 * max(0, 1 - 2 * u))); SHOTS[k - 1](c, t - CUT[k - 1]); c.restore()
        c.saveLayerAlpha(None, int(255 * min(1, 2 * u) if u < 1 else 255)); SHOTS[k](c, t - CUT[k]); c.restore()
        caption(c, t)
        if LAND: text(c, "@whatiffun", W - 70, H - 50, F_MARK, CREAM, .42, "right")
        else: text(c, "@whatiffun", W / 2, 1625, F_MARK, CREAM, .42)
        end_card(c, ss((t - CARD) / 0.5))
    return surf

OUT = os.path.join(HERE, f"eiffel-bones-{FMT}")
if ONLY:
    for t in ONLY:
        frame(t).makeImageSnapshot().save(f"{OUT}-t{t:05.2f}.png", skia.kPNG); print("still", t)
    sys.exit()

# ---------------- video ----------------
N = int(round(END * FPS)); tmp = OUT + "_v.tmp.mp4"
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                      "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
for i in range(N):
    p.stdin.write(frame(i / FPS).makeImageSnapshot().toarray().tobytes())
p.stdin.close(); assert p.wait() == 0

# ---------------- sound: voice + beds + soft cues ----------------
rng = np.random.default_rng(7)
def thud(f0=62, dur=.5):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * (f0 * t + 30 * (1 - np.exp(-t * 18)) / 18)) * np.exp(-t * 9) * np.minimum(1, t * 4000)
def mallet(f0, dur=1.4):
    t = np.arange(int(dur * SR)) / SR
    return ((np.sin(2 * np.pi * f0 * t) * np.exp(-t * 3.2) + .4 * np.sin(2 * np.pi * f0 * 3.93 * t) * np.exp(-t * 9))
            * np.minimum(1, t * 3000))
def swish(dur=.35):
    t = np.arange(int(dur * SR)) / SR; n = rng.standard_normal(len(t))
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, [500, 3000], "bandpass", fs=SR, output="sos"), n) * np.sin(np.pi * t / dur) ** 2
sfx = np.zeros(int((END + 1) * SR))
def add(sig, t0, g):
    i = int(t0 * SR); s = sig[:len(sfx) - i]; sfx[i:i + len(s)] += s * g
for tc in CUT[1:]: add(swish(), tc - 0.05, .05); add(thud(), tc, .16)
notes = [392.0, 440.0, 523.25, 587.33, 659.25, 783.99]
for k, wi in enumerate([14, 38, 43, 61, 67]): add(mallet(notes[k % len(notes)]), ws(wi), .10)
for k in range(24): add(mallet(notes[k % 3 + 2] * 2, .5), ws(67) - 0.35 + k * 0.06, .018)
add(mallet(523.25, 2.5), CARD, .1); add(mallet(659.25, 2.5), CARD + .08, .08); add(mallet(783.99, 2.5), CARD + .16, .07)
sfx_path = OUT + "_sfx.wav"
with wave.open(sfx_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(sfx, -1, 1) * 32767).astype(np.int16).tobytes())
voice = os.path.join(HERE, "..", "narration-george-continuous.mp3")
music = os.path.join(HERE, "..", "music-bed.wav"); air = os.path.join(HERE, "..", "air-bed.wav")
mix = OUT + "_mix.wav"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-i", music, "-i", air, "-i", sfx_path, "-filter_complex",
    f"[0:a]aresample={SR},adelay={int(LEAD * 1000)}:all=1,apad[v];"
    f"[1:a]aresample={SR},volume=0.12,afade=t=out:st={END - 1.5}:d=1.5[m];"
    f"[2:a]aresample={SR},volume=0.05[a];[3:a]volume=1.0[s];"
    f"[v][m][a][s]amix=inputs=4:normalize=0:duration=first,atrim=0:{END},"
    "loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.7dB,aresample=48000[out]", "-map", "[out]", "-ac", "2", mix], check=True)
final = OUT + ".mp4"; tmpf = OUT + ".tmp.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmpf], check=True)
os.replace(tmpf, final); os.remove(tmp); os.remove(sfx_path); os.remove(mix)
print("wrote", final, END)
