import numpy as np, wave
SR=44100; b=60/122; DUR=25.7; N=int(SR*DUR); L=np.zeros(N); rng=np.random.default_rng(2)
def add(s,t,g=1):
    i=int(t*SR); j=min(N,i+len(s)); 
    if i<N: L[i:j]+=s[:j-i]*g
def env(n,a,d): t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
n=int(.3*SR); t=np.arange(n)/SR; kick=np.tanh(2*np.sin(2*np.pi*np.cumsum(45+110*np.exp(-t*35))/SR))*env(n,.001,.15)
n2=int(.05*SR); hat=np.diff(np.r_[0,rng.normal(0,1,n2)])*env(n2,.0005,.015)*.25
n3=int(.25*SR); x=rng.normal(0,1,n3); clap=(x-np.convolve(x,np.ones(20)/20,'same'))*env(n3,.001,.06)*.4
k=0; tt=0
while tt<DUR-0.1:
    add(kick,tt); add(hat,tt+b/2)
    if k%2==1: add(clap,tt)
    if k%16==0: 
        n4=int(.08*SR); add(np.sin(2*np.pi*1500*np.arange(n4)/SR)*env(n4,.001,.03)*.15,tt)
    tt+=b; k+=1
m=L/np.abs(L).max()*.85; fl=int(1*SR); m[-fl:]*=np.linspace(1,0,fl)
w=wave.open('guia.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((m*32767).astype('<i2').tobytes()); w.close()
