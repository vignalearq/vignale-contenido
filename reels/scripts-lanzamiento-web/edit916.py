import numpy as np, subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FPS=30; W,H=1080,1920
L='/home/claude/lanz2/'; FA=L+'fonts/Archivo[wdth,wght].ttf'; FI=L+'fonts/Italiana-Regular.ttf'
VERDE=(0x36,0x39,0x32); BLANCO=(242,241,236)
BPM=122.0; b=60/BPM; BAR=4*b
def font(sz,wght=900,wdth=125):
    f=ImageFont.truetype(FA,int(sz)); f.set_variation_by_axes([wght,wdth]); return f
def ease(u): u=min(1,max(0,u)); return u*u*(3-2*u)
def eout(u,p=3): u=min(1,max(0,u)); return 1-(1-u)**p
# ---------- clips (1080x1920 -> 4:5) ----------
YOFF={'v5517':330,'v7779':420,'v9112':300,'v5407':330,'v7276':400,'v6193':300}
cache={}
def seg(c,s,d):
    k=(c,round(s,3),round(d,3))
    if k not in cache:
        while len(cache)>=5: cache.pop(next(iter(cache)))
        y=YOFF.get(c,285)
        raw=subprocess.run(['ffmpeg','-v','error','-ss',str(s),'-i',L+'src/'+c+'.mp4','-t',str(d+0.15),
            '-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
        cache[k]=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3)
    return cache[k]
def clip(c,s,d,dt,speed=1.0):
    a=seg(c,s,d*speed+0.1); return a[min(len(a)-1,max(0,int(dt*speed*FPS)))]
def zoom(a,s,cx=W/2,cy=H/2,dx=0,dy=0):
    if abs(s-1)<1e-4 and dx==0 and dy==0: return a
    im=Image.fromarray(a); w,h=W/s,H/s; x0,y0=cx-w*cx/W-dx/s,cy-h*cy/H-dy/s
    return np.asarray(im.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+w,y0+h)))
def blur(a,r):
    if r<0.3: return a
    return np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(float(r))))
def mix(a,b2,u): return (a.astype(np.float32)*(1-u)+b2.astype(np.float32)*u).astype(np.uint8)
def green(): return np.full((H,W,3),VERDE,np.uint8)
yy,xx=np.mgrid[:H,:W].astype(np.float32)
def leak(a,amt,cx=0.8,cy=0.25):
    if amt<=0: return a
    g=np.exp(-(((xx/W-cx)/0.55)**2+((yy/H-cy)/0.6)**2))*amt
    col=np.array([255,176,92],np.float32)
    out=a.astype(np.float32); out=out+(255-out)*0+col*g[...,None]*0.9
    return np.clip(out,0,255).astype(np.uint8)
# transición suave entre dos fuentes: blur-dissolve + zoom
def blend_tr(A,B,u,kind='blur'):
    u=ease(u)
    if kind=='blur':
        r=12*np.sin(np.pi*u); return mix(blur(A,r),blur(B,r),u)
    if kind=='zoom':
        za=zoom(A,1+0.18*u); zb=zoom(B,1.18-0.18*u); r=8*np.sin(np.pi*u)
        return mix(blur(za,r),blur(zb,r),u)
    if kind=='push':   # deslizamiento vertical con inercia
        off=int(H*u); out=np.empty_like(A)
        out[:H-off]=A[off:]; out[H-off:]=B[:off]
        r=10*np.sin(np.pi*u); return blur(out,r) if r>0.5 else out
    if kind=='leak':
        m=mix(A,B,u); return leak(m,0.9*np.sin(np.pi*u))
    return mix(A,B,u)
# ---------- textos ----------
_d=ImageDraw.Draw(Image.new('L',(1,1)))
def fit(text,maxw,wght=900,wdth=125,mx=600):
    lo,hi=10,mx
    while hi-lo>2:
        m=(lo+hi)//2
        if _d.textlength(text,font=font(m,wght,wdth))>maxw: hi=m
        else: lo=m
    return lo
