"""Música original de fondo (oscura, 90 BPM, La menor) — sin derechos."""
import numpy as np, sys
SR = 48000; BPM = 90; beat = 60 / BPM; DUR = float(sys.argv[1])
n = int(DUR * SR); out = np.zeros((n, 2), np.float32); rng = np.random.default_rng(7)
def add(x, t, pan=0.0, g=1.0):
    i = int(t * SR); x = x[:max(0, n - i)]
    if len(x) == 0: return
    out[i:i + len(x), 0] += x * g * (1 - pan) ; out[i:i + len(x), 1] += x * g * (1 + pan)
def env(N, a=0.005, d=0.2):
    t = np.arange(N) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def kick():
    N = int(0.45 * SR); t = np.arange(N) / SR
    f = 45 + 110 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * 0.9
def snare():
    N = int(0.35 * SR); t = np.arange(N) / SR
    nz = rng.standard_normal(N); nz = np.convolve(nz, [1, -0.6], 'same')
    return (nz * np.exp(-t * 14) * 0.35 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4)
def hat(open_=False):
    N = int((0.18 if open_ else 0.05) * SR); nz = rng.standard_normal(N); nz = nz - np.convolve(nz, np.ones(4) / 4, 'same')
    return nz * np.exp(-np.arange(N) / SR / (0.06 if open_ else 0.012)) * 0.12
def note(f, N, wave='saw', det=0.0):
    t = np.arange(N) / SR; s = 0
    for d in (-det, det) if det else (0,):
        ph = (f * (1 + d) * t) % 1
        s = s + ((2 * ph - 1) if wave == 'saw' else np.sin(2 * np.pi * f * (1 + d) * t))
    return s
def lp(x, a):  # one-pole lowpass
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y
A = 110.0
chords = [[0, 3, 7], [-4, 0, 3], [-7, -4, 0], [-5, -1, 2]]   # Am F Dm E
roots = [0, -4, -7, -5]
bar = 4 * beat; nbars = int(DUR / bar) + 1
# pad (lowpassed detuned saws), one chord per bar
for b in range(nbars):
    N = int(bar * SR) + int(0.3 * SR)
    pad = sum(note(A * 2 ** (s / 12) * 2, N, 'saw', 0.004) for s in chords[b % 4])
    pad = lp(pad.astype(np.float32), 0.035) * np.minimum(1, np.arange(N) / SR / 0.4) * np.minimum(1, (N - np.arange(N)) / SR / 0.3)
    add(pad * 0.06, b * bar, -0.2); add(pad * 0.06, b * bar + 0.012, 0.2)
    # sub bass: root on 1 and the "and" of 2
    for off, ln in ((0, 1.4), (1.5, 0.45), (2, 1.4), (3.5, 0.45)):
        N2 = int(ln * beat * SR); bb = note(A / 2 * 2 ** (roots[b % 4] / 12), N2, 'sine')
        add(bb * env(N2, 0.01, 0.5) * 0.35, b * bar + off * beat)
    # arpeggio (enters from bar 2), dark pluck
    if b >= 1:
        seq = chords[b % 4] + [chords[b % 4][1] + 12]
        for k in range(8):
            N3 = int(0.4 * SR); s = seq[k % 4] + 12
            pl = lp(note(A * 2 ** (s / 12), N3, 'saw').astype(np.float32), 0.08) * env(N3, 0.003, 0.15)
            add(pl * 0.05, b * bar + k * beat / 2, 0.35 if k % 2 else -0.35)
            add(pl * 0.02, b * bar + k * beat / 2 + beat * 0.75, -0.35 if k % 2 else 0.35)  # eco
    # drums
    for q in range(4):
        t0 = b * bar + q * beat
        if q in (0, 2): add(kick(), t0)
        if q == 2 and b % 2: add(kick() * 0.6, t0 + beat * 0.75)
        if q in (1, 3): add(snare(), t0); add(snare() * 0.18, t0 + beat * 0.5)
        add(hat(), t0, 0.3); add(hat(), t0 + beat / 2, -0.3, 0.7)
        if q == 3 and b % 2: add(hat(True), t0 + beat * 0.75, 0.2)
out /= np.abs(out).max() + 1e-9; out *= 0.8
out.astype(np.float32).tofile(sys.argv[2])
print('ok')
