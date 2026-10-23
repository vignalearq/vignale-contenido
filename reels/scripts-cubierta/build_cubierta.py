"""Historia 'Explicando la cubierta' (Monte Hermoso) — subtítulos palabra por palabra.
Uso: python3 build_cubierta.py  (rutas relativas al scratchpad)
"""
import subprocess, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = 'fonts/'
ARCH8 = FD + 'fontsource-archivo-5.3.0/package/files/archivo-latin-800-normal.woff2'
ARCH6 = FD + 'fontsource-archivo-5.3.0/package/files/archivo-latin-600-normal.woff2'
ITAL = FD + 'fontsource-italiana-5.3.0/package/files/italiana-latin-400-normal.woff2'
WHITE = (244, 242, 236)
fCap = ImageFont.truetype(ARCH8, 66)
fKey = ImageFont.truetype(ITAL, 112)
fLab = ImageFont.truetype(ARCH6, 36)
fTit = ImageFont.truetype(ITAL, 150)
fList = ImageFont.truetype(ARCH6, 33)
fListN = ImageFont.truetype(ARCH8, 33)
fBig = ImageFont.truetype(ARCH8, 120)

def ease(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0.0), 1.0); c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------- montaje ----------------
SEG = [('b', 0.00, 5.30), ('a', 7.10, 31.12), ('a', 32.08, 47.00), ('r', 0.0, 3.60)]
VO_OFF = -0.12   # audio nuevo de Francisco: t_salida = t_vo + VO_OFF
OFF = []; acc = 0
for s in SEG:
    OFF.append(acc); acc += s[2] - s[1]
TOTAL = acc
def A(t):  # tiempo del clip a -> tiempo de salida
    for (src, s, e), o in zip(SEG, OFF):
        if src == 'a' and s - 0.05 <= t <= e + 0.05:
            return o + (t - s)
    raise ValueError(t)
T_INTRO_END = OFF[1]; T_REM = OFF[3]; T_ANSWER = OFF[1]

# ---------------- subtítulos (texto corregido, tiempos de whisper en el clip a) ----------------
# '*' = palabra clave en Italiana
RAW = [
 "HOLA,@v0.82 ¿CÓMO@v1.18 ANDAN?@v1.38",
 "ACÁ@v1.74 ESTAMOS@v1.86 CON@v2.06 JULIÁN*@v2.22 Y@v2.52 CON@v2.60 GIAN*@v2.72",
 "Y@v2.92 LES@v3.28 QUEREMOS@v3.40 MOSTRAR@v3.58",
 "UN@v3.78 POQUITO@v3.94 LO@v4.12 QUE@v4.26 ESTAMOS@v4.34 AVANZANDO*@v4.52",
 "YA@7.36 ORGANIZANDO@7.70 EL@8.14 TEMA@8.26 DEL@8.38 TECHO*@8.56",
 "YA@8.98 TENEMOS@9.10 LOS@9.32 CLAVADORES*@9.62 PUESTOS@10.26",
 "LOS@11.30 CLAVADORES@11.38 SI@11.72 BIEN@11.90 TIENEN@12.00",
 "SU@12.18 ALTURA*@12.34 CORRESPONDIENTE@12.58",
 "PORQUE@13.62 VA@13.74 UNA@13.90 CANALETA*@14.26 INTERNA*@14.62",
 "VAMOS@15.60 A@16.30 LA@16.40 ESPERA@17.10",
 "DE@17.38 LA@17.68 LANA*@17.78 DE*@17.92 VIDRIO*@18.08",
 "Y@18.52 LA@18.78 AISLACIÓN*@18.92 TÉRMICA*@19.52",
 "YA@20.62 COLOCAMOS@20.80 ESO@21.08",
 "Y@21.40 SALIMOS@21.58 TECHANDO*@21.82",
 "LA@22.92 CHAPA*@23.28 VIENE@23.50 POR@24.20 ACÁ@24.40 ARRIBA@24.54",
 "QUEDA@25.60 LA@25.98 CANALETA*@26.14 INTERNA*@26.54",
 "DESPUÉS@27.02 ESTO@27.38 SE@27.54 REVISTE@27.66 EN@27.90",
 "FIBROCEMENTO*@28.04",
 "QUEDA@28.84 UNA@28.98 CÁMARA*@29.12 DE*@29.32 AIRE*@29.48",
 "Y@29.64 DESPUÉS@29.98 VA@30.10 UNA@30.28 CENEFA*@30.44",
 "DE@32.18 TERMINACIÓN@32.30 DEL@32.62 ALERO*@32.84",
 "Y@33.66 A@33.86 LA@33.92 VEZ@34.02 NOS@34.32 SIRVE…@34.40",
 "—¿ES@34.56 ESTA?@34.84",
 "AHÍ@35.86 VA,@36.08 LA@36.42 TENEMOS@36.56 ACÁ@36.90 PRESENTADA@37.06",
 "Y@38.32 A@38.74 LA@38.80 VEZ@38.90 NOS@39.06 SIRVE@39.20 DESPUÉS@39.46",
 "PARA@39.62 EMBUTIR@39.98 EL@40.40 REVESTIMIENTO*@40.52 EXTERIOR*@40.92",
 "Y@41.30 NO@41.52 SE@41.62 LE@41.72 VE@41.85 NINGÚN@42.02 TORNILLO*@42.25",
 "CHICHI@43.04 BOMBÓN@43.30",
 "VAMOS!@43.72 QUE!@43.92 VAMOS!@44.16",
 "EXCELENTE*@44.96",
]
END_HOLD = 0.65
chunks = []
for line in RAW:
    words = []
    for tok in line.split():
        w, t = tok.rsplit('@', 1)
        kind = 'key' if w.endswith('*') else ('big' if w.endswith('!') else 'cap')
        w = w.rstrip('*!')
        words.append((w, float(t[1:]) + VO_OFF if t.startswith('v') else A(float(t)), kind))
    chunks.append(words)
