"""Video de presentación LinkedIn con voz en off de Francisco (4:5, 1080x1350, 30 fps).
Intro: logo VA que se deshace como humo -> recopilación de obras al ritmo de la voz,
subtítulos estilo "Explicando la cubierta" -> remate VA.
Uso: python3 build_voz.py <repo> <fonts_dir> <voz.wav> <musica.wav> <out.mp4>
"""
import sys, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO, FONTS, VOZ, MUS, OUT = sys.argv[1:6]
FPS = 30; W, H = 1080, 1350
VERDE = (0x36, 0x39, 0x32); WHITE = (244, 242, 236)
VO = 1.8                       # la voz arranca en este segundo
SRC = {'P': 'reels/reel-parador-paredes-arriba.mp4', 'L': 'historias/historia-lunes-de-obra-A.mp4',
       'Z': 'reels/reel-lanzamiento-web-SIN-MUSICA.mp4', 'B': 'ideas/reel-renovacion-bano.mp4',
       'R': 'historias/historia-proyecto-direccion.mp4'}
STD = (0, 285, 1080, 1350)
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def eout(u, p=3): u = min(1, max(0, u)); return 1 - (1 - u) ** p

# ---------- montaje (inicio en la salida, fuente, desde, caja de recorte 4:5) ----------
CL = [
 (1.90, 'L', 12.0, (0, 450, 1080, 1350)),   # Monte Hermoso, panelizado superior
 (4.00, 'R', 3.0, (140, 60, 800, 1000)),    # mesa con renders: empezó este camino
 (5.80, 'P', 2.0, STD),                      # clavando: sumando experiencias
 (7.60, 'L', 3.0, (0, 450, 1080, 1350)),    # cloaca: mejorar los procesos
 (9.40, 'P', 14.0, STD),                     # deck al sol
 (10.10, 'P', 8.0, (0, 420, 1080, 1350)),   # 36 obras
 (12.30, 'B', 10.2, (60, 40, 1000, 1250)),  # viviendas (baño terminado)
 (13.20, 'B', 5.6, (60, 40, 1000, 1250)),   # reformas (revestimiento)
 (14.30, 'R', 7.0, (100, 40, 880, 1100)),   # planos, accesos
 (16.60, 'P', 6.3, (0, 60, 1080, 1350)),    # y hasta un parador
 (17.75, 'P', 12.0, (0, 150, 1080, 1350)),  # frente al mar
 (18.25, 'P', 0.2, (0, 450, 1080, 1350)),   # Monte Hermoso
 (19.90, 'B', 2.5, (60, 40, 1000, 1250)),   # vereda: picando
 (20.50, 'B', 4.0, (60, 40, 1000, 1250)),   # vereda: colocando con hilo
 (21.60, 'L', 7.0, (0, 450, 1080, 1350)),   # volver a este espacio
 (23.50, 'B', 10.6, (60, 40, 1000, 1250)),  # el resultado
 (24.90, 'L', 5.0, (0, 450, 1080, 1350)),   # todo el proceso
 (26.30, 'R', 4.9, (140, 60, 800, 1000)),   # cómo organizamos una obra
 (27.60, 'L', 10.5, (0, 450, 1080, 1350)),  # decisiones
 (29.00, 'L', 9.0, (0, 450, 1080, 1350)),   # qué salió bien
 (29.95, 'L', 14.6, (0, 450, 1080, 1350)),  # qué haríamos distinto
 (30.80, 'L', 0.0, (0, 450, 1080, 1350)),   # compartiendo
 (33.20, 'B', 7.0, (60, 40, 1000, 1250)),   # colega / construcción / sumate
 (36.10, 'Z', 18.05, (40, 160, 880, 1100)), # los leo en los comentarios
 (37.60, 'P', 16.3, (0, 150, 1080, 1350)),  # bienvenidos (equipo)
]
T_REM = 39.05; REM_D = 3.6; TOTAL = T_REM + REM_D
XF = 0.32
AVAIL = {('P', 14.0): 1.0, ('P', 6.3): 1.5, ('P', 12.0): 1.0, ('P', 0.2): 1.95, ('P', 16.3): 1.65,
         ('B', 2.5): .8, ('B', 4.0): .95, ('L', 9.0): 1.3, ('L', 14.6): 1.15, ('Z', 18.05): 1.45}

