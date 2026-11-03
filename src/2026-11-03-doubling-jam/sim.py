"""'Every time a marble hits something moving, it doubles.'
A torque-limited motor spins a paddle wheel inside a glass drum. Marble hits on the moving paddles clone
the marble. More marbles -> more load -> the wheel slows -> fewer qualifying hits -> it jams."""
import pymunk, numpy as np, pickle, math, random, sys, os
ENV = lambda k, d: float(os.environ.get(k, d))

W, H = 1080, 1920
FPS, SUB = 30, 6
TS = float(os.environ.get("TS", 1.0))
DT = TS / (FPS * SUB)
CX, CY = 540.0, 1010.0
R_BOWL = 440.0
R_ARM = float(os.environ.get("RARM", 424.0))
BR = 7.0
OMEGA = ENV("OMEGA", 2.6)          # motor target rad/s
TORQUE = ENV("TORQUE", 2.0e8)      # motor max torque
V_TH = ENV("VTH", 220.0)           # min relative speed for a hit to count as "moving"
COOL = ENV("COOL", 0.55)           # s, per-marble cloning cooldown
CAP = int(ENV("CAP", 6000))
SECONDS = ENV("SECS", 30)

random.seed(4); np.random.seed(4)
space = pymunk.Space()
space.gravity = (0, ENV('G', 0.0))
space.iterations = 12
space.collision_slop = 0.3

static = space.static_body
NSEG = 140
for i in range(NSEG):
    a0, a1 = 2 * math.pi * i / NSEG, 2 * math.pi * (i + 1) / NSEG
    s = pymunk.Segment(static, (CX + R_BOWL * math.cos(a0), CY + R_BOWL * math.sin(a0)),
                       (CX + R_BOWL * math.cos(a1), CY + R_BOWL * math.sin(a1)), 3)
    s.elasticity = ENV('EW', 0.9); s.friction = 0.2; s.collision_type = 3
    space.add(s)

NPEG = int(ENV("NPEG", 8)); R_PEG_ORB = ENV("RPEGO", 376.0); R_PEG = ENV("RPEG", 17.0)
pegs = []
for k in range(NPEG):
    a = 2 * math.pi * (k + 0.5) / NPEG
    p = (CX + R_PEG_ORB * math.cos(a), CY + R_PEG_ORB * math.sin(a))
    c = pymunk.Circle(static, R_PEG, (p[0], p[1])); c.elasticity = 0.95; c.friction = 0.2; c.collision_type = 3
    space.add(c); pegs.append(p)

wheel = pymunk.Body(400.0, 400.0 * R_ARM ** 2 / 2)
wheel.position = (CX, CY)
NARM = 3
R_ORB = ENV("RORB", 250.0)
R_DISC = ENV("RDISC", 58.0)
arms = []
for k in range(NARM):
    a = 2 * math.pi * k / NARM
    s = pymunk.Circle(wheel, R_DISC, (R_ORB * math.cos(a), R_ORB * math.sin(a)))
    s.elasticity = 0.85; s.friction = 0.3; s.collision_type = 2
    arms.append(s)
hub = pymunk.Circle(wheel, 34); hub.elasticity = 0.4; hub.friction = 0.6; hub.collision_type = 4
space.add(wheel, *arms, hub)
space.add(pymunk.PivotJoint(static, wheel, (CX, CY)))
motor = pymunk.SimpleMotor(static, wheel, OMEGA)   # static rate relative to wheel
motor.max_force = TORQUE
space.add(motor)
wheel.angular_velocity = -OMEGA

balls = []          # (body, shape)
born = []           # frame born
gen = []
last_clone = []
def add_ball(p, v, g, f):
    b = pymunk.Body(1.0, pymunk.moment_for_circle(1.0, 0, BR))
    b.position = p; b.velocity = v
    s = pymunk.Circle(b, BR); s.elasticity = ENV('EB', 0.85); s.friction = ENV('FB', 0.2); s.collision_type = 1
    s.idx = len(balls)
    space.add(b, s); balls.append(b); born.append(f); gen.append(g); last_clone.append(clock["t"])

