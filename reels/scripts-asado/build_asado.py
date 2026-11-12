"""Reel 'Hoy: asado de obra' v2 (Monte Hermoso) — Arquitectura Vignale.
Intro en blanco y negro con voz en off -> destello -> hablados en color con tomas superpuestas
-> se repite la charla del nombre en color -> cierre con la música del parlante -> remate VA.
Uso: python3 build_asado.py   (carpeta de trabajo con b/ = clips SDR 1080x1920, a/ = audios limpios)
"""
import subprocess, math, os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = 'fonts/'
ARCH8 = FD + 'fontsource-archivo-5.3.0/package/files/archivo-latin-800-normal.woff2'
ARCH6 = FD + 'fontsource-archivo-5.3.0/package/files/archivo-latin-600-normal.woff2'
ITAL = FD + 'fontsource-italiana-5.3.0/package/files/italiana-latin-400-normal.woff2'
WHITE = (244, 242, 236)
fCap = ImageFont.truetype(ARCH8, 66)
fKey = ImageFont.truetype(ITAL, 112)
fLab = ImageFont.truetype(ARCH8, 46)
fTit = ImageFont.truetype(ITAL, 165)
fBig = ImageFont.truetype(ARCH8, 120)
MUSIC = 'a/song.wav'          # De la guitarra - Intoxicados
SONG_AT_0419A = 33.42         # segundo del tema que suena en el parlante en t=0 de IMG_0419a (correlación)

def ease(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0.0), 1.0); c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------- montaje ----------------
# piezas principales (imagen + audio sincronizados): (clip, in, out, modo)
SEG = [('IMG_0419b', 3.70, 6.62, 'tv'), ('IMG_0419b', 9.72, 11.55, 'tv'),       # intro "televisión"
       ('IMG_0416', 1.15, 12.65, 'talk'), ('IMG_0417', 3.40, 8.60, 'talk'),
       ('IMG_0419a', 0.00, 6.70, 'talk')]                                       # cierre: yo + Manu con el parlante
SOFF = []; acc = 0
for c, a_, b_, m in SEG:
    SOFF.append(acc); acc += b_ - a_
T_X = SOFF[2]; T_16 = SOFF[2]; T_17 = SOFF[3]; T_A = SOFF[4]; T_REM = acc
REM_LEN = 4.2; TOTAL = T_REM + REM_LEN
def OUT(clip, t, which=None):
    for i, ((c, s_, e_, m), o) in enumerate(zip(SEG, SOFF)):
        if which is not None and i != which: continue
        if c == clip and s_ - 0.06 <= t <= e_ + 0.06: return o + (t - s_)
    raise ValueError((clip, t))
V = [(SOFF[i], SOFF[i] + e_ - s_, c, s_, m) for i, (c, s_, e_, m) in enumerate(SEG)]
def ov(clip, ss, t0, t1, mode='broll'): V.append((t0, t1, clip, ss, mode))
ov('IMG_9569', 0.40, OUT('IMG_0416', 4.00), OUT('IMG_0416', 5.05))   # "generalmente esto se hace"
ov('IMG_9564', 0.05, OUT('IMG_0416', 5.05), OUT('IMG_0416', 7.95))   # losa / techar
ov('IMG_9568', 0.10, OUT('IMG_0416', 8.40), OUT('IMG_0416', 9.90))
ov('IMG_0420', 0.00, OUT('IMG_0416', 9.90), OUT('IMG_0416', 10.50))
ov('IMG_9565', 0.00, OUT('IMG_0417', 4.40), OUT('IMG_0417', 5.88))   # los chicos
V.append((T_REM, TOTAL, 'rem', 0.0, 'rem'))
def piece_at(t):
    best = None
    for p in V:
        if p[0] <= t < p[1] and (best is None or p[4] in ('broll', 'montage', 'rem')): best = p
    return best

