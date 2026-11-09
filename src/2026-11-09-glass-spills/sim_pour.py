"""No. 12 — 'When a glass fills, / it spills over.'
A five-tier tower of 15 crystal goblets on a dark table. A thin stream of glass beads pours into the top one;
whenever a goblet is full its beads spill over the rim into the goblets below. The colour of the stream drifts
slowly, so every glass fills with soft layered bands. It ends when the last glass fills."""
import pymunk, numpy as np, pickle, math, os
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, int(E('SUB', 4))
DT = 1 / (FPS * SUB)
BR = E("BR", 5.5)
ROWS = int(E('ROWS', 4))
WA, WB = E("WA", 68), E("WB", 84)          # bowl half-width, depth
GAP = E("GAP", 36)
PITCH = 2 * WA + GAP
STEP = E("STEP", 150)
Y0 = E("Y0", 640)                           # top rim y
CX = 540.0
RATE0, RATE1 = E("R0", 70), E("R1", 150)    # beads / s
SPY = E("SPY", 545)
SECS = E("SECS", 30)
PRE = E("PRE", 1.0)
rng = np.random.default_rng(int(E("SEED", 2)))

space = pymunk.Space(); space.gravity = (0, E("G", 900)); space.iterations = 10; space.damping = E("DAMP", .6); space.collision_slop = .2
CUPS = []
for r in range(ROWS):
    for k in range(r + 1):
        CUPS.append((r, CX + (k - r / 2) * PITCH, Y0 + r * STEP))
TABLE = Y0 + ROWS * STEP - 4
def seg(a, b, rad=2.5, ct=3, fr=.5):
    s = pymunk.Segment(space.static_body, a, b, rad); s.elasticity = E("EW", .05); s.friction = fr; s.collision_type = ct; space.add(s); return s
for ci, (r, x, y) in enumerate(CUPS):
    pts = []
    for a in np.linspace(0, math.pi, 22):
        pts.append((x - WA * math.cos(a), y + WB * math.sin(a)))
    # slight outward lip
    pts = [(x - WA - 5, y - 3)] + pts + [(x + WA + 5, y - 3)]
    for a, b in zip(pts, pts[1:]):
        s = seg(a, b, 2.5, 3, E("FW", .5)); s.cup = ci
# a wide shallow glass basin the tower stands in: flat floor, walls curving up at both ends
TL, TR = 102, 978; BH = E("BH", 190)
BASIN = []
RC = E("RC", 40)   # rounded bottom corners of a straight-walled glass tank
BASIN.append((TL, TABLE - BH))
for a in np.linspace(math.pi, math.pi / 2, 8): BASIN.append((TL + RC + RC * math.cos(a), TABLE - RC + RC * math.sin(a)))
for a in np.linspace(math.pi / 2, 0, 8): BASIN.append((TR - RC + RC * math.cos(a), TABLE - RC + RC * math.sin(a)))
BASIN.append((TR, TABLE - BH))
for a, b in zip(BASIN, BASIN[1:]): seg(a, b, 4, 5, E("FW", .5))
B = []; tb = []; clk = {"t": 0.0}; hits = []
def on_hit(arb, sp, d):
    if not arb.is_first_contact: return
    imp = arb.total_impulse.length
    if imp < 25: return
    a, b = arb.shapes
    p = arb.contact_point_set.points[0].point_a
    kind = getattr(b, "cup", -1) if b.collision_type == 3 else (-2 if b.collision_type == 1 else -3)
    hits.append((clk["t"], p.x, p.y, imp, kind))
space.on_collision(1, 3, post_solve=on_hit)
space.on_collision(1, 5, post_solve=on_hit)
space.on_collision(1, 1, post_solve=on_hit)

