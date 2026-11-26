"""Plan where every pad goes so ONE marble, under real gravity, hits a pad exactly on every note.
Between hits the marble flies a ballistic arc; each pad is tilted so the bounce obeys the reflection law
(pad normal ∝ v_out/|v_out| − v_in/|v_in|). Design units = px of a 1080-wide frame, y down.
    python3 choreo.py mountain-king  -> plan/<song>.json (+ plan/<song>-preview.png)"""
import json, math, os, random, sys
import numpy as np
from songs import SONGS, notes

G = 2600.0            # px/s^2
BALL_R = 24.0
PAD_HALF = {"tube": 15, "wood": 20, "glass": 11, "saucer": 16}   # half-thickness along the normal (px)
PAD_LEN = {"tube": 92, "wood": 86, "glass": 98, "saucer": 88}
X_MIN, X_MAX = 170, 910
CLEAR = 30.0           # free space between the arc and any other pad (px)

def arc(p, v, T, n=24):
    t = np.linspace(0, T, n)[:, None]
    return p + v * t + np.array([0, .5 * G]) * t * t

def _box_hits(pts, pad, grow):
    px, py, a, f, L = pad
    ux, uy = math.cos(a), math.sin(a)
    rel = pts - np.array([px, py]); along = rel @ np.array([ux, uy]); perp = rel @ np.array([-uy, ux])
    return bool(((np.abs(along) < 0.5 * L + grow) & (np.abs(perp) < PAD_HALF[f] + grow)).any())

def plan(song_key, budget=60000):
    """Depth-first search over bounce choices: every pad must sit clear of every other pad AND of every
    stretch of the marble's flight (pads are on the wall the whole video, so the marble may never pass
    through one, before or after it is struck)."""
    song = SONGS[song_key]; ns, t_end = notes(song)
    N = len(ns)

    def options(i, p, v_in, side, pads, arcs):
        t, midi, fam, sec = ns[i]
        T = ns[i + 1][0] - t if i + 1 < N else 0.55
        slow = T >= 0.33
        base = 430.0 if not slow else 320.0
        want_flip = slow and (i % 2 == 1)
        ahead = p[0] + side * max(118.0, base * T) * 2.5
        if not (X_MIN <= ahead <= X_MAX): want_flip = True
        out = []
        # flight points near the current height (the last 3 points of the incoming arc touch the new pad by design)
        recent = [a_ for a_ in arcs[-40:]]
        if recent:
            recent[-1] = recent[-1][:-3]
            near_pts = np.concatenate(recent)
            near_pts = near_pts[np.abs(near_pts[:, 1] - p[1]) < 900]
        else:
            near_pts = np.zeros((0, 2))
        for flip in (False, True):
            for kick in (False, True):
                sgn = -side if flip else side
                for rise in (70.0, 30.0, 8.0):
                    for kscale in (1.0, 0.8, 1.25, 0.6, 1.6):
                        for dxs in (1.0, 1.3, 0.85, 1.6):
                            dy_min = T * (0.5 * G * T - math.sqrt(2 * G * rise))
                            target = max(50 + 300 * T, dy_min * 1.05) * kscale
                            cap = 0.95 * 0.5 * G * T * T
                            if flip or kick:
                                target = max(target, 150 * kscale); cap = max(cap, 3.2 * 0.5 * G * T * T)
                            dy = min(cap, max(dy_min, target))
                            need = math.sqrt(max(0.0, 118.0 ** 2 - dy * dy))
                            dx = sgn * max(need, base * T) * dxs
                            q = p + np.array([dx, dy])
                            if not (X_MIN <= q[0] <= X_MAX): continue
                            v_out = np.array([dx / T, dy / T - 0.5 * G * T])
                            nrm = v_out / np.linalg.norm(v_out) - v_in / np.linalg.norm(v_in)
                            nn = np.linalg.norm(nrm)
                            if nn < 1e-6: continue
                            nrm = nrm / nn
                            if nrm[1] > (0.05 if (flip or kick) else -0.42): continue
                            ang = math.atan2(nrm[0], -nrm[1])
                            c = p - nrm * (BALL_R + PAD_HALF[fam])
                            pad = (float(c[0]), float(c[1]), ang, fam, PAD_LEN[fam])
                            if any(math.hypot(o[0] - c[0], o[1] - c[1]) < 0.5 * (o[4] + PAD_LEN[fam]) + 4 for o in pads[-40:]):
                                continue
                            # the new pad must not sit in any earlier flight path (the last 3 points of the
                            # incoming arc touch it by design)
                            if len(near_pts) and _box_hits(near_pts[np.abs(near_pts[:, 1] - c[1]) < 160], pad, BALL_R + 2):
                                continue
                            pts = arc(p, v_out, T)
                            if pts[:, 0].min() < 120 or pts[:, 0].max() > 960: continue
                            ylo, yhi = pts[:, 1].min() - 160, pts[:, 1].max() + 160
                            if any(_box_hits(pts[3:], o, BALL_R + 6) for o in pads if ylo < o[1] < yhi): continue
                            # preference: no flip unless wanted, no kick, gentle pads, roomy landing
                            sc = 0.0
                            sc -= 2.0 if flip != want_flip else 0.0
                            sc -= 1.5 if kick else 0.0
                            sc += -nrm[1] * 1.0
                            sc -= abs(kscale - 1.0) * 0.5 + abs(dxs - 1.0) * 0.4 + (70 - rise) / 70 * 0.6
                            room = min([math.hypot(o[0] - q[0], o[1] - q[1]) for o in pads[-40:]] + [999])
                            sc += min(room, 220) / 220
                            out.append((sc, q, v_out, nrm, pad, sgn, T, pts))
        out.sort(key=lambda z: -z[0])
        return out[:10]

    p0 = np.array([540.0, 700.0]); v0 = np.array([0.0, G * 0.35])
    # stack frames: (i, p, v_in, side, pads, arcs, hits, remaining options)
    first = options(0, p0, v0, 1, [], [])
    stack = [(0, p0, v0, 1, [], [], [], first)]
    evals = 0; deepest = 0
    while stack:
        i, p, v_in, side, pads, arcs, hits, opts = stack[-1]
        if not opts:
            stack.pop(); continue
        sc, q, v_out, nrm, pad, sgn, T, pts = opts.pop(0)
        t, midi, fam, sec = ns[i]
        h = dict(t=t, x=float(p[0]), y=float(p[1]), vin=v_in.tolist(), vout=v_out.tolist(),
                 nrm=nrm.tolist(), fam=fam, midi=midi, sec=sec, T=T)
        npads, narcs, nhits = pads + [pad], arcs + [pts], hits + [h]
        if i + 1 == N:
            pads_f, hits_f = npads, nhits; break
        nv = v_out + np.array([0, G * T])
        nopts = options(i + 1, q, nv, sgn, npads, narcs)
        evals += 1; deepest = max(deepest, i + 1)
        if evals % 500 == 0: print('evals', evals, 'deepest', deepest, flush=True)
        if evals > budget: raise RuntimeError(f"search budget spent; deepest note {deepest}/{N}")
        stack.append((i + 1, q, nv, sgn, npads, narcs, nhits, nopts))
    else:
        raise RuntimeError(f"no layout found; deepest note {deepest}/{N}")
    return dict(song=song_key, title=song["title"], composer=song["composer"], g=G, ball_r=BALL_R,
                t_end=t_end + 1.6, hits=hits_f,
                pads=[dict(x=a, y=b, ang=c, fam=d, len=e, half=PAD_HALF[d]) for a, b, c, d, e in pads_f])