# ---------------- subtítulos ----------------
def L(clip, which, s):
    return [(tok.rsplit('@', 1)[0], OUT(clip, float(tok.rsplit('@', 1)[1]), which)) for tok in s.split()]
RAW = [L('IMG_0419b', 0, s) for s in ["¿NO@3.82 SE@3.86 DICE@4.0 EL@4.1 NOMBRE?*@4.24", "¿POR@5.3 AHORA?@5.38",
                                      "¿NO@5.88 SE@5.96 DICE@6.04 EL@6.12 NOMBRE*@6.24 TODAVÍA?@6.36"]]
RAW += [L('IMG_0419b', 1, "NO@9.82 SÉ@9.90 BIEN@10.02 CÓMO@10.18 ES@10.40 LA@10.60 POLÍTICA*@10.72 ACÁ@11.16")]
RAW += [L('IMG_0419a', None, s) for s in [
    "YA@0.0 TERMINANDO@0.32 LAS@1.06 ÚLTIMAS@1.48 ETAPAS*@1.72",
    "LOS@3.88 ESPERAMOS@3.96 A@4.40 TODOS*@4.46", "ESTÉN@4.80 ATENTOS!@5.00"]]
RAW += [L('IMG_0416', None, s) for s in [
    "ACÁ@1.24 ESTAMOS@1.42 EN@1.56 EL@1.64 PARADOR*@1.72", "VAMOS@2.44 AL@2.64 ASADO*@2.78 DE*@2.98 OBRA*@3.1",
    "GENERALMENTE@4.12 ESTO@4.52 SE@4.7 HACE@4.88", "CUANDO@5.16 LLENÁS@5.72 UNA@6.62 LOSA*@6.78",
    "O@7.26 TERMINÁS@7.46 DE@7.78 TECHAR*@7.88", "ACÁ@8.44 NO@8.58 TENEMOS@8.66 LOSA*@8.86",
    "ACÁ@9.94 EN@10.26 ESTE@10.48 CASO@10.6", "LO@10.78 ESTÁ@10.94 HACIENDO@11.04 EL@11.28 REY*@12.2"]]
RAW += [L('IMG_0417', None, s) for s in [
    "ACÁ@3.48 YA@3.64 TECHAMOS*@3.76", "HACE@4.12 UN@4.28 RATO@4.46 LARGO*@4.66", "ASÍ@5.24 QUE…@5.54",
    "CON@5.86 EL@5.94 ASADO@6.02 DEMORADOS*@6.14", "PERO@7.0 BIEN!@7.3"]]
RAW.sort(key=lambda c: c[0][1])
AOFF = SOFF
END_HOLD = 0.65
chunks = []
for ln in RAW:
    words = []
    for w, tt in ln:
        kind = 'key' if w.endswith('*') else ('big' if w.endswith('!') else 'cap')
        words.append((w.rstrip('*!'), tt, kind))
    chunks.append(words)
cuts = list(SOFF[1:]) + [T_REM]
spans = []
for i, ch in enumerate(chunks):
    st = ch[0][1] - 0.04
    en = ch[-1][1] + END_HOLD + 0.25
    if i + 1 < len(chunks):
        en = min(en, chunks[i + 1][0][1] - 0.04)
    for c in cuts:   # no arrastrar subtítulos a la pieza siguiente
        if st < c - 0.05 < en:
            en = c
    spans.append((st, en))

def font_for(kind):
    return fKey if kind == 'key' else (fBig if kind == 'big' else fCap)

def layout(words):
    SP = 22; MAXW = 900
    lines = [[]]; lw = 0
    for w, t, k in words:
        ww = font_for(k).getlength(w)
        if lines[-1] and lw + SP + ww > MAXW:
            lines.append([]); lw = 0
        lines[-1].append((w, t, k, ww)); lw += (SP if lw else 0) + ww
    out = []
    LH = [max(118 if k == 'big' else (96 if k == 'key' else 78) for *_, k, _ in ln) for ln in lines]
    y = 1235 - sum(LH) / 2
    for ln, lh in zip(lines, LH):
        y += lh
        width = sum(x[3] for x in ln) + SP * (len(ln) - 1)
        x = (W - width) / 2
        for w, t, k, ww in ln:
            out.append((w, t, k, x, y - 12)); x += ww + SP
    return out
