import sys, math, time, numpy as np, sim
t0=time.time(); res=[]
a0,a1=int(sys.argv[1]),int(sys.argv[2])
for js in range(a0,a1):
  for b in (60,80,100,120):
    _,ev,_,_=sim.run(b,0.0,None,14.5,jit=.06,jseed=js)
    hits=[(e[0],math.atan2(e[3]-sim.CY,e[2]-sim.CX)) for e in ev if e[1]=="cage"]
    for ga in np.linspace(-np.pi,np.pi,90,endpoint=False):
      offs=[(t,sim.ang_diff(a,ga)*sim.RC) for t,a in hits]
      T=next((t for t,o in offs if abs(o)<sim.GAPW/2),None)
      if T is None or not(11<=T<=14): continue
      if sum(1 for t,o in offs if t<T and abs(o)<76)<3: continue
      _,ev2,_,to=sim.run(b,0.0,float(ga),14.5,jit=.06,jseed=js)
      if to is None or not(11.5<=to<=13.8): continue
      near=[(e[0],e[1]) for e in ev2 if e[0]<to-.05 and ((e[1]=="post") or (e[1]=="cage" and abs(e[4])<68))]
      tt=[x[0] for x in near]
      if len(tt)<4: continue
      gaps=np.diff([0]+tt+[to]); posts=sum(1 for x in near if x[1]=="post")
      score=len(set(int(x/1.5) for x in tt))*10+len(tt)+4*posts-4*max(0,gaps.max()-2.5)-6*(tt[-1]<to-2.2)
      res.append((round(score,1),js,b,round(float(ga),3),round(to,2),posts,[round(x,1) for x in tt]))
res.sort(reverse=True)
for r in res[:6]: print(r)
print("t",time.time()-t0,file=sys.stderr)
