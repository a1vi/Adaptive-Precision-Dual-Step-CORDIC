import re, json

with open("leakage_table.json") as f:
    leak = json.load(f)

def cell_counts_from_netlist(fn):
    with open(fn) as f:
        text = f.read()
    counts = {}
    for m in re.finditer(r'\bsky130_fd_sc_hd__\w+\s+\\?[\w$.\[\]]+\s*\(', text):
        # extract cell type token
        tok = m.group(0).split()[0]
        counts[tok] = counts.get(tok, 0) + 1
    return counts

configs = {"baseline":"0_0", "earlyonly":"0_1", "dualonly":"1_0", "combined":"1_1"}
results = {}
for name, tag in configs.items():
    counts = cell_counts_from_netlist(f"netlist_{tag}.v")
    total_nW = 0.0
    missing = []
    for cell, n in counts.items():
        if cell in leak:
            total_nW += leak[cell]*n
        else:
            missing.append(cell)
    results[name] = dict(total_leakage_nW=total_nW, total_leakage_uW=total_nW/1000.0, n_cell_types=len(counts), missing=missing)
    print(name, f"{total_nW:.1f} nW  ({total_nW/1000:.3f} uW)", "missing types:", missing)

with open("leakage_results.json","w") as f:
    json.dump(results, f, indent=2)
