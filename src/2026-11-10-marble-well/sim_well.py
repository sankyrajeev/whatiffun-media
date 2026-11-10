"""No. 15 — 'Everything rolls / toward the middle.'
Glossy glass marbles drop in at the rim of a round glass basin (top-down view) and roll downhill: the basin
dips steeply in the middle, so each marble orbits in precessing rosette loops (central pull a ~ 1/(r+r0)^1.5,
the shape of a coin-funnel well), slowly losing speed to rolling drag until it rests on the growing heap
in the centre. Escalation ladder 1 -> 10 -> 100 -> 1,000 marbles, each rung smaller marbles; the heap
packs into a rainbow mosaic that fills the basin.
Writes well.pkl: positions per frame, radii, birth frames, collision events."""
import numpy as np, math, pickle, os, sys
import pymunk

E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 8
RB = 418.0                       # basin rim radius (px)
G = E("G", 2.6e6)                # pull strength
R0 = E("R0", 90.0)
P = 1.5
DRAG0 = E("DRAG", 0.28)          # rolling drag per second
SEED = int(E("SEED", 3))
# ladder: birth times of marble i (1-indexed count curve, log-linear between rungs)
KT = [0.0, 3.6, 8.0, 13.6]
KN = [1, 10, 100, 1000]
NM = 1000
T_SIM = E("TSIM", 22.5)
rng = np.random.default_rng(SEED)

def count_at(t):
    if t <= KT[1]: return 1 + 9 * (t / KT[1])                        # rung 1: linear, one by one
    return 10 ** np.interp(t, KT, np.log10(KN))
tt = np.linspace(0, KT[-1], 400001)
NN = np.array([count_at(x) for x in tt[::100]]); tts = tt[::100]
birth = np.interp(np.arange(1, NM + 1), NN, tts); birth[0] = 0.0    # first marble drops in on frame 1
# rung 1 marbles get nudged so they don't fall exactly on a grid
birth[1:10] += rng.uniform(-.08, .08, 9)
def rad(i):                                         # i 0-based
    n = i + 1
    return 24.0 * n ** -.15 if n > 1 else 26.0
R = np.array([rad(i) for i in range(NM)])

space = pymunk.Space(); space.iterations = 20
def a_of(r): return G / (r + R0) ** P
drag = [DRAG0]
def vfunc(body, gravity, damping, dt):
    p = body.position; r = math.hypot(p.x, p.y) + 1e-6
    a = a_of(r)
    v = body.velocity
    # rolling drag, and a little extra when slow (settling)
    sp = math.hypot(v.x, v.y)
    k = drag[0] + (1.6 if sp < 60 else 0.0)
    body.velocity = (v.x + (-a * p.x / r - k * v.x) * dt, v.y + (-a * p.y / r - k * v.y) * dt)
# basin wall
wall = pymunk.Body(body_type=pymunk.Body.STATIC)
segs = []
for k in range(96):
    a0, a1 = 2 * math.pi * k / 96, 2 * math.pi * (k + 1) / 96
    s = pymunk.Segment(wall, (RB * math.cos(a0), RB * math.sin(a0)), (RB * math.cos(a1), RB * math.sin(a1)), 6)
    s.elasticity = .5; s.friction = .3; s.collision_type = 2; segs.append(s)
space.add(wall, *segs)

bodies = [None] * NM
events = []
cur_t = [0.0]
def post(arb, sp, data):
    if not arb.is_first_contact: return
    imp = arb.total_impulse.length
    sa, sb = arb.shapes
    ia = getattr(sa, "idx", -1); ib = getattr(sb, "idx", -1)
    pt = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else sa.body.position
    m = min(sa.body.mass if ia >= 0 else 1e9, sb.body.mass if ib >= 0 else 1e9)
    events.append((cur_t[0], pt.x, pt.y, imp / m, ia, ib))   # impulse/mass = speed change
space.on_collision(1, 1, post_solve=post)
space.on_collision(1, 2, post_solve=post)

def spawn(i):
    # drops in just inside the rim at a random angle, rolling counter-clockwise
    for _ in range(40):
        ang = rng.uniform(0, 2 * math.pi) if i > 0 else -math.pi * .62
        r = RB - R[i] - rng.uniform(4, 30)
        x, y = r * math.cos(ang), r * math.sin(ang)
        if all(b is None or (b.position - (x, y)).length > R[i] + R[j] + 2 for j, b in enumerate(bodies[:i])
               if b is not None and (b.position - (x, y)).length < 80): break
    vc = math.sqrt(r * a_of(r))
    f = rng.uniform(.62, .9) if i > 0 else .78
    m = (R[i] / 10) ** 2
    b = pymunk.Body(m, pymunk.moment_for_circle(m, 0, R[i]))
    b.position = (x, y)
    tx, ty = -math.sin(ang), math.cos(ang)
    b.velocity = (vc * f * tx - rng.uniform(0, .15) * vc * math.cos(ang), vc * f * ty - rng.uniform(0, .15) * vc * math.sin(ang))
    b.velocity_func = vfunc
    s = pymunk.Circle(b, R[i]); s.elasticity = .55; s.friction = .15; s.collision_type = 1; s.idx = i
    space.add(b, s); bodies[i] = b

NF = int(T_SIM * FPS)
POS = np.full((NF, NM, 2), np.nan, np.float32)
nxt = 0
t = 0.0
dt = 1 / (FPS * SUB)
# pre-roll so marble 0 is mid-orbit on frame 0
while t < 0:
    while nxt < NM and birth[nxt] <= t: spawn(nxt); nxt += 1
    space.step(dt); t += dt
for f in range(NF):
    for s in range(SUB):
        cur_t[0] = t
        while nxt < NM and birth[nxt] <= t: spawn(nxt); nxt += 1
        space.step(dt); t += dt
    for i in range(nxt):
        p = bodies[i].position; POS[f, i] = (p.x, p.y)
    if f % 60 == 0:
        sp = np.array([bodies[i].velocity.length for i in range(nxt)])
        print(f"t={f/FPS:5.1f} n={nxt:4d} moving>40px/s={int((sp>40).sum()):4d} maxsp={sp.max():6.0f} ev={len(events)}", flush=True)
sp = np.array([b.velocity.length for b in bodies])
print("final moving>20", int((sp > 20).sum()), "max r of heap", float(np.nanmax(np.hypot(POS[-1, :, 0], POS[-1, :, 1]) + R)))
pickle.dump(dict(POS=POS, R=R, birth=birth, events=np.array(events, np.float32), RB=RB, KT=KT, KN=KN, FPS=FPS),
            open("well.pkl", "wb"))
