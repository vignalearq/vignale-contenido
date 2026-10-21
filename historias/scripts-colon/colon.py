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

# título con la letra del logo: gruesa, itálica, blanco/celeste con borde negro
def title_img():
    f1 = ImageFont.truetype(BLACK, 128)
    f2 = ImageFont.truetype(BLACK, 92)
    img = Image.new('RGBA', (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((W / 2, 120), 'COLON', font=f1, fill=(255, 255, 255), anchor='ms', stroke_width=9, stroke_fill=(0, 0, 0))
    d.text((W / 2, 245), 'CAR WASH', font=f2, fill=CELESTE, anchor='ms', stroke_width=8, stroke_fill=(0, 0, 0))
    return img
TITLE = title_img()

# ---------- clips ----------
def load_clip(spec, dur):
    path, _, ss = spec.partition('@')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', ss or '0.3', '-i', path, '-t', str(dur + 0.4), '-vf',
        f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=saturation=0.75:contrast=1.03',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)

CD = 1.45
clips = [load_clip(c, CD) for c in CLIPS]

grad = np.zeros((H, W, 4), np.uint8)
ys = np.arange(H)[:, None]
grad[..., 3] = np.broadcast_to(np.clip((ys - 1250) / 550, 0, 1) ** 1.2 * 190, (H, W)).astype(np.uint8)
grad[..., :3] = (20, 22, 19)
shade = Image.fromarray(grad, 'RGBA')
small_title = TITLE.resize((W // 2, 150), Image.LANCZOS)

# ---------- línea de tiempo ----------
S1 = 3.2                    # intro: mano de obra para viviendas y comercios
S2 = S1 + 3.4               # trabajo realizado + logo
S3 = S2 + CD * len(clips)   # montaje de clips
S4 = S3 + 3.1               # ¿necesitás mano de obra...?
S5 = S4 + 2.9               # viviendas y comercios · contactanos
XF = 0.3

def green(t, t0, t1, label, lines, top=795, va=True):
    img = empty.copy()
    out = 1 - ease((t - (t1 - 0.4)) / 0.4)
    if va:
        img = with_va(img, ease((t - t0) / 0.6) * out)
    img = img.convert('RGBA')
    text_block(img, label, lines, top, t, t0 + 0.35, out)
    return img.convert('RGB')

def seg_logo(t):
    t0 = S1
    out = 1 - ease((t - (S2 - 0.4)) / 0.4)
    img = empty.copy().convert('RGBA')
    pl = ease((t - t0 - 0.1) / 0.45)
    tmp = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
    tracked(tmp, 'TRABAJO REALIZADO', fA, 40, pl * out)
    img.alpha_composite(tmp, (0, int(470 + (1 - pl) * 25)))
    p = ease((t - t0 - 0.25) / 0.7)
    s = 0.92 + 0.08 * p
    lg = logo_rgba.resize((int(logo_rgba.width * s), int(logo_rgba.height * s)), Image.LANCZOS)
    a = lg.getchannel('A').point(lambda v: int(v * p * out))
    lg.putalpha(a)
    img.alpha_composite(lg, ((W - lg.width) // 2, int(620 + (LW * 0.84 - lg.height) / 2)))
    pt = ease((t - t0 - 0.7) / 0.6)
    tt = TITLE.copy()
    tt.putalpha(tt.getchannel('A').point(lambda v: int(v * pt * out)))
    img.alpha_composite(tt, (0, int(1360 + (1 - pt) * 40)))
    return img.convert('RGB')

def seg_clips(t):
    k = t - S2 + XF
    i = min(int(k // CD), len(clips) - 1)
    fr = clips[i]
    n = min(int((k - i * CD) * FPS), len(fr) - 1)
    img = Image.fromarray(fr[n]).convert('RGBA')
    # flash suave entre cortes
    dk = k - i * CD
    if i > 0 and dk < 0.12:
        img = Image.blend(img, Image.new('RGBA', (W, H), (255, 250, 240, 255)), 0.35 * (1 - dk / 0.12))
    img.alpha_composite(shade)
    img.alpha_composite(small_title, (W // 4, 1560))
    tmp = Image.new('RGBA', (W, 80), (0, 0, 0, 0))
    tracked(tmp, 'TRABAJO REALIZADO', fA, 40, 1.0)
    img.alpha_composite(tmp, (0, 1490))
    return img.convert('RGB')

def render(t):
    segs = [
        (0, S1, lambda t: green(t, 0, S1, 'MANO DE OBRA PARA', ['viviendas', 'y comercios.'])),
        (S1, S2, seg_logo),
        (S2, S3, seg_clips),
        (S3, S4, lambda t: green(t, S3, S4, '¿NECESITÁS MANO DE OBRA PARA', ['reformar tu casa', 'o tu local?'])),
        (S4, S5, lambda t: green(t, S4, S5, 'NO DUDES EN', ['contactarnos.'])),
    ]
    for j, (a, b, fn) in enumerate(segs):
        if t < b - XF or j == len(segs) - 1:
            if t < b - XF:
                return fn(t)
            return Image.blend(fn(t), empty, ease((t - (b - XF)) / XF))
        if t < b:
            return Image.blend(fn(t), segs[j + 1][2](t), ease((t - (b - XF)) / XF))
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
