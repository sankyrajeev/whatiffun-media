"""ONE HOLE / FILL IT: one big glowing ball bounces on a brass plate with ONE hole, inside a tall
glass jar. Each landing creeps sideways (side walls fold it back), so it lands beside the hole again
and again (and rattles off its rim) until it drops through. The hole seals; below, every bounce may
add a ball, and balls that have bounced enough settle into a hex packing, so the jar fills from the
bottom up until it is full."""
import sys, math, pickle, time
import numpy as np

FPS = 30
SUB = 8
DT = 1 / (FPS * SUB)
XL, XR = 160.0, 920.0           # jar inner walls
YTOP = 548.0                    # jar ceiling (upper chamber top)
YLID = 880.0                    # top of the brass plate
LIDT = 18.0                     # plate thickness
YLB = YLID + LIDT               # plate underside
YFL = 1560.0                    # jar floor
RH, RS = 34.0, 10.5             # hero / swarm radius
HW = RH + 8.0                   # hole half width
G = 2200.0
VLO, VHI = 450.0, 820.0

# hex slots
SL = []
dx = 2 * RS + .6; dy = dx * math.sqrt(3) / 2
row = 0
while True:
    y = YFL - RS - row * dy
    if y < YLB + 16: break
    off = 0 if row % 2 == 0 else dx / 2
    x = XL + RS + 1 + off
    while x <= XR - RS - 1:
        SL.append((row, x, y)); x += dx
    row += 1
