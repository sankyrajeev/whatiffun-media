import subprocess, re, os, sys, itertools
from concurrent.futures import ThreadPoolExecutor
def run(p):
    env = dict(os.environ, NOSAVE="1", SECS=os.environ.get("SS","40"), **{k: str(v) for k, v in p.items()})
    out = subprocess.run(["python3", "sim.py"], env=env, capture_output=True, text=True).stdout
    rs = [float(x) for x in re.findall(r" r=([\d.na]+)", out)]
    t9 = (next((i for i, r in enumerate(rs) if r > 0.5), None), next((i for i, r in enumerate(rs) if r > 0.997), None))
    return p, [round(rs[i], 2) for i in range(0, len(rs), 5)], t9
grid = eval(sys.argv[1])
keys = list(grid)
combos = [dict(zip(keys, v)) for v in itertools.product(*grid.values())]
with ThreadPoolExecutor(2) as ex:
    for p, rs, t9 in ex.map(run, combos): print(p, rs, "t0.9=", t9, flush=True)
