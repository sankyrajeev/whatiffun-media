import sys, json, numpy as np, sim, itertools
def sync_counts(P, fl, T, win=0.06):
    N = len(P); last = np.full(N, -9.0); out = []; k = 0
    for fr in range(int(T * 30)):
        t = fr / 30
        while k < len(fl) and fl[k][0] <= t: last[fl[k][1]] = fl[k][0]; k += 1
        s = np.sort(last[last > t - 1.3])
        if len(s) == 0: out.append(0); continue
        j = np.searchsorted(s, s + win, side="right"); out.append(int((j - np.arange(len(s))).max()))
    return np.array(out)
if __name__ == "__main__":
    res = []
    for seed, df, lam, e1, r1 in itertools.product([1,2,3,4], [0.05,0.08,0.11], [60,90], [0.25,0.4,0.6], [12,16]):
        kw = dict(seed=seed, left_df=df, lam=lam, eps=[0.03, e1], ramp=[0, r1], T=20)
        P, f, fl = sim.run(**kw)
        c = sync_counts(P, fl, 20)
        full = np.nonzero(c >= 297)[0]
        tf = full[0] / 30 if len(full) else 99
        # how fast the final climb: time from 200 to 297
        t200 = np.nonzero(c >= 200)[0]; t200 = t200[0] / 30 if len(t200) else 99
        plateau = c[int(6*30):int(max(6, tf - 1) * 30)]
        res.append((tf, t200, int(plateau.mean()) if len(plateau) else 0, kw))
    res.sort(key=lambda r: abs(r[0] - 13) + 2 * (r[0] - r[1]))
    for r in res[:15]: print(r)
