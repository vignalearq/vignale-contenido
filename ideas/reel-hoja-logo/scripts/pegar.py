import sys, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
def pegar(bg_path, out_path, sheet_path='/home/claude/out/hoja_A4_logo_verde.png', seed=0, glass=False, lsig=80, lamt=0.5, shadow=1.0):
    OW,OH=1080,1350
    bg=Image.open(bg_path).convert('RGB')
    # crop to 4:5 then resize
    w,h=bg.size; t=4/5
    if w/h>t: nw=int(h*t); bg=bg.crop(((w-nw)//2,0,(w-nw)//2+nw,h))
    else: nh=int(w/t); bg=bg.crop((0,(h-nh)//2,w,(h-nh)//2+nh))
    bg=bg.resize((OW,OH),Image.LANCZOS); B=np.array(bg).astype(float)
    W=int(OW*0.54); H=int(W*1.4142); x0=(OW-W)//2; y0=(OH-H)//2-10
    S=np.array(Image.open(sheet_path).convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
    rng=np.random.default_rng(seed)
    # paper waviness: low-freq noise -> normal-ish shading
    n=ndimage.gaussian_filter(rng.normal(0,1,(H,W)),60); n/=np.abs(n).max()+1e-6
    n2=ndimage.gaussian_filter(rng.normal(0,1,(H,W)),18); n2/=np.abs(n2).max()+1e-6
    hgt=n*1.0+n2*0.08
    gy,gx=np.gradient(hgt); shade=1+(-gx*0.6-gy*1.0)*14
    shade=np.clip(shade,0.96,1.04)
    yy,xx=np.mgrid[:H,:W]; shade*=1.04-0.08*(0.6*xx/W+0.4*yy/H)
    # scene light: relative luminance of blurred bg under the sheet
    L=ndimage.gaussian_filter(B.mean(2),lsig); reg=L[y0:y0+H,x0:x0+W]; light=reg/reg.mean()
    light=1+(light-1)*lamt
    grain=ndimage.gaussian_filter(rng.normal(0,1,(H,W)),0.7)*2.5
    P=S*(shade*light)[...,None]+grain[...,None]
    # warm/cool tint from bg
    tint=B[y0:y0+H,x0:x0+W].reshape(-1,3).mean(0); tint=tint/tint.mean()
    P*=(1+(tint-1)*0.06)
    if glass:
        yy2,xx2=np.mgrid[:H,:W]; hl=np.clip(1-np.abs((xx2/W+yy2/H)-0.55)/0.08,0,1)*0.05
        P=P*(1-hl[...,None])+255*hl[...,None]
    P=np.clip(P,0,255)
    # shadow
    m=np.zeros((OH,OW)); dx,dy=(3,5) if glass else (6,10)
    m[y0+dy:y0+H+dy,x0+dx:x0+W+dx]=1
    m=ndimage.gaussian_filter(m,6 if glass else 12)*(0.35 if glass else 0.5)*shadow
    out=B*(1-m[...,None])
    # edge lift highlight on top/left edges
    out[y0:y0+H,x0:x0+W]=P
    e=np.ones((H,W)); e[1:-1,1:-1]=0
    out[y0:y0+H,x0:x0+W]=out[y0:y0+H,x0:x0+W]*(1-0.25*e[...,None])+255*0.25*e[...,None]*0.6
    Image.fromarray(out.astype('uint8')).save(out_path,quality=95)
if __name__=='__main__':
    pegar(sys.argv[1],sys.argv[2],glass=len(sys.argv)>3)
