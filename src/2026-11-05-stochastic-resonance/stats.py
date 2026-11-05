import numpy as np
D=np.load("sr.npz"); EV=D["EV"]; TS=D["TS"]; T=float(D["T"]); N=1000; TOTAL=750
S=np.zeros((TOTAL,N),np.int8); s=-np.ones(N,np.int8); j=0
for f in range(TOTAL):
    while j<len(EV) and EV[j,0]<f+1: s[int(EV[j,1])]=EV[j,2]; j+=1
    S[f]=s
np.save("state.npy",S)
ph=2*np.pi*TS/T
for lag in np.linspace(0,np.pi,7):
    r=np.sign(np.sin(ph-lag))
    m=(S[150:560]==r[150:560,None]).mean(0)
    print(round(lag,2),[round(float(2*m[a:b].mean()-1),2) for a,b in [(0,333),(333,667),(667,1000)]])
r=np.sign(np.sin(ph-0.6))
m=2*(S[150:560]==r[150:560,None]).mean(0)-1
SIG=D["SIG"]
for k in range(20): print(round(float(SIG[k*50]),2), round(float(m[k*50:(k+1)*50].mean()),2))
