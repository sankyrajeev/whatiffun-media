"""Synthesize the soundtrack from simulation events."""
import pickle, math, wave
import numpy as np

d = pickle.load(open("sim.pkl", "rb"))
import importlib.util
spec = importlib.util.spec_from_file_location("render_consts", "render.py")
# avoid importing render (heavy); recompute timing constants here
FPS, DONE = d["FPS"], d["done"]
FREEZE, BURST, HOLD, XFADE = 15, 36, 24, 15
TOTAL = DONE + 1 + FREEZE + BURST + HOLD + XFADE
SR = 48000
N = int(TOTAL / FPS * SR)
L = np.zeros(N); Rch = np.zeros(N)
rng = np.random.default_rng(3)
T_END = (DONE + 1) / FPS

PENTA = [0, 3, 5, 7, 10]
def note_freq(i):
    octave, deg = divmod(i, 5)
    return 220.0 * 2 ** ((PENTA[deg] + 12 * octave) / 12)

def pluck(freq, dur, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * (9 + 6 * bright)) * np.minimum(1, t * 800)
    s = np.sin(2 * np.pi * freq * t) + 0.35 * bright * np.sin(2 * np.pi * 2 * freq * t) \
        + 0.12 * bright * np.sin(2 * np.pi * 3 * freq * t) * np.exp(-t * 30)
    return s * env

def tick(dur=0.05):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120)

def add(sig, t0, gain, pan):
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    L[i:i + len(sig)] += sig * gain * l
    Rch[i:i + len(sig)] += sig * gain * r

# --- bounce / split events, thinned per frame ---
ev = d["events"]
by_frame = {}
for e in ev:
    by_frame.setdefault(int(e[0] * FPS), []).append(e)
pcache = {}
for fr, es in sorted(by_frame.items()):
    splits = [e for e in es if e[3]]
    plain = [e for e in es if not e[3]]
    rng.shuffle(splits); rng.shuffle(plain)
    n = es[-1][4]
    chosen = splits[:4] + plain[: max(0, 2 - len(splits[:4]))]
    for (t, x, ang, split, cnt) in chosen:
        pan = max(-0.8, min(0.8, (x - 540) / 540))
        if split:
            idx = int(((ang + math.pi) / (2 * math.pi)) * 15) % 15
            key = idx
            if key not in pcache:
                pcache[key] = pluck(note_freq(idx), 0.5)
            g = 0.32 / (1 + 0.35 * math.log(cnt))
            add(pcache[key], t, g, pan)
        else:
            g = 0.06 / (1 + 0.3 * math.log(max(cnt, 1)))
            add(tick(), t, g, pan)

# --- dense shimmer bed as it fills (noise filtered, rising) ---
t = np.arange(N) / SR
prog = np.clip(t / T_END, 0, 1)
noise = rng.standard_normal(N)
# one-pole lowpass with rising cutoff
fc = 300 + 5000 * prog ** 3
alpha = 1 - np.exp(-2 * np.pi * fc / SR)
y = np.zeros(N); acc = 0.0
for i in range(N):
    acc += alpha[i] * (noise[i] - acc)
    y[i] = acc
bed = y * 0.065 * prog ** 2.5 * (t < T_END)
L += bed; Rch += bed * 0.95

# --- sub drone building with count ---
drone_amp = 0.16 * prog ** 1.6 * (t < T_END)
drone = (np.sin(2 * np.pi * 55 * t) + 0.4 * np.sin(2 * np.pi * 82.5 * t)) * drone_amp
L += drone; Rch += drone

# --- impact at 1,000 ---
ti = np.arange(int(2.5 * SR)) / SR
boom = np.sin(2 * np.pi * (45 * ti + 60 * (1 - np.exp(-ti * 12)) / 12)) * np.exp(-ti * 2.2) * 0.75
crack = rng.standard_normal(len(ti)) * np.exp(-ti * 25) * 0.25
chord = sum(pluck(f, 2.5, bright=0.6) for f in [220, 261.63, 329.63, 392, 493.88]) * 0.11
chord = chord[: len(ti)]
add(boom + crack, T_END, 1.0, 0)
add(chord, T_END + 0.01, 1.0, -0.3)
add(chord, T_END + 0.03, 1.0, 0.3)
# sparkle on the burst
for k in range(18):
    tt = T_END + FREEZE / FPS + k * 0.045
    add(pluck(note_freq(10 + (k * 3) % 5), 0.6, bright=0.4), tt, 0.09, rng.uniform(-0.7, 0.7))

# fade out the very end so the loop restarts clean
fade_n = int(0.4 * SR)
L[-fade_n:] *= np.linspace(1, 0, fade_n); Rch[-fade_n:] *= np.linspace(1, 0, fade_n)

st = np.stack([L, Rch], 1)
st = st / np.max(np.abs(st)) * 0.89
pcm = (st * 32767).astype(np.int16)
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("audio", N / SR, "s")