clock = {"t": 0.0, "f": 0}
pending = []
events = []          # (t, x, y, value, kind)
def on_arm(arb, sp, data):
    ms = arb.shapes[0]
    if not arb.is_first_contact: return
    p = arb.contact_point_set.points[0].point_a
    vb = ms.body.velocity
    vw = wheel.velocity_at_world_point(p)
    n = arb.contact_point_set.normal
    rel = arb.total_impulse.length / 1.45   # impulse = m(1+e)v_rel, m=1
    wall_speed = vw.length
    imp = arb.total_impulse.length
    events.append((clock["t"], p.x, p.y, imp, "arm"))
    i = ms.idx
    if wall_speed > V_TH and clock["t"] - last_clone[i] > COOL:
        pending.append(i)
def on_mm(arb, sp, data):
    if arb.is_first_contact:
        imp = arb.total_impulse.length
        if imp > 30:
            p = arb.contact_point_set.points[0].point_a
            events.append((clock["t"], p.x, p.y, imp, "ball"))
def on_wall(arb, sp, data):
    if arb.is_first_contact:
        imp = arb.total_impulse.length
        if imp > 30:
            p = arb.contact_point_set.points[0].point_a
            events.append((clock["t"], p.x, p.y, imp, "wall"))
space.on_collision(1, 2, post_solve=on_arm)
space.on_collision(1, 4, post_solve=on_arm)
space.on_collision(1, 1, post_solve=on_mm)
space.on_collision(1, 3, post_solve=on_wall)

add_ball((CX - 60, CY - 330), (0, 380), 0, 0)

frames, omegas, counts, clones = [], [], [], []
jam_frame = None
slow_for = 0
nf = int(SECONDS * FPS)
for f in range(nf):
    clock["f"] = f
    for s_ in range(SUB):
        clock["t"] = (f + s_ / SUB) / FPS
        space.step(DT)
        if pending:
            seen = set()
            for i in pending:
                if i in seen or len(balls) >= CAP: continue
                seen.add(i)
                b = balls[i]
                last_clone[i] = clock["t"]
                v = b.velocity
                ang = random.uniform(0.25, 0.45) * random.choice((-1, 1))
                v2 = v.rotated(ang); b.velocity = v.rotated(-ang)
                off = v2.normalized() * BR * 0.9 if v2.length > 1 else pymunk.Vec2d(BR * 0.9, 0)
                add_ball(b.position + off, v2, gen[i] + 1, f)
                clones.append((clock["t"], b.position.x, b.position.y, gen[i] + 1, len(balls)))
            pending.clear()
    w = wheel.angular_velocity
    pos = np.array([[b.position.x, b.position.y] for b in balls], np.float32)
    frames.append(pos)
    omegas.append((w, wheel.angle))
    counts.append(len(balls))
    if f % 60 == 0:
        print(f"t={f / FPS:5.1f}s n={len(balls):5d} omega={w:5.2f}", flush=True)
    if jam_frame is None and f > 60 and abs(w) < 0.06:
        slow_for += 1
        if slow_for >= 20:
            jam_frame = f - 19
            print("JAM at", jam_frame, "%.1fs" % (jam_frame / FPS), "n", len(balls), flush=True)
    else:
        slow_for = 0 if jam_frame is None else slow_for
    if jam_frame is not None and f >= jam_frame + 75:
        break

if jam_frame is None:
    print("no jam; final n", len(balls))
print("frames", len(frames), "clones", len(clones), "events", len(events))
pickle.dump(dict(frames=frames, omegas=np.array(omegas), counts=np.array(counts), born=np.array(born),
                 gen=np.array(gen), clones=clones, events=events, jam=jam_frame, arms=NARM,
                 pegs=pegs, geom=dict(R_PEG=R_PEG, CX=CX, CY=CY, R_BOWL=R_BOWL, R_ARM=R_ARM, R_ORB=R_ORB, R_DISC=R_DISC, BR=BR, OMEGA=OMEGA)),
            open("sim.pkl", "wb"))
