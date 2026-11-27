"""Gold bar cut-out drawn in code (no credits). Output: art/raw/gold-bar.png"""
from PIL import Image, ImageDraw
S = 4; W, H = 900 * S, 520 * S
im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
def P(pts): return [(x * S, y * S) for x, y in pts]
top = P([(200, 120), (700, 120), (820, 260), (80, 260)])          # top face (trapezoid seen from above-front)
front = P([(80, 260), (820, 260), (820, 420), (80, 420)])
side_l = None
ink = (30, 22, 14, 255); lw = 14 * S
d.polygon(front, fill=(214, 150, 38, 255)); d.polygon(top, fill=(248, 200, 70, 255))
d.polygon(P([(80, 260), (820, 260), (820, 300), (80, 300)]), fill=(236, 176, 52, 255))
for a, b in [((250, 140), (330, 140)), ((260, 150), (600, 240))]:
    pass
d.polygon(P([(300, 140), (420, 140), (330, 240), (210, 240)]), fill=(255, 236, 160, 255))   # shine streak
d.polygon(P([(470, 140), (520, 140), (430, 240), (380, 240)]), fill=(255, 228, 140, 255))
d.line(top + [top[0]], fill=ink, width=lw, joint="curve"); d.line(front + [front[0]], fill=ink, width=lw, joint="curve")
for cx, cy, r in [(720, 90, 34), (130, 200, 22)]:                 # sparkles
    d.polygon(P([(cx, cy - r), (cx + r * .25, cy - r * .25), (cx + r, cy), (cx + r * .25, cy + r * .25),
                 (cx, cy + r), (cx - r * .25, cy + r * .25), (cx - r, cy), (cx - r * .25, cy - r * .25)]), fill=(255, 246, 200, 255))
im.resize((W // S, H // S), Image.LANCZOS).save("art/raw/gold-bar.png")
