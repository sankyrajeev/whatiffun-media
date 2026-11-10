"""No. 15 soundtrack, built from the sim's own events.
- every marble dropping in: a small glass bell (pentatonic; bigger marble = lower note), panned by x
- marble-on-marble touches: crisp glass clicks, pitch by the smaller marble's size, level by impact speed
- marble-on-rim touches: a soft rounded glass tock
- rolling: a soft, low glassy rumble that follows how much is moving
- each rung (10 / 100 / 1,000): a low thump + chord; the glint: rising ticks; end card: resolving chord"""
import math, os
import numpy as np
from scipy.signal import butter, sosfilt
from kit import Mix, SR, FPS, glass_click, mallet, thud, note

def audio(path, M):
    R, BIRTH, EV, POS = M.R, M.BIRTH, M.EV, M.POS
    TOTAL, NF, CX = M.TOTAL, M.NF, M.CX
    m = Mix(TOTAL / FPS + .5)
    rng = np.random.default_rng(15)
    def size_note(r):                        # 26 px -> low, 8 px -> high
        u = (26 - r) / 18
        return int(round(2 + u * 9))
    bells = {k: mallet(note(k, 392.0), 1.4, .7) for k in range(0, 14)}
    clicks = {k: [glass_click(note(k, 1046.5) * rng.uniform(.995, 1.005), rng.uniform(90, 140), .14, .2) for _ in range(3)]
              for k in range(0, 14)}
    tock = [mallet(f, .35, .25) for f in (196.0, 220.0, 261.6)]
    # 1) drop-ins
    for i, tb in enumerate(BIRTH):
        if tb > M.KT[-1] + .1: break
        rate = 1.0 / max(1e-3, (BIRTH[min(i + 1, len(BIRTH) - 1)] - BIRTH[max(i - 1, 0)]) / 2)
        p = rng.random()
        if rate > 6 and p > 6 / rate: continue                # thin out when they rain in
        x = CX + float(POS[min(int(tb * FPS) + 1, POS.shape[0] - 1), i, 0]) if not np.isnan(POS[min(int(tb * FPS) + 1, POS.shape[0] - 1), i, 0]) else CX
        g = float(os.environ.get('GB', 1)) * (.17 if i < 10 else .12 if i < 100 else .09)
        m.add(bells[size_note(R[i])], max(0, tb), g, x)
    # 2) contacts: per 1/60 s slot keep the strongest few
    ev = EV[np.argsort(EV[:, 0])]
    slot = (ev[:, 0] * 60).astype(int)
    for s in np.unique(slot):
        sel = ev[slot == s]
        sel = sel[np.argsort(-sel[:, 3])][:4]
        n_all = int((slot == s).sum())
        for e in sel:
            t, x, y, dv, ia, ib = e
            if dv < 12: continue
            lvl = min(1.0, (dv / 260) ** .7)
            dens = 1 / (1 + n_all / 6) ** .35
            if ib < 0 or ia < 0:                               # rim
                m.add(tock[rng.integers(3)], float(t), float(os.environ.get('GC', 1)) * .14 * lvl, CX + float(x))
            else:
                r = min(R[int(ia)], R[int(ib)])
                k = size_note(r) + int(rng.integers(0, 2)) * 2
                m.add(clicks[min(k, 13)][rng.integers(3)], float(t), float(os.environ.get('GC', 1)) * .16 * lvl * dens, CX + float(x))
    # 3) rolling rumble that follows the moving marbles (left/right weighted by where they roll)
    N = m.N
    v = np.zeros((POS.shape[0], 2))
    for f in range(1, POS.shape[0]):
        d = POS[f] - POS[f - 1]
        sp = np.linalg.norm(d, axis=1) * FPS
        ok = ~np.isnan(sp)
        w = np.clip(sp[ok] / 300, 0, 1) * (R[ok] / 20) ** 2
        xs = POS[f, ok, 0]
        v[f, 0] = (w * (xs < 0)).sum() + .5 * (w * (xs >= 0)).sum()
        v[f, 1] = (w * (xs >= 0)).sum() + .5 * (w * (xs < 0)).sum()
    env = np.sqrt(v / (np.max(v) + 1e-9))
    tt = np.arange(N) / SR
    sos = butter(2, [140, 700], btype="band", fs=SR, output="sos")
    for ch, buf in ((0, m.L), (1, m.R)):
        noise = sosfilt(sos, rng.standard_normal(N))
        noise *= (1 + .35 * np.sin(2 * np.pi * 7.3 * tt + ch))   # a gentle grainy wobble
        e = np.interp(tt, np.arange(POS.shape[0]) / FPS, env[:, ch], right=0)
        e[tt > NF / FPS] = 0
        buf += noise / np.std(noise) * e * .05 * float(os.environ.get('GR', 1))
    # 4) rungs: low thump + chord
    chords = [[0, 2, 4], [2, 4, 7], [4, 7, 9]]
    for mt, ch in zip(M.MILE_T, chords):
        m.add(thud(56, .7), mt, .2, CX)
        for j, nn in enumerate(ch):
            m.add(mallet(note(nn, 261.63), 2.4, .6), mt + j * .05, .08, CX + (j - 1) * 160)
    m.add(thud(48, .9), M.T_SET, .14, CX)
    # 5) the glint gliding out: rising pentatonic ticks
    for k in range(12):
        tk = M.GL0 + (M.GL1 - M.GL0) * k / 12
        m.add(mallet(note(k + 3, 523.25), .8, .5), tk, .05, CX + 300 * math.sin(k * 1.7))
    tc = (NF + M.HOLD) / FPS
    for i, nn in enumerate([0, 2, 4, 7]):
        m.add(mallet(note(nn, 261.63 / 2), 3.0, .5), tc + i * .08, .12, CX + (i - 1.5) * 110)
    return m.save(path)
