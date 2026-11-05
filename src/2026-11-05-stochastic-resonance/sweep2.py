import numpy as np
rng=np.random.default_rng(1)
def run(T, A, sig, dur=16, dt=0.02):
    n=len(sig); x=-np.ones(n); w=2*np.pi/T
    st=-np.ones(n); flips=np.zeros(n); corr=np.zeros(n); steps=int(dur*T/dt)
    for k in range(steps):
        t=k*dt; s=A*np.sin(w*t)
        x+= (x-x**3+s)*dt + sig*np.sqrt(dt)*rng.standard_normal(n)
        ns=np.where(x>0.4,1,np.where(x<-0.4,-1,st)); flips+=ns!=st; st=ns
        corr+=st*np.sin(w*t-np.pi/2*0)  # phase lag later
    return flips/dur, corr/steps*2
sig=np.linspace(0.1,1.6,1000)
for T in [60,80]:
  for A in [0.25,0.3]:
    f,c=run(T,A,sig)
    fb=f.reshape(10,100).mean(1); cb=c.reshape(10,100).mean(1)
    print(T,A,'flips/period',np.round(fb,1)); print('   corr',np.round(cb,2))
