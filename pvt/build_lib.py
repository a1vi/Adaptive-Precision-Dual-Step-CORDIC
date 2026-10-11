#!/usr/bin/env python3
"""
Assemble a complete, OpenSTA-readable plain-text .lib file for a given
SKY130 PVT corner, from Google's real skywater-pdk-libs-sky130_fd_sc_hd
JSON release data:
  - timing/sky130_fd_sc_hd__common.lib.json       (shared library-level attrs/templates)
  - timing/sky130_fd_sc_hd__<corner>.lib.json      (corner-specific operating_conditions etc.)
  - cells/<type>/sky130_fd_sc_hd__<type>_<drive>__<corner_tag>.lib.json  (per-cell data)

This is a faithful re-serialization of real, authentic SkyWater-released
PDK data (cloned directly from github.com/google/skywater-pdk-libs-sky130_fd_sc_hd),
restricted to the exact list of standard cells actually instantiated in
this project's own synthesized netlists. No timing/power/area numbers are
invented; only CCS-noise-only groups/attributes (present in some corner
releases as a bundled extra, not needed by OpenSTA's table-lookup STA
engine) are dropped.
"""
import json, os, sys

PDK_ROOT = "/home/claude/google/skywater-pdk-libs-sky130_fd_sc_hd"
TIMING_DIR = os.path.join(PDK_ROOT, "timing")
CELLS_DIR = os.path.join(PDK_ROOT, "cells")

DROP_KEYS = {"input_voltage", "output_voltage"}
def should_drop(key):
    base = key.split(",")[0]
    if base in DROP_KEYS:
        return True
    if base.startswith("ccsn") or base.startswith("ccs_") or "noise" in base.lower():
        return True
    return False

