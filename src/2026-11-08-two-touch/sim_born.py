"""No. 10 — 'When two touch, / a new one is born.'
A hexagonal glass cell in zero-g. Two pearls drift together; every time two grown pearls touch, a tiny new
pearl buds out of the contact point and swells to full size. Births multiply until the cell is full, then
everything cools and settles into a packed honeycomb of pearls."""
import pymunk, numpy as np, pickle, math, os
E = lambda k, d: float(os.environ.get(k, d))
FPS, SUB = 30, 4
DT = 1 / (FPS * SUB)
CX, CY, RH = 540.0, 1030.0, E("RH", 470)
BR = E("BR", 10.5); R0 = 1.5
GROW = E("GROW", .5); COOL = E("COOL", .6)
FAM = E("FAM", 1.0)
PHI = E("PHI", .80)
SECS = E("SECS", 28)
rng = np.random.default_rng(int(E("SEED", 3)))
VERT = [(CX + RH * math.cos(math.radians(-90 + 60 * k)), CY + RH * math.sin(math.radians(-90 + 60 * k))) for k in range(6)]
AREA = 1.5 * math.sqrt(3) * RH ** 2
NMAX = int(PHI * AREA / (math.pi * BR ** 2))

space = pymunk.Space(); space.iterations = 12; space.collision_slop = .15
for k in range(6):
    s = pymunk.Segment(space.static_body, VERT[k], VERT[(k + 1) % 6], 5)
    s.elasticity = 1.0; s.friction = 0; s.collision_type = 3; space.add(s)

B, S = [], []
born, last, parent = [], [], []
clock = {"t": 0.0}; pend = []; births = []; clacks = []
def add(p, v, t, par=(-1, -1)):
    b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR)); b.position = p; b.velocity = v
    s = pymunk.Circle(b, R0 if t > 0 else BR); s.elasticity = .98; s.friction = 0; s.collision_type = 1; s.idx = len(B)
    space.add(b, s); B.append(b); S.append(s); born.append(t if t > 0 else -9); last.append(t if t > 0 else -9); parent.append(par)
def on_bead(arb, sp, d):
    if not arb.is_first_contact: return
    a, b = arb.shapes; i, j = a.idx, b.idx; t = clock["t"]
    p = arb.contact_point_set.points[0].point_a; imp = arb.total_impulse.length
    ok = (t - born[i] > GROW and t - born[j] > GROW and t - last[i] > COOL and t - last[j] > COOL
          and len(B) + len(pend) < NMAX and not ((j in parent[i] and t - born[i] < FAM) or (i in parent[j] and t - born[j] < FAM)) and not stop["v"])
    if ok:
        last[i] = last[j] = t
        n = arb.contact_point_set.normal
        pend.append((i, j, (p.x, p.y), (n.x, n.y)))
    elif imp > 6:
        clacks.append((t, p.x, p.y, imp, 0))
def on_wall(arb, sp, d):
    if arb.is_first_contact and arb.total_impulse.length > 6:
        p = arb.contact_point_set.points[0].point_a
        clacks.append((clock["t"], p.x, p.y, arb.total_impulse.length, 1))
space.on_collision(1, 1, post_solve=on_bead)
space.on_collision(1, 3, post_solve=on_wall)
stop = {"v": False}

V0 = E("V0", 170)
D0 = E("D0", 230)
add((CX - D0, CY - 40), (V0, 18), 0)
add((CX + D0, CY + 40), (-V0, -18), 0)

frames, rads, counts = [], [], []
stop_t = None
for f in range(int(SECS * FPS)):
    t = f / FPS
    if stop_t is None and len(B) >= NMAX: stop_t = t; stop["v"] = True
    # thermostat: mean speed target
    if stop_t is None:
        vt = E("VA", 170) + E("VB", 90) * min(1, t / 6)
    else:
        vt = (E("VA", 170) + E("VB", 90)) * max(0, 1 - (t - stop_t) / E("COOLT", 3.5)) ** 2
    for s_ in range(SUB):
        clock["t"] = t + s_ * DT
        for k, s in enumerate(S):
            if born[k] > 0:
                age = clock["t"] - born[k]
                if age < GROW + DT:
                    s.unsafe_set_radius(R0 + (BR - R0) * min(1, age / GROW) ** .7)
        kw = E("KW", 10) * max(0, 1 - (len(B) - 2) / E("KN", 80)) ** 2
        if kw > 0:
            for b in B:
                b.apply_force_at_world_point((kw * (CX - b.position.x), kw * (CY - b.position.y)), b.position)
        space.step(DT)
        for (i, j, p, n) in pend:
            vi, vj = B[i].velocity, B[j].velocity
            sp_ = max(60, (vi.length + vj.length) / 2)
            sgn = 1 if rng.random() < .5 else -1
            v = (-n[1] * sp_ * sgn, n[0] * sp_ * sgn)
            births.append((clock["t"], p[0], p[1], len(B)))
            add(p, v, clock["t"], (i, j))
        pend.clear()
    if stop_t is not None:
        u = min(1, (t - stop_t) / E("SWT", 2.5)); rr = BR * (1 + E("SW", .05) * u * u * (3 - 2 * u))
        for k, s in enumerate(S):
            if clock["t"] - born[k] >= GROW: s.unsafe_set_radius(rr)
    V = np.array([b.velocity for b in B]); ms = np.sqrt((V ** 2).sum(1)).mean()
    fac = 1.0 if ms < 1e-6 else (vt / ms) ** .15 if stop_t is None else max(0.0, min(1, vt / ms))
    if stop_t is not None and vt < 1: fac = .85
    for b in B: b.velocity = b.velocity * fac
    P = np.array([b.position for b in B], np.float32)
    R = np.array([s.radius for s in S], np.float32)
    frames.append(P); rads.append(R); counts.append(len(B))
    if f % 30 == 0: print(f"t={t:4.1f} n={len(B):5d} ms={ms:6.1f}", flush=True)
    if stop_t is not None and t > stop_t + E("TAIL", 5): break
print("frames", len(frames), "N", len(B), "NMAX", NMAX, "stop", stop_t)
# escape check
P = frames[-1]
print("max |dx|", np.abs(P[:, 0] - CX).max(), "y", P[:, 1].min(), P[:, 1].max())
pickle.dump(dict(frames=frames, rads=rads, counts=np.array(counts), born=np.array(born), births=births, clacks=clacks,
                 stop=stop_t, geom=dict(CX=CX, CY=CY, RH=RH, BR=BR, VERT=VERT)), open("born.pkl", "wb"))
