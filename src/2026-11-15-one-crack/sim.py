"""ONE CRACK: a glass hopper packed with ~1,000 glossy balls (rainbow layers) rests on ONE small glass pane
over its neck. The pane cracks in steps (each step it sags a little and the whole pile settles), then shatters:
the shards and the pile pour through a forest of brass pegs into a glass tray below, until the hopper is empty.
Real pymunk physics (seeded, deterministic)."""
import sys, math, pickle, time
import numpy as np, pymunk

FPS, SUB = 30, 6
R = 7.0
# hopper
JX0, JX1, JY0, JY1 = 130, 950, 610, 860     # rectangular part
NX0, NX1, NY = 472, 608, 990                 # neck
PEGY0, PEGY1, PEGDX = 1050, 1160, 62
TX0, TX1, TY = 112, 968, 1585                # tray
N_BALLS = 1300
N_BASE = 0
CRACKS = [0.0, 0.8, 1.5, 2.15, 2.7, 3.15, 3.55, 3.85, 4.1, 4.3]   # crack steps (s); shatter after the last
T_BREAK = 4.6

def pegs():
    out = []
    for j, y in enumerate(np.arange(PEGY0, PEGY1 + 1, 55)):
        off = 0 if j % 2 == 0 else PEGDX / 2
        for x in np.arange(TX0 + 40 + off, TX1 - 30, PEGDX): out.append((float(x), float(y)))
    return out

RAD = []
def build():
    sp = pymunk.Space(); sp.gravity = (0, 1500); sp.iterations = 20
    st = sp.static_body
    segs = [((JX0, JY0 - 40), (JX0, JY1)), ((JX1, JY0 - 40), (JX1, JY1)),
            ((JX0, JY1), (NX0, NY)), ((JX1, JY1), (NX1, NY)),
            ((TX0, 1005), (TX0, TY)), ((TX1, 1005), (TX1, TY)), ((TX0, TY), (TX1, TY))]
    for a, b in segs:
        s = pymunk.Segment(st, a, b, 4); s.friction = .5; s.elasticity = .3; s.collision_type = 3; sp.add(s)
    for x, y in pegs():
        s = pymunk.Circle(st, 6, (x, y)); s.friction = .3; s.elasticity = .55; s.collision_type = 2; sp.add(s)
    pane = pymunk.Body(body_type=pymunk.Body.KINEMATIC); pane.position = (540, NY + 4)
    ps = pymunk.Segment(pane, (NX0 - 540 - 8, 0), (NX1 - 540 + 8, 0), 9); ps.friction = .5; ps.elasticity = .1; ps.collision_type = 5
    sp.add(pane, ps)
    return sp, pane, ps

def run(seed=1, T=17.0):
    rng = np.random.default_rng(seed)
    sp, pane, ps = build()
    balls = []; RAD.clear()
    for i in range(N_BALLS):       # pour in from above (pre-roll, not shown)
        rr = rng.uniform(5.3, 8.6); RAD.append(rr)
        b = pymunk.Body(rr * rr / 49, pymunk.moment_for_circle(rr * rr / 49, 0, rr))
        b.position = (rng.uniform(JX0 + 12, JX1 - 12), JY0 - 60 - i * 1.1 + rng.uniform(-5, 5))
        s = pymunk.Circle(b, rr); s.friction = .45; s.elasticity = .35; s.collision_type = 1
        sp.add(b, s); balls.append(b)
    for i in range(N_BASE):        # a bed of teal balls already resting in the tray
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, R))
        b.position = (rng.uniform(TX0 + 12, TX1 - 12), TY - 20 - i * 1.0)
        s = pymunk.Circle(b, R); s.friction = .45; s.elasticity = .35; s.collision_type = 1
        sp.add(b, s); balls.append(b)
    for k in range(int(6 * FPS * SUB)): sp.step(1 / (FPS * SUB))
    for b in balls: b.velocity = (0, 0)
    for k in range(int(1.5 * FPS * SUB)): sp.step(1 / (FPS * SUB))
    ys = np.array([b.position.y for b in balls[:N_BALLS]])
    print("pre-roll top", ys.min(), "bottom", ys.max())
    order = np.argsort(np.argsort(ys))          # rank by height: 0 = top
    layer = order / N_BALLS
    events = []; tnow = [0.0]
    def post(arb, space, data):
        a, b = arb.bodies
        rv = abs((a.velocity - b.velocity).dot(arb.normal))
        if rv > 140:
            p = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else a.position
            events.append((tnow[0], data, float(p.x), float(p.y), float(rv)))
    for ct, nm in ((2, "peg"), (3, "wall"), (1, "ball"), (4, "shard")):
        sp.on_collision(1, ct, begin=post, data=nm)
    frames, shards = [], []
    ci = 0; sag = 0.0; broke = False
    for f in range(int(T * FPS)):
        t = f / FPS
        for s in range(SUB):
            tnow[0] = t + s / (FPS * SUB)
            if not broke:
                while ci < len(CRACKS) and tnow[0] >= CRACKS[ci]:
                    ci += 1; events.append((tnow[0], "crack", 540.0, NY + 4, float(ci)))
                target = 1.1 * ci + (1.5 if ci == len(CRACKS) else 0)
                vy = (target - sag) * 25; pane.velocity = (0, vy)
                sag += vy / (FPS * SUB)
                if tnow[0] >= T_BREAK:
                    broke = True; sp.remove(pane, ps); events.append((tnow[0], "break", 540.0, NY + 4, 0.0))
                    xs = np.sort(np.concatenate([[NX0 - 6, NX1 + 6], rng.uniform(NX0, NX1, 13)]))
                    for a, bx in zip(xs[:-1], xs[1:]):
                        w = bx - a; h = 16
                        poly = [(-w / 2 + rng.uniform(0, 4), -h / 2), (w / 2, -h / 2 + rng.uniform(0, 3)), (w / 2 - rng.uniform(0, 4), h / 2), (-w / 2, h / 2 - rng.uniform(0, 3))]
                        body = pymunk.Body(2, pymunk.moment_for_poly(2, poly))
                        body.position = ((a + bx) / 2, NY + 4 + sag); body.angle = 0
                        body.velocity = (rng.uniform(-60, 60) + ((a + bx) / 2 - 540) * .9, rng.uniform(60, 200))
                        body.angular_velocity = rng.uniform(-9, 9)
                        sh = pymunk.Poly(body, poly); sh.friction = .4; sh.elasticity = .3; sh.collision_type = 4
                        sp.add(body, sh); shards.append((body, poly))
            sp.step(1 / (FPS * SUB))
        P = np.array([(b.position.x, b.position.y) for b in balls])
        SH = [(b.position.x, b.position.y, b.angle) for b, _ in shards]
        frames.append((P, SH, sag if not broke else None))
    return frames, events, layer, [p for _, p in shards], np.array(RAD)

if __name__ == "__main__":
    t0 = time.time()
    fr, ev, layer, polys, rad = run(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    out = [int(((f[0][:N_BALLS, 1] > NY + 20)).sum()) for f in fr]
    for s in range(0, len(fr), 15): print(round(s / FPS, 1), out[s], end=" | ")
    print("\nsim s", round(time.time() - t0, 1), "events", len(ev))
    pickle.dump((fr, ev, layer, polys, rad), open("sim.pkl", "wb"))
