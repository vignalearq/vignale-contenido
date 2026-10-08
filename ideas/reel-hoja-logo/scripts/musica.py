import numpy as np, wave
SR=44100; BPM=120; BEAT=60/BPM; DUR=11.6
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(7)
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); s=sig[:j-i]*g
    L[i:j]+=s*(1-pan)/1; R[i:j]+=s*(1+pan)/1
def env(n,a=0.005,d=0.3):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def kick():
    n=int(.35*SR); t=np.arange(n)/SR; f=50+120*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.001,.18)*1.0
def snare():
    n=int(.25*SR); t=np.arange(n)/SR
    return (rng.normal(0,1,n)*env(n,.001,.07)*0.6+np.sin(2*np.pi*190*t)*env(n,.001,.05)*0.4)
def hat(o=False):
    n=int((.18 if o else .05)*SR); x=rng.normal(0,1,n); x=np.diff(np.concatenate([[0],x]))
    return x*env(n,.001,.06 if o else .015)*0.25
def crash():
    n=int(2.5*SR); x=rng.normal(0,1,n); x=np.diff(np.concatenate([[0],x]))
    return x*env(n,.002,.9)*0.3
def guitar(freqs,dur,g=1.0):
    n=int(dur*SR); t=np.arange(n)/SR; s=np.zeros(n)
    for f in freqs:
        for det in (-0.12,0.12):
            ph=(t*f*2**(det/12))%1; s+=2*ph-1
    s=np.tanh(s*2.5)*0.35; e=np.minimum(1,t/.004)*np.exp(-t/1.2)
    # simple lowpass
    s=np.convolve(s,np.ones(6)/6,'same'); return s*e*g
def bass(f,dur):
    n=int(dur*SR); t=np.arange(n)/SR
    s=np.tanh(np.sin(2*np.pi*f*t)*2+0.3*np.sin(4*np.pi*f*t))*env(n,.003,.25)
    return s*0.5
def chord(root): return [root,root*1.5,root*2]
E,B,Cs,A=82.41,123.47/1,69.30*1,110.0
# Intro bar 0-2s: muted chug swelling + hats + riser
for k in range(8):
    add(guitar(chord(E),0.12,0.35+0.08*k),k*BEAT/2,pan=-0.3); add(guitar(chord(E*1.002),0.12,0.35+0.08*k),k*BEAT/2+0.01,pan=0.3)
for k in range(8): add(hat(),k*BEAT/2,0.2)
n=int(2*SR); t=np.arange(n)/SR; r=rng.normal(0,1,n); r=np.convolve(r,np.ones(20)/20,'same')*(t/2)**3*0.5
add(r,0.0)
# Drop: bars at 2.0, 4.0, 6.0 (E, B, C#m) with rock beat
prog=[(2.0,E),(4.0,B/2*1.0),(6.0,Cs)]
for t0,root in prog:
    for h in range(8):
        tt=t0+h*BEAT/2
        add(guitar(chord(root),BEAT/2*0.95,0.9),tt,pan=-0.35); add(guitar(chord(root*1.003),BEAT/2*0.95,0.9),tt+0.012,pan=0.35)
        add(bass(root/2,BEAT/2*0.9),tt); add(hat(h%2==1),tt,0.25)
    for b in range(4):
        tt=t0+b*BEAT
        if b in (0,2): add(kick(),tt)
        if b in (1,3): add(snare(),tt,0.05)
    add(kick(),t0+2.5*BEAT,g=0.7)
add(crash(),2.0,-0.2)
# 8.0: final ringing E chord + crash (remate)
add(guitar(chord(E),3.6,1.1),8.0,-0.3); add(guitar(chord(E*1.003),3.6,1.1),8.01,0.3)
add(bass(E/2,1.5)*1.0,8.0); add(kick(),8.0); add(crash(),8.0,0.2)
# whoosh de la hoja volando (0.9-2.0) y golpe de papel al estamparse (2.0)
n=int(1.1*SR); t=np.arange(n)/SR; w=rng.normal(0,1,n)
for k in (3,9,25): w=np.convolve(w,np.ones(k)/k,'same')
add(w*(t/1.1)**2.5*1.6,0.9,0.25)
n=int(.12*SR); sl=rng.normal(0,1,n); sl=np.convolve(sl,np.ones(4)/4,'same')*env(n,.0005,.03)*1.4
add(sl,2.0); add(np.sin(2*np.pi*95*np.arange(n)/SR)*env(n,.0005,.04)*0.6,2.0)
m=np.stack([L,R],1); m/=np.abs(m).max()*1.12
fade=np.ones(N); fl=int(1.2*SR); fade[-fl:]=np.linspace(1,0,fl); m*=fade[:,None]
w=wave.open('/home/claude/reel_build/musica.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((m*32767).astype('<i2').tobytes()); w.close(); print('ok')
