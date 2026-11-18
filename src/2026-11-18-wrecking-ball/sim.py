"""WRECKING BALL: a glass tank packed with ~1,300 glossy balls, its left side one brick wall. A heavy brass
wrecking ball swings at it: a near miss, a kiss that knocks one brick out (balls trickle through), then a
full swing smashes the wall and the tank floods out under the ball. Real pymunk (seeded)."""
import sys, math, pickle, time
import numpy as np, pymunk

FPS, SUB = 30, 7
PVX, PVY, L, WR = 262, 520, 742, 76      # pivot, chain length, wrecking-ball radius
WX0, BW, BH = 450, 48, 36                 # brick wall 1: left face, brick size
WX2, WX3, WX4 = 590, 720, 850             # brick walls 2-4: left faces
WALLS = (WX0, WX2, WX3, WX4)
X1, FY, WTOP = 975, 1590, 798             # tank right glass wall, floor, wall top
XL = 104                                  # left glass wall of the bin
NROW = int(round((FY - WTOP) / BH))
RMIN, RMAX = 6.2, 8.8
SLOPE = 150                               # tank floor rises this much toward the right glass wall
# (time, angle deg) swing peaks; + = toward the wall
PEAKS = [(-0.45, -9), (0.4, 6.5), (1.25, -9.5), (2.1, 10.2), (2.95, -10), (3.95, 18), (4.9, -9),
         (5.95, 27), (7.0, -9), (8.1, 38), (9.2, -9), (10.4, 52), (11.6, -8), (12.7, 28), (13.8, -6), (14.8, 14), (15.7, -3), (16.6, 0), (40, 0)]

def ang(t):
    for (t0, a0), (t1, a1) in zip(PEAKS, PEAKS[1:]):
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0); return math.radians(a0 + (a1 - a0) * (1 - math.cos(math.pi * u)) / 2)
    return 0.0
def wpos(t):
    a = ang(t); return PVX + L * math.sin(a), PVY + L * math.cos(a)

