"""Música original de fondo, emotiva y suave (76 BPM, La menor -> Do). Sin derechos.
Uso: python3 music_presentacion.py <duración> <out.wav>
"""
import sys, wave, numpy as np
SR = 48000; DUR = float(sys.argv[1]); OUT = sys.argv[2]
BPM = 76; beat = 60 / BPM
N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N)
def hz(m): return 440 * 2 ** ((m - 69) / 12)

def add(x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR); j = min(N, i + len(x))
    if i >= N: return
    L[i:j] += x[:j - i] * g * (1 - pan) ; R[i:j] += x[:j - i] * g * (1 + pan)

def piano(m, d, vel=1.0):
    n = int(d * SR); t = np.arange(n) / SR; f = hz(m)
    s = sum(np.sin(2 * np.pi * f * k * t) * a * np.exp(-t * (1.2 + k * 0.9)) for k, a in [(1, 1), (2, .45), (3, .18), (4, .08)])
    att = np.minimum(1, t / 0.006)
    return s * att * vel * 0.22

def pad(ms, d):
    n = int(d * SR); t = np.arange(n) / SR
    env = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.0)
    s = sum(np.sin(2 * np.pi * hz(m) * (1 + det) * t) for m in ms for det in (-0.003, 0.003))
    return s * env * 0.035

# progresión Am - F - C - G (2 compases de 4 tiempos... un acorde por compás)
chords = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
bar = 4 * beat
t = 0.0; c = 0
arp = [0, 1, 2, 1, 2, 3, 2, 1]
while t < DUR:
    root, notes = chords[c % 4]
    add(pad([n + 12 for n in notes] + [root - 12 + 12], bar + 1.0), t)
    add(piano(root - 12, bar, 0.7), t, 0.9)
    if t > 2.0:  # el arpegio entra cuando aparece la obra
        tones = notes + [notes[0] + 12]
        for k, a in enumerate(arp):
            add(piano(tones[a] + 12, 2.0, 0.55 + 0.1 * (k % 2 == 0)), t + k * beat / 2, 1.0, 0.25 * (-1) ** k)
    if t > 8.0:  # melodía simple
        mel = {0: [76, 74], 1: [72, 74], 2: [76, 79], 3: [74, 71]}[c % 4]
        add(piano(mel[0] + 0, 2.5, 0.8), t, 0.7, -0.1)
        add(piano(mel[1] + 0, 2.5, 0.7), t + 2 * beat, 0.7, 0.1)
    t += bar; c += 1

# reverb sencilla (combs + allpass)
def reverb(x):
    y = np.zeros_like(x)
    for dl, g in [(1557, .82), (1617, .81), (1491, .83), (1422, .8), (1277, .84), (1356, .82)]:
        d = int(dl * SR / 44100); b = np.zeros(len(x) + d)
        for i in range(0, len(x), d):  # bloques de tamaño d
            seg = x[i:i + d] + g * b[i:i + min(d, len(x) - i)]
            b[i + d:i + d + len(seg)] = seg
        y += b[d:d + len(x)]
    return y / 6
wet = 0.35
L = L * (1 - wet) + reverb(L) * wet * 1.6
R = R * (1 - wet) + reverb(R) * wet * 1.6
# fundidos
tt = np.arange(N) / SR
env = np.minimum(1, tt / 1.5) * np.minimum(1, (DUR - tt) / 2.5)
st = np.stack([L * env, R * env], 1)
st = st / np.abs(st).max() * 0.6
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