def grade(f):
    f = f.astype(np.float32) / 255
    f = (f - 0.5) * 1.08 + 0.5
    g = f.mean(axis=-1, keepdims=True); f = g + (f - g) * 1.15
    f[..., 0] *= 1.03; f[..., 2] *= 0.96
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)

_cache = {}
def load(i):
    if i in _cache: return _cache[i]
    while len(_cache) >= 3: _cache.pop(next(iter(_cache)))
    t0, src, s, (x, y, w, h) = CL[i]
    t1 = CL[i + 1][0] if i + 1 < len(CL) else T_REM
    need = t1 - t0 + XF
    av = AVAIL.get((src, s), 3.0)
    vf = f'crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos'
    if av < need:   # cámara lenta fluida (interpolación de movimiento)
        sp = av / need
        vf += f',setpts=PTS/{sp:.4f},minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'
        dur = av
    else:
        dur = need
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-t', f'{dur + 0.05:.3f}', '-i', REPO + '/' + SRC[src],
                          '-vf', vf, '-r', str(FPS), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    _cache[i] = [grade(f) for f in a]
    return _cache[i]

def zoom(a, s):
    if abs(s - 1) < 1e-4: return a
    M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def blur(a, r):
    if r < 0.3: return a
    return cv2.GaussianBlur(a, (0, 0), r)

def clip_at(i, t):
    fr = load(i); t0 = CL[i][0]; t1 = CL[i + 1][0] if i + 1 < len(CL) else T_REM
    k = min(len(fr) - 1, max(0, int(round((t - t0) * FPS))))
    return zoom(fr[k], 1.0 + 0.05 * (t - t0) / (t1 - t0 + XF))

yy, xx = np.mgrid[:H, :W].astype(np.float32)
LEAK = np.exp(-(((xx / W - 0.85) / 0.5) ** 2 + ((yy / H - 0.2) / 0.55) ** 2))
def leak(a, amt):
    if amt <= 0.01: return a
    out = a.astype(np.float32) + np.array([255, 170, 90], np.float32) * (LEAK * amt * 0.8)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

def montage(t):
    i = max(j for j, c in enumerate(CL) if c[0] <= t + 1e-6)
    a = clip_at(i, t)
    if i > 0 and t < CL[i][0] + XF:            # fundido con desenfoque desde el clip anterior
        u = ease((t - CL[i][0]) / XF); r = 9 * np.sin(np.pi * u)
        b = clip_at(i - 1, t)
        a = cv2.addWeighted(blur(b, r), 1 - u, blur(a, r), u, 0)
        a = leak(a, 0.3 * np.sin(np.pi * u))
    return a

# ---------- logo VA y humo ----------
lg = np.array(Image.open(REPO + '/ideas/reel-hoja-logo/hoja_A4_logo_verde.png').convert('L')).astype(np.float32)
ys, xs = np.where(lg > 128); lg = lg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
LOGO = Image.fromarray(np.clip((lg - 60) * 1.4, 0, 255).astype(np.uint8))
def logo_mask(w, cy=H / 2 - 30):
    lw = LOGO.resize((int(w), int(w * LOGO.height / LOGO.width)), Image.LANCZOS)
    m = Image.new('L', (W, H), 0); m.paste(lw, (int((W - lw.width) / 2), int(cy - lw.height / 2)))
    return np.asarray(m).astype(np.float32) / 255
LM = logo_mask(320)

