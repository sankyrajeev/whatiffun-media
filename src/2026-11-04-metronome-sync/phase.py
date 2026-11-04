"""Per-frame phase of every metronome (from its own zero crossings) and a hysteresis 'in step' flag."""
import numpy as np
def analyse(d, FPS=30):
    th = d["theta"]; NFR, N = th.shape
    t = (np.arange(NFR) + 1) / FPS
    # phase from the state itself: theta = A sin(phi), thetad = A w_eff cos(phi)
    w_eff = d["w"] * (1 - (2 * d["TH0"]) ** 2 / 16)          # large-swing pendulum runs slow
    ph = np.arctan2(th * w_eff[None, :], d["thetad"])
    z = np.exp(1j * ph).mean(1)
    # 'in step' = members of the biggest group (within +-WIN of the group's centre), centre tracked in time
    WIN = np.radians(13)
    dev = np.zeros((NFR, N)); centre = None
    for f in range(NFR):
        p = ph[f]
        dd = np.abs(np.angle(np.exp(1j * (p[None, :] - p[:, None]))))      # [cand, i]
        cnt = (dd < WIN).sum(1).astype(float)
        if centre is not None:
            dc = np.abs(np.angle(np.exp(1j * (p - centre))))
            cnt += 0.5 * (dc < WIN)                                          # stickiness: keep following the same group
        c = p[np.argmax(cnt)]
        members = np.abs(np.angle(np.exp(1j * (p - c)))) < WIN
        centre = np.angle(np.exp(1j * p[members]).mean())
        if abs(z[f]) > 0.5: centre = np.angle(z[f])                          # one dominant group: its mean
        dev[f] = np.abs(np.angle(np.exp(1j * (p - centre))))
    lock = np.zeros((NFR, N), bool); state = np.zeros(N, bool); run = np.full(N, 99)
    for f in range(NFR):
        close = dev[f] < WIN
        run = np.where(close, run + 1, 0)
        state = np.where(state, dev[f] < WIN * 1.8, run >= 5)
        lock[f] = state
    # bridge one-off gaps when the tracked group hands over (hold each flag for 8 frames)
    held = lock.copy()
    for k in range(1, 15): held[k:] |= lock[:-k]
    return ph, np.abs(z), dev, held
if __name__ == "__main__":
    import pickle
    d = pickle.load(open("sim.pkl", "rb")); ph, r, dev, lock = analyse(d)
    for f in range(0, len(r), 15): print(f"{f/30:5.1f} r={r[f]:.2f} lock={lock[f].sum()}")