def word(a,text,t,tin,tout=None,y=None,maxw=960,sz=None,dark=0.78):
    """palabra ancha: entra con desenfoque + tracking que se cierra; sale con fade"""
    if t<tin: return a
    u=eout((t-tin)/0.35); v=1.0
    if tout is not None and t>tout-0.2: v=max(0,(tout-t)/0.2)
    al=u*v
    if al<=0: return a
    sz=sz or fit(text,maxw); f=font(sz)
    sp=int((1-u)*sz*0.18)   # tracking
    widths=[_d.textlength(ch,font=f) for ch in text]; tw=sum(widths)+sp*(len(text)-1)
    bb=_d.textbbox((0,0),text,font=f); th=bb[3]-bb[1]
    y0=(H-th)/2 if y is None else y; y0+=18*(1-u)
    lay=Image.new('L',(W,H),0); d=ImageDraw.Draw(lay); x=(W-tw)/2
    for ch,w in zip(text,widths): d.text((x,y0-bb[1]),ch,font=f,fill=255); x+=w+sp
    if u<1: lay=lay.filter(ImageFilter.GaussianBlur(float(6*(1-u))))
    m=np.asarray(lay).astype(np.float32)/255*al
    base=a.astype(np.float32)*(1-(1-dark)*al)
    out=base*(1-m[...,None])+np.array(BLANCO,np.float32)*m[...,None]
    return out.astype(np.uint8)
def typed(a,text,t0,t,dt,f,y,color=BLANCO,cursor=True,cx=W/2):
    n=max(0,min(len(text),int((t-t0)/dt)+1)) if t>=t0 else 0
    im=Image.fromarray(a); d=ImageDraw.Draw(im); full=d.textlength(text,font=f)
    bb=d.textbbox((0,0),text,font=f); x=cx-full/2
    d.text((x,y),text[:n],font=f,fill=color)
    if cursor and (n<len(text) or int(t*2.5)%2==0):
        cxp=x+d.textlength(text[:n],font=f)+14; d.rectangle([cxp,y+bb[1],cxp+5,y+bb[3]],fill=color)
    return np.asarray(im)
# logo VA
lg=np.array(Image.open('/home/claude/out/hoja_A4_logo_verde.png').convert('L')).astype(np.float32)
ys,xs=np.where(lg>128); lg=lg[ys.min():ys.max()+1,xs.min():xs.max()+1]
LOGO=Image.fromarray(np.clip((lg-60)*1.4,0,255).astype(np.uint8))
def logo_at(a,w,cx,cy,al=1.0):
    lgw=LOGO.resize((int(w),int(w*LOGO.height/LOGO.width)),Image.LANCZOS)
    im=Image.fromarray(a); im.paste(BLANCO,(int(cx-lgw.width/2),int(cy-lgw.height/2)),lgw.point(lambda v:int(v*al))); return np.asarray(im)
def marca(a): return logo_at(a,74,W-50-37,150,0.9)
# ---------- letras-ventana (máscara 4x, nítida) ----------
SS=4; _lm={}
def text_masks(lines,maxw=1000,gap=18):
    sizes=[fit(t,maxw) for t in lines]
    boxes=[_d.textbbox((0,0),t,font=font(s)) for t,s in zip(lines,sizes)]
    hs=[bx[3]-bx[1] for bx in boxes]; tot=sum(hs)+gap*(len(lines)-1); y=(H-tot)/2; out=[]
    for t,s,h in zip(lines,sizes,hs):
        F=font(s*SS); bb=_d.textbbox((0,0),t,font=F)
        m=Image.new('L',(W*SS,H*SS),0); ImageDraw.Draw(m).text(((W*SS-(bb[2]-bb[0]))/2-bb[0],y*SS-bb[1]),t,font=F,fill=255)
        out.append(m); y+=h+gap
    return out
def mview(m,s=1.0,cx=W/2,cy=H/2):
    box=(SS*(cx-cx/s),SS*(cy-cy/s),SS*(cx+(W-cx)/s),SS*(cy+(H-cy)/s))
    return np.asarray(m.resize((W,H),Image.LANCZOS,box=box)).astype(np.float32)/255
