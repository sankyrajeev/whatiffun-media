"""Builds the stickman-video-director (B1, native 9:16) project.json for
"What if the Eiffel Tower was made of human bones?" from the narration's per-line timings.
Design plane: 1280 x 2275.56. Content lives in y 200..1700 (caption band below)."""
import json, os, sys
from PIL import ImageFont

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/story/eiffel-project"
FONT = os.path.expanduser("~/.claude/skills/directing-stickman-videos/assets/fonts/Caveat.ttf")
LEAD = 0.15
LINES = [  # (start, dur, caption) from the vidIQ voiceover job (George)
    (0.0, 1.881, "What if the Eiffel Tower"), (1.881, 2.038, "was made of human bones?"),
    (3.918, 1.802, "The real tower is"), (5.721, 3.396, "7,300 tonnes of iron."),
    (9.117, 2.508, "Bone is about four times lighter."), (11.624, 2.351, "Built in the same shape from bone,"),
    (13.976, 3.004, "it would weigh about 1,800 tonnes."), (16.980, 3.553, "That's about 250,000 skeletons."),
    (20.532, 1.646, "Where would Paris get them?"), (22.178, 1.881, "Right under its streets."),
    (24.059, 2.273, "The Catacombs hold the bones"), (26.331, 1.959, "of six million people."),
    (28.291, 2.586, "That's enough for 24 towers."), (30.877, 1.802, "So, would it stand?"),
    (32.679, 2.926, "Pound for pound, bone is nearly"), (35.605, 2.351, "as strong as the tower's iron."),
    (37.956, 1.724, "But it's much bendier,"), (39.680, 2.038, "so it would sway in the wind."),
    (41.718, 2.691, "And the rain would slowly rot it away."), (44.408, 2.273, "Follow for more what-ifs."),
]
VOICE = 46.680
TAIL = 0.6
END = round(LEAD + VOICE + TAIL, 3)
def T(i): return round(LEAD + LINES[i][0], 3)
import math
def fl(x): return math.floor(x * 100) / 100

SIZES = {"catacombs.png": (1000, 1362), "lift-iron-vs-bone.png": (1000, 1240), "skeleton-queue.png": (789, 1400),
         "tower-bones.png": (766, 1400), "tower-iron.png": (691, 1400), "tower-rain.png": (625, 1400),
         "tower-sway.png": (785, 1400)}
def img_h(name, w): sw, sh = SIZES[name]; return w * sh / sw

def tw(text, size): return ImageFont.truetype(FONT, size).getlength(text) * 1.04
def ctext(id_, text, y, size, color=None, frm=None, to=None, bold=True):
    l = {"type": "text", "id": id_, "text": text, "x": round(640 - tw(text, size) / 2, 1) - 40, "y": y,
         "w": round(tw(text, size) + 40, 1), "size": size, "bold": bold}
    l["x"] = max(90, l["x"] + 40)
    if color: l["color"] = color
    if frm is not None: l["from"] = frm
    if to is not None: l["to"] = to
    return l
def image(id_, name, x, y, w, keys, reason, role="prop", frm=None, to=None):
    l = {"type": "image", "id": id_, "path": f"art/{name}", "x": x, "y": y, "w": w, "h": round(img_h(name, w), 1),
         "motion": {"role": role, "reason": reason}, "keys": keys}
    if frm is not None: l["from"] = frm
    if to is not None: l["to"] = to
    return l
def sway(dur, x, y, amp=0.02, period=1.6, extra=None):
    ks, t, s = [], 0.0, 1
    while t < dur - 0.15:
        k = {"t": round(t, 2), "angle": round(s * amp, 4), "x": x, "y": y}
        if extra: k.update(extra(t))
        ks.append(k); t += period / 2; s = -s
    ks.append({"t": fl(dur), "angle": 0, "x": x, "y": y}); return ks
def region(id_, role, ids, x, y, w, h, intent):
    x = max(78, x); y = max(184, y); w = min(w, 1125 - x); h = min(h, 1675 - y)
    return {"id": id_, "role": role, "layer_ids": ids, "region": {"x": x, "y": y, "w": w, "h": h}, "intent": intent}

shots = []
def shot(start, end, layers, regions, intent):
    shots.append({"start": round(start, 3), "end": round(end, 3), "layers": layers,
                  "portrait": {"intent": intent, "regions": regions}})