spans = []
for i, ch in enumerate(chunks):
    st = ch[0][1] - 0.04
    en = ch[-1][1] + END_HOLD + 0.25
    if i + 1 < len(chunks):
        en = min(en, chunks[i + 1][0][1] - 0.04)
    spans.append((st, en))

def font_for(kind, w):
    if kind == 'key':
        return fKey
    if kind == 'big':
        return fBig
    return fCap

def layout(words):
    """reparte palabras en líneas (máx 900 px) y devuelve [(word,t,kind,x,baseline)]"""
    SP = 22; MAXW = 900
    lines = [[]]; lw = 0
    for w, t, k in words:
        f = font_for(k, w); ww = f.getlength(w if k != 'key' else w.capitalize() if False else w)
        if lines[-1] and lw + SP + ww > MAXW:
            lines.append([]); lw = 0
        lines[-1].append((w, t, k, ww)); lw += (SP if lw else 0) + ww
    out = []
    LH = [max(118 if k == 'big' else (96 if k == 'key' else 78) for *_, k, _ in ln) for ln in lines]
    total = sum(LH)
    y = 1235 - total / 2
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
            f = font_for(k, w)
            txt = w
            if k == 'key':
                txt = w.lower().capitalize() if False else w
            dy = (1 - ease(p)) * 26
            sc = back(p) if k == 'big' else 1.0
            if k == 'big' or sc != 1.0:
                tmp = Image.new('RGBA', (int(f.getlength(txt)) + 40, 200), (0, 0, 0, 0))
                ImageDraw.Draw(tmp).text((20, 160), txt, font=f, fill=WHITE + (int(255 * a),), anchor='ls')
                s = max(0.2, 0.55 + 0.45 * sc)
                tmp = tmp.resize((max(1, int(tmp.width * s)), max(1, int(tmp.height * s))), Image.BICUBIC)
                cx = x + f.getlength(txt) / 2
                layer.alpha_composite(tmp, (int(cx - tmp.width / 2), int(y - 160 * s + dy)))
            else:
                ImageDraw.Draw(layer).text((x, y + dy), txt, font=f, fill=WHITE + (int(255 * a),), anchor='ls')