LAY = [layout(c) for c in chunks]

def draw_caps(layer, t):
    for (st, en), lay in zip(spans, LAY):
        if not (st <= t < en):
            continue
        fade_out = 1 - ease((t - (en - 0.10)) / 0.10) if t > en - 0.10 else 1
        for w, tw, k, x, y in lay:
            p = (t - tw) / 0.16
            if p <= 0:
                continue
            a = ease(p) * fade_out
            f = font_for(k)
            dy = (1 - ease(p)) * 26
            if k == 'big':
                sc = back(p)
                tmp = Image.new('RGBA', (int(f.getlength(w)) + 40, 200), (0, 0, 0, 0))
                ImageDraw.Draw(tmp).text((20, 160), w, font=f, fill=WHITE + (int(255 * a),), anchor='ls')
                s = max(0.2, 0.55 + 0.45 * sc)
                tmp = tmp.resize((max(1, int(tmp.width * s)), max(1, int(tmp.height * s))), Image.BICUBIC)
                cx = x + f.getlength(w) / 2
                layer.alpha_composite(tmp, (int(cx - tmp.width / 2), int(y - 160 * s + dy)))
            else:
                ImageDraw.Draw(layer).text((x, y + dy), w, font=f, fill=WHITE + (int(255 * a),), anchor='ls')

def tracked(d, x, y, text, font, alpha, track=4.0, anchor='ls'):
    for c in text:
        d.text((x, y), c, font=font, fill=WHITE + (int(255 * alpha),), anchor=anchor)
        x += font.getlength(c) + track
    return x

def rising(layer, text, font, cx, baseline, p, alpha=1.0):
    if p <= 0: return
    tmp = Image.new('RGBA', (W, 280), (0, 0, 0, 0))
    off = (1 - ease(p)) * 220
    ImageDraw.Draw(tmp).text((cx, 215 + off), text, font=font, fill=WHITE + (int(255 * alpha),), anchor='ms')
    layer.alpha_composite(tmp, (0, int(baseline - 215)))

TITLE_END = 4.5
fLT = ImageFont.truetype(ITAL, 104)
def draw_title(layer, t):
    """zócalo de televisión: HOY · Asado de obra"""
    if t >= TITLE_END: return
    out = 1 - ease((t - (TITLE_END - 0.3)) / 0.3)
    p = ease((t - 0.1) / 0.45)
    d = ImageDraw.Draw(layer)
    Y = 1452                      # línea de base del texto
    a_txt = out * min(1, max(0, (p - 0.3) / 0.5))
    if p > 0.3:
        dy = (1 - p) * 30
        tracked(d, 110, Y + dy, 'HOY', fLab, out * min(1, (p - 0.3) / 0.4), 10)
        d.text((268, Y + dy), 'Asado de obra', font=fLT, fill=WHITE + (int(255 * a_txt),), anchor='ls')
    wbar = int(860 * p)           # subrayado por debajo del texto
    d.rectangle((110, Y + 26, 110 + wbar, Y + 29), fill=WHITE + (int(220 * out),))
# ---------------- logo VA (del remate) ----------------
rem_fr = Image.open('b/rem_3.png').convert('L')
_m = np.asarray(rem_fr, np.float32)[690:990]
_cols = np.where((_m > 110).any(0))[0]
mark = _m[:, max(0, _cols.min() - 12):_cols.max() + 13]
alpha = np.clip((mark - 60) / (240 - 60), 0, 1)
ys, xs = np.where(alpha > 0.1)
alpha = np.pad(alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 6)
logo = Image.new('RGBA', (alpha.shape[1], alpha.shape[0]), WHITE + (0,))
logo.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
lh = 78
logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)