# 1 — hook: the bone tower rises into frame under the question
s, e = 0, T(2); d = e - s
shot(s, e, [
    ctext("s1-whatif", "WHAT IF...", 230, 150, "#EC4338"),
    ctext("s1-q", "THE EIFFEL TOWER", 400, 96), ctext("s1-q2", "WAS MADE OF BONES?", 500, 96, frm=1.8),
    image("s1-tower", "tower-bones.png", 410, 640, 460,
          [{"t": 0, "y": 760, "alpha": 0}, {"t": 0.6, "y": 640, "alpha": 1}, {"t": 1.4, "angle": 0.02, "y": 640},
           {"t": 2.4, "angle": -0.02, "y": 640}, {"t": fl(d), "angle": 0, "y": 640}],
          "The bone tower rises into view as the question is asked"),
], [region("r1-head", "information", ["s1-whatif", "s1-q", "s1-q2"], 90, 220, 1030, 380, "Question stacked at the top, the red WHAT IF read first"),
    region("r1-tower", "prop", ["s1-tower"], 340, 610, 600, 1065, "Full bone tower below the question with its rise and sway")],
  "Question on top, the impossible tower filling the lower picture")

# 2 — the real tower: 7,300 tonnes of iron
s, e = T(2), T(4); d = e - s
shot(s, e, [
    ctext("s2-real", "THE REAL ONE:", 240, 96),
    ctext("s2-iron", "7,300 TONNES OF IRON", 350, 96, "#EC4338", frm=1.6),
    image("s2-tower", "tower-iron.png", 445, 500, 400, sway(d, 445, 500, 0.012, 1.4), "The iron tower stands and settles"),
], [region("r2-head", "information", ["s2-real", "s2-iron"], 90, 230, 1030, 230, "Heading then the tonnage when it is spoken"),
    region("r2-tower", "prop", ["s2-tower"], 380, 480, 540, 1195, "The iron tower occupies the picture")],
  "Real iron tower with its weight revealed on the spoken number")

# 3 — bone is four times lighter
s, e = T(4), T(5); d = e - s
shot(s, e, [
    ctext("s3-h", "BONE = 4× LIGHTER", 260, 104),
    image("s3-lift", "lift-iron-vs-bone.png", 150, 470, 900,
          [{"t": 0, "y": 500, "angle": 0}, {"t": 0.5, "y": 470, "angle": -0.015}, {"t": 1.0, "y": 485, "angle": 0.012},
           {"t": 1.6, "y": 470, "angle": -0.01}, {"t": fl(d), "y": 478, "angle": 0}], "The two lifters strain and bob", role="actor"),
], [region("r3-head", "information", ["s3-h"], 90, 250, 1030, 140, "One comparison line"),
    region("r3-lift", "actor", ["s3-lift"], 120, 440, 960, 1180, "Strain vs easy lift, the whole comparison visible")],
  "Comparison heading above the iron-vs-bone lift")

# 4 — same shape in bone: ~1,800 tonnes
s, e = T(5), T(7); d = e - s
shot(s, e, [
    ctext("s4-h", "SAME SHAPE, IN BONE:", 240, 96),
    ctext("s4-n", "≈ 1,800 TONNES", 350, 110, "#EC4338", frm=2.3),
    image("s4-iron", "tower-iron.png", 140, 560, 260,
          [{"t": 0, "alpha": 1, "x": 140}, {"t": 1.2, "alpha": 0.25, "x": 120}, {"t": fl(d), "alpha": 0.25, "x": 120}],
          "The iron tower fades back as the bone version takes over"),
    image("s4-bone", "tower-bones.png", 600, 520, 330,
          [{"t": 0, "alpha": 0, "y": 600}, {"t": 1.0, "alpha": 1, "y": 520}, {"t": 2.2, "angle": 0.015, "y": 520},
           {"t": 3.4, "angle": -0.015, "y": 520}, {"t": fl(d), "angle": 0, "y": 520}], "The bone tower rises beside the fading iron one"),
], [region("r4-head", "information", ["s4-h", "s4-n"], 90, 230, 1030, 250, "Shape statement, then the new weight"),
    region("r4-towers", "prop", ["s4-iron", "s4-bone"], 100, 500, 980, 1180, "Iron fades left while bone rises right")],
  "Side-by-side swap from iron to bone with the weight landing late")

# 5 — about 250,000 skeletons
s, e = T(7), T(8); d = e - s
shot(s, e, [
    ctext("s5-n", "≈ 250,000", 230, 150, "#EC4338"),
    ctext("s5-s", "SKELETONS", 400, 104),
    image("s5-queue", "skeleton-queue.png", 310, 560, 600,
          [{"t": 0, "y": 600, "alpha": 0}, {"t": 0.6, "y": 560, "alpha": 1}, {"t": 1.6, "y": 548, "angle": 0.01},
           {"t": 2.6, "y": 560, "angle": -0.01}, {"t": fl(d), "y": 552, "angle": 0}], "The queue of skeletons shuffles forward", role="actor"),
], [region("r5-head", "information", ["s5-n", "s5-s"], 90, 220, 1030, 300, "Big number first"),
    region("r5-queue", "actor", ["s5-queue"], 260, 540, 700, 1150, "Endless friendly queue")],
  "Number on top, the winding queue below")

