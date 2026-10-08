import numpy as np, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FPS=30; W,H=1080,1350
O='/home/claude/out/'; RE=O+'reel/'; F='/home/claude/scratch/fonts/'
rng=np.random.default_rng(3)
def load(p): return Image.open(p).convert('RGB').resize((W,H),Image.LANCZOS)
vacia=load(O+'foto00_ladrillo_vacia.png')
fotos={k:load(RE+k+'.png') for k in ['01_ladrillo','02_vidrio','03_hormigon','04_losa','05_madera','06_chapa','07_plano','08_encofrado','10_fachada']}
# hoja (sprite) recortada de la foto 01
SW=int(W*0.54); SH=int(SW*1.4142); SX=(W-SW)//2; SY=(H-SH)//2-10
sprite=fotos['01_ladrillo'].crop((SX,SY,SX+SW,SY+SH))
seq=[(2.0,'01_ladrillo'),(2.5,'02_vidrio'),(3.0,'03_hormigon'),(3.5,'04_losa'),(4.0,'05_madera'),
     (4.5,'06_chapa'),(5.0,'07_plano'),(5.5,'08_encofrado'),(6.0,'10_fachada'),(8.0,'REMATE')]
tf=ImageFont.truetype(F+'CormorantGaramond%5Bwght%5D.ttf',46); tf.set_variation_by_axes([600])
itf=ImageFont.truetype(F+'CormorantGaramond-Italic%5Bwght%5D.ttf',50); itf.set_variation_by_axes([400])
VERDE=(0x36,0x39,0x32)
def texto(img,a):
    if a<=0: return img
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay); al=int(255*a)
    for txt,fn,y in (('T U   P R Ó X I M A   O B R A',tf,1150),('empieza con una idea.',itf,1215)):
        w=d.textlength(txt,font=fn); d.text(((W-w)/2,y-10*(1-a)),txt,font=fn,fill=VERDE+(al,))
    return Image.alpha_composite(img.convert('RGBA'),lay).convert('RGB')
# cámara en mano: ruido suave
NT=int(12*FPS)
def smooth(n,s):
    x=rng.normal(0,1,n+200); k=np.exp(-np.linspace(-3,3,61)**2); x=np.convolve(x,k/k.sum(),'same')[100:100+n]
    return x/np.abs(x).max()*s
hx,hy,hr=smooth(NT,5),smooth(NT,5),smooth(NT,0.25)
def camara(img,i,extra=(0,0,0),zoom=1.0):
    dx,dy,dr=hx[i]+extra[0],hy[i]+extra[1],hr[i]+extra[2]
    s=1.025*zoom
    im=img.rotate(dr,resample=Image.BICUBIC,center=(W/2,H/2))
    w,h=int(W*s),int(H*s); im=im.resize((w,h),Image.BILINEAR)
    x=(w-W)//2-int(dx); y=(h-H)//2-int(dy); return im.crop((x,y,x+W,y+H))
yy,xx=np.mgrid[:H,:W]; vig=1-0.22*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
def acabado(fr,photo=True):
    a=np.asarray(fr).astype(np.float32)
    if photo: a*=vig[...,None]
    a+=rng.normal(0,3.2,(H,W))[...,None]
    return np.clip(a,0,255).astype(np.uint8)
def hoja_volando(t):
    # 0.9 -> 2.0 s, entra desde arriba a la derecha, acelera y se estampa
    T0,T1=0.9,2.0
    if t<T0: return vacia
    u=min(1,(t-T0)/(T1-T0)); e=u**2.2
    out=vacia.copy()
    for sub in range(5):   # motion blur por subcuadros
        uu=min(1,u+(sub-2)*0.012/(T1-T0)); ee=max(0,uu)**2.2
        sc=1.45-0.45*ee; ang=-28*(1-ee); cx=SX+SW/2+380*(1-ee); cy=SY+SH/2-520*(1-ee)
        sp=sprite.resize((int(SW*sc),int(SH*sc)),Image.BILINEAR).convert('RGBA').rotate(ang,expand=True,resample=Image.BICUBIC)
        # sombra: más lejos y difusa cuanto más separada de la pared
        sh=Image.new('L',sp.size,0); sh.paste(sp.split()[3])
        off=int(10+90*(1-ee)); blur=6+30*(1-ee); op=0.5*(0.4+0.6*ee)
        sh=sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v,o=op:int(v*o))
        lay=out.copy()
        lay.paste((0,0,0),(int(cx-sp.width/2+off*0.6),int(cy-sp.height/2+off)),sh)
        lay.paste(sp,(int(cx-sp.width/2),int(cy-sp.height/2)),sp)
        out=lay if sub==0 else Image.blend(out,lay,1/(sub+1))
    return out
rem=subprocess.run(['ffmpeg','-v','error','-i','/home/claude/scratch/remate_45.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
rem=np.frombuffer(rem,np.uint8).reshape(-1,H,W,3)
TOT=8.0+len(rem)/FPS
p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
   '-i','/home/claude/reel_build/musica.wav','-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p',
   '-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','/home/claude/out/reel_hoja_v2.mp4'],stdin=subprocess.PIPE)
for i in range(int(TOT*FPS)):
    t=i/FPS
    if t<2.0:
        fr=acabado(camara(hoja_volando(t),i))
    elif t>=8.0:
        fr=rem[min(len(rem)-1,i-int(8.0*FPS))]
    else:
        st,k=[s for s in seq if s[0]<=t+1e-6][-1]; dt=t-st
        img=fotos[k]
        if k=='10_fachada': img=texto(img,min(1,max(0,(t-6.5)/0.5)))
        # golpe de cámara al estamparse (2.0) y micro-punch en cada corte
        sk=np.exp(-(t-2.0)*9) if t<2.6 else 0
        ex=(sk*14*np.sin((t-2.0)*55),sk*18*np.cos((t-2.0)*47),sk*0.6*np.sin((t-2.0)*40))
        z=1+0.03*max(0,1-dt/0.16)**2 if st>2.0 else 1
        fr=acabado(camara(img,i,ex,z))
    p.stdin.write(np.ascontiguousarray(fr).tobytes())
p.stdin.close(); p.wait(); print('ok')