# ---------------- "capa por capa" (lista que se va completando) ----------------
CAPAS = [('CLAVADORES', 9.62), ('CANALETA INTERNA', 14.26), ('LANA DE VIDRIO', 17.78),
         ('AISLACIÓN TÉRMICA', 18.92), ('CHAPA', 23.28), ('FIBROCEMENTO', 28.04),
         ('CÁMARA DE AIRE', 29.12), ('CENEFA', 30.44)]
CAPAS = [(n, A(t)) for n, t in CAPAS]
LIST_IN = A(9.2); LIST_OUT = A(33.4)

def tracked(d, x, y, text, font, alpha, track=4.0, anchor='ls'):
    for c in text:
        d.text((x, y), c, font=font, fill=WHITE + (int(255 * alpha),), anchor=anchor)
        x += font.getlength(c) + track
    return x

def draw_list(layer, t):
    if not (LIST_IN <= t < LIST_OUT + 0.4):
        return
    a0 = ease((t - LIST_IN) / 0.4) * (1 - ease((t - LIST_OUT) / 0.4))
    d = ImageDraw.Draw(layer)
    x0, y0 = 64, 300
    tracked(d, x0, y0, 'LA CUBIERTA,', fList, a0 * 0.95, 5)
    d.text((x0, y0 + 50), 'capa por capa', font=ImageFont.truetype(ITAL, 58), fill=WHITE + (int(255 * a0),), anchor='ls')
    d.line((x0, y0 + 76, x0 + 290, y0 + 76), fill=WHITE + (int(160 * a0),), width=2)
    for i, (n, tn) in enumerate(CAPAS):
        p = (t - tn) / 0.3
        if p <= 0:
            continue
        a = ease(p) * a0
        yy = y0 + 130 + i * 49
        xx = x0 - (1 - ease(p)) * 30
        tracked(d, xx, yy, f'{i+1:02d}', fListN, a, 2)
        tracked(d, xx + 62, yy, n, fList, a, 3)

# ---------------- intro y estampa final ----------------
def rising(layer, text, font, cx, baseline, p, alpha=1.0):
    if p <= 0: return
    tmp = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    off = (1 - ease(p)) * 200
    ImageDraw.Draw(tmp).text((cx, 200 + off), text, font=font, fill=WHITE + (int(255 * alpha),), anchor='ms')
    layer.alpha_composite(tmp, (0, int(baseline - 200)))

def draw_intro(layer, t):
    if t >= T_INTRO_END: return
    TITLE_END = 3.2
    if t >= TITLE_END: return
    out = 1 - ease((t - (TITLE_END - 0.35)) / 0.35)
    pl = ease((t - 0.25) / 0.45)
    d = ImageDraw.Draw(layer)
    lab = 'HOY EN LA OBRA'
    wl = sum(fLab.getlength(c) for c in lab) + 8 * (len(lab) - 1)
    tracked(d, (W - wl) / 2, 745 + (1 - pl) * 25, lab, fLab, pl * out, 8)
    rising(layer, 'Explicando', fTit, W / 2, 905, (t - 0.45) / 0.6, out)
    rising(layer, 'la cubierta', fTit, W / 2, 1058, (t - 0.62) / 0.6, out)

