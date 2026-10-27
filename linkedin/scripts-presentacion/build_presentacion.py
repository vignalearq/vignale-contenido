"""Video de presentación para LinkedIn (4:5, 1080x1350, 30 fps).
Recopilación de obras + textos "nuevo espacio" + logo VA que se difumina + remate VA.
Uso: python3 build_presentacion.py <repo> <fonts_dir> <out.mp4>
"""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FPS = 30; W, H = 1080, 1350; SW, SH = 1080, 1920
VERDE = (0x36, 0x39, 0x32); BLANCO = (242, 241, 236)
FA = FONTS + '/Archivo.ttf'; FI = FONTS + '/Italiana.ttf'
SRC = {'P': REPO + '/reels/reel-parador-paredes-arriba.mp4',
       'L': REPO + '/historias/historia-lunes-de-obra-A.mp4',
       'Z': REPO + '/reels/reel-lanzamiento-web-SIN-MUSICA.mp4'}

def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def eout(u, p=3): u = min(1, max(0, u)); return 1 - (1 - u) ** p

# ---------- lectura de clips ----------
_cache = {}
def frames(src, s, d, yoff):
    k = (src, s, d, yoff)
    if k not in _cache:
        while len(_cache) >= 3: _cache.pop(next(iter(_cache)))
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-i', SRC[src], '-t', str(d + 0.1),
                              '-vf', f'crop={W}:{H}:0:{yoff}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True).stdout
        a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
        _cache[k] = np.stack([grade(f) for f in a])
    return _cache[k]

def grade(a):
    """color cálido y soleado: más contraste y saturación"""
    f = a.astype(np.float32) / 255
    f = (f - 0.5) * 1.10 + 0.5
    g = f.mean(axis=-1, keepdims=True); f = g + (f - g) * 1.18
    f[..., 0] *= 1.04; f[..., 2] *= 0.95
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)

def zoom(a, s, dy=0.0):
    if abs(s - 1) < 1e-4 and dy == 0: return a
    w, h = W / s, H / s; x0 = (W - w) / 2; y0 = (H - h) / 2 + dy
    return np.asarray(Image.fromarray(a).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)))

def blur(a, r):
    if r < 0.3: return a
    return np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(float(r))))

def mix(a, b, u): return (a.astype(np.float32) * (1 - u) + b.astype(np.float32) * u).astype(np.uint8)
def green(): return np.full((H, W, 3), VERDE, np.uint8)

yy, xx = np.mgrid[:H, :W].astype(np.float32)
def leak(a, amt, cx=0.85, cy=0.2):
    if amt <= 0: return a
    g = np.exp(-(((xx / W - cx) / 0.5) ** 2 + ((yy / H - cy) / 0.55) ** 2)) * amt
    out = a.astype(np.float32) + np.array([255, 170, 90], np.float32) * g[..., None] * 0.85
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------- montaje: (inicio, dur, fuente, desde, disponible, yoff) ----------
SEQ = []
def add(d, src, s, avail, yoff=285):
    t0 = SEQ[-1][0] + SEQ[-1][1] if SEQ else 2.2
    SEQ.append((t0, d, src, s, avail, yoff))
add(2.4, 'P', 8.0, 1.9)          # vista al mar, estructura
add(1.8, 'P', 2.0, 1.9)          # clavando
for s, d in [(4.22, .18), (4.70, .28), (5.10, .14), (5.30, .14), (5.56, .1), (5.76, .16)]:
    add(0.22, 'Z', s, d)         # ráfaga
add(1.8, 'L', 3.0, 1.9, 450)     # cloaca
add(1.6, 'P', 6.3, 1.1, 60)      # levantando paneles
add(1.8, 'L', 12.0, 1.9, 450)    # panelizado superior
add(1.5, 'P', 14.0, 0.9)         # deck al sol
add(1.8, 'L', 7.0, 1.9, 450)     # agua
add(1.6, 'P', 0.2, 1.7, 450)     # deck con el equipo
add(1.2, 'P', 12.0, 0.45)        # ventana al mar
add(1.9, 'P', 16.9, 1.05, 150)   # equipo, saludo
T_REM = SEQ[-1][0] + SEQ[-1][1]
REM_D = 3.6
TOTAL = T_REM + REM_D
XF = 0.3  # fundido entre clips

