import numpy as np
N=32; ALPHA=0.25; A=1.0; dt=0.05
j=np.arange(1,N+1)
k=np.arange(1,N+1)
S=np.sqrt(2/(N+1))*np.sin(np.outer(j,k)*np.pi/(N+1))
om=2*np.sin(k*np.pi/(2*(N+1)))
def acc(x):
    xp=np.concatenate([[0],x,[0]])
    d=np.diff(xp)
    f=d+ALPHA*d*d
    return f[1:]-f[:-1]
def run(T,x0,v0=None,every=4):
    x=x0.copy(); v=np.zeros(N) if v0 is None else v0.copy()
    a=acc(x); out=[];ts=[]
    n=int(T/dt)
    for i in range(n):
        if i%every==0: out.append(np.concatenate([x,v])); ts.append(i*dt)
        v+=0.5*dt*a; x+=dt*v; a=acc(x); v+=0.5*dt*a
    return np.array(ts),np.array(out)
if __name__=="__main__":
    x0=A*np.sin(np.pi*j/(N+1))
    ts,X=run(30000,x0)
    np.save("traj.npy",X); np.save("ts.npy",ts)
    q=X[:,:N]@S; p=X[:,N:]@S
    E=0.5*(p**2+(om*q)**2)
    Ef=E/E.sum(1,keepdims=True)
    T1=2*np.pi/om[0]; print("T1",T1)
    for t in range(0,30000,500):
        i=int(t/(dt*4)); print(t, round(t/T1,1), np.round(Ef[i,:6]*100,1))