ST_IN = A(45.25); ST_OUT = T_REM
def draw_stamp(layer, t):
    if not (ST_IN <= t < ST_OUT): return
    p = (t - ST_IN) / 0.35
    s = 1.6 - 0.6 * ease(p)
    a = min(1, p * 2)
    tmp = Image.new('RGBA', (760, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.rounded_rectangle((10, 10, 750, 320), radius=26, outline=WHITE + (int(255 * a),), width=7)
    d.text((380, 135), 'Cubierta', font=ImageFont.truetype(ITAL, 118), fill=WHITE + (int(255 * a),), anchor='ms')
    lab = 'APROBADA'
    f = ImageFont.truetype(ARCH8, 84)
    wl = sum(f.getlength(c) for c in lab) + 10 * (len(lab) - 1)
    tracked(d, 380 - wl / 2, 262, lab, f, a, 10)
    tmp = tmp.rotate(7, resample=Image.BICUBIC, expand=True)
    tmp = tmp.resize((int(tmp.width * s), int(tmp.height * s)), Image.BICUBIC)
    layer.alpha_composite(tmp, (int(W / 2 - tmp.width / 2), int(470 - tmp.height / 2)))

# ---------------- logo VA (sacado del remate) ----------------
rem_fr = Image.open('b/rem_3.png').convert('L')
_m = np.asarray(rem_fr, np.float32)[690:990]
_cols = np.where((_m > 110).any(0))[0]
mark = _m[:, max(0, _cols.min() - 12):_cols.max() + 13]
alpha = np.clip((mark - 60) / (240 - 60), 0, 1)
ys, xs = np.where(alpha > 0.1)
alpha = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
alpha = np.pad(alpha, 6)
logo = Image.new('RGBA', (alpha.shape[1], alpha.shape[0]), WHITE + (0,))
logo.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
lh = 78
logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)

# ---------------- grade de legibilidad (degradés suaves, sin recuadros) ----------------
yy = np.arange(H, dtype=np.float32)
band = np.exp(-((yy - 1215) / 260) ** 2) * 0.42
top = np.clip(1 - yy / 1000, 0, 1) ** 1.3 * 0.5
SHADE_FULL = np.clip(band + top, 0, 0.6)[:, None, None]
SHADE_TOP = (top)[:, None, None]

# ---------------- zoom (punch-in en palabras clave) ----------------
punch = []
for ch in chunks:
    for w, t, k in ch:
        if k in ('key', 'big'):
            punch.append(t); break
def zoom_at(t):
    z = 1.0
    for i, tp in enumerate(punch):
        if tp - 0.02 <= t:
            nxt = punch[i + 1] if i + 1 < len(punch) else 1e9
            if t < nxt:
                amt = 0.06 if i % 2 == 0 else 0.04
                z = 1 + amt * ease((t - tp) / 0.18) * (1 - ease((t - tp - 1.4) / 0.6))
    return z

def shake(t):
    t0, t1 = A(43.72), A(44.6)
    if t0 <= t < t1:
        k = 1 - (t - t0) / (t1 - t0)
        return 9 * k * math.sin(t * 61), 7 * k * math.cos(t * 47)
    return 0, 0

# ---------------- render ----------------
def reader(path, ss, dur):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(ss), '-t', str(dur), '-i', path, '-vf', f'fps={FPS},scale={W}:{H}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    return subprocess.Popen(cmd, stdout=subprocess.PIPE)

SRC = {'a': 'b/a_sun.mp4', 'b': 'b/n.mp4', 'r': 'b/rem.mov'}
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', 'w/video.mp4'],
                       stdin=subprocess.PIPE)
fi = 0
NF = int(round(TOTAL * FPS))
for (src, s, e), o in zip(SEG, OFF):
    n = int(round((o + (e - s)) * FPS)) - int(round(o * FPS))
    p = reader(SRC[src], s, e - s + 0.2)
    last = None
    for j in range(n):
        raw = p.stdout.read(W * H * 3)
        if len(raw) == W * H * 3:
            last = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        frame = last
        t = fi / FPS
        img = Image.fromarray(frame)
        if src == 'b' and t < 1.7:
            rad = 38 * (1 - ease(t / 1.7))
            if rad > 0.3:
                img = img.filter(ImageFilter.GaussianBlur(rad))
        if src == 'r':
            fin = ease(j / 8)
            arr = (np.asarray(img, np.float32) * fin).astype(np.uint8)
            enc.stdin.write(arr.tobytes()); fi += 1; continue
        z = zoom_at(t) if src == 'a' else 1.0 + 0.05 * (t / T_INTRO_END)
        sx, sy = shake(t)
        if z != 1.0 or sx or sy:
            cw, ch_ = W / z, H / z
            cx, cy = W / 2 + sx, H * 0.47 + sy
            img = img.transform((W, H), Image.EXTENT, (cx - cw / 2, cy - ch_ * 0.47, cx + cw / 2, cy + ch_ * 0.53), Image.BICUBIC)
        arr = np.asarray(img, np.float32)
        if src == 'b':
            arr = arr * (1 - SHADE_FULL)
        else:
            arr = arr * (1 - SHADE_FULL)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        if src == 'b':
            draw_intro(lay, t)
            draw_caps(lay, t)
        else:
            draw_caps(lay, t)
            draw_list(lay, t)
            draw_stamp(lay, t)
        lay.alpha_composite(logo, (W - logo.width - 64, 230))
        img.alpha_composite(lay)
        # destello al entrar al primer clip
        rgb = np.asarray(img.convert('RGB'), np.float32)
        if T_INTRO_END - 0.07 <= t < T_INTRO_END + 0.2:
            k = 1 - abs(t - T_INTRO_END) / 0.2
            rgb = rgb + (255 - rgb) * max(0, k) * 0.85
        enc.stdin.write(np.clip(rgb, 0, 255).astype(np.uint8).tobytes()); fi += 1
    p.kill()
