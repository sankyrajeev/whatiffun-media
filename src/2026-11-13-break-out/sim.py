"""BREAK OUT: one glowing ball bounces inside a round glass cage with ONE gap. Its hit points creep
around the rim (a circle preserves the impact parameter), grazing the gap again and again; once it
slips out, the gap seals, and every curved brick in the rainbow ring around the cage that it breaks
may add a ball, until the ring is cleared."""
import sys, math, pickle, time
import numpy as np

FPS = 30
CX, CY = 540.0, 1010.0
RC = 196.0                 # cage radius (inner surface)
RB0, BT, NRING = 232.0, 19.5, 10   # brick ring: inner radius, thickness, rings
RO = RB0 + BT * NRING + 4  # outer steel wall (inner surface) = 431
RH, RS = 18.0, 5.0         # hero / swarm ball radius
GAPW = 2 * RH + 14         # gap arc length (px at RC)
SPEED_H, SPEED_S = 620.0, 610.0
SUB = 8
DT = 1 / (FPS * SUB)
MAXB = 1500
NSEC = [int(round(2 * math.pi * (RB0 + (k + .5) * BT) / 22)) for k in range(NRING)]
MAXS = max(NSEC)

def bricks():
    g = np.zeros((NRING, MAXS), bool)
    for k in range(NRING): g[k, :NSEC[k]] = True
    return g

def ang_diff(a, b): return (a - b + math.pi) % (2 * math.pi) - math.pi

def run(b, phi0, gap_ang, T, pspawn=.4, seed=3, jit=0.0, jseed=0):
    """b = impact parameter offset of the start, phi0 = launch direction, gap_ang = gap centre angle."""
    g = bricks(); nsec = np.array(NSEC)
    rng = np.random.default_rng(seed); jr = np.random.default_rng(jseed)
    P = np.zeros((MAXB, 2)); V = np.zeros((MAXB, 2)); Rr = np.full(MAXB, RS); out = np.zeros(MAXB, bool)
    P[0] = (CX + b * math.cos(phi0 + math.pi / 2), CY + b * math.sin(phi0 + math.pi / 2))
    V[0] = (SPEED_H * math.cos(phi0), SPEED_H * math.sin(phi0)); Rr[0] = RH; n = 1
    half = GAPW / 2 / RC
    sealed = gap_ang is None; t_out = None
    if gap_ang is None: gap_ang = 0.0
    frames, events, broken = [], [], []
    src = [None]
    for f in range(int(T * FPS)):
        for s in range(SUB):
            t = (f * SUB + s) * DT
            p, v, rr, o = P[:n], V[:n], Rr[:n], out[:n]
            q = p + v * DT
            d = q - (CX, CY); r = np.hypot(d[:, 0], d[:, 1]); nrm = d / r[:, None]
            th = np.arctan2(d[:, 1], d[:, 0])
            hit = np.zeros(n, bool); refl_r = np.zeros(n, bool); handled = np.zeros(n, bool)
            # inside the cage
            ins = ~o
            if ins.any():
                wall = ins & (r + rr > RC)
                for k in np.where(wall)[0]:
                    off = ang_diff(th[k], gap_ang) * RC          # arc offset of the centre from the gap centre
                    if sealed or abs(off) > GAPW / 2:             # centre outside the opening: plain wall bounce
                        events.append((t, "cage", q[k, 0], q[k, 1], float(off)))
                        hit[k] = True; refl_r[k] = True
                    else:                                         # in the opening: only the two posts can stop it
                        for sg in (-1, 1):
                            pa = gap_ang + sg * GAPW / 2 / RC
                            px, py = CX + RC * math.cos(pa), CY + RC * math.sin(pa)
                            dx, dy = q[k, 0] - px, q[k, 1] - py; dd = math.hypot(dx, dy)
                            if dd < rr[k]:
                                nx_, ny_ = dx / dd, dy / dd; vn = V[k, 0] * nx_ + V[k, 1] * ny_
                                if vn < 0: V[k] -= 2 * vn * np.array([nx_, ny_])
                                events.append((t, "post", px, py, float(off)))
                                hit[k] = True; handled[k] = True; break
                    esc = ins & (r - rr > RC + 7)
                    if esc.any():
                        out[:n][esc] = True
                        if t_out is None: t_out = t; events.append((t, "out", q[0, 0], q[0, 1]))
            # outside: cage outer skin (sealed), outer wall, bricks
            o = out[:n]
            if t_out is not None:
                if not sealed:                       # the gap seals right behind the escaping ball
                    sealed = True; events.append((t, "seal", CX + RC * math.cos(gap_ang), CY + RC * math.sin(gap_ang)))
                skin = o & (r - rr < RC + 7) & sealed
                hit |= skin; refl_r |= skin
                ow = o & (r + rr > RO)
                for k in np.where(ow)[0]: events.append((t, "wall", q[k, 0], q[k, 1]))
                hit |= ow; refl_r |= ow
                # brick probe along velocity
                cand = o & ~hit
                if cand.any():
                    idx = np.where(cand)[0]
                    vn = v[idx] / np.hypot(v[idx, 0], v[idx, 1])[:, None]
                    pr = q[idx] + vn * rr[idx, None]
                    dd = pr - (CX, CY); rp = np.hypot(dd[:, 0], dd[:, 1]); tp = np.arctan2(dd[:, 1], dd[:, 0]) % (2 * np.pi)
                    ki = np.floor((rp - RB0) / BT).astype(int)
                    ok = (ki >= 0) & (ki < NRING)
                    kc = np.clip(ki, 0, NRING - 1)
                    si = np.floor(tp / (2 * np.pi) * nsec[kc]).astype(int) % nsec[kc]
                    occ = ok & g[kc, si]
                    # was the previous probe in the same ring? -> crossed a sector edge (tangential)
                    dp = p[idx] + vn * rr[idx, None] - (CX, CY)
                    kprev = np.floor((np.hypot(dp[:, 0], dp[:, 1]) - RB0) / BT).astype(int)
                    for m in np.where(occ)[0]:
                        k = idx[m]; a, sct = kc[m], si[m]
                        if not g[a, sct]: continue
                        g[a, sct] = False
                        broken.append((t, int(a), int(sct)))
                        events.append((t, "pop", q[k, 0], q[k, 1], int(a)))
                        hit[k] = True
                        if kprev[m] != a: refl_r[k] = True
                        if n < MAXB and (len(broken) <= 6 or rng.random() < pspawn):
                            rot = rng.uniform(-.7, .7); c_, s_ = math.cos(rot), math.sin(rot)
                            vx, vy = -V[k]
                            sp = SPEED_S / math.hypot(vx, vy)
                            P[n] = p[k]; V[n] = (sp * (vx * c_ - vy * s_), sp * (vx * s_ + vy * c_)); out[n] = True; n += 1; src.append((int(a), int(sct)))
                            p, v, rr = P[:n], V[:n], Rr[:n]
                            hit = np.append(hit, False); refl_r = np.append(refl_r, False); handled = np.append(handled, False)
                            q = np.vstack([q, P[n - 1:n]]); nrm = np.vstack([nrm, nrm[k:k + 1]])
            m = len(hit)
            # reflect
            rad = hit & refl_r & ~handled
            if rad.any():
                vn = (V[:m][rad] * nrm[:m][rad]).sum(1)
                V[:m][rad] -= 2 * vn[:, None] * nrm[:m][rad]
            if jit and t_out is None and hit[0]:      # tiny, deterministic wobble on each cage bounce
                a = jr.normal(0, jit); c_, s_ = math.cos(a), math.sin(a); vx, vy = V[0]
                V[0] = (vx * c_ - vy * s_, vx * s_ + vy * c_)
            tan = hit & ~refl_r & ~handled
            if tan.any():
                tv = np.stack([-nrm[:m][tan][:, 1], nrm[:m][tan][:, 0]], 1)
                vt = (V[:m][tan] * tv).sum(1)
                V[:m][tan] -= 2 * vt[:, None] * tv
            mv = ~hit
            P[:m][mv] = q[:m][mv]
            if t_out is not None and Rr[0] > RS:      # hero shrinks to swarm size once out
                Rr[0] = max(RS, Rr[0] - 40 * DT)
                sp = math.hypot(*V[0]); V[0] *= (sp + (SPEED_S - sp) * .02) / sp
        frames.append((P[:n].copy(), len(broken), Rr[0]))
    run.src = src
    return frames, events, broken, t_out

