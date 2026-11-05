"""Sample B — 'Every bounce splits it in two.'
One big sphere in a round glass arena (no gravity). Each wall bounce splits a sphere into two of half the
area. When nothing is left that can split, gravity fades in and the glitter rains down and settles."""
import pymunk, numpy as np, pickle, math, random, os
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 6
DT = E("TS", 1.0) / (FPS * SUB)
CX, CY, R = 540.0, 1010.0, 400.0
R0 = E("R0", 110.0); RMIN = E("RMIN", 2.6)
COOL = E("COOL", 0.25)
SECS = E("SECS", 26)
random.seed(7)

space = pymunk.Space(); space.gravity = (0, 0); space.iterations = 10; space.collision_slop = .2
st = space.static_body
NSEG = 160
for i in range(NSEG):
    a0, a1 = 2 * math.pi * i / NSEG, 2 * math.pi * (i + 1) / NSEG
    s = pymunk.Segment(st, (CX + R * math.cos(a0), CY + R * math.sin(a0)), (CX + R * math.cos(a1), CY + R * math.sin(a1)), 4)
    s.elasticity = 1.0; s.friction = 0.0; s.collision_type = 3; space.add(s)

balls, rad, gen, born, lastsplit = [], [], [], [], []
clock = {"t": 0.0}; pending = []; events = []
def add_ball(p, v, r, g, f):
    m = (r / R0) ** 2 * 100
    b = pymunk.Body(m, pymunk.moment_for_circle(m, 0, r)); b.position = p; b.velocity = v
    s = pymunk.Circle(b, r); s.elasticity = .97; s.friction = 0; s.collision_type = 1; s.idx = len(balls)
    space.add(b, s); balls.append((b, s)); rad.append(r); gen.append(g); born.append(f); lastsplit.append(clock["t"])
def on_wall(arb, sp, d):
    if not arb.is_first_contact: return
    s = arb.shapes[0]; i = s.idx
    p = arb.contact_point_set.points[0].point_a
    events.append((clock["t"], p.x, p.y, arb.total_impulse.length, "wall", rad[i]))
    if rad[i] / math.sqrt(2) >= RMIN and clock["t"] - lastsplit[i] > COOL and not split_off["v"]:
        pending.append(i)
def on_ball(arb, sp, d):
    if arb.is_first_contact and arb.total_impulse.length > 2:
        a, b = arb.shapes; p = arb.contact_point_set.points[0].point_a
        events.append((clock["t"], p.x, p.y, arb.total_impulse.length, "ball", min(rad[a.idx], rad[b.idx])))
space.on_collision(1, 3, post_solve=on_wall)
space.on_collision(1, 1, post_solve=on_ball)
split_off = {"v": False}

add_ball((CX - 60, CY - 120), (520, 380), R0, 0, 0)

frames, counts, gravity_at, radf = [], [], None, []
nosplit = 0
for f in range(int(SECS * FPS)):
    did = False
    for s_ in range(SUB):
        clock["t"] = (f + s_ / SUB) / FPS
        space.step(DT)
        for b, sh in balls:
            dx, dy = b.position.x - CX, b.position.y - CY
            dist = math.hypot(dx, dy); lim = R - sh.radius - 2
            if dist > lim:
                nx, ny = dx / dist, dy / dist
                b.position = (CX + nx * lim, CY + ny * lim)
                vn = b.velocity.x * nx + b.velocity.y * ny
                if vn > 0: b.velocity = (b.velocity.x - 2 * vn * nx, b.velocity.y - 2 * vn * ny)
        if not split_off["v"] and s_ == 0:
            vmin = E('VMIN', 480)
            for b, sh in balls:
                sp_ = b.velocity.length
                if sp_ < vmin:
                    b.velocity = (b.velocity.normalized() if sp_ > 1 else pymunk.Vec2d(random.uniform(-1, 1), random.uniform(-1, 1)).normalized()) * vmin
        if pending:
            done = set()
            for i in pending:
                if i in done: continue
                done.add(i)
                b, s = balls[i]
                r2 = rad[i] / math.sqrt(2)
                pos, v = b.position, b.velocity
                v = (v.normalized() if v.length > 1 else pymunk.Vec2d(1, 0)) * E('SPD', 620)
                # replace parent by two children placed side by side, perpendicular to motion
                perp = v.perpendicular_normal() if v.length > 1 else pymunk.Vec2d(1, 0)
                space.remove(b, s)
                rad[i] = r2; gen[i] += 1; lastsplit[i] = clock["t"]
                m = (r2 / R0) ** 2 * 100
                nb = pymunk.Body(m, pymunk.moment_for_circle(m, 0, r2)); nb.position = pos + perp * r2 * 1.02
                nb.velocity = v.rotated(.28)
                ns = pymunk.Circle(nb, r2); ns.elasticity = .97; ns.friction = 0; ns.collision_type = 1; ns.idx = i
                space.add(nb, ns); balls[i] = (nb, ns)
                add_ball(pos - perp * r2 * 1.02, v.rotated(-.28), r2, gen[i], f)
                events.append((clock["t"], pos.x, pos.y, 0, "split", r2))
                did = True
            pending.clear()
    frames.append(np.array([[b.position.x, b.position.y] for b, s in balls], np.float32))
    counts.append(len(balls)); radf.append(np.array(rad, np.float32))
    can = any(r / math.sqrt(2) >= RMIN for r in rad)
    if gravity_at is None and (not can or len(balls) >= E("NGRAV", 1950) or (f > 60 and nosplit > 45)):
        gravity_at = f; split_off["v"] = True
        print("gravity on at", round(f / FPS, 1), "n", len(balls))
    nosplit = 0 if did else nosplit + 1
    if gravity_at is not None:
        u = min(1.0, (f - gravity_at) / 30)
        space.gravity = (0, 1500 * u)
        if f - gravity_at == 1:
            for b, s in balls: s.elasticity = .35; s.friction = .3
    if f % 60 == 0: print(f"t={f / FPS:4.1f} n={len(balls)} rmin={min(rad):.1f}", flush=True)
    if gravity_at is not None and f > gravity_at + E('SETTLE', 120): break
print("frames", len(frames), "n", len(balls))
pickle.dump(dict(frames=frames, radf=radf, counts=np.array(counts), rad=np.array(rad), gen=np.array(gen), born=np.array(born),
                 events=events, gravity_at=gravity_at, geom=dict(CX=CX, CY=CY, R=R, R0=R0)), open("split.pkl", "wb"))