# ---------------- degradés de legibilidad ----------------
yy = np.arange(H, dtype=np.float32)
band = np.exp(-((yy - 1215) / 260) ** 2) * 0.42
top = np.clip(1 - yy / 1000, 0, 1) ** 1.3 * 0.5
SHADE = np.clip(band + top, 0, 0.6)[:, None, None]
xx = np.arange(W, dtype=np.float32)
VIG = (1 - 0.55 * (((xx[None, :] - W / 2) / (W * 0.75)) ** 2 + ((yy[:, None] - H / 2) / (H * 0.62)) ** 2))[:, :, None]
VIG = np.clip(VIG, 0.35, 1)
TSH2 = (np.exp(-((yy - 1420) / 140) ** 2) * 0.35)[:, None, None]

# ---------------- zoom en palabras clave ----------------
punch = []
for ch in chunks:
    for w, tt, k in ch:
        if k in ('key', 'big'):
            punch.append(tt); break
def zoom_at(t):
    z = 1.0
    for i, tp in enumerate(punch):
        if tp - 0.02 <= t:
            nxt = punch[i + 1] if i + 1 < len(punch) else 1e9
            if t < nxt:
                amt = 0.06 if i % 2 == 0 else 0.04
                z = 1 + amt * ease((t - tp) / 0.18) * (1 - ease((t - tp - 1.4) / 0.6))
    return z


# punch-in sobre mí al arrancar el color
def focus_me(t):
    if T_A <= t < T_A + 4.6:
        k = 1 - ease((t - (T_A + 3.6)) / 1.0)
        return 1 + 0.12 * k * ease((t - T_A - 0.5) / 0.6)
    return 1.0

