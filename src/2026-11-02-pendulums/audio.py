"""Sonify the pendulums: 160 voices, one per sampled pendulum.
Unison while they agree -> beating as they drift -> an A-minor-pentatonic cloud in chaos -> back to unison."""
import numpy as np, math, wave

FPS, SR = 30, 48000
FR = np.load("frames.npy")
P = np.load("timeline.npy")
TOTAL = len(P)
A, D = 435, 30
N_S = int(TOTAL / FPS * SR)
rng = np.random.default_rng(11)

def state(p):
    i = int(math.floor(p)); fr = p - i
    if i >= len(FR) - 1: return FR[-1]
    return FR[i] * (1 - fr) + FR[i + 1] * fr

def wrap(a): return (a + np.pi) % (2 * np.pi) - np.pi

N = FR.shape[2]
VOICES = np.linspace(0, N - 1, 160).astype(int)
st = np.array([state(p) for p in P])          # (T, 2, N)
t1 = st[:, 0, VOICES]; t2 = st[:, 1, VOICES]
delta = wrap(t2 - t2[:, :1])                   # deviation from pendulum 0
raw = 12 * np.sign(delta) * np.sqrt(np.abs(delta) / np.pi)
SCALE = np.array([d + 12 * o for o in (-1, 0, 1) for d in (0, 3, 5, 7, 10)] + [24])
q = SCALE[np.argmin(np.abs(raw[..., None] - SCALE), axis=-1)]
semis = q + 0.22 * (raw - q)

# tip speed (for breathing amplitude)
tx = np.sin(st[:, 0]) + np.sin(st[:, 1]); ty = np.cos(st[:, 0]) + np.cos(st[:, 1])
spd = np.hypot(np.diff(tx, axis=0, prepend=tx[:1]), np.diff(ty, axis=0, prepend=ty[:1])).mean(1)
spd = spd / (np.percentile(spd, 95) + 1e-9)

# playback speed for tape-stop
pspeed = np.abs(np.gradient(P))
tape = np.ones(TOTAL)
for f in range(A, A + D + 20):
    tape[f] = 0.55 + 0.45 * min(1.0, pspeed[f])

ft = np.arange(TOTAL) / FPS
ts = np.arange(N_S) / SR
interp = lambda arr: np.interp(ts, ft, arr)
tape_s = interp(tape)
breath = interp(0.55 + 0.45 * np.clip(spd, 0, 1.2))

L = np.zeros(N_S); R = np.zeros(N_S)
BASE = 220.0
for k, v in enumerate(range(len(VOICES))):
    fr = BASE * 2 ** (interp(semis[:, v]) / 12) * tape_s
    ph = 2 * np.pi * np.cumsum(fr) / SR + rng.uniform(0, 0.02)
    sig = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    pan = -0.75 + 1.5 * k / (len(VOICES) - 1)
    L += sig * math.cos((pan + 1) * math.pi / 4)
    R += sig * math.sin((pan + 1) * math.pi / 4)
unis = (np.abs(semis) < 0.5).mean(1)
comp = interp(1.3 - 0.97 * unis)
L *= breath * comp / len(VOICES); R *= breath * comp / len(VOICES)

# low drone
drone = 0.18 * (np.sin(2 * np.pi * 55 * ts) + 0.3 * np.sin(2 * np.pi * 110 * ts + 0.4))
L += drone; R += drone

def add(sig, t0, gain, pan=0.0):
    i = int(t0 * SR)
    if i >= N_S: return
    sig = sig[: N_S - i]
    L[i:i + len(sig)] += sig * gain * math.cos((pan + 1) * math.pi / 4)
    R[i:i + len(sig)] += sig * gain * math.sin((pan + 1) * math.pi / 4)

def tick():
    t = np.arange(int(0.06 * SR)) / SR
    return (np.sin(2 * np.pi * 1320 * t) + 0.5 * np.sin(2 * np.pi * 2640 * t)) * np.exp(-t * 90)

def bell(f, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    return sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * dcy)
               for m, a, dcy in [(1, 1, 1.4), (2.0, 0.4, 2.2), (2.76, 0.25, 3.5), (5.4, 0.1, 6)])

# clock ticks on every whole second of simulated time (they speed up in rewind)
TK = tick()
for f in range(1, TOTAL):
    a, b = P[f - 1] / FPS, P[f] / FPS
    if math.floor(a) != math.floor(b):
        add(TK, f / FPS, 0.10, 0.0)

# reverse-cymbal swell into the freeze, hard cut at the stop
t_stop = (A + D * 0.5) / FPS
sw_len = 2.2
n = int(sw_len * SR)
tt = np.arange(n) / SR
noise = rng.standard_normal(n)
y = np.zeros(n); acc = 0.0
for i in range(n):
    c = 1 - math.exp(-2 * math.pi * (400 + 7000 * (i / n) ** 2) / SR)
    acc += c * (noise[i] - acc); y[i] = acc
add(y * (tt / sw_len) ** 3 * 0.55, t_stop - sw_len, 1.0)
# soft thump at the turnaround
th = np.arange(int(1.2 * SR)) / SR
add(np.sin(2 * np.pi * (48 * th + 40 * (1 - np.exp(-th * 14)) / 14)) * np.exp(-th * 3.2), t_stop, 0.55)

# resolution bell when everything is back to one line
add(bell(880.0), (TOTAL - 14) / FPS, 0.10, 0.0)
add(bell(440.0), (TOTAL - 14) / FPS, 0.08, 0.0)

# loop-friendly fades
fi = int(0.15 * SR); fo = int(0.35 * SR)
L[:fi] *= np.linspace(0, 1, fi); R[:fi] *= np.linspace(0, 1, fi)
L[-fo:] *= np.linspace(1, 0.3, fo); R[-fo:] *= np.linspace(1, 0.3, fo)

out = np.stack([L, R], 1)
out = out / np.max(np.abs(out)) * 0.89
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
sr = SR
for s in range(0, int(N_S / SR)):
    seg = out[s * sr:(s + 1) * sr]
    print(s, round(float(np.sqrt((seg ** 2).mean())), 3), end=" | ")
print()