def letters(t,t0,lines,fills,step,zoom_from,zdur):
    key=tuple(lines)
    if key not in _lm: _lm[key]=text_masks(lines)
    masks=_lm[key]; out=green().astype(np.float32)
    sc=1.0; px,py=W/2,H/2
    if t>=zoom_from:
        pk=('pt',key)
        if pk not in _lm:
            a=np.asarray(masks[-1].resize((W,H),Image.BILINEAR)); ys,xs=np.where(a>230); cy=ys.mean()
            i=np.argmin((xs-W/2)**2+(ys-cy)**2*4); _lm[pk]=(float(xs[i]),float(ys[i]))
        px,py=_lm[pk]; u=min(1,(t-zoom_from)/zdur); sc=1+13*(ease(u)**2.2)
        if u>=1:
            c,s0=fills[-1]; return clip(c,s0,3.0,t-(t0+step*(len(lines)-1)))
    for k,(m,(c,s0)) in enumerate(zip(masks,fills)):
        tin=t0+step*k
        if t<tin: continue
        u=eout((t-tin)/0.4); al=u
        e=1.08-0.08*u
        mm=mview(m,sc*e,px if sc>1 else W/2,py if sc>1 else H/2)*al
        if u<1: mm=np.asarray(Image.fromarray((mm*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(float(5*(1-u))))).astype(np.float32)/255
        v=clip(c,s0,3.0,t-tin).astype(np.float32)
        out=out*(1-mm[...,None])+v*mm[...,None]
    return out.astype(np.uint8)
# ---------- web (para el final del buscador) ----------
wm=Image.open('/home/claude/lanz/web/logo-wordmark.png').convert('RGBA'); wm=wm.resize((620,int(620*wm.height/wm.width)),Image.LANCZOS)
hero=Image.open('/home/claude/lanz/web/hero-foto.webp').convert('RGB'); r=max(W/hero.width,H/hero.height)*1.1
hero=hero.resize((int(hero.width*r),int(hero.height*r)),Image.LANCZOS)
def pagina(t,t0):
    return Image.fromarray(rem[min(len(rem)-1,max(0,int((t-T_ENTER)*FPS)))])
def _pagina_old(t,t0):
    s=1.0+0.04*(t-t0); w,h=W/s,H/s; x0=(hero.width-w)/2; y0=(hero.height-h)/2
    p=hero.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+w,y0+h)).convert('RGBA'); p.alpha_composite(wm,((W-wm.width)//2,160)); return p.convert('RGB')
# ---------- guion (en compases de 122 BPM) ----------
T_INTRO=0; T_BURST=2*BAR; T_NW=3*BAR; T_SERV=5*BAR; T_ONL=7*BAR; T_TODO=8*BAR; T_BIEN=9*BAR; T_BUS=10*BAR; T_ENTER=11*BAR; T_REM=11*BAR+0.46
BURST=[('v9126',0.5),('v5883',1.0),('v7276',0.4),('v9112',0.6),('v6193',2.2),('v7779',2.6),('v9162',4.0),('v5407',2.0)]
SERV=[('PROYECTO','v7779',1.2,'blur'),('DIRECCIÓN','v9112',0.0,'push'),('OBRA','v6193',3.0,'zoom'),('REFORMAS','v5883',0.4,'leak')]
TODO=[('TODO LO QUE','v7276',0.0),('HACEMOS','v9126',1.5),('EN UN SOLO','v9162',2.5),('LUGAR','v5407',3.0)]
fDate=font(118,800,112); fIt=ImageFont.truetype(FI,78); fBus=None
rem=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',L+'remate_916.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout,np.uint8).reshape(-1,H,W,3)
TOT=T_ENTER+len(rem)/FPS
def intro(t):
    fr=green()
    # logo abajo centrado (aparece suave)
    fr=logo_at(fr,130,W/2,H-430,ease(t/0.8))
    fr=typed(fr,'08.10.2026',0.45,t,0.11,fDate,H/2-110,cursor=t<T_BURST-0.25)
    if t>=1.9:
        u=eout((t-1.9)/0.6); im=Image.fromarray(fr); d=ImageDraw.Draw(im); txt='algo nuevo'
        w=d.textlength(txt,font=fIt); col=tuple(int(VERDE[i]+(BLANCO[i]-VERDE[i])*u) for i in range(3))
        d.text(((W-w)/2,H/2+60+14*(1-u)),txt,font=fIt,fill=col); fr=np.asarray(im)
    return fr
def burst(t):
    i=min(len(BURST)-1,int((t-T_BURST)/(b/2))); c,s=BURST[i]; dt=t-T_BURST-i*b/2
    fr=zoom(clip(c,s,0.4,dt),1.06-0.06*eout(dt/(b/2)))
    if dt<0.07 and i>0:   # micro-disolvencia entre fotos
        pc,ps=BURST[i-1]; fr=mix(zoom(clip(pc,ps,0.4,b/2),1.0),fr,dt/0.07)
    return marca(fr)
def services(t):
    seg_d=2*b; i=min(3,int((t-T_SERV)/seg_d)); w,c,s,kind=SERV[i]; tin=T_SERV+i*seg_d; dt=t-tin
    fr=zoom(clip(c,s,1.3,dt),1.0+0.04*dt/seg_d)
    TR=0.32
    if dt<TR:
        if i==0: prev=clip('v9162',0.0,3.0,t-(T_NW+2*b))   # viene del zoom por la letra
        else:
            pw,pc,ps,_=SERV[i-1]; prev=zoom(clip(pc,ps,1.3,seg_d+dt),1.04)
            prev=word(prev,pw,seg_d+dt,0,None)
        fr=blend_tr(prev,fr,dt/TR,kind)
        return marca(word(fr,w,t,tin+TR*0.5,tin+seg_d))
    return marca(word(fr,w,t,tin+TR*0.5,tin+seg_d))
def todo(t):
    i=min(3,int((t-T_TODO)/b)); w,c,s=TODO[i]; tin=T_TODO+i*b; dt=t-tin
    fr=zoom(clip(c,s,0.7,dt),1.03-0.03*eout(dt/b))
    if dt<0.12 and i>0:
        pw,pc,ps=TODO[i-1]; fr=blend_tr(zoom(clip(pc,ps,0.7,b),1.0),fr,dt/0.12,'blur')
    # palabras: "TODO LO QUE HACEMOS" (2 líneas) y "EN UN SOLO LUGAR"
    first=i<2
    l1,l2=('TODO LO QUE','HACEMOS') if first else ('EN UN SOLO','LUGAR')
    t1=T_TODO+(0 if first else 2*b)
    fr=word(fr,l1,t,t1,t1+2*b,y=H/2-150,sz=fit('TODO LO QUE',940))
    fr=word(fr,l2,t,t1+b,t1+2*b,y=H/2+10,sz=fit('TODO LO QUE',940))
    return marca(fr)
def bienvenidos(t):
    dt=t-T_BIEN; fr=zoom(clip('v5517',17.0,BAR+0.2,dt),1.03+0.04*dt/BAR)
    if dt<0.35: fr=blend_tr(zoom(clip('v5407',3.0,1.0,b+dt),1.0),fr,dt/0.35,'leak')
    fr=word(fr,'BIENVENIDOS',t,T_BIEN+0.25,None,y=H-620)
    if dt>BAR-0.6: fr=leak(fr,ease((dt-(BAR-0.6))/0.6)*1.1,0.65,0.4)
    return marca(fr)
def buscador(t):
    dt=t-T_BUS; S2=2
    img=Image.new('RGB',(W*S2,H*S2),VERDE); d=ImageDraw.Draw(img)
    bw,bh=920,112; cx,cy=W/2,H/2+40
    u=eout(dt/0.45); sc=0.9+0.1*u
    if t>=T_ENTER-0.08: sc*=1-0.03*np.sin(min(1,(t-T_ENTER+0.08)/0.14)*np.pi)
    e=0.0
    if t>=T_ENTER: e=ease((t-T_ENTER)/0.45)
    w=bw*sc+(W-bw*sc)*e; h=bh*sc+(H-bh*sc)*e; rr=(bh*sc/2)*(1-e)
    box=[S2*(cx-w/2)*(1-e),S2*((cy-h/2)*(1-e)),S2*((cx+w/2)*(1-e)+W*e),S2*((cy+h/2)*(1-e)+H*e)]
    if e<1:
        lw=150; lg2=LOGO.resize((lw*S2,int(lw*S2*LOGO.height/LOGO.width)),Image.LANCZOS)
        img.paste(BLANCO,(int((W*S2-lg2.width)/2),int(S2*(cy-320))),lg2.point(lambda v:int(v*u*(1-e))))
    d.rounded_rectangle(box,radius=int(rr*S2),fill=(250,250,247))
    if e<0.05:
        lx,ly=cx-bw*sc/2+58,cy; R=17*sc
        d.ellipse([S2*(lx-R),S2*(ly-R-4),S2*(lx+R),S2*(ly+R-4)],outline=VERDE,width=int(5*S2))
        d.line([S2*(lx+R*0.7),S2*(ly+R*0.7-4),S2*(lx+R*1.6),S2*(ly+R*1.6-4)],fill=VERDE,width=int(6*S2))
        txt='vignalearquitectura.com.ar'; t0=T_BUS+0.5; n=max(0,min(len(txt),int((t-t0)/0.05)+1)) if t>=t0 else 0
        F=font(int(46*S2*sc),500,100); tx=S2*(lx+42); bb=d.textbbox((0,0),'Ag',font=F); ty=S2*cy-(bb[1]+bb[3])/2
        d.text((tx,ty),txt[:n] if n else 'Buscar',font=F,fill=(40,42,38) if n else (160,162,156))
        if (n<len(txt) or int(t*2.5)%2==0) and t<T_ENTER:
            cxp=tx+(d.textlength(txt[:n],font=F) if n else 0)+4; d.rectangle([cxp,S2*(cy-24*sc),cxp+3*S2,S2*(cy+24*sc)],fill=(40,42,38))
    out=img.resize((W,H),Image.LANCZOS)
    if e>0:
        pg=pagina(t,T_ENTER); m=Image.new('L',(W*S2,H*S2),0); ImageDraw.Draw(m).rounded_rectangle(box,radius=int(rr*S2),fill=255)
        out.paste(pg,(0,0),m.resize((W,H),Image.LANCZOS).point(lambda v:int(v*min(1,e*3))))
    fr=np.asarray(out)
    if dt<0.4:   # viene del destello de BIENVENIDOS
        fr=leak(fr,1.1*(1-ease(dt/0.4)),0.65,0.4)
    return fr
def frame(t):
    if t<T_BURST: return intro(t)
    if t<T_NW: return burst(t)
    if t<T_SERV:
        fr=letters(t,T_NW,['NUEVA','WEB'],[('v5883',2.0),('v9162',0.0)],2*b,T_NW+5*b,3*b*0.9)
        if t-T_NW<0.25: fr=mix(burst(T_NW-0.01),fr,ease((t-T_NW)/0.25))
        return fr
    if t<T_ONL: return services(t)
    if t<T_TODO:
        fr=letters(t,T_ONL,['YA ESTÁ','ONLINE'],[('v9112',2.0),('v9162',1.0)],b,T_ONL+2*b,2*b*0.95)
        if t-T_ONL<0.3: fr=mix(np.asarray(services(T_ONL-0.01)),fr,ease((t-T_ONL)/0.3))
        return fr
    if t<T_BIEN:
        fr=todo(t)
        if t-T_TODO<0.25: fr=blend_tr(clip('v9162',1.0,3.0,t-(T_ONL+b)),fr,(t-T_TODO)/0.25,'zoom')
        return fr
    if t<T_BUS: return bienvenidos(t)
    if t<T_REM: return buscador(t)
    return rem[min(len(rem)-1,int((t-T_ENTER)*FPS))]
if __name__=='__main__':
    if len(sys.argv)>1:
        S='/tmp/claude-0/-home-claude-vignale-contenido/85090f47-759b-5063-928e-688f346edae7/scratchpad/n/'
        for ts in sys.argv[1:]: Image.fromarray(frame(float(ts))).resize((360,450)).save(S+f't_{ts}.png')
        sys.exit()
    out=os.environ.get('OUTV','/home/claude/out/lanz_916_hq.mp4'); mus=os.environ.get('MUS')
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-']
    if mus: cmd+=['-i',mus,'-c:a','aac','-b:a','192k','-shortest']
    cmd+=['-c:v','libx264','-crf','15','-preset','slow','-tune','film','-pix_fmt','yuv420p','-movflags','+faststart',out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(int(TOT*FPS)): p.stdin.write(np.ascontiguousarray(frame(i/FPS)).tobytes())
    p.stdin.close(); p.wait(); print('ok',TOT)
