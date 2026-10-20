"""Historia 'Proyecto y dirección de obra' — mismo formato que historia-reforma-bano.mp4.
Uso: python3 build.py FOTO BANO_MP4 OUT_MP4 [CLIP_MOV]
Sin CLIP_MOV, el tramo 3 usa un acercamiento a los renders de la foto (borrador).
"""
import sys, subprocess, math
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter, ImageEnhance

PLAN_A, PLAN_B, BANO, OUT = sys.argv[1:5]
CLIP = None
HERE = sys.path[0]
FD = HERE + '/../fonts/'
ITAL = FD + 'fontsource-italiana-5.3.0/package/files/italiana-latin-400-normal.woff2'
ARCH = FD + 'fontsource-archivo-5.3.0/package/files/archivo-latin-600-normal.woff2'
W, H, FPS = 1080, 1920, 30
fI = ImageFont.truetype(ITAL, 173)
fA = ImageFont.truetype(ARCH, 34)
WHITE = (240, 238, 232)

# ---------- fondos ----------
def frame_at(t):
    import io
    png = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', BANO, '-frames:v', '1',
                          '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGB')

empty = frame_at(9.65)
intro_ref = frame_at(2.0)
logo_band = intro_ref.crop((0, 280, W, 500))           # VA sobre el mismo fondo
logo_mask = Image.new('L', (W, 220), 0)
ImageDraw.Draw(logo_mask).rectangle((380, 20, 700, 200), fill=255)
logo_mask = logo_mask.filter(ImageFilter.GaussianBlur(12))

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3