# 6 — where would Paris get them? right under its streets
s, e = T(8), T(10); d = e - s
shot(s, e, [
    ctext("s6-q", "WHERE FROM?", 260, 120),
    ctext("s6-a", "UNDER THE STREETS", 420, 96, "#EC4338", frm=1.6),
    image("s6-cat", "catacombs.png", 290, 640, 700,
          [{"t": 0, "y": 720, "alpha": 0}, {"t": 1.6, "y": 720, "alpha": 0}, {"t": 2.6, "y": 640, "alpha": 1},
           {"t": fl(d), "y": 630, "alpha": 1}], "The catacomb tunnel rises up from below the street line"),
    {"type": "line", "id": "s6-street", "points": [[110, 560], [1120, 560]], "color": "#191916", "lineWidth": 4,
     "motion": {"role": "information", "reason": "The street line draws across before the tunnel appears beneath it"},
     "keys": [{"t": 0, "progress": 0}, {"t": 1.2, "progress": 1}]},
], [region("r6-head", "information", ["s6-q", "s6-a", "s6-street"], 90, 250, 1040, 330, "Question, street line, then the answer"),
    region("r6-cat", "prop", ["s6-cat"], 190, 580, 840, 1140, "Tunnel emerging below the street")],
  "Street line drawn, then the catacombs revealed beneath it")

# 7 — the Catacombs hold six million; enough for 24 towers (sequential build of 24 mini towers)
s, e = T(10), T(13); d = e - s
mini = []
for k in range(24):
    r_, c_ = divmod(k, 8)
    t0 = round(T(12) - s + k * 0.075, 2)
    mini.append(image(f"s7-m{k}", "tower-bones.png", 130 + c_ * 125, 1090 + r_ * 200, 100,
                      [{"t": t0, "alpha": 0, "y": 1070 + r_ * 200}, {"t": round(t0 + 0.3, 2), "alpha": 1, "y": 1090 + r_ * 200}],
                      "Mini towers stack up one by one as 24 is spoken", frm=t0))
shot(s, e, [
    ctext("s7-n", "6,000,000 PEOPLE", 240, 110, "#EC4338"),
    ctext("s7-t", "= 24 BONE TOWERS", 370, 96, frm=round(T(12) - s, 2)),
    image("s7-cat", "catacombs.png", 430, 470, 420,
          [{"t": 0, "angle": 0}, {"t": 1.2, "angle": 0.015}, {"t": 2.4, "angle": -0.015},
           {"t": round(T(12) - s, 2), "angle": 0}, {"t": fl(d), "angle": 0.01}],
          "The explorer's tunnel holds while the number is spoken", role="actor"),
] + mini, [region("r7-head", "information", ["s7-n", "s7-t"], 90, 230, 1040, 270, "Population, then the tower count"),
           region("r7-cat", "actor", ["s7-cat"], 400, 450, 480, 620, "Catacomb tunnel with the explorer"),
           region("r7-minis", "information", [f"s7-m{k}" for k in range(24)], 110, 1060, 1010, 615, "24 mini towers building left to right")],
  "Number, tunnel, then a counted grid of 24 bone towers")

# 8 — would it stand? nearly as strong pound for pound
s, e = T(13), T(16); d = e - s
shot(s, e, [
    ctext("s8-q", "WOULD IT STAND?", 240, 120),
    ctext("s8-a", "ALMOST AS STRONG", 400, 96, "#EC4338", frm=round(T(14) - s + 0.5, 2)),
    ctext("s8-b", "AS IRON, POUND FOR POUND", 500, 76, frm=round(T(15) - s, 2)),
    image("s8-lift", "lift-iron-vs-bone.png", 610, 980, 440,
          [{"t": 0, "alpha": 0, "x": 560}, {"t": 0.8, "alpha": 1, "x": 610}, {"t": 2.2, "angle": -0.02, "x": 610},
           {"t": 3.6, "angle": 0.02, "x": 610}, {"t": 5.0, "angle": -0.015, "x": 610}, {"t": fl(d), "angle": 0, "x": 610}],
          "The lifters reappear to test strength", role="actor"),
    image("s8-tower", "tower-bones.png", 150, 620, 380, sway(d, 150, 620, 0.02, 1.5), "The bone tower wobbles while the strength is judged"),
], [region("r8-head", "information", ["s8-q", "s8-a", "s8-b"], 90, 230, 1040, 370, "Question, then the verdict in two parts"),
    region("r8-pics", "actor", ["s8-lift", "s8-tower"], 110, 590, 1010, 1085, "Wobbling tower beside the strength test")],
  "Strength question with the verdict building line by line")