def run(seed=1, T=18.0):
    rng = np.random.default_rng(seed)
    sp = pymunk.Space(); sp.gravity = (0, 1150); sp.iterations = 20
    st = sp.static_body
    for a, b in (((XL, 760), (XL, FY + 20)), ((X1, 560), (X1, FY)), ((XL - 30, FY + 16), (X1 + 30, FY + 16)), ((WX0 + BW, FY), (X1, FY - SLOPE))):
        s = pymunk.Segment(st, a, b, 14); s.friction = .5; s.elasticity = .3; s.collision_type = 3; sp.add(s)
    wb = pymunk.Body(body_type=pymunk.Body.KINEMATIC); wb.position = wpos(0)
    ws = pymunk.Circle(wb, WR); ws.friction = .3; ws.elasticity = .2; ws.collision_type = 5; sp.add(wb, ws)
    bricks = []
    for wi, wx in enumerate(WALLS):
        fl = FY - (wx + BW / 2 - WX0 - BW) / (X1 - WX0 - BW) * SLOPE if wi else FY
        for r in range(int((fl - WTOP) // BH)):
            y = fl - 12 - (r + .5) * BH if wi else fl - (r + .5) * BH
            b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = (wx + BW / 2, y)
            s = pymunk.Poly.create_box(b, (BW - 2, BH - 2), 2); s.friction = .55; s.elasticity = .15; s.collision_type = 4
            sp.add(b, s); bricks.append([b, s, wi, False])
    balls, RAD = [], []
    def vlim(body, g, damp, dt_):
        pymunk.Body.update_velocity(body, g, damp, dt_)
        if body.velocity.length > 850: body.velocity = body.velocity * (850 / body.velocity.length)
    d = 2 * RMAX + .3
    j = 0; y = FY - RMAX - 2
    while y > WTOP - 40:
        for x in np.arange(WX0 + BW + RMAX + 2 + (d / 2 if j % 2 else 0), X1 - RMAX - 3, d):
            rr = rng.uniform(RMIN, RMAX); m = rr * rr / 64
            if y > FY - (x - WX0 - BW) / (X1 - WX0 - BW) * SLOPE - 14 - rr: continue
            if any(wx - rr - 1 < x < wx + BW + rr + 1 for wx in WALLS[1:]): continue
            b = pymunk.Body(m, pymunk.moment_for_circle(m, 0, rr)); b.position = (x + rng.uniform(-.4, .4), y)
            b.velocity_func = vlim
            s = pymunk.Circle(b, rr); s.friction = .38; s.elasticity = .3; s.collision_type = 1
            sp.add(b, s); balls.append(b); RAD.append(rr)
        y -= d * .866; j += 1
    dt = 1 / (FPS * SUB)
    for k in range(int(2.5 * FPS * SUB)): sp.step(dt)
    for b in balls: b.velocity = (0, 0)
    Y0 = [b.position.y for b in balls]; X0 = [b.position.x for b in balls]
    events = []; tnow = [0.0]
    def post(arb, space, data):
        a, b = arb.bodies
        rv = abs((a.velocity - b.velocity).dot(arb.normal))
        if rv > 130:
            p = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else a.position
            events.append((tnow[0], data, float(p.x), float(p.y), float(rv)))
    for (ca, cb), nm in (((1, 3), "wall"), ((1, 1), "ball"), ((1, 4), "ballbrick"), ((4, 3), "brick"), ((4, 4), "brick2"), ((5, 1), "wb"), ((5, 4), "wbbrick")):
        sp.on_collision(ca, cb, begin=post, data=nm)
    smashed = [False] * 4
    def release(br, vx, vy, kind, t):
        b = br[0]; br[3] = True
        b.body_type = pymunk.Body.DYNAMIC; b.mass = 5; b.moment = pymunk.moment_for_box(5, (BW - 2, BH - 2))
        b.velocity = (vx, vy); b.angular_velocity = rng.uniform(-3, 3)
        events.append((t, kind, float(b.position.x), float(b.position.y), math.hypot(vx, vy)))
    frames = []
    for f in range(int(T * FPS)):
        t = f / FPS
        for s in range(SUB):
            tn = t + s * dt; tnow[0] = tn
            x0, y0 = wpos(tn); x1, y1 = wpos(tn + dt)
            wb.position = (x0, y0); wb.velocity = ((x1 - x0) / dt, (y1 - y0) / dt)
            for br in bricks:
                if br[3]: continue
                bx, by = br[0].position
                cx = min(max(x1, bx - BW / 2), bx + BW / 2); cy = min(max(y1, by - BH / 2), by + BH / 2)
                if (x1 - cx) ** 2 + (y1 - cy) ** 2 < (WR + 1) ** 2:
                    v = wb.velocity
                    wi = br[2]
                    if v.length > 450 and not smashed[wi]:
                        smashed[wi] = True
                        for b2 in bricks:
                            if b2[3] or b2[2] != wi: continue
                            dy = b2[0].position.y - y1
                            k = math.exp(-(dy / 170) ** 2)
                            release(b2, v.x * (.25 + 1.0 * k) + rng.uniform(-60, 60), max(-160, v.y * k * .4) - rng.uniform(0, 100) * k, ("smash", "smash2", "smash3", "smash4")[wi] if b2 is br else "fall", tn)
                    else:
                        release(br, v.x * .35, v.y * .3, "kiss", tn)
            sp.step(dt)
        P = np.array([(b.position.x, b.position.y) for b in balls])
        B = np.array([(br[0].position.x, br[0].position.y, br[0].angle) for br in bricks])
        frames.append((P, B, ang(t), (wb.position.x, wb.position.y)))
    return frames, events, dict(rad=np.array(RAD), nb=len(bricks), y0=np.array(Y0), x0=np.array(X0))

X0G = None
def out_count(P, x0, y0):
    return int((np.hypot(P[:, 0] - x0, P[:, 1] - y0) > 45).sum())

if __name__ == "__main__":
    t0 = time.time()
    fr, ev, meta = run(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    out = [out_count(f[0], meta['x0'], meta['y0']) for f in fr]
    print("balls", len(meta["rad"]), "rows", NROW)
    for s in range(0, len(fr), 15): print(round(s / FPS, 1), out[s], end=" | ")
    P = np.array([f[0] for f in fr]); print("\nminy", P[:, :, 1].min().round(), "maxy", P[:, :, 1].max().round(), "minx", P[:, :, 0].min().round(), "maxx", P[:, :, 0].max().round())
    print([(round(e[0], 2), e[1]) for e in ev if e[1] in ("kiss", "smash", "smash2", "smash3", "smash4")])
    print("sim s", round(time.time() - t0, 1), "events", len(ev))
    pickle.dump((fr, ev, meta), open("sim.pkl", "wb"))
