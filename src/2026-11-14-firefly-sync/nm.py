import sim, search, numpy as np, json, sys
def show(kw):
    P,f,fl=sim.run(**kw); sim.P_X=P[:,0]; c=search.sync_counts(P,fl,kw['T'])
    tm=np.nonzero(c>=297)[0][0]/30
    b=[(t,n,x) for t,n,x in sim.bursts([e for e in fl if tm-6<e[0]<tm+1],gap=.012) if n>=20]
    print(kw, 'merge', tm); print('  '+' '.join(f"{t:.2f}:{n}{'L' if x<480 else 'R' if x>600 else 'M'}" for t,n,x in b))
for a in sys.argv[1:]: show(json.loads(a))