# 9 — much bendier, sways in the wind
s, e = T(16), T(18); d = e - s
shot(s, e, [
    ctext("s9-h", "BUT IT BENDS", 250, 120, "#EC4338"),
    image("s9-sway", "tower-sway.png", 320, 470, 620, sway(d, 340, 480, 0.05, 0.9), "The tower sways hard in the wind while the man braces", role="actor"),
], [region("r9-head", "information", ["s9-h"], 90, 230, 1040, 160, "Single warning line"),
    region("r9-sway", "actor", ["s9-sway"], 100, 400, 1020, 1275, "Big sway with the worried stickman bracing")],
  "Warning on top, a big visible sway below")

# 10 — rain would rot it away
s, e = T(18), T(19); d = e - s
shot(s, e, [
    ctext("s10-h", "AND RAIN ROTS BONE", 250, 104),
    image("s10-rain", "tower-rain.png", 390, 440, 500,
          [{"t": 0, "y": 440, "angle": 0}, {"t": 0.9, "y": 455, "angle": 0.012}, {"t": 1.8, "y": 468, "angle": -0.012},
           {"t": fl(d), "y": 480, "angle": 0.008}], "The tower slumps as the rain eats its legs"),
], [region("r10-head", "information", ["s10-h"], 90, 240, 1040, 150, "The rain warning heading above the picture"),
    region("r10-rain", "prop", ["s10-rain"], 300, 410, 700, 1265, "Rain cloud and crumbling legs fully visible")],
  "Rain and crumbling tower below the line")

# 11 — follow
s, e = T(19), END; d = e - s
shot(s, e, [
    ctext("s11-f", "FOLLOW FOR MORE", 260, 110),
    ctext("s11-w", "WHAT-IFS", 390, 150, "#EC4338"),
    ctext("s11-h", "@whatiffun", 1500, 80, bold=False),
    image("s11-tower", "tower-bones.png", 450, 580, 380, sway(d, 450, 580, 0.03, 1.0), "The bone tower waves goodbye"),
], [region("r11-head", "information", ["s11-f", "s11-w"], 90, 250, 1040, 330, "Call to follow"),
    region("r11-tower", "prop", ["s11-tower", "s11-h"], 330, 560, 640, 1100, "Tower with the handle beneath")],
  "Follow call with the tower and handle")

captions = []
for i, (st, du, txt) in enumerate(LINES):
    nxt = LINES[i + 1][0] if i + 1 < len(LINES) else st + du
    captions.append({"start": round(LEAD + st + 0.02, 3), "end": round(LEAD + min(st + du, nxt) - 0.03, 3), "text": txt})

sfx = []
for t_, kind in [(T(0), "pop"), (T(3), "tap"), (T(5) + 1.0, "paper"), (T(7) + 0.6, "pop"), (T(9) + 1.0, "paper"),
                 (T(12), "chime"), (T(14), "tap"), (T(16) + 0.3, "paper"), (T(19), "chime")]:
    sfx.append({"time": round(t_, 3), "kind": kind, "gain": 0.03})

project = {
    "version": 1, "style": "B1", "width": 1080, "height": 1920, "fps": 30,
    "voice": {"path": "audio/narration.wav", "lead": LEAD, "tail": TAIL},
    "music": {"path": "audio/music-bed.wav", "gain": 0.12},
    "portrait": {"safe_area": {"left": 0.06, "right": 0.12, "top": 0.08, "bottom": 0.18}},
    "captions": captions, "shots": shots, "sfx": sfx,
    "ambience": [{"path": "audio/air-bed.wav", "start": 0, "end": END, "gain": 0.05, "fadeIn": 0.5, "fadeOut": 1.0}],
    "reference_review": {"author_id": "claude-whatiffun", "capability": {"mode": "limited", "environment": "cloud workspace, vidIQ images + voice",
        "limitations": ["Approved Ryan V4 and portrait reference clips were not played back with sound by an independent reviewer",
                        "Character art is generated per scene, not a hand-built pose sheet; local motion is whole-drawing keyframes"]}},
}
json.dump(project, open(os.path.join(P, "project.json"), "w"), indent=1, ensure_ascii=False)
print("shots", len(shots), "end", END, "captions", len(captions))
