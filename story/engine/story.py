"""whatiffun story-video engine: one story.json -> native 16:9 (YouTube) and 9:16 (Shorts/Reels) videos.

    python3 story/engine/story.py prep   story/<slug>                # art/raw/*.png -> art/*.png (trim + cream sticker outline)
    python3 story/engine/story.py stills story/<slug> 16x9 3.0,12.5  # preview frames -> <slug>/stills/
    python3 story/engine/story.py render story/<slug> 16x9           # -> <slug>/out/<slug>-16x9.mp4
    python3 story/engine/story.py render story/<slug> 9x16
    python3 story/engine/story.py thumb  story/<slug>                # -> <slug>/out/<slug>-thumb.jpg (1280x720)

story.json (all word indices refer to narration.words.json from the align-words workflow):
{
  "title": "What if the Eiffel Tower was made of human bones?",
  "voice": "narration.mp3", "words": "narration.words.json",
  "end": ["Subscribe", "@whatiffun", "for more what-ifs"],
  "thumb": {"l1": "EIFFEL TOWER", "l2": "MADE OF BONES?", "img": "tower-bones.png"},
  "word_fix": {"69": 28.08},          # optional: corrected start (s) for a word whisper timed badly
  "shots": [
    {"at": 0,                          # shot starts at this word (cut 0.22 s before it); or "at_s": seconds
     "kicker": "WHAT IF", "l1": "The Eiffel Tower", "l2": "was made of bones?", "l2_at": 5,
     "num": "7,300 tonnes", "num_at": 14,          # optional big amber number, pops in on that word (+ a soft note)
     "art": [{"img": "tower-bones.png", "h": 0.98, "x": 0.0, "y": 0.0,
              "move": "sway", "amp": 0.012, "per": 3.2,          # sway | bob | pulse | sink | none
              "enter": "rise", "in_at": null, "out_at": null, "dim_at": null,
              "grid": null}]}                   # grid: {"n": 24, "cols": 8, "h": 0.3} pops n copies at in_at
  ]
}
x / y / h are fractions of the stage height (x>0 right, y>0 down). Groups that are too wide are scaled to fit each format.
"""
import json, math, os, re, subprocess, sys, wave
import numpy as np, skia
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FPS, SR = 30, 48000
CREAM, AMBER = (0.96, 0.92, 0.84), (0.88, 0.64, 0.30)
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
FD = os.path.join(ROOT, "fonts") + "/"
TF_SERIF = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Regular.ttf")
TF_SERIF_I = skia.Typeface.MakeFromFile(FD + "InstrumentSerif-Italic.ttf")
TF_SEMI = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf")
TF_XB = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
def font(tf, s):
    f = skia.Font(tf, s); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True); return f
def ss(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def eob(u): u = min(1, max(0, u)); c = 1.4; return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2
LEAD, XF = 0.30, 0.40

# ======================= art prep =======================
def prep(d):
    src, dst = os.path.join(d, "art", "raw"), os.path.join(d, "art")
    for f in sorted(os.listdir(src)):
        if not f.lower().endswith(".png"): continue
        im = Image.open(os.path.join(src, f)).convert("RGBA")
        a = np.asarray(im)[..., 3]
        if a.min() > 200:   # no transparency came back: key out a flat light/white background
            rgb = np.asarray(im)[..., :3].astype(int); bg = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), 0)
            dist = np.abs(rgb - bg).sum(-1); alpha = np.clip((dist - 18) * 8, 0, 255).astype(np.uint8)
            im.putalpha(Image.fromarray(alpha))
        im = im.crop(im.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox())
        if max(im.size) > 1500: im.thumbnail((1500, 1500), Image.LANCZOS)
        W, H = im.size; pad = 24
        big = Image.new("RGBA", (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0)); big.paste(im, (pad, pad), im)
        mask = big.split()[3].point(lambda v: 255 if v > 40 else 0)
        ring = mask.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(1.2))
        st = Image.new("RGBA", big.size, (245, 235, 214, 0)); st.putalpha(ring)
        Image.alpha_composite(st, big).save(os.path.join(dst, f)); print("prepped", f, big.size)