def clip_frame(i, t):
    t0, d, src, s, avail, yoff = SEQ[i]
    fr = frames(src, s, avail, yoff)
    sp = min(1.0, avail / (d + XF))
    u = (t - t0) / d
    k = min(len(fr) - 1, max(0, int((t - t0) * sp * FPS)))
    a = fr[k]
    if src != 'Z':
        a = zoom(a, 1.0 + 0.06 * u)   # acercamiento lento
    return a

def montage(t):
    idx = [i for i, c in enumerate(SEQ) if c[0] <= t < c[0] + c[1] + (XF if c[2] != 'Z' else 0)]
    if not idx: return None
    i = idx[-1]
    a = clip_frame(i, t)
    if len(idx) > 1 and SEQ[i][2] != 'Z' and SEQ[idx[-2]][2] != 'Z':
        j = idx[-2]; u = ease((t - SEQ[i][0]) / XF)
        b = clip_frame(j, t); r = 10 * np.sin(np.pi * u)
        a = mix(blur(b, r), blur(a, r), u)
        a = leak(a, 0.35 * np.sin(np.pi * u))
    return a

# ---------- logo VA ----------
lg = np.array(Image.open(REPO + '/ideas/reel-hoja-logo/hoja_A4_logo_verde.png').convert('L')).astype(np.float32)
ys, xs = np.where(lg > 128); lg = lg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
LOGO = Image.fromarray(np.clip((lg - 60) * 1.4, 0, 255).astype(np.uint8))
def logo_layer(w, al, r=0.0):
    lw = LOGO.resize((int(w), int(w * LOGO.height / LOGO.width)), Image.LANCZOS)
    m = Image.new('L', (W, H), 0); m.paste(lw, (int((W - lw.width) / 2), int((H - lw.height) / 2 - 40)))
    if r > 0.3: m = m.filter(ImageFilter.GaussianBlur(r))
    return np.asarray(m).astype(np.float32) / 255 * al

def comp(a, m, col=BLANCO):
    out = a.astype(np.float32) * (1 - m[..., None]) + np.array(col, np.float32) * m[..., None]
    return out.astype(np.uint8)

def intro(t):
    """logo nítido sobre verde que se difumina y deja ver la obra"""
    base = green()
    if t >= 1.5:
        a = clip_frame(0, max(t, SEQ[0][0])) if t >= SEQ[0][0] else frames('P', 8.0, 1.9, 285)[0]
        u = ease((t - 1.5) / 1.1); base = mix(base, blur(a, 18 * (1 - u)), u)
    al = eout(t / 0.9) * (1 - ease((t - 1.6) / 1.0))
    r = 0 if t < 1.3 else 26 * ease((t - 1.3) / 1.3)
    w = 300 * (1 + 0.25 * ease((t - 1.3) / 1.4))
    return comp(base, logo_layer(w, al, r))

# ---------- textos (Archivo + Italiana) ----------
_d = ImageDraw.Draw(Image.new('L', (1, 1)))
def fa(sz): f = ImageFont.truetype(FA, int(sz)); f.set_variation_by_axes([900, 125]); return f
def fit(text, maxw, mx=150):
    lo, hi = 10, mx
    while hi - lo > 1:
        m = (lo + hi) // 2
        if _d.textlength(text, font=fa(m)) > maxw: hi = m
        else: lo = m
    return lo
FIT = ImageFont.truetype(FI, 84)