TOTAL_BRICKS = sum(NSEC)

def plan():
    """search start offset + launch + gap angle: escape in 11.5–13.5 s with the most spread near misses"""
    best = []
    for b in (60, 80, 100, 120):
        for js in range(int(sys.argv[2]), int(sys.argv[3])):
            phi = 0.0
            fr, ev, br, to = run(b, phi, None, 14.5, jit=.06, jseed=js)   # sealed cage: just the hero's hit points
            hits = [(e[0], math.atan2(e[3] - CY, e[2] - CX)) for e in ev if e[1] == "cage"]
            for ga in np.linspace(-np.pi, np.pi, 72, endpoint=False):
                # first time a hit lands inside the passable window
                lim = GAPW / 2 - RH + 1.5
                T = next((t for t, a in hits if abs(ang_diff(a, ga)) * RC < lim), None)
                if T is None or not (11.0 <= T <= 14.0): continue
                near = [t for t, a in hits if t < T and lim <= abs(ang_diff(a, ga)) * RC < lim + 40]
                if len(near) < 3: continue
                # spread: distinct seconds, earliest near miss early
                spread = len(set(int(t / 1.5) for t in near))
                gaps = np.diff([0] + near + [T]); score = spread * 10 + len(near) - 4 * max(0, gaps.max() - 2.5) - 6 * (near[-1] < T - 2.2)
                best.append((score, js, round(float(b), 1), round(float(phi), 3), round(float(ga), 3), round(T, 2), [round(x, 1) for x in near]))
    best.sort(reverse=True)
    for x in best[:12]: print(x)

if __name__ == "__main__":
    if sys.argv[1] == "plan": plan()
    elif sys.argv[1] == "sim":
        b, phi, ga, ps, js = map(float, sys.argv[2:7])
        t0 = time.time()
        fr, ev, br, to = run(b, phi, ga, 26, pspawn=ps, jit=.06, jseed=int(js))
        nb = [len(f[0]) for f in fr]; nbr = [f[1] for f in fr]
        clear = next((k for k, x in enumerate(nbr) if x >= TOTAL_BRICKS), None)
        print("bricks", TOTAL_BRICKS, "out", to, "cleared", clear and clear / FPS, "max balls", max(nb), "sim s", round(time.time() - t0, 1))
        for s in range(10, 26): print(s, nb[s * FPS], nbr[s * FPS])
        near = [(round(e[0], 2), round(e[4])) for e in ev if e[1] == "cage" and abs(e[4]) < 60]
        print("near:", near[:20])
        pickle.dump((fr, ev, br, to, (b, phi, ga, ps), run.src), open(sys.argv[7] if len(sys.argv) > 7 else "sim.pkl", "wb"))