rng = np.random.default_rng(7)
def fbm(seed_shape, octaves):
    acc = np.zeros((H, W), np.float32); amp = 1.0; tot = 0
    for o in octaves:
        n = rng.standard_normal((max(2, H // o), max(2, W // o))).astype(np.float32)
        acc += cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC) * amp; tot += amp; amp *= 0.55
    return acc / tot
N1 = fbm(None, [180, 90, 40, 18]); N2 = fbm(None, [180, 90, 40, 18]); N3 = fbm(None, [120, 50, 20])

def smoke(p, t):
    """p=0 logo nítido; p=1 disipado. Hilos de humo que suben, se enroscan y se abren."""
    if p <= 0: return LM
    out = np.zeros_like(LM)
    for k, (rise, curl, spread, wgt) in enumerate([(380, 120, 1.0, 0.55), (560, 190, 1.5, 0.35), (260, 80, 0.7, 0.45)]):
        q = p ** (1.2 + 0.2 * k)
        ph = t * (1.3 + 0.4 * k)
        sx = xx + curl * q * (N1 if k % 2 == 0 else N2) + 45 * q * np.sin(yy / (55 + 20 * k) + ph) * spread
        sy = yy + rise * q + 120 * q * (N2 if k % 2 == 0 else N3) + 25 * q * np.cos(xx / 70 + ph)
        m = cv2.remap(LM, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderValue=0)
        m = cv2.GaussianBlur(m, (0, 0), 0.6 + (10 + 8 * k) * q)
        w = (1 - q) if k == 0 else q * (1 - q) * 2.2
        out += m * w * (wgt if k else 1.0)
    thr = np.clip(1.3 - 1.5 * p + 0.5 * N3, 0, 1)
    out = out * (0.35 + 0.65 * thr) * 1.25
    return np.clip(out, 0, 1) * (1 - ease((p - 0.6) / 0.4))

def comp(a, m, col=WHITE):
    out = a.astype(np.float32) * (1 - m[..., None]) + np.array(col, np.float32) * m[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

def intro(t):
    base = np.full((H, W, 3), VERDE, np.uint8)
    vign = (1 - 0.35 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2)[..., None]
    base = (base * vign).astype(np.uint8)
    if t >= CL[0][0]:
        u = ease((t - CL[0][0]) / 1.0)
        base = cv2.addWeighted(base, 1 - u, blur(clip_at(0, t), 16 * (1 - u)), u, 0)
    al = eout(t / 0.7)
    p = max(0.0, (t - 0.8) / 2.2)
    return comp(base, smoke(min(p, 1.0), t) * al)

# ---------- subtítulos ----------
FW = REPO  # noqa
fCap = ImageFont.truetype(FONTS + '/Archivo.ttf', 60); fCap.set_variation_by_axes([800, 100])
fBig = ImageFont.truetype(FONTS + '/Archivo.ttf', 104); fBig.set_variation_by_axes([900, 112])
fKey = ImageFont.truetype(FONTS + '/Italiana.ttf', 100)
# '*' palabra clave (Italiana); '!' palabra grande. Tiempos de la voz (whisper, voz final).
RAW = [
 "HACE@0.0 UN@0.64 TIEMPO*@0.76",
 "NO@0.92 PASABA@1.06 POR@1.32 ACÁ*@1.48",
 "HACE@2.16 CINCO*@2.32 AÑOS*@2.56",
 "EMPEZÓ@2.74 ESTE@3.06 CAMINO*@3.2",
 "SUMANDO@4.04 EXPERIENCIAS*@4.38",
 "APRENDIENDO@5.2 EN@5.54 CADA@5.66 OBRA*@5.76",
 "Y@6.12 TRATANDO@6.36 DE@6.66 MEJORAR@6.74 LOS@6.98 PROCESOS*@7.14",
 "DÍA@7.56 A@7.76 DÍA*@7.92",
 "HOY@8.64 LLEVAMOS@8.9 MÁS@9.28 DE@9.44 36!@9.56",
 "OBRAS*@9.94 REALIZADAS@10.32",
 "VIVIENDAS@11.3 REFORMAS@12.02 LOCALES@12.5",
 "PLANOS@13.3 ACCESOS@14.46",
 "Y@14.9 HASTA@15.34 UN@15.5 PARADOR*@15.66",
 "FRENTE@15.94 AL@16.12 MAR*@16.34",
 "HOY@16.44 EN@16.76 DÍA@16.88 EN@16.98 MONTE*@17.08 HERMOSO*@17.22",
 "Y@18.1 CADA@18.22 UNA@18.36 SE@18.6 EJECUTA@18.74",
 "MEJOR*@19.06 QUE@19.28 LA@19.36 ANTERIOR@19.44",
 "POR@20.04 ESO@20.48 HOY@20.6 QUIERO@20.72 VOLVER*@20.84",
 "A@21.0 ESTE@21.14 ESPACIO*@21.22",
 "PARA@22.02 MOSTRAR@22.12 NO@22.3 SOLO@22.44 EL@22.64 RESULTADO*@22.74",
 "SINO@23.16 TODO@23.44 EL@23.66 PROCESO*@23.82",
 "¿CÓMO@24.5 ORGANIZAMOS@24.66 UNA@25.06 OBRA?*@25.24",
 "¿QUÉ@25.76 DECISIONES*@25.82 TOMAMOS?@26.26",
 "¿QUÉ@26.84 SALIÓ@26.92 BIEN?*@27.18",
 "¿Y@27.42 QUÉ@27.62 HARÍAMOS@27.72 DISTINTO?*@27.98",
 "PORQUE@28.92 CREO@29.14 QUE@29.3 SE@29.4 APRENDE@29.5 MÁS@29.76",
 "COMPARTIENDO*@29.9",
 "QUE@30.44 TRABAJANDO@30.54 SOLO*@30.8",
 "ASÍ@31.64 QUE@31.84 SI@32.06 SOS@32.28 COLEGA*@32.42",
 "O@32.84 TE@33.08 GUSTA@33.18 LA@33.3 CONSTRUCCIÓN*@33.44",
 "SUMATE!@34.32",
 "LOS@34.86 LEO@34.94 EN@35.12 LOS@35.16 COMENTARIOS*@35.22",
 "BIENVENIDOS!@36.14",
]
chunks = []
for line in RAW:
    ws = []
    for tok in line.split():
        w, tt = tok.rsplit('@', 1)
        k = 'key' if w.endswith('*') else ('big' if w.endswith('!') else 'cap')
        ws.append((w.rstrip('*!'), float(tt) + VO - 0.03, k))
    chunks.append(ws)
spans = []
for i, ch in enumerate(chunks):
    st = ch[0][1] - 0.04; en = ch[-1][1] + 0.9
    if i + 1 < len(chunks): en = min(en, chunks[i + 1][0][1] - 0.04)
    spans.append((st, en))
def F(k): return fKey if k == 'key' else (fBig if k == 'big' else fCap)
YC = 1010
def layout(ws):
    SP = 20; MAXW = 920; lines = [[]]; lw = 0
    for w, t, k in ws:
        ww = F(k).getlength(w)
        if lines[-1] and lw + SP + ww > MAXW: lines.append([]); lw = 0
        lines[-1].append((w, t, k, ww)); lw += (SP if lw else 0) + ww
    LH = [max(112 if k == 'big' else (92 if k == 'key' else 72) for _, _, k, _ in ln) for ln in lines]
    y = YC - sum(LH) / 2; out = []
    for ln, lh in zip(lines, LH):
        y += lh; width = sum(x[3] for x in ln) + SP * (len(ln) - 1); x = (W - width) / 2
        for w, t, k, ww in ln: out.append((w, t, k, x, y - 10)); x += ww + SP
    return out
LAY = [layout(c) for c in chunks]

def back(u):
    u = min(max(u, 0.0), 1.0); c = 1.7; return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2

def subs(a, t):
    act = [(sp, lay) for sp, lay in zip(spans, LAY) if sp[0] <= t < sp[1]]
    if not act: return a
    (st, en), lay = act[0]
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    fo = 1 - ease((t - (en - 0.1)) / 0.1) if t > en - 0.1 else 1
    for w, tw, k, x, y in lay:
        p = (t - tw) / 0.16
        if p <= 0: continue
        al = ease(p) * fo; f = F(k); dy = (1 - ease(p)) * 24
        if k in ('key', 'big'):        # zoom leve en la palabra clave
            s = (1.18 - 0.18 * ease((t - tw) / 0.35)) if k == 'key' else max(0.3, 0.55 + 0.45 * back(p))
            tw_ = int(f.getlength(w)) + 60
            tmp = Image.new('RGBA', (tw_, 220), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((30, 170), w, font=f, fill=WHITE + (int(255 * al),), anchor='ls')
            tmp = tmp.resize((max(1, int(tmp.width * s)), max(1, int(tmp.height * s))), Image.BICUBIC)
            cx = x + f.getlength(w) / 2
            layer.alpha_composite(tmp, (int(cx - tmp.width / 2), int(y + dy - 170 * s)))
        else:
            ImageDraw.Draw(layer).text((x, y + dy), w, font=f, fill=WHITE + (int(255 * al),), anchor='ls')
    # degradé oscuro suave detrás (sin recuadro)
    g = (1 - 0.38 * fo * np.exp(-((yy - YC) / 230) ** 2))[..., None]
    a = (a.astype(np.float32) * g).astype(np.uint8)
    L = np.asarray(layer).astype(np.float32) / 255
    return np.clip(a * (1 - L[..., 3:]) + L[..., :3] * 255 * L[..., 3:], 0, 255).astype(np.uint8)

lw_ = LOGO.resize((66, int(66 * LOGO.height / LOGO.width)), Image.LANCZOS)
_m = Image.new('L', (W, H), 0); _m.paste(lw_, (W - 48 - 66, 46)); MARCA = np.asarray(_m).astype(np.float32) / 255
def marca(a, t):
    if t < 3.2 or t > T_REM - 0.2: return a
    al = 0.85 * min(1, (t - 3.2) / 0.5) * min(1, (T_REM - 0.2 - t) / 0.3)
    return comp(a, MARCA * al)

def remate(t):
    if 'rem' not in _cache:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '18.0', '-t', str(REM_D + 0.1), '-i', REPO + '/' + SRC['P'],
                              '-vf', 'crop=1080:1350:0:285', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        _cache['rem'] = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    R = _cache['rem']; return R[min(len(R) - 1, int((t - T_REM) * FPS))]

# ---------- render ----------
import os
N = int(round(float(os.environ.get('UNTIL', TOTAL)) * FPS))
tmpv = OUT + '.video.mp4'
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', tmpv],
                       stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS
    if t < CL[0][0] + 1.1:
        a = intro(t)
    elif t < T_REM:
        a = montage(t); a = marca(a, t)
        if t > T_REM - 0.4: a = (a.astype(np.float32) * max(0, (T_REM - t) / 0.4)).astype(np.uint8)
    else:
        a = remate(t)
    if t < T_REM: a = subs(a, t)
    enc.stdin.write(np.ascontiguousarray(a).tobytes())
    if n % 150 == 0: print(f'{t:.1f}s', flush=True)
enc.stdin.close(); enc.wait()
if os.environ.get('UNTIL'): sys.exit(0)

# ---------- audio: voz + música de fondo (baja debajo de la voz) ----------
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmpv, '-i', VOZ, '-i', MUS, '-filter_complex',
                f'[1:a]adelay={int(VO*1000)}|{int(VO*1000)},aformat=channel_layouts=stereo[v];'
                f"[2:a]volume='if(between(t,{VO-0.3},{VO+37.0}),0.16,0.55)':eval=frame[m];"
                '[v][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1.5[a]',
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
print('total', TOTAL)
