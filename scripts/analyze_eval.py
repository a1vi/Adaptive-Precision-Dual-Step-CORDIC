import numpy as np, json

FRAC=20
SCALE=1<<FRAC
def fromfx(v): return v/SCALE

def load(fn):
    rows=[]
    with open(fn) as f:
        for line in f:
            a,b,c,cyc = map(int, line.split())
            rows.append((a,b,c,cyc))
    return rows

def stats_rot(rows):
    errs=[]; cycs=[]
    for th_fx,c_fx,s_fx,cyc in rows:
        th=fromfx(th_fx); c=fromfx(c_fx); s=fromfx(s_fx)
        errs.append(max(abs(c-np.cos(th)), abs(s-np.sin(th)))); cycs.append(cyc)
    return dict(avg=float(np.mean(errs)), max=float(np.max(errs)), p99=float(np.percentile(errs,99)), cyc=float(np.mean(cycs)), n=len(rows))

def stats_vec(rows):
    errs=[]; cycs=[]
    for x_fx,y_fx,a_fx,cyc in rows:
        x=fromfx(x_fx); y=fromfx(y_fx); a=fromfx(a_fx)
        ref = np.arctan2(y,x)
        errs.append(abs(a-ref)); cycs.append(cyc)
    return dict(avg=float(np.mean(errs)), max=float(np.max(errs)), p99=float(np.percentile(errs,99)), cyc=float(np.mean(cycs)), n=len(rows))

results = {}
for tag in ["baseline","earlyonly","dualonly","combined"]:
    for p,pname in enumerate(["High","Medium","Low"]):
        r_eval = stats_rot(load(f"eval_rot_{tag}_p{p}.txt"))
        v_eval = stats_vec(load(f"eval_vec_{tag}_p{p}.txt"))
        r_struct = stats_rot(load(f"struct_rot_{tag}_p{p}.txt"))
        v_struct = stats_vec(load(f"struct_vec_{tag}_p{p}.txt"))
        results[f"{tag}_{pname}"] = dict(eval_rot=r_eval, eval_vec=v_eval, struct_rot=r_struct, struct_vec=v_struct)

with open("eval_results.json","w") as f:
    json.dump(results, f, indent=2)

print(f"{'Config':10s} {'Mode':7s} | {'EvalRotAvg':>10s} {'EvalRotMax':>10s} {'EvalRotCyc':>10s} | {'EvalVecAvg':>10s} {'EvalVecMax':>10s} {'EvalVecCyc':>10s} | {'StructRotMax':>12s} {'StructVecMax':>12s}")
for tag in ["baseline","earlyonly","dualonly","combined"]:
    for pname in ["High","Medium","Low"]:
        r = results[f"{tag}_{pname}"]
        print(f"{tag:10s} {pname:7s} | {r['eval_rot']['avg']:.3e} {r['eval_rot']['max']:.3e} {r['eval_rot']['cyc']:10.3f} | {r['eval_vec']['avg']:.3e} {r['eval_vec']['max']:.3e} {r['eval_vec']['cyc']:10.3f} | {r['struct_rot']['max']:.3e} {r['struct_vec']['max']:.3e}")
