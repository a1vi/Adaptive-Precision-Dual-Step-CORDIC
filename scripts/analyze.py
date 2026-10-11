import numpy as np, glob, re

FRAC=20
SCALE=1<<FRAC

def fromfx(v): return v/SCALE

def load_rot(fn):
    rows=[]
    with open(fn) as f:
        for line in f:
            th,c,s,cyc = map(int, line.split())
            rows.append((th,c,s,cyc))
    return rows

def load_vec(fn):
    rows=[]
    with open(fn) as f:
        for line in f:
            x,y,a,cyc = map(int, line.split())
            rows.append((x,y,a,cyc))
    return rows

results = {}
for tag in ["baseline","earlyonly","dualonly","combined"]:
    for p,pname in enumerate(["High","Medium","Low"]):
        rf = f"rot_{tag}_p{p}.txt"
        vf = f"vec_{tag}_p{p}.txt"
        rrows = load_rot(rf)
        vrows = load_vec(vf)
        rerrs=[]; rcycs=[]
        for th_fx,c_fx,s_fx,cyc in rrows:
            th = fromfx(th_fx); c=fromfx(c_fx); s=fromfx(s_fx)
            err = max(abs(c-np.cos(th)), abs(s-np.sin(th)))
            rerrs.append(err); rcycs.append(cyc)
        verrs=[]; vcycs=[]
        for x_fx,y_fx,a_fx,cyc in vrows:
            x=fromfx(x_fx); y=fromfx(y_fx); a=fromfx(a_fx)
            ref = np.arctan2(y,x)
            err = abs(a-ref)
            verrs.append(err); vcycs.append(cyc)
        results[(tag,pname)] = dict(
            rot_avg=np.mean(rerrs), rot_max=np.max(rerrs), rot_cyc=np.mean(rcycs),
            vec_avg=np.mean(verrs), vec_max=np.max(verrs), vec_cyc=np.mean(vcycs),
        )

print(f"{'Config':10s} {'Mode':7s} {'RotAvgErr':>10s} {'RotMaxErr':>10s} {'RotCyc':>7s}   {'VecAvgErr':>10s} {'VecMaxErr':>10s} {'VecCyc':>7s}")
for tag in ["baseline","earlyonly","dualonly","combined"]:
    for pname in ["High","Medium","Low"]:
        r = results[(tag,pname)]
        print(f"{tag:10s} {pname:7s} {r['rot_avg']:.3e} {r['rot_max']:.3e} {r['rot_cyc']:7.2f}   {r['vec_avg']:.3e} {r['vec_max']:.3e} {r['vec_cyc']:7.2f}")

import json
with open("ablation_results.json","w") as f:
    json.dump({f"{k[0]}_{k[1]}":v for k,v in results.items()}, f, indent=2)