def tracked(draw_img, text, font, cy, alpha, track=7.5):
    """texto en mayúsculas espaciadas, centrado en cy"""
    widths = [font.getlength(c) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = (W - total) / 2
    d = ImageDraw.Draw(draw_img)
    for c, w in zip(text, widths):
        d.text((x, cy), c, font=font, fill=WHITE + (int(255 * alpha),), anchor='lm')
        x += w + track

def rising_line(layer, text, font, baseline, p, alpha=1.0):
    """línea que sube desde abajo dentro de una máscara (como en la del baño)"""
    if p <= 0:
        return
    tmp = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    if font.getlength(text) > 940:
        font = ImageFont.truetype(ITAL, int(173 * 940 / font.getlength(text)))
    off = (1 - ease(p)) * 200
    ImageDraw.Draw(tmp).text((W / 2, 200 + off), text, font=font, fill=WHITE + (int(255 * alpha),), anchor='ms')
    layer.alpha_composite(tmp, (0, int(baseline - 200)))

def text_block(layer, label, lines, top_label, t, t0, alpha=1.0):
    pl = ease((t - t0) / 0.45)
    if pl > 0:
        tmp = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
        tracked(tmp, label, fA, 40, alpha * pl)
        layer.alpha_composite(tmp, (0, int(top_label - 40 + (1 - pl) * 25)))
    for i, ln in enumerate(lines):
        rising_line(layer, ln, fI, top_label + 150 + i * 170, (t - t0 - 0.12 - i * 0.14) / 0.6, alpha)

# ---------- planos (invertidos: líneas claras sobre el verde del estudio) ----------
BAND = (75, 650, 4875, 2350)          # solo el dibujo: sin carátula ni dirección
def load_plan(path):
    im = Image.open(path).convert('L').crop(BAND)
    return im
planA, planB = load_plan(PLAN_A), load_plan(PLAN_B)
PW, PH = planA.size
bg_np = np.asarray(empty, np.float32)
LINE = np.array([236, 232, 222], np.float32)

def plan_frame(plan, box):
    g = plan.transform((W, H), Image.EXTENT, box, Image.BICUBIC)
    ink = 1 - np.asarray(g, np.float32)[..., None] / 255.0       # 1 donde hay línea
    ink = np.clip(ink * 1.25, 0, 1) * 0.88
    out = bg_np * (1 - ink) + LINE * ink
    return Image.fromarray(out.astype(np.uint8))

grad = np.zeros((H, W, 4), np.uint8)
ys = np.arange(H)[:, None]
a = np.clip((ys - 950) / 500, 0, 1) ** 1.2 * 200
grad[..., 3] = np.broadcast_to(a, (H, W)).astype(np.uint8)
grad[..., :3] = (24, 26, 23)
shade = Image.fromarray(grad, 'RGBA')

def foto_pan(p):
    """plano de arquitectura recorrido de izquierda a derecha"""
    ch = PH * 0.92
    cw = ch * 9 / 16
    cx = cw / 2 + (PW - cw) * p
    cy = PH / 2
    return plan_frame(planA, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def foto_zoom(p):
    """plano de gas: acercamiento lento sobre la cocina/baño"""
    cx, cy = PW * 0.47, PH * 0.45
    ch = PH * (1.0 - 0.28 * p)
    cw = ch * 9 / 16
    return plan_frame(planB, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

clip_frames = None
if CLIP:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', CLIP, '-t', '3.2', '-vf',
        'zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,'
        f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=saturation=0.35:brightness=-0.03',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
    if raw.returncode != 0:   # sin HDR: conversión simple
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', CLIP, '-t', '3.2', '-vf',
            f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=saturation=0.35:brightness=-0.03',
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True)
    buf = np.frombuffer(raw.stdout, np.uint8)
    clip_frames = buf.reshape(-1, H, W, 3)

# ---------- línea de tiempo ----------
T1, T2, T3 = 3.0, 7.2, 10.2       # intro | foto | clip | (cierre del baño)
XF = 0.3                          # fundido entre tramos

def intro(t):
    img = empty.copy().convert('RGBA')
    la = ease(t / 0.6) * (1 - ease((t - (T1 - 0.4)) / 0.4))
    band = Image.composite(logo_band, empty.crop((0, 280, W, 500)), logo_mask.point(lambda v: int(v * la)))
    img.paste(band, (0, 280))
    out = 1 - ease((t - (T1 - 0.4)) / 0.4)
    text_block(img, '¿NECESITÁS', ['actualizar', 'tus planos?'], 795, t, 0.45, out)
    return img.convert('RGB')

def seg_foto(t):
    p = (t - T1 + XF) / (T2 - T1 + XF)
    img = foto_pan(p).convert('RGBA')
    img.alpha_composite(shade)
    out = 1 - ease((t - (T2 - 0.35)) / 0.35)
    text_block(img, '¿TENÉS QUE PRESENTAR TU CASA', ['para un crédito?'], 1150, t, T1 + 0.2, out)
    return img.convert('RGB')

def seg_clip(t):
    i = int((t - T2 + XF) * FPS)
    if clip_frames is not None:
        img = Image.fromarray(clip_frames[min(i, len(clip_frames) - 1)]).convert('RGBA')
    else:
        img = foto_zoom((t - T2 + XF) / (T3 - T2 + XF)).convert('RGBA')
    img.alpha_composite(shade)
    out = 1 - ease((t - (T3 - 0.35)) / 0.35)
    text_block(img, 'NOS OCUPAMOS DE', ['todo el trámite.'], 1150, t, T2 + 0.15, out)
    return img.convert('RGB')

def render(t):
    if t < T1 - XF:
        return intro(t)
    if t < T1:
        k = ease((t - (T1 - XF)) / XF)
        return Image.blend(intro(t), seg_foto(t), k)
    if t < T2 - XF:
        return seg_foto(t)
    if t < T2:
        k = ease((t - (T2 - XF)) / XF)
        return Image.blend(seg_foto(t), seg_clip(t), k)
    if t < T3 - XF:
        return seg_clip(t)
    k = ease((t - (T3 - XF)) / XF)
    return Image.blend(seg_clip(t), empty, k)

body = OUT + '.body.mp4'
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
    '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', body], stdin=subprocess.PIPE)
for n in range(int(T3 * FPS)):
    enc.stdin.write(render(n / FPS).tobytes())
enc.stdin.close(); enc.wait()

# cierre idéntico al de la historia del baño (desde 9,6 s) + audio mudo
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', body, '-ss', '9.6', '-i', BANO,
    '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
    '-filter_complex', '[0:v]setsar=1[a];[1:v]fps=30,setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]',
    '-map', '[v]', '-map', '2:a', '-shortest', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', OUT], check=True)
print('ok', OUT)
