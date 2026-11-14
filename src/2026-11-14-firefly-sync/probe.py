import sys, json, numpy as np, sim
kw = json.loads(sys.argv[1])
P, f, fl = sim.run(**kw); sim.P_X = P[:, 0]
b = [x for x in sim.bursts(fl) if x[1] >= int(sys.argv[2]) ]
print(" ".join(f"{t:.2f}:{n}{'L' if x<480 else 'R' if x>600 else 'M'}" for t, n, x in b))