def fmt_num(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return f"{v:.10f}"
    return str(v)

def emit_scalar(key, val, indent, out):
    if isinstance(val, bool):
        out.append(f'{indent}{key} : {"true" if val else "false"};')
    elif isinstance(val, (int, float)):
        out.append(f'{indent}{key} : {fmt_num(val)};')
    else:
        out.append(f'{indent}{key} : "{val}";')

def emit_table_attr(key, val, indent, out):
    if key == "values" and val and isinstance(val[0], list):
        rows = ['"' + ", ".join(fmt_num(v) for v in row) + '"' for row in val]
        joiner = ", \\\n" + indent + "    "
        out.append(f"{indent}values({joiner.join(rows)});")
    else:
        out.append(f'{indent}{key}("{", ".join(fmt_num(v) for v in val)}");')

def emit_comp_attribute(name, val, indent, out):
    """comp_attribute,<name> entries are rendered as function-call-style
    library attributes, e.g. technology("cmos"); capacitive_load_unit(1.0,"pf");
    voltage_map("VSS", 0.0); (repeated per pair for a list-of-pairs value)."""
    if isinstance(val, list) and val and isinstance(val[0], list):
        # list of [name, value] pairs -> repeated name(...) statements
        for pair in val:
            args = ", ".join(f'"{a}"' if isinstance(a, str) else fmt_num(a) for a in pair)
            out.append(f"{indent}{name}({args});")
    elif isinstance(val, dict):
        # e.g. {'VGND': 0.0, 'VNB': 0.0} style map -> name("K", v); per entry
        for k, v in val.items():
            out.append(f'{indent}{name}("{k}", {fmt_num(v)});')
    elif isinstance(val, list):
        args = ", ".join(f'"{a}"' if isinstance(a, str) else fmt_num(a) for a in val)
        out.append(f"{indent}{name}({args});")
    elif isinstance(val, str):
        out.append(f'{indent}{name}("{val}");')
    else:
        out.append(f"{indent}{name}({fmt_num(val)});")

def emit_define(entries, indent, out):
    for e in entries:
        out.append(f'{indent}define({e["attribute_name"]},{e["group_name"]},{e["attribute_type"]});')

def emit_group(name, args, obj, indent, out):
    argstr = ", ".join(f'"{a}"' for a in args)
    out.append(f"{indent}{name} ({argstr}) {{")
    inner = indent + "    "
    for key, val in obj.items():
        if should_drop(key):
            continue
        if "," in key:
            gname, rest = key.split(",", 1)
            gargs = rest.split(",")
        else:
            gname, gargs = key, []
        if key in ("index_1", "index_2", "index_3", "values"):
            emit_table_attr(key, val, inner, out)
        elif isinstance(val, dict):
            emit_group(gname, gargs, val, inner, out)
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            for item in val:
                emit_group(gname, gargs, item, inner, out)
        elif isinstance(val, list):
            out.append(f'{inner}{key} ({", ".join(fmt_num(v) for v in val)});')
        else:
            emit_scalar(key, val, inner, out)
    out.append(f"{indent}}}")

def emit_cell_group(cell_json_path, cell_full_name, indent, out):
    d = json.load(open(cell_json_path))
    emit_group("cell", [cell_full_name], d, indent, out)

def build_header(corner_file_tag, lib_name, out):
    common = json.load(open(os.path.join(TIMING_DIR, "sky130_fd_sc_hd__common.lib.json")))
    corner = json.load(open(os.path.join(TIMING_DIR, f"sky130_fd_sc_hd__{corner_file_tag}.lib.json")))
    merged = {}
    merged.update(common)
    merged.update(corner)  # corner-specific values win on key collision

    out.append(f'library ("{lib_name}") {{')
    indent = "    "

    # 1. define() statements first (matches real-file convention)
    if "define" in merged:
        emit_define(merged["define"], indent, out)

    # 2. everything else, in merged dict order
    for key, val in merged.items():
        if key == "define":
            continue
        if should_drop(key):
            continue
        if key.startswith("comp_attribute,"):
            name = key.split(",", 1)[1]
            emit_comp_attribute(name, val, indent, out)
            continue
        if "," in key:
            gname, rest = key.split(",", 1)
            gargs = rest.split(",")
        else:
            gname, gargs = key, []
        if isinstance(val, dict):
            emit_group(gname, gargs, val, indent, out)
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            for item in val:
                emit_group(gname, gargs, item, indent, out)
        elif isinstance(val, list):
            out.append(f'{indent}{key} ({", ".join(fmt_num(v) for v in val)});')
        else:
            emit_scalar(key, val, indent, out)
    # header left open; cells appended by caller, then closing brace

def build_full_lib(corner_file_tag, lib_name, cell_type_drive_list, corner_cell_tag=None):
    """cell_type_drive_list: list of (celltype, drivename) e.g. [('nand2','nand2_1'), ...]
    corner_cell_tag: filename corner tag for cell json files if different from corner_file_tag
    (e.g. ff corner cells are released only as *_ccsnoise.lib.json)."""
    if corner_cell_tag is None:
        corner_cell_tag = corner_file_tag
    out = []
    build_header(corner_file_tag, lib_name, out)
    missing = []
    for celltype, drivename in cell_type_drive_list:
        path = os.path.join(CELLS_DIR, celltype, f"sky130_fd_sc_hd__{drivename}__{corner_cell_tag}.lib.json")
        if not os.path.exists(path):
            missing.append(path)
            continue
        emit_cell_group(path, f"sky130_fd_sc_hd__{drivename}", "    ", out)
    out.append("}")
    return "\n".join(out) + "\n", missing

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("corner_file_tag", help="e.g. ss_100C_1v60 or ff_n40C_1v95_ccsnoise")
    ap.add_argument("lib_name", help="e.g. sky130_fd_sc_hd__ss_100C_1v60")
    ap.add_argument("cell_list_file", help="file with one 'type/drivename' per line, e.g. nand2/nand2_1")
    ap.add_argument("out_file")
    ap.add_argument("--cell-corner-tag", default=None, help="corner tag used in cell json filenames if different")
    args = ap.parse_args()
    cells = []
    for line in open(args.cell_list_file):
        line = line.strip()
        if not line:
            continue
        t, d = line.split("/")
        cells.append((t, d))
    text, missing = build_full_lib(args.corner_file_tag, args.lib_name, cells, args.cell_corner_tag)
    with open(args.out_file, "w") as f:
        f.write(text)
    print(f"wrote {args.out_file}, {len(cells)-len(missing)}/{len(cells)} cells found")
    if missing:
        print("MISSING:", file=sys.stderr)
        for m in missing:
            print(" ", m, file=sys.stderr)
