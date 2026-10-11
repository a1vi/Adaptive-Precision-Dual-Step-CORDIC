import re

def parse_leakage(libfile):
    with open(libfile) as f:
        text = f.read()
    # split into cell blocks
    cells = {}
    for m in re.finditer(r'cell\s*\(\"([\w]+)\"\)\s*\{', text):
        name = m.group(1)
        start = m.end()
        # find matching closing brace by counting depth
        depth = 1
        i = start
        while depth > 0 and i < len(text):
            if text[i] == '{': depth += 1
            elif text[i] == '}': depth -= 1
            i += 1
        block = text[start:i]
        vals = [float(v) for v in re.findall(r'leakage_power\s*\(\)\s*\{[^}]*?value\s*:\s*([\d.eE+-]+)\s*;', block)]
        if not vals:
            vals = [float(v) for v in re.findall(r'cell_leakage_power\s*:\s*([\d.eE+-]+)\s*;', block)]
        if vals:
            cells[name] = sum(vals)/len(vals)  # average over listed states, in nW
    return cells

leak = parse_leakage("sky130_fd_sc_hd__tt_025C_1v80.lib")
print(f"parsed leakage for {len(leak)} cells")
import json
with open("leakage_table.json","w") as f:
    json.dump(leak, f)
# sanity print a few
for k in list(leak.keys())[:5]:
    print(k, leak[k], "nW")