SL = np.array(SL); NSL = len(SL); NROW = row
NB_BIN = int((XR - XL) // 8) + 1

def run(x0, vx0, hx, T, p=.8, nb=3, seed=3, jit=0.0, jseed=0, apex=YTOP + 60, stop=False):
    rng = np.random.default_rng(seed); jr = np.random.default_rng(jseed)
    vy0 = -math.sqrt(2 * G * (YLID - RH - apex))
    hx_, hy_ = x0, YLID - RH
    hv = [vx0, vy0]
    events = []; frames = []
    t_in = None
    # swarm (inside jar)
    MAX = NSL + 50
    P = np.zeros((MAX, 2)); V = np.zeros((MAX, 2)); nbn = np.zeros(MAX, int); act = np.zeros(MAX, bool); gen = np.zeros(MAX, int)
    rad = np.full(MAX, RS)
    n = 0
    free = np.ones(NSL, bool); settle = []            # (t, slot, ball idx, x, y)
    slot_of = {}
    BX = XL + 4 + 8 * np.arange(NB_BIN)
    near_bin = [np.where(np.abs(SL[:, 1] - bx) < dx * .75)[0] for bx in BX]
    LEV = np.zeros(NB_BIN)
    def upd(bins):
        for b in bins:
            ids = near_bin[b]; ids = ids[free[ids]]
            LEV[b] = SL[ids, 2].max() if len(ids) else YLB + RS
    upd(range(NB_BIN))
    def lowest_free(xs):
        return LEV[np.clip(((xs - XL - 4) / 8 + .5).astype(int), 0, NB_BIN - 1)]
    hero_r = RH
    for f in range(int(T * FPS)):
        for s in range(SUB):
            t = (f * SUB + s) * DT
            if t_in is None:
                vx, vy = hv
                vy += G * DT
                nx, ny = hx_ + vx * DT, hy_ + vy * DT
                if nx - RH < XL: nx = 2 * (XL + RH) - nx; vx = -vx; events.append((t, "side", nx, ny))
                if nx + RH > XR: nx = 2 * (XR - RH) - nx; vx = -vx; events.append((t, "side", nx, ny))
                off = nx - hx
                if abs(off) >= HW:
                    if ny + RH > YLID and vy > 0:
                        ny = 2 * (YLID - RH) - ny; vy = -vy
                        events.append((t, "lid", nx, YLID, float(off)))
                        if jit:
                            a = jr.normal(0, jit); vx += a * 60
                else:
                    hit = False
                    for sg in (-1, 1):
                        cx, cy = hx + sg * HW, YLID
                        ddx, ddy = nx - cx, ny - cy; d = math.hypot(ddx, ddy)
                        if d < RH:
                            ux, uy = ddx / d, ddy / d; vn = vx * ux + vy * uy
                            if vn < 0:
                                vx -= 2 * vn * ux; vy -= 2 * vn * uy
                                nx, ny = cx + ux * RH, cy + uy * RH
                                events.append((t, "rim", cx, cy, float(off))); hit = True
                            break
                    if not hit and ny - RH > YLB + 2:
                        t_in = t; events.append((t, "in", nx, ny))
                        # the hero becomes the first swarm ball
                        P[0] = (nx, ny); V[0] = (vx, vy); act[0] = True; n = 1; rad[0] = RH
                        if stop: return None, events, None, t_in
                hx_, hy_, hv = nx, ny, [vx, vy]
            else:
                a = act[:n]
                if not a.any(): continue
                idx = np.where(a)[0]
                V[idx, 1] += G * DT
                Q = P[idx] + V[idx] * DT
                # walls
                lw = Q[:, 0] - rad[idx] < XL; Q[lw, 0] = 2 * (XL + rad[idx][lw]) - Q[lw, 0]; V[idx[lw], 0] *= -1
                rw = Q[:, 0] + rad[idx] > XR; Q[rw, 0] = 2 * (XR - rad[idx][rw]) - Q[rw, 0]; V[idx[rw], 0] *= -1
                cl = (Q[:, 1] - rad[idx] < YLB) & (V[idx, 1] < 0); V[idx[cl], 1] *= -1; Q[cl, 1] = 2 * (YLB + rad[idx][cl]) - Q[cl, 1]
                lev = lowest_free(Q[:, 0])
                bo = (Q[:, 1] > lev + (rad[idx] - RS)) & (V[idx, 1] > 0)
                P[idx] = Q
                for j in np.where(bo)[0]:
                    k = idx[j]
                    P[k, 1] = lev[j] + (rad[k] - RS)
                    nbn[k] += 1
                    events.append((t, "bounce", P[k, 0], P[k, 1], int(gen[k])))
                    total = n
                    if nbn[k] >= nb and free.sum() > (act[:n].sum() - 1):
                        # settle into the best free slot near it (lowest first)
                        cand = np.where(free)[0]
                        cost = -SL[cand, 2] + .5 * np.abs(SL[cand, 1] - P[k, 0])
                        sl = cand[np.argmin(cost)]
                        free[sl] = False; act[k] = False
                        b0 = int((SL[sl, 1] - XL - 4) / 8); upd(range(max(0, b0 - 4), min(NB_BIN, b0 + 6)))
                        settle.append((t, int(sl), int(k), float(P[k, 0]), float(P[k, 1])))
                        events.append((t, "settle", SL[sl, 1], SL[sl, 2], int(SL[sl, 0])))
                        continue
                    sp = math.hypot(*V[k])
                    V[k, 1] = -abs(V[k, 1]) * .9
                    if rad[k] > RS: V[k, 1] = -abs(V[k, 1]) * .75
                    if n < NSL and (n < 4 or rng.random() < p):
                        P[n] = P[k]; vyu = rng.uniform(VLO, VHI); V[n] = (rng.uniform(-380, 380), -vyu)
                        gen[n] = gen[k] + 1; act[n] = True; n += 1
                # hero shrinks to swarm size
                if rad[0] > RS: rad[0] = max(RS, rad[0] - 30 * DT)
        if t_in is None:
            frames.append(((hx_, hy_), None, None, 0))
        else:
            frames.append((None, P[:n].copy(), act[:n].copy(), float(rad[0])))
    return frames, events, settle, t_in

if __name__ == "__main__":
    if sys.argv[1] == "plan":
        best = []; t0 = time.time()
        for x0 in np.linspace(XL + 60, XR - 60, 12):
            for vx in np.linspace(140, 560, 36):
                for sgn in (-1, 1):
                    for hx in np.linspace(XL + 140, XR - 140, 24):
                        _, ev, _, T = run(x0, sgn * vx, hx, 14.2, stop=True)
                        if T is None or T < 11.3: continue
                        near = [(e[0], e[1]) for e in ev if e[1] in ("lid", "rim") and abs(e[4]) < 85]
                        nt = [t for t, k in near]
                        if len(nt) < 5: continue
                        gaps = np.diff([0] + nt + [T]); nrim = sum(k == "rim" for _, k in near)
                        score = len(nt) * 5 + 4 * min(nrim, 2) - 5 * max(0, gaps.max() - 2.6) - 5 * (nt[0] > 2.5)
                        best.append((round(score, 1), float(x0), float(sgn * vx), float(hx), round(T, 2), [(round(t, 1), k[0]) for t, k in near]))
        best.sort(reverse=True)
        for b_ in best[:15]: print(b_)
        print("plan s", round(time.time() - t0))
    elif sys.argv[1] == "sim":
        x0, vx, hx, p, nb = map(float, sys.argv[2:7])
        t0 = time.time()
        fr, ev, st, ti = run(x0, vx, hx, 26, p=p, nb=int(nb))
        print("slots", NSL, "rows", NROW, "in", ti, "sim s", round(time.time() - t0, 1))
        full = st[-1][0] if len(st) == NSL else None
        print("settled", len(st), "full at", full)
        for s in range(int(ti or 0), 26):
            f = s * FPS
            if fr[f][1] is not None: print(s, len(fr[f][1]), int(fr[f][2].sum()))
        print("lid/rim:", [(round(e[0], 2), e[1], round(e[4])) for e in ev if e[1] in ("lid", "rim") and abs(e[4]) < 130])
        pickle.dump((fr, ev, st, ti, (x0, vx, hx, p, nb)), open(sys.argv[7] if len(sys.argv) > 7 else "sim.pkl", "wb"))