# ======================= story model =======================
class Story:
    def __init__(self, d, fmt):
        self.d, self.fmt = d, fmt
        self.s = json.load(open(os.path.join(d, "story.json")))
        self.slug = os.path.basename(os.path.abspath(d))
        self.words = json.load(open(os.path.join(d, self.s.get("words", "narration.words.json"))))["words"]
        for k, v in self.s.get("word_fix", {}).items(): self.words[int(k)]["start"] = v
        self.voice = os.path.join(d, self.s.get("voice", "narration.mp3"))
        self.vdur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                          self.voice], capture_output=True, text=True).stdout)
        self.land = fmt == "16x9"
        self.W, self.H = (1920, 1080) if self.land else (1080, 1920)
        # stage: centre x, floor y, height, allowed width
        self.box = (1380, 935, 800, 900) if self.land else (540, 1450, 860, 860)
        self.cuts = [self.cut_t(sh) for sh in self.s["shots"]]; self.cuts[0] = 0.0
        self.card = LEAD + self.vdur + 0.25
        self.end = round(self.card + 2.6, 2)
        self.caps = self.captions()
        self.art_cache = {}
    def ws(self, i): return LEAD + self.words[i]["start"]
    def we(self, i): return LEAD + self.words[i]["end"]
    def cut_t(self, sh): return LEAD + sh["at_s"] if "at_s" in sh else self.ws(sh["at"]) - 0.22
    def wt(self, i, t0):   # word index -> shot-local time
        return None if i is None else self.ws(i) - t0

    def captions(self):
        toks = []   # merge whisper's split numbers (",300") into the previous token
        for i, w in enumerate(self.words):
            txt = w["word"].strip()
            if toks and re.match(r"^[,.]?\d", txt) and re.search(r"\d$", toks[-1][2]) or (toks and txt[:1] in ",.%" ):
                toks[-1] = (toks[-1][0], i, toks[-1][2] + txt)
            else: toks.append((i, i, txt))
        sents, cur = [], []      # sentences, then balanced pieces of <= ~34 chars (prefer breaking after commas)
        for tk in toks:
            cur.append(tk)
            if re.search(r"[.?!]$", tk[2]): sents.append(cur); cur = []
        if cur: sents.append(cur)
        chunks = []
        for se in sents:
            L = len(" ".join(t[2] for t in se)); n = max(1, math.ceil(L / 34))
            while n > 1 and len(se) < 2 * n: n -= 1
            pos, acc = [], 0
            for i, t in enumerate(se[:-1]): acc += len(t[2]) + 1; pos.append((acc, i, t[2].endswith(",")))
            cuts, last = [], -1
            for k in range(1, n):
                target = L * k / n
                best = min((p for p in pos if p[1] > last), key=lambda p: abs(p[0] - target) - (6 if p[2] else 0))
                bi = best[1]
                while bi - 1 > last and se[bi][2].lower() in ("the", "a", "an", "and", "of", "to", "in", "its", "his", "her", "their"): bi -= 1
                cuts.append(bi); last = bi
            prev = 0
            for c_ in cuts + [len(se) - 1]: chunks.append(se[prev:c_ + 1]); prev = c_ + 1
        caps = []
        for k, ch in enumerate(chunks):
            st = self.ws(ch[0][0]) - 0.08
            nx = self.ws(chunks[k + 1][0][0]) - 0.14 if k + 1 < len(chunks) else 1e9
            caps.append((st, min(self.we(ch[-1][1]) + 0.45, nx), " ".join(t[2] for t in ch)))
        return caps

    # ---------------- drawing helpers ----------------
    def img(self, name):
        if name not in self.art_cache:
            im = Image.open(os.path.join(self.d, "art", name)).convert("RGBA")
            a = np.asarray(im).astype(np.float32) / 255; a[..., :3] *= a[..., 3:4]
            self.art_cache[name] = skia.Image.fromarray((a * 255).astype(np.uint8), colorType=skia.kRGBA_8888_ColorType,
                                                         alphaType=skia.kPremul_AlphaType)
        return self.art_cache[name]
    def aspect(self, name): i = self.img(name); return i.width() / i.height()
    def fit_scale(self, arts):
        bx, by, bh, bw = self.box; lo, hi = 1e9, -1e9
        for a in arts:
            if a.get("grid"):
                g = a["grid"]; cols = g.get("cols", 8); hh = g.get("h", .3)
                w = (cols - 1) * hh * self.aspect(a["img"]) * 1.15 + hh * self.aspect(a["img"])
                lo, hi = min(lo, -w / 2), max(hi, w / 2); continue
            w = a.get("h", .95) * self.aspect(a["img"]); x = a.get("x", 0)
            lo, hi = min(lo, x - w / 2), max(hi, x + w / 2)
        span = (hi - lo) * bh
        return min(1.0, bw / span) if span > 0 else 1.0, (lo + hi) / 2
    def draw_img(self, c, name, h, x, y, ang, alpha, sc):
        if alpha <= 0.003: return
        im = self.img(name); bx, by, bh, _ = self.box
        hh = bh * h * sc; ww = hh * im.width() / im.height()
        c.save(); c.translate(bx + x * bh, by + y * bh); c.rotate(math.degrees(ang))
        p = skia.Paint(AntiAlias=True); p.setAlphaf(min(1, alpha))
        c.drawImageRect(im, skia.Rect(-ww / 2, -hh, ww / 2, 0), SAMP, p); c.restore()
    def shadow(self, c, wf, alpha, x):
        bx, by, bh, _ = self.box
        if alpha <= 0.01: return
        c.drawOval(skia.Rect(bx + x * bh - bh * wf / 2, by - 20, bx + x * bh + bh * wf / 2, by + 20),
                   skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .5 * alpha),
                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
    def text(self, c, s, x, y, f, rgb, a=1.0, align="center", spacing=0.0):
        if a <= 0.003 or not s: return
        p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*rgb, a))
        wl = [f.measureText(ch) for ch in s] if spacing else None
        w = (sum(wl) + spacing * (len(s) - 1)) if spacing else f.measureText(s)
        if align == "center": x -= w / 2
        elif align == "right": x -= w
        if not spacing: c.drawString(s, x, y, f, p); return
        for ch, cw in zip(s, wl): c.drawString(ch, x, y, f, p); x += cw + spacing
    def fitted(self, tf, size, s, maxw):
        f = font(tf, size)
        while f.measureText(s) > maxw and size > 40: size -= 4; f = font(tf, size)
        return f

    # ---------------- one shot ----------------
    def draw_shot(self, c, k, t):
        sh = self.s["shots"][k]; t0 = self.cuts[k]
        land = self.land
        TX, AL = (150, "left") if land else (self.W / 2, "center")
        KY, L1Y, L2Y, NY = (330, 455, 575, 720) if land else (250, 355, 455, 575)
        maxw = 790 if land else 940
        hs, ns = (118, 150) if land else (104, 124)
        def line(s, y, f, rgb, at, pop=False, spacing=0.0, a=1.0):
            if not s or at is None: return
            u = ss((t - at) / 0.35)
            if u <= 0: return
            dy = 18 * (1 - u)
            if pop:
                kk = 0.85 + 0.15 * eob((t - at) / 0.45); w = f.measureText(s)
                ax = TX + (w / 2 if AL == "left" else 0); ay = y - f.getSize() * .35
                c.save(); c.translate(ax, ay); c.scale(kk, kk); c.translate(-ax, -ay)
                self.text(c, s, TX, y + dy, f, rgb, u * a, AL, spacing); c.restore()
            else: self.text(c, s, TX, y + dy, f, rgb, u * a, AL, spacing)
        line(sh.get("kicker", "").upper(), KY, font(TF_SEMI, 30), AMBER, 0.0, spacing=7)
        line(sh.get("l1"), L1Y, self.fitted(TF_SERIF, hs, sh.get("l1", ""), maxw), CREAM, 0.08)
        l2at = self.wt(sh.get("l2_at"), t0); l2at = 0.16 if l2at is None else l2at
        line(sh.get("l2"), L2Y, self.fitted(TF_SERIF_I, hs, sh.get("l2", ""), maxw), CREAM, l2at, a=.92)
        if sh.get("num"):
            line(sh["num"], NY, self.fitted(TF_SERIF, ns, sh["num"], maxw), AMBER, self.wt(sh.get("num_at"), t0) or 0.3, pop=True)
        arts = sh.get("art", [])
        sc, cx = self.fit_scale(arts) if arts else (1, 0)
        for j, a in enumerate(arts):
            tin = self.wt(a.get("in_at"), t0) or 0.0
            tout = self.wt(a.get("out_at"), t0); tdim = self.wt(a.get("dim_at"), t0)
            alpha = 1.0
            if tout is not None: alpha *= 1 - ss((t - tout + 0.3) / 0.5)
            if tdim is not None: alpha *= 1 - .7 * ss((t - tdim) / 0.8)
            mv, amp, per = a.get("move", "sway"), a.get("amp", .012), a.get("per", 2.8)
            ang, dy, k2 = 0.0, 0.0, 1.0
            ph = j * 1.3
            if mv == "sway": ang = amp * math.sin(2 * math.pi * t / per + ph)
            elif mv == "bob": dy = amp * math.sin(2 * math.pi * t / per + ph)
            elif mv == "pulse": k2 = 1 + amp * math.sin(2 * math.pi * t / per + ph)
            elif mv == "sink": dy = amp * ss(t / per)
            x = (a.get("x", 0) - cx) * sc; y = a.get("y", 0) * sc; h = a.get("h", .95)
            if a.get("grid"):
                g = a["grid"]; n, cols, gh = g.get("n", 24), g.get("cols", 8), g.get("h", .3)
                rows = math.ceil(n / cols); gw = gh * self.aspect(a["img"]) * 1.15
                for q in range(n):
                    r, col = divmod(q, cols); tq = tin - 0.35 + q * min(0.06, 1.4 / n); u = ss((t - tq) / 0.25)
                    if u <= 0: continue
                    ox = ((col - (cols - 1) / 2) * gw - cx) * sc; oy = -(rows - 1 - r) * gh * 1.1 * sc
                    self.draw_img(c, a["img"], gh, ox, oy + (1 - u) * .04,
                                  .02 * math.sin(2 * math.pi * t / 1.8 + q), u * alpha, sc)
                continue
            en = a.get("enter", "rise"); ue = ss((t - tin) / 0.7)
            if en == "none": ue = 1.0 if t >= tin else 0.0
            if en == "rise": y += (1 - ue) * .08
            if en == "pop": k2 *= 0.8 + 0.2 * eob((t - tin) / 0.5)
            self.shadow(c, h * self.aspect(a["img"]) * .8 * sc, ue * alpha, x)
            self.draw_img(c, a["img"], h * k2, x, y + dy, ang, ue * alpha, sc)

    # ---------------- frame ----------------
    def background(self):
        W, H = self.W, self.H; bx, by, bh, _ = self.box
        s = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(W, H))
        with s as c:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
                (bx, by - bh * .45), max(W, H) * .95, [skia.Color(34, 27, 20), skia.Color(15, 12, 10), skia.Color(7, 6, 5)], [0, .5, 1])))
            c.drawOval(skia.Rect(bx - bh * .75, by - 70, bx + bh * .75, by + 70),
                       skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*AMBER, .10),
                                  MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
        return s.makeImageSnapshot()
    def caption(self, c, t):
        f = font(TF_SEMI, 44 if self.land else 50); y = 1022 if self.land else 1540
        for st, en, txt in self.caps:
            if st <= t <= en:
                a = ss((t - st) / 0.12) * ss((en - t) / 0.12)
                ff = self.fitted(TF_SEMI, f.getSize(), txt, self.W - 220)
                w = ff.measureText(txt)
                c.drawString(txt, self.W / 2 - w / 2, y + 3, ff, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .75 * a),
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)))
                self.text(c, txt, self.W / 2, y, ff, CREAM, a)
    def end_card(self, c, a):
        if a <= 0: return
        W, H = self.W, self.H; e = self.s.get("end", ["Subscribe", "@whatiffun", "for more what-ifs"])
        cw, ch = (900, 330) if self.land else (780, 300)
        cy0 = H / 2 - ch / 2 - (40 if self.land else 60)
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Color4f=skia.Color4f(0.03, 0.025, 0.02, .85 * a)))
        card = skia.RRect.MakeRectXY(skia.Rect(W / 2 - cw / 2, cy0, W / 2 + cw / 2, cy0 + ch), 34, 34)
        c.drawRRect(card.makeOffset(0, 14), skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .6 * a),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26)))
        c.drawRRect(card, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(.09, .075, .06, .95 * a)))
        c.drawRRect(card, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5, Color4f=skia.Color4f(*AMBER, .45 * a)))
        dy = 12 * (1 - a)
        self.text(c, e[0], W / 2, cy0 + 118 + dy, font(TF_SERIF, 80), CREAM, a)
        self.text(c, e[1], W / 2, cy0 + 205 + dy, font(TF_SERIF_I, 80), AMBER, a)
        self.text(c, e[2], W / 2, cy0 + 262 + dy, font(TF_SERIF_I, 42), CREAM, .6 * a)
    def frame(self, surf, bg, t):
        with surf as c:
            c.drawImage(bg, 0, 0)
            k = max(i for i, s in enumerate(self.cuts) if s <= t + 1e-9)
            u = ss((t - self.cuts[k]) / XF) if k > 0 else 1
            if u < 1:
                c.saveLayerAlpha(None, int(255 * max(0, 1 - 2 * u))); self.draw_shot(c, k - 1, t - self.cuts[k - 1]); c.restore()
            c.saveLayerAlpha(None, int(255 * (min(1, 2 * u) if u < 1 else 1))); self.draw_shot(c, k, t - self.cuts[k]); c.restore()
            self.caption(c, t)
            if self.land: self.text(c, "@whatiffun", self.W - 70, self.H - 50, font(TF_SERIF_I, 34), CREAM, .42, "right")
            else: self.text(c, "@whatiffun", self.W / 2, 1625, font(TF_SERIF_I, 34), CREAM, .42)
            self.end_card(c, ss((t - self.card) / 0.5))
        return surf

    # ---------------- outputs ----------------
    def outdir(self, sub="out"):
        p = os.path.join(self.d, sub); os.makedirs(p, exist_ok=True); return p
    def stills(self, times):
        surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(self.W, self.H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
        bg = self.background(); out = []
        for t in times:
            p = os.path.join(self.outdir("stills"), f"{self.fmt}-t{t:05.2f}.png")
            self.frame(surf, bg, t).makeImageSnapshot().save(p, skia.kPNG); out.append(p)
        print("\n".join(out))
    def render(self):
        W, H = self.W, self.H; base = os.path.join(self.outdir(), f"{self.slug}-{self.fmt}")
        surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
        bg = self.background(); N = int(round(self.end * FPS)); tmp = base + "_v.tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                              "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        for i in range(N): p.stdin.write(self.frame(surf, bg, i / FPS).makeImageSnapshot().toarray().tobytes())
        p.stdin.close(); assert p.wait() == 0
        mix = self.soundtrack(base)
        tmpf = base + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmpf], check=True)
        os.replace(tmpf, base + ".mp4"); os.remove(tmp); os.remove(mix)
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", base + ".mp4", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
        lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
        print("wrote", base + ".mp4", f"{self.end:.2f}s", "LUFS", lufs[-1] if lufs else "?")
    def soundtrack(self, base):
        rng = np.random.default_rng(7); n = int((self.end + 1) * SR); sfx = np.zeros(n)
        def add(sig, t0, g):
            i = int(t0 * SR)
            if 0 <= i < n: s = sig[:n - i]; sfx[i:i + len(s)] += s * g
        def thud(f0=62, dur=.5):
            t = np.arange(int(dur * SR)) / SR
            return np.sin(2 * np.pi * (f0 * t + 30 * (1 - np.exp(-t * 18)) / 18)) * np.exp(-t * 9) * np.minimum(1, t * 4000)
        def mallet(f0, dur=1.4):
            t = np.arange(int(dur * SR)) / SR
            return (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 3.2) + .4 * np.sin(2 * np.pi * f0 * 3.93 * t) * np.exp(-t * 9)) * np.minimum(1, t * 3000)
        from scipy.signal import butter, sosfilt
        def swish(dur=.35):
            t = np.arange(int(dur * SR)) / SR
            return sosfilt(butter(2, [500, 3000], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.sin(np.pi * t / dur) ** 2
        for tc in self.cuts[1:]: add(swish(), tc - 0.05, .05); add(thud(), tc, .16)
        notes = [392.0, 440.0, 523.25, 587.33, 659.25, 783.99]; k = 0
        for i, sh in enumerate(self.s["shots"]):
            if sh.get("num_at") is not None: add(mallet(notes[k % 6]), self.ws(sh["num_at"]), .10); k += 1
            for a in sh.get("art", []):
                if a.get("grid") and a.get("in_at") is not None:
                    g = a["grid"]; nn = g.get("n", 24)
                    for q in range(nn): add(mallet(notes[q % 3 + 2] * 2, .5), self.ws(a["in_at"]) - 0.35 + q * min(0.06, 1.4 / nn), .018)
        for j, f0 in enumerate([523.25, 659.25, 783.99]): add(mallet(f0, 2.5), self.card + .08 * j, .1 - .015 * j)
        sp = base + "_sfx.wav"
        with wave.open(sp, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(sfx, -1, 1) * 32767).astype(np.int16).tobytes())
        beds = os.path.join(ROOT, "story", "engine", "beds")
        mix = base + "_mix.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", self.voice, "-stream_loop", "-1", "-i", os.path.join(beds, "music-bed.wav"),
                        "-stream_loop", "-1", "-i", os.path.join(beds, "air-bed.wav"), "-i", sp, "-filter_complex",
                        f"[0:a]aresample={SR},adelay={int(LEAD * 1000)}:all=1,apad[v];"
                        f"[1:a]aresample={SR},volume=0.12,atrim=0:{self.end},afade=t=out:st={self.end - 1.5}:d=1.5[m];"
                        f"[2:a]aresample={SR},volume=0.05,atrim=0:{self.end}[a];[3:a]volume=1.0[s];"
                        f"[v][m][a][s]amix=inputs=4:normalize=0:duration=first,atrim=0:{self.end},"
                        "loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.7dB,aresample=48000[out]", "-map", "[out]", "-ac", "2", mix], check=True)
        os.remove(sp); return mix
    def thumb(self):
        th = self.s.get("thumb", {}); W, H = 1280, 720
        surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
        with surf as c:
            c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
                (900, 330), 1100, [skia.Color(52, 38, 24), skia.Color(18, 14, 11), skia.Color(7, 6, 5)], [0, .5, 1])))
            if th.get("img"):
                im = self.img(th["img"]); hh = 660; ww = hh * im.width() / im.height()
                if ww > 560: ww = 560; hh = ww * im.height() / im.width()
                c.drawImageRect(im, skia.Rect(940 - ww / 2, 700 - hh, 940 + ww / 2, 700), SAMP, skia.Paint(AntiAlias=True))
            l1, l2 = th.get("l1", ""), th.get("l2", "")
            f1 = self.fitted(TF_XB, 112, l1, 640); f2 = self.fitted(TF_XB, 112, l2, 640)
            for s_, y, f, col in ((l1, 330, f1, CREAM), (l2, 460, f2, AMBER)):
                c.drawString(s_, 60, y + 6, f, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, .8),
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
                self.text(c, s_, 60, y, f, col, 1, "left")
        p = os.path.join(self.outdir(), f"{self.slug}-thumb.jpg")
        Image.fromarray(surf.makeImageSnapshot().toarray()[..., :3]).save(p, quality=92); print("wrote", p)

if __name__ == "__main__":
    cmd, d = sys.argv[1], sys.argv[2]
    if cmd == "prep": prep(d)
    elif cmd == "stills": Story(d, sys.argv[3]).stills([float(x) for x in sys.argv[4].split(",")])
    elif cmd == "render": Story(d, sys.argv[3]).render()
    elif cmd == "thumb": Story(d, "16x9").thumb()
