"""Historia adelanto del reel 'Explicando la cubierta' (viernes a la mañana)."""
import subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H, FPS = 1080, 1920, 30
FD = 'fonts/'
ARCH6 = FD + 'fontsource-archivo-5.3.0/package/files/archivo-latin-600-normal.woff2'
ITAL = FD + 'fontsource-italiana-5.3.0/package/files/italiana-latin-400-normal.woff2'
WHITE = (244, 242, 236); GREEN = np.array([0x36, 0x39, 0x32], np.float32)
SRC = 'historia-cubierta.mp4'; T0, T1 = 19.9, 30.0; CARD = 3.8
fLab = ImageFont.truetype(ARCH6, 38); fT = ImageFont.truetype(ITAL, 150); fS = ImageFont.truetype(ARCH6, 30)
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def tracked(d, cy, text, font, a, tr=8):
    ws = [font.getlength(c) for c in text]; x = (W - sum(ws) - tr * (len(text) - 1)) / 2
    for c, w in zip(text, ws):
        d.text((x, cy), c, font=font, fill=WHITE + (int(255 * a),), anchor='lm'); x += w + tr
# logo VA desde el remate (completo)
rem = np.asarray(Image.open('b/rem_3.png').convert('L'), np.float32)[690:990]
cols = np.where((rem > 110).any(0))[0]; m = rem[:, cols.min() - 12:cols.max() + 13]
al = np.clip((m - 60) / 180, 0, 1); ys, xs = np.where(al > 0.1); al = np.pad(al[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 6)
logo = Image.new('RGBA', (al.shape[1], al.shape[0]), WHITE + (0,)); logo.putalpha(Image.fromarray((al * 255).astype(np.uint8)))
logo = logo.resize((int(logo.width * 110 / logo.height), 110), Image.LANCZOS)
# fondo verde con viñeta
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vig = 1 - 0.45 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
bg = np.clip(GREEN[None, None] * vig[..., None], 0, 255)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', 'w/teaser_v.mp4'], stdin=subprocess.PIPE)
rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(T0), '-t', str(T1 - T0), '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
n1 = int((T1 - T0) * FPS); last = None
for i in range(n1):
    raw = rd.stdout.read(W * H * 3)
    if len(raw) == W * H * 3: last = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)
    f = last.copy()
    k = (i - (n1 - 9)) / 9  # fundido al verde
    if k > 0: f = f * (1 - k) + bg * k
    enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
for i in range(int(CARD * FPS)):
    t = i / FPS
    img = Image.fromarray(bg.astype(np.uint8)).convert('RGBA'); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    lay.alpha_composite(logo, ((W - logo.width) // 2, 330))
    tracked(d, 720 + (1 - ease(t / 0.4)) * 25, 'HOY · 18 H', fLab, ease(t / 0.4), 10)
    for j, ln in enumerate(['Cómo se arma', 'una cubierta']):
        p = ease((t - 0.2 - j * 0.15) / 0.6)
        if p > 0:
            tmp = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((W / 2, 200 + (1 - p) * 200), ln, font=fT, fill=WHITE + (255,), anchor='ms')
            lay.alpha_composite(tmp, (0, 900 + j * 165 - 200))
    tracked(d, 1250, 'NUEVO REEL EN EL PERFIL', fS, ease((t - 0.8) / 0.5), 6)
    img.alpha_composite(lay); enc.stdin.write(np.asarray(img.convert('RGB')).tobytes())
enc.stdin.close(); enc.wait()
dur = T1 - T0 + CARD
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'w/teaser_v.mp4', '-ss', str(T0), '-t', str(T1 - T0), '-i', SRC,
  '-filter_complex', f'[1:a]afade=t=out:st={T1-T0-0.6}:d=0.6,apad=whole_dur={dur}[a]', '-map', '0:v', '-map', '[a]',
  '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', 'historia-adelanto-cubierta.mp4'], check=True)
print('ok', dur)