def ball_at(P, t):
    """marble centre at time t (falls in before the first hit)."""
    hs = P["hits"]
    if t <= hs[0]["t"]:
        dt = hs[0]["t"] - t; vin = np.array(hs[0]["vin"])
        # reverse ballistic: position dt before the hit
        p = np.array([hs[0]["x"], hs[0]["y"]]) - vin * dt + np.array([0, .5 * G]) * dt * dt
        return p
    for h in reversed(hs):
        if t >= h["t"]:
            dt = t - h["t"]
            return np.array([h["x"], h["y"]]) + np.array(h["vout"]) * dt + np.array([0, .5 * G]) * dt * dt

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "mountain-king"
    P = plan(key)
    os.makedirs("plan", exist_ok=True)
    json.dump(P, open(f"plan/{key}.json", "w"), indent=1)
    ys = [h["y"] for h in P["hits"]]
    print(len(P["hits"]), "hits; depth", round(ys[-1] - ys[0]), "px; end", round(P["t_end"], 2), "s")
    # quick 2D preview
    from PIL import Image, ImageDraw
    H = int(ys[-1] + 900); im = Image.new("RGB", (1080, H), (20, 16, 13)); d = ImageDraw.Draw(im)
    col = {"tube": (230, 170, 90), "wood": (150, 90, 50), "glass": (250, 190, 80), "saucer": (200, 110, 70)}
    for pd in P["pads"]:
        ux, uy = math.cos(pd["ang"]), math.sin(pd["ang"]); L = pd["len"] / 2
        d.line([(pd["x"] - ux * L, pd["y"] - uy * L), (pd["x"] + ux * L, pd["y"] + uy * L)], fill=col[pd["fam"]], width=2 * pd["half"])
    pts = [ball_at(P, t) for t in np.arange(0, P["hits"][-1]["t"] + 0.5, 1 / 60)]
    d.line([tuple(p) for p in pts], fill=(240, 230, 210), width=2)
    im.resize((540, H // 2)).save(f"plan/{key}-preview.png")
