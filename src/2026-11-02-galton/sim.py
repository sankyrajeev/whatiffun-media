"""Galton board: glass marbles through brass pins into wooden bins (pymunk, y-down)."""
import pymunk, numpy as np, pickle, math, random, sys, os
ENV = lambda k, d: float(os.environ.get(k, d))

W, H = 1080, 1920
FPS, SUB = 30, 8
DT = 1.0 / (FPS * SUB)
CX = W / 2

NB = int(sys.argv[1]) if len(sys.argv) > 1 else 450      # marbles
ROWS = 16
PITCH = 50.0                 # horizontal pin spacing == bin width
VSP = 35.0                   # vertical pin spacing
BR = 7.0                     # marble radius
PR = 4.2                     # pin radius
OUTLET = float(sys.argv[2]) if len(sys.argv) > 2 else 34.0

HOP_TOP, HOP_BOT, OUT_Y = 320.0, 440.0, 565.0
PIN_Y0 = 605.0
PIN_Y1 = PIN_Y0 + (ROWS - 1) * VSP
NBINS = ROWS + 1
BOARD_W = NBINS * PITCH
BX0, BX1 = CX - BOARD_W / 2, CX + BOARD_W / 2
BIN_TOP = PIN_Y1 + 30
FLOOR = 1495.0

random.seed(5)
space = pymunk.Space()
space.gravity = (0, ENV('G', 2300))
space.iterations = 20
space.damping = ENV('DAMP', 0.995)
static = space.static_body

def seg(a, b, r=2.0, ct=3, e=0.2, fr=0.5):
    s = pymunk.Segment(static, a, b, r); s.elasticity = e; s.friction = fr; s.collision_type = ct
    space.add(s); return s

# hopper: box + funnel to outlet
HW = 235.0
seg((CX - HW, HOP_TOP - 100), (CX - HW, HOP_BOT), ct=3)
seg((CX + HW, HOP_TOP - 100), (CX + HW, HOP_BOT), ct=3)
seg((CX - HW, HOP_BOT), (CX - OUTLET / 2, OUT_Y), ct=3)
seg((CX + HW, HOP_BOT), (CX + OUTLET / 2, OUT_Y), ct=3)
gate = seg((CX - OUTLET / 2 - 4, OUT_Y + 2), (CX + OUTLET / 2 + 4, OUT_Y + 2), ct=3)

# pins (staggered rows inside board)
pins = []
for r in range(ROWS):
    y = PIN_Y0 + r * VSP
    off = 0.0 if r % 2 == 0 else PITCH / 2
    x = BX0 + off
    while x <= BX1 + 0.1:
        if BX0 + 4 < x < BX1 - 4 or r % 2 == 0:
            c = pymunk.Circle(static, PR, (x, y)); c.elasticity = ENV('PE', 0.35); c.friction = ENV('PF', 0.3); c.collision_type = 2
            space.add(c); pins.append((x, y))
        x += PITCH
# side walls of board
seg((BX0 - 2, PIN_Y0 - 40), (BX0 - 2, FLOOR), ct=3)
seg((BX1 + 2, PIN_Y0 - 40), (BX1 + 2, FLOOR), ct=3)
# bin dividers
dividers = []
for k in range(1, NBINS):
    x = BX0 + k * PITCH
    seg((x, BIN_TOP), (x, FLOOR), r=2.0, ct=4, e=0.1)
    dividers.append(x)
seg((BX0, FLOOR), (BX1, FLOOR), r=3, ct=5, e=0.08, fr=0.6)

# marbles: fill hopper
balls = []
for i in range(NB):
    b = pymunk.Body(1.0, pymunk.moment_for_circle(1.0, 0, BR))
    b.position = (CX - HW + 15 + random.random() * (2 * HW - 30), HOP_TOP - 40 - i * 1.6 + random.random() * 4)
    s = pymunk.Circle(b, BR); s.elasticity = ENV('BE', 0.25); s.friction = 0.05; s.collision_type = 1
    space.add(b, s); balls.append(b)

events = []        # (t, x, y, impulse, kind)
clock = {"t": 0.0, "rec": False}
def make_cb(kind):
    def cb(arb, sp, data):
        if not clock["rec"] or not arb.is_first_contact:
            return
        imp = arb.total_impulse.length
        if imp < 25: return
        p = arb.contact_point_set.points[0].point_a
        events.append((clock["t"], p.x, p.y, imp, kind))
    return cb
space.on_collision(1, 2, post_solve=make_cb("pin"))
space.on_collision(1, 1, post_solve=make_cb("ball"))
space.on_collision(1, 3, post_solve=make_cb("wall"))
space.on_collision(1, 4, post_solve=make_cb("wood"))
space.on_collision(1, 5, post_solve=make_cb("floor"))

# settle the hopper
for _ in range(FPS * SUB * 3):
    space.step(DT)

GATE_OPEN = 12          # frame
frames = []
clock["rec"] = True
f = 0
settled_for = 0
while True:
    if f == GATE_OPEN:
        space.remove(gate)
    for s_ in range(SUB):
        clock["t"] = (f + s_ / SUB) / FPS
        if f > GATE_OPEN:
            for bd in balls:
                y = bd.position.y
                if PIN_Y0 - 20 < y < BIN_TOP and bd.velocity.length < 25:
                    bd.apply_impulse_at_local_point((random.choice((-1, 1)) * 6.0, 0))
        space.step(DT)
    pos = np.array([[b.position.x, b.position.y] for b in balls], np.float32)
    frames.append(pos)
    f += 1
    ke = sum(b.velocity.length for b in balls) / NB
    above = int((pos[:, 1] < BIN_TOP).sum())
    if "poured" in clock and ke < 4:
        settled_for += 1
        if settled_for > 20: break
    if f > FPS * 45:
        print("timeout; above", above, "ke", ke); break
    if above <= 2 and "poured" not in clock and f > GATE_OPEN:
        clock["poured"] = f; print("poured by frame", f, "= %.1fs" % (f / FPS))
    if f % 150 == 0:
        print("frame", f, "above", above, "ke %.1f" % ke, flush=True)

pos = frames[-1]
bins = np.clip(((pos[:, 0] - BX0) // PITCH).astype(int), 0, NBINS - 1)
counts = np.bincount(bins, minlength=NBINS)
heights = {k: float(FLOOR - pos[bins == k, 1].min() + BR) if counts[k] else 0.0 for k in range(NBINS)}
print("frames", len(frames), "= %.1fs" % (len(frames) / FPS), "events", len(events))
print("counts", counts.tolist())
print("max pile height", max(heights.values()), "bin top room", FLOOR - BIN_TOP)
pickle.dump(dict(frames=np.array(frames), events=events, pins=pins, dividers=dividers, counts=counts,
                 geom=dict(CX=CX, HW=HW, HOP_TOP=HOP_TOP, HOP_BOT=HOP_BOT, OUT_Y=OUT_Y, OUTLET=OUTLET,
                           PIN_Y0=PIN_Y0, PIN_Y1=PIN_Y1, BX0=BX0, BX1=BX1, BIN_TOP=BIN_TOP, FLOOR=FLOOR,
                           PITCH=PITCH, BR=BR, PR=PR, NBINS=NBINS, ROWS=ROWS, GATE_OPEN=GATE_OPEN)),
            open("sim.pkl", "wb"))