enc.stdin.close(); enc.wait()
print('frames', fi, 'total', TOTAL)

# ---------------- audio ----------------
SR = 48000
def load(path, ss=0, dur=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(ss)] + (['-t', str(dur)] if dur else []) + ['-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
mix = np.zeros((int(TOTAL * SR) + SR, 2), np.float32)
def put(x, t0):
    i = int(t0 * SR); mix[i:i + len(x)] += x[:len(mix) - i]
def fade(x, fi_=0.012, fo=0.012):
    n1, n2 = int(fi_ * SR), int(fo * SR)
    x[:n1] *= np.linspace(0, 1, n1)[:, None]; x[-n2:] *= np.linspace(1, 0, n2)[:, None]; return x
for (src, s, e), o in zip(SEG, OFF):
    if src == 'a' and s < 1.0:
        pass  # Julián escuchando: sin audio original (va la voz nueva + ambiente)
    elif src == 'a' and s < 7.2:
        put(fade(load('w/a_clean.wav', 7.18, e - 7.18), 0.04), o + (7.18 - s))
    elif src == 'a':
        put(fade(load('w/a_clean.wav', s, e - s)), o)
    if src == 'r':
        put(fade(load('b/rem.mov', s, e - s), 0.15, 0.4), o)
rng = np.random.default_rng(3)
def whoosh(dur=0.7, gain=0.18):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X *= 1 / np.sqrt(np.maximum(f, 40)); x = np.fft.irfft(X, n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2; x = x / np.abs(x).max() * env * gain
    return np.stack([x, x], 1).astype(np.float32)
def tick(freq=1750, gain=0.10):
    n = int(0.07 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 70) * gain
    return np.stack([x, x], 1).astype(np.float32)
vo = load('w/vo_clean.wav', max(0, -VO_OFF))
put(fade(vo, 0.03, 0.2), max(0, VO_OFF))
bed = load('w/bed.wav')[:int((T_ANSWER + 0.5) * SR)] * (10 ** ((41 - 31) / 20))
put(fade(bed, 0.25, 0.6), 0.0)
# música original de fondo: arriba en el arranque, muy de fondo debajo de la voz
mus = load('w/music.wav')[:int(T_REM * SR) + SR // 2]
tt = np.arange(len(mus)) / SR
g = np.interp(tt, [0, 0.55, 1.0, T_REM - 0.6, T_REM + 0.4], [0.75, 0.75, 0.17, 0.17, 0.0])
put(fade(mus * g[:, None].astype(np.float32), 0.05, 0.3), 0.0)
put(whoosh(0.45, 0.20), T_INTRO_END - 0.3)
for i, (n, tn) in enumerate(CAPAS):
    put(tick(1500 + 90 * i, 0.07), tn)
put(whoosh(0.35, 0.22), ST_IN - 0.1)
mix = mix[:int(TOTAL * SR)]
mix.tofile('w/mix.f32')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', 'w/mix.f32',
                '-af', 'alimiter=limit=0.89', '-c:a', 'pcm_s16le', 'w/mix.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'w/video.mp4', '-i', 'w/mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-movflags', '+faststart', 'historia-cubierta.mp4'], check=True)
print('ok')
