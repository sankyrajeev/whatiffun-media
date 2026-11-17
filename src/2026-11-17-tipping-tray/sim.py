"""TIPPING TRAY: a big glass tray packed with ~1,000 glossy balls, its open end held shut by a dam of loose
bricks, tilts further and further. Dam bricks pop out one after another (balls trickle through the gaps),
then the dam bursts and the tray pours into the bin below, smashing a brick pyramid. Real pymunk (seeded)."""
import sys, math, pickle, time
import numpy as np, pymunk

FPS, SUB = 30, 6
PX, PY = 505, 888                 # pivot (tray centre)
HW, HH = 360, 188                 # tray half extents (local)
DCOLS, DROWS, DW = 1, 9, 40       # dam: 2 columns x 7 rows of bricks at the open (right) end
DH = 2 * HH / DROWS
BX0, BX1, BTOP, BY = 120, 965, 1080, 1590
BRTOP = 880
PB_W, PB_H, PB_N, PB_CX = 66, 36, 7, 700
RMIN, RMAX = 4.6, 7.0
TBACK = 11.3
TB = 4.8                          # dam bursts
REL = [(0.25, 0, 4), (1.25, 0, 2), (2.25, 0, 6), (3.20, 0, 3), (4.05, 0, 1)]  # (t, col, row 0=top)
LATE = [(7.8, 0, 8)]   # the last bricks of the weir go

def tilt(t):
    a0, a1, a2 = math.radians(3), math.radians(17), math.radians(38)
    if t < TB: return a0 + (a1 - a0) * (t / TB) ** 1.6
    if t < TBACK:
        u = min(1, (t - TB) / 10.0); return a1 + (a2 - a1) * (u * u * (3 - 2 * u))
    u0 = min(1, (TBACK - TB) / 10.0); aa = a1 + (a2 - a1) * (u0 * u0 * (3 - 2 * u0))
    u = min(1, (t - TBACK) / 1.5); return aa + (math.radians(4) - aa) * (u * u * (3 - 2 * u))

