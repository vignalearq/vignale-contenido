"""Historia 'Trabajo realizado · Colón Car Wash' (mano de obra para viviendas y comercios).
Uso: python3 colon.py LOGO BANO_MP4 OUT_MP4 CLIP1 CLIP2 ...
"""
import sys, subprocess, io
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter

LOGO, BANO, OUT = sys.argv[1:4]
CLIPS = sys.argv[4:]
HERE = sys.path[0]
FD = HERE + '/../fonts/fontsource-'
ITAL = FD + 'italiana-5.3.0/package/files/italiana-latin-400-normal.woff2'
ARCH = FD + 'archivo-5.3.0/package/files/archivo-latin-600-normal.woff2'
BLACK = FD + 'archivo-5.3.0/package/files/archivo-latin-900-italic.woff2'
W, H, FPS = 1080, 1920, 30
fI = ImageFont.truetype(ITAL, 173)
fA = ImageFont.truetype(ARCH, 34)
WHITE = (240, 238, 232)
CELESTE = (14, 171, 235)

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3

def frame_at(t):
    png = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', BANO, '-frames:v', '1',
                          '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGB')

empty = frame_at(9.65)
intro_ref = frame_at(2.0)
logo_band = intro_ref.crop((0, 280, W, 500))
logo_mask = Image.new('L', (W, 220), 0)
ImageDraw.Draw(logo_mask).rectangle((380, 20, 700, 200), fill=255)
logo_mask = logo_mask.filter(ImageFilter.GaussianBlur(12))

def with_va(img, a):
    band = Image.composite(logo_band, img.crop((0, 280, W, 500)), logo_mask.point(lambda v: int(v * a)))
    img.paste(band, (0, 280))
    return img

def tracked(img, text, font, cy, alpha, track=7.5):
    widths = [font.getlength(c) for c in text]
    x = (W - (sum(widths) + track * (len(text) - 1))) / 2
    d = ImageDraw.Draw(img)
    for c, w in zip(text, widths):
        d.text((x, cy), c, font=font, fill=WHITE + (int(255 * alpha),), anchor='lm')
        x += w + track

def rising_line(layer, text, baseline, p, alpha=1.0):
    if p <= 0:
        return
    font = fI
    if font.getlength(text) > 940:
        font = ImageFont.truetype(ITAL, int(173 * 940 / font.getlength(text)))
    tmp = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((W / 2, 200 + (1 - ease(p)) * 200), text, font=font,
                             fill=WHITE + (int(255 * alpha),), anchor='ms')
    layer.alpha_composite(tmp, (0, int(baseline - 200)))

def text_block(layer, label, lines, top, t, t0, alpha=1.0):
    pl = ease((t - t0) / 0.45)
    if pl > 0:
        tmp = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
        tracked(tmp, label, fA, 40, alpha * pl)
        layer.alpha_composite(tmp, (0, int(top - 40 + (1 - pl) * 25)))
    for i, ln in enumerate(lines):
        rising_line(layer, ln, top + 150 + i * 170, (t - t0 - 0.12 - i * 0.14) / 0.6, alpha)

# ---------- logo del lavadero (fondo blanco → transparente) ----------
logo = Image.open(LOGO).convert('RGB')
la = np.asarray(logo).astype(int)
near_white = (la.min(axis=2) > 225).astype(np.uint8) * 255
mask_img = Image.fromarray(near_white, 'L').copy()
# relleno desde las esquinas: solo el blanco de afuera se vuelve transparente
ImageDraw.floodfill(mask_img, (2, 2), 128)
for xy in ((logo.width - 3, 2), (2, logo.height - 3), (logo.width - 3, logo.height - 3)):
    ImageDraw.floodfill(mask_img, xy, 128)
outside = np.asarray(mask_img) == 128
alpha = np.where(outside, 0, 255).astype(np.uint8)
logo_rgba = logo.convert('RGBA')
logo_rgba.putalpha(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2)))
logo_rgba = logo_rgba.crop(logo_rgba.getbbox())
LW = 860
logo_rgba = logo_rgba.resize((LW, int(logo_rgba.height * LW / logo_rgba.width)), Image.LANCZOS)


# ---------- palabras grandes: itálica más inclinada, sin borde ----------
def word_img(text, size, color):
    f = ImageFont.truetype(BLACK, size)
    l, t_, r, b = f.getbbox(text)
    pad = 60
    im = Image.new('RGBA', (r - l + pad * 2 + 120, b - t_ + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t_), text, font=f, fill=color + (255,))
    sh = 0.22   # inclinación extra
    im = im.transform(im.size, Image.AFFINE, (1, sh, -sh * im.height * 0.5, 0, 1, 0), Image.BICUBIC)
    im = im.crop(im.getbbox())
    if im.width > 990:
        im = im.resize((990, int(im.height * 990 / im.width)), Image.LANCZOS)
    return im
WORDS = [word_img('COLON', 330, (255, 255, 255)), word_img('CAR', 330, CELESTE), word_img('WASH', 330, CELESTE)]
RIGHT = W - 50
YS = [430, 790, 1150]

def smoke(im, k):
    """k 0→1: se deshace en humo (blur, sube, se agranda, se apaga)"""
    if k <= 0:
        return im, 0, 1.0
    r = 2 + 38 * k
    g = im.filter(ImageFilter.GaussianBlur(r))
    s_ = 1 + 0.12 * k
    g = g.resize((int(g.width * s_), int(g.height * s_)), Image.BILINEAR)
    return g, -int(120 * k), (1 - k) ** 1.6

def appear(im, p):
    """p 0→1: entra desde el humo y se acomoda contra la derecha"""
    r = 30 * (1 - p)
    g = im.filter(ImageFilter.GaussianBlur(r)) if r > 0.5 else im
    return g, int(140 * (1 - p)), p