SLOTS = [k * 2.1 * BR for k in (-2, -1, 0, 1, 2)]
def add(t):
    xs = [CX + d for d in SLOTS]; rng.shuffle(xs)
    for x in xs:
        q = space.point_query_nearest((x, SPY), BR * 2.1, pymunk.ShapeFilter())
        if q is None: break
    else: return False
    b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR))
    b.position = (x + rng.normal(0, .5), SPY); b.velocity = (rng.normal(0, 4), E("VY", 600))
    s = pymunk.Circle(b, BR); s.elasticity = E("EB", .05); s.friction = E("FB", .5); s.collision_type = 1
    space.add(b, s); B.append(b); tb.append(t); return True

# fill test: cup is full when its count reaches capacity measure (beads inside the bowl ellipse)
def inside(P):
    occ = np.zeros(len(CUPS), int)
    for ci, (r, x, y) in enumerate(CUPS):
        dx = (P[:, 0] - x) / (WA - BR * .5); dy = (P[:, 1] - y) / (WB - BR * .5)
        occ[ci] = np.sum((dy > -0.02) & (dx * dx + dy * dy < 1))
    return occ
frames, counts, occs = [], [], []
acc = 0.0; full_t = [None] * len(CUPS); peak = np.zeros(len(CUPS), int); stop_t = None
CAP = E("CAP", .9)
CAPN = None
NT = int((SECS + PRE) * FPS)
for f in range(NT):
    t = f / FPS - PRE
    if stop_t is not None:
        u = min(1, max(0, (t - stop_t - E('SETT', 2.2)) / 1.0)); space.damping = E('DAMP', .6) * (1 - u) + E('DEND', .6) * u
    for s_ in range(SUB):
        clk["t"] = t + s_ * DT
        if stop_t is None:
            u = min(1, max(0, (t + PRE) / E("RAMP", 12)))
            acc += (RATE0 + (RATE1 - RATE0) * u) * DT
            while acc >= 1:
                if not add(clk["t"]): break
                acc -= 1
        space.step(DT)
        VX = E('VX', 220)
        for b in B:
            vx, vy = b.velocity
            if abs(vx) > VX: b.velocity = (math.copysign(VX, vx), vy)
    # remove escapees
    for i, b in enumerate(B):
        if not getattr(b, "out", False) and (b.position.x < 95 or b.position.x > 985 or b.position.y > 1700):
            b.out = True; print("ESC", round(t, 2), i, tuple(round(v) for v in b.position), tuple(round(v) for v in b.velocity))
    P = np.array([b.position for b in B], np.float32) if B else np.zeros((0, 2), np.float32)
    o = inside(P); peak = np.maximum(peak, o)
    if CAPN is None and f > 3 * FPS:
        pass
    occs.append(o)
    if t >= 0:
        frames.append(P); counts.append(len(B))
    if f % 30 == 0: print(f"t={t:5.1f} n={len(B):5d} occ={o.tolist()}", flush=True)
    if stop_t is not None and t > stop_t + E("TAIL", 4.5): break
    # stop the pour once every cup has saturated
    if stop_t is None and t > 5:
        o_hist = np.array(occs[-30:])
        sat = (o_hist.min(0) >= CAP * E("NCAP", 60))
        if sat.all(): stop_t = t; print("stop", t)
print("frames", len(frames), "N", len(B), "stop", stop_t, "peak", peak.tolist())
P = frames[-1]
print("x", P[:, 0].min(), P[:, 0].max(), "y", P[:, 1].min(), P[:, 1].max(), "below table", int(np.sum(P[:, 1] > TABLE + 10)))
pickle.dump(dict(frames=frames, counts=np.array(counts), tb=np.array(tb), hits=hits, occs=np.array(occs[int(PRE * FPS):]), stop=stop_t,
                 geom=dict(BASIN=BASIN, CUPS=CUPS, WA=WA, WB=WB, STEP=STEP, TABLE=TABLE, TL=TL, TR=TR, BR=BR, SPY=SPY, PRE=PRE, LIP=E("LIP", 70))),
            open("pour.pkl", "wb"))
