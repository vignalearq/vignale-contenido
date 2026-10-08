import numpy as np, subprocess
from PIL import Image, ImageDraw, ImageFont
FPS=30; W,H=1080,1350
O='/home/claude/out/'; RE=O+'reel/'; F='/home/claude/scratch/fonts/'
def load(p): return Image.open(p).convert('RGB').resize((W,H),Image.LANCZOS)
vacia=load(O+'foto00_ladrillo_vacia.png')
fotos={k:load(RE+k+'.png') for k in ['01_ladrillo','02_vidrio','03_hormigon','04_losa','05_madera','06_chapa','07_plano','08_encofrado','10_fachada']}
# cortes al beat (120 BPM -> 0.5 s)
seq=[(0.0,'VACIA'),(1.6,'01_ladrillo'),
     (2.0,'02_vidrio'),(2.5,'03_hormigon'),(3.0,'04_losa'),(3.5,'05_madera'),
     (4.0,'06_chapa'),(4.5,'07_plano'),(5.0,'08_encofrado'),(5.5,'01_ladrillo'),  # 5.5 = lugar de la arena
     (6.0,'10_fachada'),(8.0,'REMATE')]
tf=ImageFont.truetype(F+'CormorantGaramond%5Bwght%5D.ttf',46); tf.set_variation_by_axes([600])
itf=ImageFont.truetype(F+'CormorantGaramond-Italic%5Bwght%5D.ttf',50); itf.set_variation_by_axes([400])
VERDE=(0x36,0x39,0x32)
def texto(img,a):
    if a<=0: return img
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    t1='T U   P R Ó X I M A   O B R A'; t2='empieza con una idea.'
    al=int(255*a)
    w1=d.textlength(t1,font=tf); d.text(((W-w1)/2,1150-10*(1-a)),t1,font=tf,fill=VERDE+(al,))
    w2=d.textlength(t2,font=itf); d.text(((W-w2)/2,1215-10*(1-a)),t2,font=itf,fill=VERDE+(al,))
    return Image.alpha_composite(img.convert('RGBA'),lay).convert('RGB')
def punch(img,dt):
    s=1+0.035*max(0,1-dt/0.18)**2
    if s<=1.0005: return img
    w,h=int(W*s),int(H*s); im=img.resize((w,h),Image.BILINEAR); x,y=(w-W)//2,(h-H)//2
    return im.crop((x,y,x+W,y+H))
rem=subprocess.run(['ffmpeg','-v','error','-i','/home/claude/scratch/remate_45.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
rem=np.frombuffer(rem,np.uint8).reshape(-1,H,W,3)
TOT=8.0+len(rem)/FPS
p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
   '-i','/home/claude/reel_build/musica.wav','-c:v','libx264','-crf','17','-preset','slow','-pix_fmt','yuv420p',
   '-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','/home/claude/out/reel_hoja_borrador.mp4'],stdin=subprocess.PIPE)
for i in range(int(TOT*FPS)):
    t=i/FPS
    st,k=[s for s in seq if s[0]<=t+1e-6][-1]
    if k=='REMATE':
        fr=Image.fromarray(rem[min(len(rem)-1,i-int(8.0*FPS))])
    else:
        img=vacia if k=='VACIA' else fotos[k]
        fr=img if st<2.0 else punch(img,t-st)
        if k=='10_fachada': fr=texto(fr,min(1,max(0,(t-6.5)/0.5)))
        if 2.0<=st and t-st<0.05: fr=Image.blend(fr,Image.new('RGB',(W,H),'white'),0.35 if st==2.0 else 0.0)
    p.stdin.write(np.asarray(fr,np.uint8).tobytes())
p.stdin.close(); p.wait(); print('ok',TOT)