def clip_frame(i, k):
    fr = clips[i]
    n = min(int(k * FPS), len(fr) - 1)
    return Image.fromarray(fr[n])

# ---------- clips ----------
def load_clip(spec, dur):
    path, _, ss = spec.partition('@')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', ss or '0.3', '-i', path, '-t', str(dur + 0.4), '-vf',
        f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=saturation=0.75:contrast=1.03',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)

BIG = CLIPS[0]           # clip de fondo para las palabras grandes
REST = CLIPS[1:]
S1 = 2.0                 # intro
S2 = S1 + 1.5            # trabajo realizado + logo
S3 = S2 + 2.6            # COLON CAR WASH gigante
CD = 0.9
S4 = S3 + CD * len(REST)
S5 = S4 + 2.1            # ¿necesitás...? contactanos
XF = 0.25
big_clip = load_clip(BIG, S3 - S2 + 0.5)
clips = [load_clip(c, CD) for c in REST]

grad = np.zeros((H, W, 4), np.uint8)
ys = np.arange(H)[:, None]
grad[..., 3] = np.broadcast_to(np.clip((ys - 1300) / 500, 0, 1) ** 1.2 * 170, (H, W)).astype(np.uint8)
grad[..., :3] = (20, 22, 19)
shade = Image.fromarray(grad, 'RGBA')
dark = Image.new('RGBA', (W, H), (16, 18, 15, 95))

def green(t, t0, t1, label, lines, top=795):
    img = empty.copy()
    out = 1 - ease((t - (t1 - 0.35)) / 0.35)
    img = with_va(img, ease((t - t0) / 0.5) * out).convert('RGBA')
    text_block(img, label, lines, top, t, t0 + 0.2, out)
    return img.convert('RGB')

def seg_logo(t):
    t0 = S1
    out = 1 - ease((t - (S2 - 0.3)) / 0.3)
    img = empty.copy().convert('RGBA')
    pl = ease((t - t0) / 0.4)
    tmp = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
    tracked(tmp, 'TRABAJO REALIZADO', fA, 40, pl * out)
    img.alpha_composite(tmp, (0, int(560 + (1 - pl) * 25)))
    p = ease((t - t0 - 0.1) / 0.5)
    s_ = 0.92 + 0.08 * p
    lg = logo_rgba.resize((int(logo_rgba.width * s_), int(logo_rgba.height * s_)), Image.LANCZOS)
    lg.putalpha(lg.getchannel('A').point(lambda v: int(v * p * out)))
    img.alpha_composite(lg, ((W - lg.width) // 2, int(700 + (LW * 0.84 - lg.height) / 2)))
    return img.convert('RGB')

def seg_big(t):
    k = t - S2 + XF
    img = Image.fromarray(big_clip[min(int(k * FPS), len(big_clip) - 1)]).convert('RGBA')
    img.alpha_composite(dark)
    starts = [0.15, 0.55, 0.95]          # una palabra por vez (más lento)
    t_smoke = 1.75                        # cuando ya están las tres, humo
    for w_, y, st in zip(WORDS, YS, starts):
        p = ease((k - st) / 0.55)
        if p <= 0:
            continue
        g, dx, a = appear(w_, p)
        sk = min(max((k - t_smoke - (st - 0.15) * 0.4) / 0.75, 0), 1)
        dy = 0
        if sk > 0:
            g, dy, a2 = smoke(w_, sk)
            dx, a = 0, a2
        g = g.copy()
        g.putalpha(g.getchannel('A').point(lambda v: int(v * a)))
        img.alpha_composite(g, (RIGHT - g.width + dx, y - g.height // 2 + dy))
    return img.convert('RGB')

def seg_clips(t):
    k = t - S3 + XF
    i = min(int(k // CD), len(clips) - 1)
    img = clip_frame(i, k - i * CD).convert('RGBA')
    dk = k - i * CD
    if i > 0 and dk < 0.1:
        img = Image.blend(img, Image.new('RGBA', (W, H), (255, 250, 240, 255)), 0.3 * (1 - dk / 0.1))
    img.alpha_composite(shade)
    tmp = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
    tracked(tmp, 'TRABAJO REALIZADO · COLON CAR WASH', fA, 40, 1.0, track=5)
    img.alpha_composite(tmp, (0, 1580))
    return img.convert('RGB')

def render(t):
    segs = [
        (S1, lambda t: green(t, 0, S1, 'MANO DE OBRA PARA', ['viviendas', 'y comercios.'])),
        (S2, seg_logo),
        (S3, seg_big),
        (S4, seg_clips),
        (S5, lambda t: green(t, S4, S5, '¿NECESITÁS MANO DE OBRA? ESCRIBINOS', ['reformamos tu', 'casa o local.'])),
    ]
    for j, (b, fn) in enumerate(segs):
        if t < b - XF:
            return fn(t)
        if t < b:
            nxt = segs[j + 1][1] if j + 1 < len(segs) else (lambda t: empty)
            return Image.blend(fn(t), nxt(t), ease((t - (b - XF)) / XF))
    return empty

body = OUT + '.body.mp4'
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
    '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', '-pix_fmt', 'yuv420p', body], stdin=subprocess.PIPE)
for n in range(int(S5 * FPS)):
    enc.stdin.write(render(n / FPS).tobytes())
enc.stdin.close(); enc.wait()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', body, '-ss', '9.6', '-i', BANO,
    '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
    '-filter_complex', '[0:v]setsar=1[a];[1:v]fps=30,setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]',
    '-map', '[v]', '-map', '2:a', '-shortest', '-c:v', 'libx264', '-crf', '19', '-preset', 'medium',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', OUT], check=True)
print('ok', OUT, S5 + 4.4)
