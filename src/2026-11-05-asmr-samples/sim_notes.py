"""Sample A — 'Every note drops a new ball.'
Glass chimes hang in open space. Each time a ball rings a chime, a new ball falls from the top above it.
The pile rising from the floor buries the chimes from the bottom up; the music thins out and stops."""
import pymunk, numpy as np, pickle, math, random, os
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 6
DT = E("TS", 1.0) / (FPS * SUB)
LEFT, RIGHT, TOP, FLOOR = E("LEFT", 190.0), E("RIGHT", 890.0), E("TOP", 560.0), 1470.0
BR = E("BR", 6.5)
COOL = E("COOL", 0.4)
CAP = int(E("CAP", 3600))
SECS = E("SECS", 36)
random.seed(int(E("SEED", 3))); np.random.seed(int(E("SEED", 3)))

space = pymunk.Space(); space.gravity = (0, E("G", 1400)); space.iterations = 12; space.collision_slop = .3
st = space.static_body
def seg(a, b, r, ct, e=.35, f=.4):
    s = pymunk.Segment(st, a, b, r); s.elasticity = e; s.friction = f; s.collision_type = ct; space.add(s); return s
seg((LEFT, TOP - 140), (LEFT, FLOOR), 4, 3); seg((RIGHT, TOP - 140), (RIGHT, FLOOR), 4, 3)
seg((LEFT, FLOOR), (RIGHT, FLOOR), 5, 5, e=.2)

# chimes: 5 rows, staggered, steep tilt
chimes = []
D = E("DX", 210); ROWS = [(760, [540 - D, 540 + D]), (900, [540]), (1040, [540 - D, 540 + D]), (1180, [540]), (1320, [540 - D, 540 + D])]
k = 0
for y, xs in ROWS:
    for x in xs:
        ang = math.radians(30 if (k % 2 == 0) else -30)
        L = 150
        a = (x - L / 2 * math.cos(ang), y - L / 2 * math.sin(ang)); b = (x + L / 2 * math.cos(ang), y + L / 2 * math.sin(ang))
        s = seg(a, b, 7, 2, e=.72, f=.05); s.chime = k
        chimes.append(dict(a=a, b=b, x=x, y=y)); k += 1
NC = len(chimes)

balls, born, src = [], [], []
clock = {"t": 0.0}; pending = []; events = []; cool = {}
def add_ball(p, v, f, c=-1):
    b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR)); b.position = p; b.velocity = v
    s = pymunk.Circle(b, BR); s.elasticity = .55; s.friction = .1; s.collision_type = 1; s.idx = len(balls)
    space.add(b, s); balls.append(b); born.append(f); src.append(c)
def on_chime(arb, sp, d):
    if not arb.is_first_contact: return
    ms, cs = arb.shapes; imp = arb.total_impulse.length
    p = arb.contact_point_set.points[0].point_a
    events.append((clock["t"], p.x, p.y, imp, "chime", cs.chime))
    if imp < E("RING", 120): return
    key = (ms.idx, cs.chime)
    if clock["t"] - cool.get(key, -9) < COOL: return
    cool[key] = clock["t"]; pending.append(cs.chime)
def on_any(kind):
    def cb(arb, sp, d):
        if arb.is_first_contact and arb.total_impulse.length > 25:
            p = arb.contact_point_set.points[0].point_a
            events.append((clock["t"], p.x, p.y, arb.total_impulse.length, kind, -1))
    return cb
space.on_collision(1, 2, post_solve=on_chime)
for kind, ct in (("ball", 1), ("wall", 3), ("floor", 5)):
    space.on_collision(1, ct, post_solve=on_any(kind))

add_ball((395, TOP - 60), (0, 250), 0, -1)

frames, counts, rings_f = [], [], []
end_frame, quiet = None, 0
for f in range(int(SECS * FPS)):
    for s_ in range(SUB):
        clock["t"] = (f + s_ / SUB) / FPS
        space.step(DT)
        if pending:
            for c in pending:
                if len(balls) >= CAP: break
                x = random.uniform(LEFT + 20, RIGHT - 20)
                add_ball((x, TOP - random.uniform(40, 120)), (random.uniform(-40, 40), random.uniform(0, 120)), f, c)
            pending.clear()
    frames.append(np.array([[b.position.x, b.position.y] for b in balls], np.float32)); counts.append(len(balls))
    r = sum(1 for e in events if e[4] == "chime" and e[3] >= E("RING", 120) and e[0] > (f - 20) / FPS)
    rings_f.append(r)
    if f % 60 == 0:
        per = [sum(1 for e in events if e[4] == "chime" and e[3] >= E("RING", 120) and e[5] == c and e[0] > (f - 60) / FPS) for c in range(NC)]
        print(f"t={f / FPS:5.1f} n={len(balls):5d} rings2s={per}", flush=True)
    if f > 90 and r == 0:
        quiet += 1
        if quiet == 1: end_frame = f
        if quiet > 70: break
    else:
        quiet, end_frame = 0, None
print("frames", len(frames), "n", len(balls), "silence at", end_frame and round(end_frame / FPS, 1))
pickle.dump(dict(frames=frames, counts=np.array(counts), born=np.array(born), src=np.array(src), events=events,
                 chimes=chimes, end=end_frame, bars=[(c["a"], c["b"]) for c in chimes],
                 geom=dict(LEFT=LEFT, RIGHT=RIGHT, TOP=TOP, FLOOR=FLOOR, BR=BR)), open("notes.pkl", "wb"))