def run(seed=1, T=19.5):
    rng = np.random.default_rng(seed)
    sp = pymunk.Space(); sp.gravity = (0, 1100); sp.iterations = 22
    st = sp.static_body
    for a, b in (((BX0, BTOP), (BX0, BY)), ((BX1, BRTOP), (BX1, BY)), ((BX0 - 4, BY), (BX1 + 4, BY))):
        s = pymunk.Segment(st, a, b, 7); s.friction = .5; s.elasticity = .3; s.collision_type = 3; sp.add(s)
    tray = pymunk.Body(body_type=pymunk.Body.KINEMATIC); tray.position = (PX, PY); tray.angle = tilt(0)
    sp.add(tray)
    for a, b in (((-HW, -HH - 20), (-HW, HH)), ((-HW, HH), (HW, HH))):
        s = pymunk.Segment(tray, a, b, 5); s.friction = .45; s.elasticity = .3; s.collision_type = 3; sp.add(s)
    dam = []
    for c in range(DCOLS):
        for r in range(DROWS):
            b = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            loc = (HW - DW * (DCOLS - c) + DW / 2, -HH + (r + .5) * DH)
            s = pymunk.Poly.create_box(b, (DW - 3, DH - 3), 2.5); s.mass = 6; s.friction = .4; s.elasticity = .2
            s.collision_type = 4; sp.add(b, s); dam.append([b, loc, c, r, False])
    pyr = []
    for row in range(PB_N):
        n = PB_N - row
        for k in range(n):
            b = pymunk.Body(3, pymunk.moment_for_box(3, (PB_W - 3, PB_H - 2)))
            b.position = (PB_CX + (k - (n - 1) / 2) * PB_W, BY - 3 - (row + .5) * PB_H)
            s = pymunk.Poly.create_box(b, (PB_W - 3, PB_H - 2), 2); s.friction = .55; s.elasticity = .15; s.collision_type = 4
            sp.add(b, s); pyr.append(b)
    def follow(th, w):
        tray.angle = th; tray.angular_velocity = w; tray.position = (PX, PY); tray.velocity = (0, 0)
        cs, sn = math.cos(th), math.sin(th)
        for d in dam:
            if d[4]: continue
            b, (lx, ly) = d[0], d[1]
            rx, ry = lx * cs - ly * sn, lx * sn + ly * cs
            b.position = (PX + rx, PY + ry); b.angle = th; b.velocity = (-w * ry, w * rx); b.angular_velocity = w
    follow(tilt(0), 0)
    balls, RAD, U = [], [], []
    d = 2 * RMAX + .6
    th = tilt(0); cs, sn = math.cos(th), math.sin(th)
    xmax = HW - DW * DCOLS - RMAX - 2
    j = 0; y = HH - RMAX - 3
    while y > -HH + 22:
        for x in np.arange(-HW + RMAX + 4 + (d / 2 if j % 2 else 0), xmax, d):
            rr = rng.uniform(RMIN, RMAX); m = rr * rr / 49
            b = pymunk.Body(m, pymunk.moment_for_circle(m, 0, rr))
            lx, ly = x + rng.uniform(-.3, .3), y
            b.position = (PX + lx * cs - ly * sn, PY + lx * sn + ly * cs)
            s = pymunk.Circle(b, rr); s.friction = .4; s.elasticity = .35; s.collision_type = 1
            sp.add(b, s); balls.append(b); RAD.append(rr); U.append((lx, ly))
        y -= d * .866; j += 1
    for k in range(int(2.5 * FPS * SUB)): follow(tilt(0), 0); sp.step(1 / (FPS * SUB))
    for b in balls: b.velocity = (0, 0)
    for b in pyr: b.velocity = (0, 0); b.angular_velocity = 0
    for k in range(int(.6 * FPS * SUB)): follow(tilt(0), 0); sp.step(1 / (FPS * SUB))
    U = np.array(U)
    events = []; tnow = [0.0]
    def post(arb, space, data):
        a, b = arb.bodies
        rv = abs((a.velocity - b.velocity).dot(arb.normal))
        if rv > 140:
            p = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else a.position
            events.append((tnow[0], data, float(p.x), float(p.y), float(rv)))
    for (ca, cb), nm in (((1, 3), "wall"), ((1, 1), "ball"), ((1, 4), "ballbrick"), ((4, 3), "brick"), ((4, 4), "brick2")):
        sp.on_collision(ca, cb, begin=post, data=nm)
    def release(sel, t, burst):
        for dd in dam:
            if dd[4] or not sel(dd): continue
            dd[4] = True; b = dd[0]
            b.body_type = pymunk.Body.DYNAMIC; b.mass = 6; b.moment = pymunk.moment_for_box(6, (DW - 3, DH - 3))
            th = tray.angle
            push = rng.uniform(170, 240) * (1.2 if burst else 1)
            b.velocity = (b.velocity.x + push * math.cos(th), b.velocity.y + push * math.sin(th) - rng.uniform(0, 60))
            b.angular_velocity = rng.uniform(-4, 4)
            events.append((t, "all" if burst else "release", float(b.position.x), float(b.position.y), 0.0, 1, float(PX + (HW - 10) * math.cos(th)), float(PY + (HW - 10) * math.sin(th))))
    frames = []; ri = 0; li = 0; burst = False
    dt = 1 / (FPS * SUB)
    for f in range(int(T * FPS)):
        t = f / FPS
        for s in range(SUB):
            tn = t + s * dt; tnow[0] = tn
            while ri < len(REL) and tn >= REL[ri][0]:
                c_, r_ = REL[ri][1], REL[ri][2]; release(lambda dd: dd[2] == c_ and dd[3] == r_, tn, False); ri += 1
            if not burst and tn >= TB: release(lambda dd: dd[3] <= 7, tn, True); burst = True
            while li < len(LATE) and tn >= LATE[li][0]:
                r_ = LATE[li][2]; release(lambda dd: dd[3] == r_, tn, True); li += 1
            th = tilt(tn); w = (tilt(tn + dt) - th) / dt
            follow(th, w); sp.step(dt)
        P = np.array([(b.position.x, b.position.y) for b in balls])
        B = np.array([(dd[0].position.x, dd[0].position.y, dd[0].angle) for dd in dam] +
                     [(b.position.x, b.position.y, b.angle) for b in pyr])
        frames.append((P, B, tray.angle))
    return frames, events, dict(u=U, rad=np.array(RAD), ndam=len(dam), npyr=len(pyr))

def out_count(P, th):
    cs, sn = math.cos(th), math.sin(th)
    dx, dy = P[:, 0] - PX, P[:, 1] - PY
    lx = dx * cs + dy * sn; ly = -dx * sn + dy * cs
    return int(((lx > HW + 4) | (ly > HH + 6) | (lx < -HW - 6)).sum())

if __name__ == "__main__":
    t0 = time.time()
    fr, ev, meta = run(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    out = [out_count(f[0], f[2]) for f in fr]
    print("balls", len(meta["u"]))
    for s in range(0, len(fr), 15): print(round(s / FPS, 1), out[s], end=" | ")
    P = np.array([f[0] for f in fr]); print("\nminy", P[:, :, 1].min().round(), "maxy", P[:, :, 1].max().round(), "minx", P[:, :, 0].min().round(), "maxx", P[:, :, 0].max().round())
    print("sim s", round(time.time() - t0, 1), "events", len(ev))
    pickle.dump((fr, ev, meta), open("sim.pkl", "wb"))