# efecto televisión
rngv = np.random.default_rng(11)
SCAN = np.ones((H, 1, 1), np.float32); SCAN[::4] = 0.72; SCAN[1::4] = 0.86
TVVIG = np.clip(1 - 0.9 * (((xx[None, :] - W / 2) / (W * 0.62)) ** 4 + ((yy[:, None] - H / 2) / (H * 0.6)) ** 4), 0.0, 1)[:, :, None]
fRec = ImageFont.truetype(ARCH8, 34)
def tv_look(arr, fi, t):
    g = arr @ np.array([0.30, 0.59, 0.11], np.float32)
    g = np.clip((g - 128) * 1.25 + 124, 0, 255)
    n = rngv.normal(0, 11, (H // 3, W // 3)).astype(np.float32)
    g = g + np.kron(n, np.ones((3, 3), np.float32))[:H, :W]
    if fi % 17 in (0, 1):   # línea que rueda
        y0 = int((t * 900) % H); g[y0:y0 + 26] += 28
    out = np.repeat(g[:, :, None], 3, 2) * SCAN * TVVIG
    return out
def glitch(arr, k, fi):
    """k 0..1: estática + corrimiento de canales + franjas desplazadas"""
    r = np.random.default_rng(fi)
    out = arr.copy()
    sh = int(40 * k)
    out[:, :, 0] = np.roll(arr[:, :, 0], sh, 1); out[:, :, 2] = np.roll(arr[:, :, 2], -sh, 1)
    for _ in range(int(10 * k) + 1):
        y0 = r.integers(0, H - 80); hgt = r.integers(10, 120)
        out[y0:y0 + hgt] = np.roll(out[y0:y0 + hgt], r.integers(-160, 160), 1)
    static = r.integers(0, 255, (H // 4, W // 4)).astype(np.float32)
    static = np.kron(static, np.ones((4, 4), np.float32))[:, :, None]
    return out * (1 - 0.85 * k) + static * 0.85 * k
GL0, GL1 = T_X - 0.22, T_X + 0.16
def glitch_k(t):
    if GL0 <= t < GL1:
        return 1 - abs(t - T_X) / (0.22 if t < T_X else 0.16)
    return 0

class Src:
    """lector secuencial de un clip (reabre si hace falta saltar)"""
    def __init__(self, clip):
        self.path = 'b/rem.mp4' if clip == 'rem' else f'b/{clip}.mp4'
        self.p = None; self.pos = None; self.last = None
    def get(self, ts):
        fidx = int(round(ts * FPS))
        if self.p is None or self.pos is None or fidx < self.pos or fidx > self.pos + 3:
            if self.p: self.p.kill()
            self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{fidx / FPS:.4f}', '-i', self.path,
                                       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
            self.pos = fidx - 1
        while self.pos < fidx:
            raw = self.p.stdout.read(W * H * 3)
            self.pos += 1
            if len(raw) == W * H * 3:
                self.last = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        return self.last
SRCS = {}
def frame_of(clip, ts):
    if clip not in SRCS: SRCS[clip] = Src(clip)
    return SRCS[clip].get(ts)

def transform(img, z, cx_frac=0.5, cy_frac=0.47):
    if abs(z - 1) < 1e-3: return img
    cw, ch_ = W / z, H / z
    cx, cy = W * cx_frac, H * cy_frac
    x0 = min(max(cx - cw * cx_frac, 0), W - cw); y0 = min(max(cy - ch_ * cy_frac, 0), H - ch_)
    return img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch_), Image.BICUBIC)

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', 'out/video.mp4'],
                       stdin=subprocess.PIPE)
NF = int(round(TOTAL * FPS))
for fi in range(NF):
    t = fi / FPS
    t0, t1, clip, ss, mode = piece_at(t)
    fr = frame_of(clip, ss + (t - t0))
    if mode == 'rem':
        k = ease((t - t0) / 0.3)
        enc.stdin.write((fr.astype(np.float32) * k).astype(np.uint8).tobytes()); continue
    img = Image.fromarray(fr)
    cxf = 0.5
    if mode == 'tv':
        z = 1.06 + 0.04 * (t / T_X)
    elif mode in ('broll', 'montage'):
        z = (1.10 if mode == 'montage' else 1.03) + 0.06 * ((t - t0) / (t1 - t0))
    else:
        z = zoom_at(t) * focus_me(t)
        if clip == 'IMG_0419a' and t < T_A + 4.6: cxf = 0.60
    img = transform(img, z, cxf, 0.40 if clip == 'IMG_0419a' else 0.47)
    arr = np.asarray(img, np.float32)
    if mode == 'tv':
        arr = tv_look(arr, fi, t)
    arr = arr * (1 - SHADE)
    if t < TITLE_END:
        arr = arr * (1 - TSH2 * (1 - ease((t - (TITLE_END - 0.3)) / 0.3)))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_title(lay, t)
    draw_caps(lay, t)
    if mode == 'tv':   # cartel de transmisión
        d = ImageDraw.Draw(lay)
        if int(t * 2) % 2 == 0: d.ellipse((72, 236, 98, 262), fill=(214, 48, 40, 235))
        tracked(d, 112, 262, 'EN VIVO', fRec, 0.95, 5)
        tracked(d, 72, 312, 'MONTE HERMOSO', fLab.font_variant(size=26) if hasattr(fLab, 'font_variant') else fLab, 0.75, 6)
    lay.alpha_composite(logo, (W - logo.width - 64, 230))
    img.alpha_composite(lay)
    rgb = np.asarray(img.convert('RGB'), np.float32)
    kf = max(0.0, 1 - abs(t - T_17) / 0.13) * 0.6 if abs(t - T_17) < 0.13 else 0.0
    if kf > 0: rgb = rgb + (np.array([255, 246, 228], np.float32) - rgb) * kf
    k = glitch_k(t)
    if k > 0: rgb = glitch(rgb, k, fi)
    enc.stdin.write(np.clip(rgb, 0, 255).astype(np.uint8).tobytes())
    if fi % 150 == 0: print(f'{t:.1f}/{TOTAL:.1f}', flush=True)
for s_ in SRCS.values():
    if s_.p: s_.p.kill()
enc.stdin.close(); enc.wait()

# ---------------- audio ----------------
SR = 48000
def load(path, ss=0, dur=None, af=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(ss)] + (['-t', str(dur)] if dur else []) + ['-i', path] + (['-af', af] if af else []) + ['-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
mix = np.zeros((int(TOTAL * SR) + SR, 2), np.float32)
def put(x, t0, g=1.0):
    i = int(t0 * SR); n = min(len(x), len(mix) - i); mix[i:i + n] += x[:n] * g
def fade(x, a=0.015, b=0.015):
    n1, n2 = int(a * SR), int(b * SR)
    x[:n1] *= np.linspace(0, 1, n1)[:, None]; x[-n2:] *= np.linspace(1, 0, n2)[:, None]; return x
TV_AF = ('highpass=f=320,lowpass=f=3400,acompressor=threshold=-24dB:ratio=6:attack=3:release=60:makeup=8,'
         'asoftclip=type=tanh:param=1.6,equalizer=f=1800:t=q:w=1.2:g=5,aecho=0.8:0.5:18:0.18,volume=0.9')
for i, ((c, s_, e_, m), o) in enumerate(zip(SEG, SOFF)):
    if m == 'tv':
        put(fade(load(f'a/{c}.wav', s_, e_ - s_, TV_AF), 0.01, 0.06 if i == 0 else 0.12), o, 1.0)
    else:
        put(fade(load(f'a/{c}.wav', s_, e_ - s_)), o)
rng = np.random.default_rng(3)
def noise_burst(dur, gain, lo=900, hi=7000):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] *= 0.08; x = np.fft.irfft(X, n)
    env = np.minimum(1, np.linspace(0, 6, n)) * np.linspace(1, 0.2, n); x = x / np.abs(x).max() * env * gain
    return np.stack([x, x], 1).astype(np.float32)
put(noise_burst(0.38, 0.22), GL0)           # estática de la tele
def whoosh(dur=0.45, gain=0.16):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X *= 1 / np.sqrt(np.maximum(f, 40)); x = np.fft.irfft(X, n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2; x = x / np.abs(x).max() * env * gain
    return np.stack([x, x], 1).astype(np.float32)
put(whoosh(), T_17 - 0.26)
tic = np.zeros((int(0.03 * SR), 2), np.float32); tic[:40] = 0.6; put(tic, T_X - 0.01)   # "tic"
# canción: continua desde que arranca el color, alineada con el parlante de IMG_0419a
song_start = SONG_AT_0419A - (T_A - T_X)     # continuo desde la transición, en fase con el parlante de Manu
mus = load(MUSIC, song_start, TOTAL - T_X + 0.5)
tt = T_X + np.arange(len(mus)) / SR
P2 = OUT('IMG_0419a', 4.30)
g = np.interp(tt, [T_X, T_X + 0.6, T_A - 0.3, T_A, P2 - 0.3, P2, T_REM - 0.1, T_REM + 0.6, TOTAL - 1.4, TOTAL],
                  [0.0, 0.17, 0.17, 0.20, 0.20, 0.45, 0.45, 0.85, 0.85, 0.0])
put(fade(mus * g[:, None].astype(np.float32), 0.05, 0.05), T_X)
mix = mix[:int(TOTAL * SR)]
mix.tofile('out/mix.f32')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', 'out/mix.f32',
                '-af', 'loudnorm=I=-14:TP=-1.2,alimiter=limit=0.89', '-ar', str(SR), '-c:a', 'pcm_s16le', 'out/mix.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'out/video.mp4', '-i', 'out/mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-movflags', '+faststart', 'out/reel-asado-de-obra.mp4'], check=True)
print('ok', TOTAL, 'T_X', T_X, 'T_16', T_16, 'T_REM', T_REM)
