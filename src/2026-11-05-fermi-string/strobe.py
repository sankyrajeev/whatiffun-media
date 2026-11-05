import numpy as np, sim_explore as sim, sys
N=32; sim.N=N; sim.ALPHA=float(sys.argv[1]); A=float(sys.argv[2])
j=np.arange(1,N+1); sim.j=j
S=np.sqrt(2/(N+1))*np.sin(np.outer(j,j)*np.pi/(N+1)); om=2*np.sin(j*np.pi/(2*(N+1)))
T1=2*np.pi/om[0]
ts,X=sim.run(200*T1,A*np.sin(np.pi*j/(N+1)),every=1)
q=X[:,:N]@S;p=X[:,N:]@S;E=0.5*(p**2+(om*q)**2);Ef=E/E.sum(1,keepdims=True)
q1=q[:,0]
pk=np.where((q1[1:-1]>q1[:-2])&(q1[1:-1]>=q1[2:])&(q1[1:-1]>0))[0]+1
sw=ts/T1
# recurrence: max E1 after 40 swings
m=sw>40; ir=np.argmax(np.where(m,Ef[:,0],0)); 
pr=pk[np.argmin(np.abs(pk-ir))]
print("rec swing",sw[pr],"E1",Ef[pr,0])
# count periods = round((t_pr)/T1_eff) where early period
Tearly=ts[pk[1]]-ts[pk[0]] if ts[pk[0]]>0 else ts[pk[1]]
n=round(ts[pr]/Tearly); Ts=ts[pr]/n
print("Tearly",Tearly,"n",n,"Ts",Ts, "T1",T1)
np.savez("strobe_%s_%s.npz"%(sys.argv[1],sys.argv[2]),ts=ts,X=X,Ef=Ef,Ts=Ts,n=n,dt=sim.dt)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(10,1,figsize=(6,14))
for r,s in enumerate(np.linspace(0,n,10).astype(int)):
    i=int(round(s*Ts/sim.dt)); x=np.concatenate([[0],X[i,:N],[0]])
    ax[r].plot(x,'o-'); ax[r].set_ylim(-A*1.6,A*1.6); ax[r].set_title(f"swing {s} E1 {Ef[i,0]*100:.0f}%",fontsize=8)
plt.tight_layout(); plt.savefig("strobe_%s_%s.png"%(sys.argv[1],sys.argv[2]),dpi=60)
# strain strip
rows=[]
for s in range(n+1):
    i=int(round(s*Ts/sim.dt)); rows.append(np.diff(np.concatenate([[0],X[i,:N],[0]])))
plt.figure(figsize=(4,6)); plt.imshow(np.array(rows),aspect='auto',cmap='inferno'); plt.savefig("strip_%s_%s.png"%(sys.argv[1],sys.argv[2]),dpi=60)
