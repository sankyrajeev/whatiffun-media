"""THREE FLOORS: a tall glass silo holds four bands of glossy balls (violet / magenta / coral / gold), the
top three each resting on a full-width floor of loose bricks (14 columns x 3 rows). The top floor lets go
column by column, faster and faster (each column drops out as a tumbling stack and a stream of balls pours
through), then gives way; the falling load lands on the next floor, which starts to go, and so on, until
everything crashes into the bottom of the silo. Real pymunk physics (seeded, deterministic)."""
import sys, math, pickle, time
import numpy as np, pymunk

FPS, SUB = 30, 6
JX0, JX1, JTOP, TY = 130, 950, 540, 1585
ROWS, COLS, BH = 3, 14, 23
BW = (JX1 - JX0) / COLS
FLOORS = [732, 1051, 1370]                 # floor top y
FH = ROWS * BH
HB = 134
BANDS = [(f - HB, f) for f in FLOORS] + [(TY - HB, TY)]
RMIN, RMAX = 6.0, 9.2
REL = [  # (time, floor, column or None=all)
    (0.15, 0, 5), (1.05, 0, 9), (1.70, 0, 2), (2.30, 0, 11), (2.80, 0, 7), (3.25, 0, 0), (3.60, 0, 13), (3.95, 0, None),
    (4.45, 1, 6), (5.45, 1, 10), (6.10, 1, 3), (6.70, 1, 12), (7.20, 1, 8), (7.60, 1, 1), (7.95, 1, 5), (8.25, 1, None),
    (9.05, 2, 7), (9.65, 2, 1), (10.20, 2, 11), (10.70, 2, 4), (11.10, 2, 13), (11.40, 2, 9), (11.65, 2, None)]

def run(seed=1, T=18.5, rel=REL):
    rng = np.random.default_rng(seed)
    sp = pymunk.Space(); sp.gravity = (0, 1500); sp.iterations = 22
    st = sp.static_body
    for a, b in (((JX0, JTOP), (JX0, TY)), ((JX1, JTOP), (JX1, TY)), ((JX0 - 4, TY), (JX1 + 4, TY))):
        s = pymunk.Segment(st, a, b, 4); s.friction = .5; s.elasticity = .3; s.collision_type = 3; sp.add(s)
    bricks = []
    for fl, fy in enumerate(FLOORS):
        for c in range(COLS):
            for r in range(ROWS):
                b = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
                b.position = (JX0 + (c + .5) * BW, fy + (r + .5) * BH)
                s = pymunk.Poly.create_box(b, (BW - 9, BH - 8), 2.5); s.mass = 7; s.friction = .35; s.elasticity = .25
                s.collision_type = 4; sp.add(b, s); bricks.append((b, fl, c, r))
    balls, RAD, BAND = [], [], []
    d = 2 * RMAX + .6
    for k, (y0, y1) in enumerate(BANDS):
        rows = int((y1 - y0 - 2 * RMAX) / (d * .866))
        for j in range(rows):
            y = y1 - RMAX - 1 - j * d * .866
            xs = np.arange(JX0 + RMAX + 3 + (d / 2 if j % 2 else 0), JX1 - RMAX - 3, d)
            for x in xs:
                rr = rng.uniform(RMIN, RMAX)
                b = pymunk.Body(rr * rr / 49, pymunk.moment_for_circle(rr * rr / 49, 0, rr))
                b.position = (x + rng.uniform(-.3, .3), y)
                s = pymunk.Circle(b, rr); s.friction = .45; s.elasticity = .35; s.collision_type = 1
                sp.add(b, s); balls.append(b); RAD.append(rr); BAND.append(k)
    for k in range(int(3 * FPS * SUB)): sp.step(1 / (FPS * SUB))
    for b in balls: b.velocity = (0, 0)
    for k in range(int(1.0 * FPS * SUB)): sp.step(1 / (FPS * SUB))
    BAND = np.array(BAND); Y0 = np.array([b.position.y for b in balls])
    for k in range(4):
        m = BAND == k; print("band", k, m.sum(), "top", Y0[m].min().round(), "bottom", Y0[m].max().round())
    # colour position within band (0 top .. 1 bottom)
    sub = np.zeros(len(balls))
    for k in range(4):
        m = BAND == k; yy = Y0[m]; sub[m] = (yy - yy.min()) / (np.ptp(yy) + 1e-9)
    events = []; tnow = [0.0]
    def post(arb, space, data):
        a, b = arb.bodies
        rv = abs((a.velocity - b.velocity).dot(arb.normal))
        if rv > 140:
            p = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else a.position
            events.append((tnow[0], data, float(p.x), float(p.y), float(rv)))
    for (ca, cb), nm in (((1, 3), "wall"), ((1, 1), "ball"), ((1, 4), "ballbrick"), ((4, 3), "brick"), ((4, 4), "brick2")):
        sp.on_collision(ca, cb, begin=post, data=nm)
    def release(fl, col, t):
        n = 0
        for b, f_, c, r in bricks:
            if f_ == fl and (col is None or c == col) and b.body_type != pymunk.Body.DYNAMIC:
                b.body_type = pymunk.Body.DYNAMIC; n += 1
                b.velocity = (rng.uniform(-50, 50), rng.uniform(60, 200) * (1.6 if col is None else 1))
                b.angular_velocity = rng.uniform(-3, 3) * (2 if col is None else 1)
        x = JX0 + ((col if col is not None else 6.5) + .5) * BW
        events.append((t, "release" if col is not None else "all", x, FLOORS[fl], float(fl), n))
    frames = []; ri = 0
    for f in range(int(T * FPS)):
        t = f / FPS
        for s in range(SUB):
            tnow[0] = t + s / (FPS * SUB)
            while ri < len(rel) and tnow[0] >= rel[ri][0]:
                release(rel[ri][1], rel[ri][2], tnow[0]); ri += 1
            sp.step(1 / (FPS * SUB))
        P = np.array([(b.position.x, b.position.y) for b in balls])
        B = np.array([(b.position.x, b.position.y, b.angle) for b, *_ in bricks])
        frames.append((P, B))
    return frames, events, dict(band=BAND, sub=sub, y0=Y0, rad=np.array(RAD), bricks=[(f_, c, r) for _, f_, c, r in bricks])

def fallen(P, y0): return int((P[:, 1] > y0 + 60).sum())

if __name__ == "__main__":
    t0 = time.time()
    fr, ev, meta = run(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    out = [fallen(f[0], meta["y0"]) for f in fr]
    for s in range(0, len(fr), 15): print(round(s / FPS, 1), out[s], end=" | ")
    B = np.array([f[1] for f in fr]); print("\nmax |pos|", np.abs(B[:, :, :2]).max().round())
    print("sim s", round(time.time() - t0, 1), "events", len(ev))
    pickle.dump((fr, ev, meta), open("sim.pkl", "wb"))