TEXTS = [  # (desde, hasta, MAYÚSCULA, itálica)
    (2.7, 4.5, 'HACE UN TIEMPO', 'que no pasaba por acá'),
    (4.8, 8.0, 'CINCO AÑOS', 'y más de 36 obras'),
    (8.3, 9.9, 'CADA OBRA', 'nos dejó algo'),
    (11.2, 13.4, 'HOY ABRO', 'un nuevo espacio'),
    (13.9, 16.4, 'PARA COMPARTIR', 'el proceso'),
    (16.8, 19.0, 'Y CRECER', 'entre colegas'),
]
TEXTS.append((SEQ[-1][0] + 0.25, T_REM - 0.05, 'BIENVENIDOS', 'a este espacio'))

def text_layer(t, t0, t1, big, small):
    u = eout((t - t0) / 0.45); v = 1.0 if t < t1 - 0.3 else max(0, (t1 - t) / 0.3)
    al = u * v
    if al <= 0: return None, 0
    sz = fit(big, 880); f = fa(sz); sp = int((1 - u) * sz * 0.2)
    widths = [_d.textlength(c, font=f) for c in big]; tw = sum(widths) + sp * (len(big) - 1)
    bb = _d.textbbox((0, 0), big, font=f); th = bb[3] - bb[1]
    sb = _d.textbbox((0, 0), small, font=FIT); sh = sb[3] - sb[1]
    tot = th + 26 + sh; y0 = (H - tot) / 2 + 14 * (1 - u)
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m); x = (W - tw) / 2
    for c, w_ in zip(big, widths): d.text((x, y0 - bb[1]), c, font=f, fill=255); x += w_ + sp
    u2 = eout((t - t0 - 0.25) / 0.5)
    if u2 > 0:
        sl = Image.new('L', (W, H), 0)
        ImageDraw.Draw(sl).text(((W - (sb[2] - sb[0])) / 2 - sb[0], y0 + th + 26 - sb[1] + 10 * (1 - u2)), small, font=FIT, fill=int(255 * u2))
        m = Image.fromarray(np.maximum(np.asarray(m), np.asarray(sl)))
    if u < 1: m = m.filter(ImageFilter.GaussianBlur(5 * (1 - u)))
    return np.asarray(m).astype(np.float32) / 255 * al, al

def texts(a, t):
    for t0, t1, big, small in TEXTS:
        if t0 <= t <= t1:
            m, al = text_layer(t, t0, t1, big, small)
            if m is None: continue
            dark = 1 - 0.32 * al * np.exp(-((yy / H - 0.5) / 0.28) ** 2)
            a = (a.astype(np.float32) * dark[..., None]).astype(np.uint8)
            a = comp(a, m)
    return a

def marca(a, t):
    """VA chico arriba a la derecha durante el montaje"""
    if t < 3.0 or t > T_REM - 0.2: return a
    al = 0.85 * min(1, (t - 3.0) / 0.5) * min(1, (T_REM - 0.2 - t) / 0.3)
    lw = LOGO.resize((70, int(70 * LOGO.height / LOGO.width)), Image.LANCZOS)
    m = Image.new('L', (W, H), 0); m.paste(lw, (W - 50 - 70, 50))
    return comp(a, np.asarray(m).astype(np.float32) / 255 * al)

# ---------- remate fijo (final del Pompidou, tomado del reel del parador) ----------
def remate(t):
    REM = frames('P', 18.0, REM_D, 285)
    k = min(len(REM) - 1, int((t - T_REM) * FPS))
    return REM[k]

# ---------- render ----------
N = int(TOTAL * FPS)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', OUT],
                       stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS
    if t < SEQ[0][0] + 0.4:
        a = intro(t)
        if t >= SEQ[0][0]: a = texts(a, t)
    elif t < T_REM:
        a = montage(t); a = texts(a, t); a = marca(a, t)
        if t > T_REM - 0.35:  # fundido a negro hacia el remate
            a = (a.astype(np.float32) * max(0, (T_REM - t) / 0.35)).astype(np.uint8)
    else:
        a = remate(t)
    enc.stdin.write(np.ascontiguousarray(a).tobytes())
enc.stdin.close(); enc.wait()
print('dur', TOTAL)
