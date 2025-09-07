#!/usr/bin/env python3
# make_assembly_matrix.py
# Usage: python make_assembly_matrix.py tree_<19Jan2025>.txt ##change name of file to process accordingly.

import sys, re, os
from collections import defaultdict, Counter
from functools import lru_cache

try:
    import pandas as pd
except Exception as e:
    raise SystemExit("Please install pandas: pip install pandas") from e

# ---------------- Utilities ----------------

def normalize_instance_suffix(name: str) -> str:
    """Strip trailing 3-digit instance suffix (e.g., Body003 -> Body)."""
    name = name.strip()
    m = re.match(r"^(.*?)(\d{3})$", name)
    return m.group(1) if m else name

def compute_level(line: str) -> int:
    """Indent level from index of tree branch glyph (├ or └)."""
    idxs = [i for i in (line.find("├"), line.find("└")) if i >= 0]
    if not idxs:
        return 0
    idx = min(idxs)
    return ((idx - 1) // 4) + 1

def extract_name_and_type(line: str):
    """
    Return (name, kind) where kind in {'assembly', 'part', None}.
    - Skips 'Constraints'/'Configurations'
    - Skips 'Circular_*' containers (pattern features, not physical)
    - Assemblies: '=> Assembly' or ' (Assembly) @'
    - Parts: '=> Body'/'=> Part' or 'Name (Screw|Nut|Washer|...)'
    """
    stripped = line.strip()
    if stripped.endswith("Constraints") or stripped.endswith("Configurations"):
        return None, None

    m = re.search(r"[├└]─\s*(.*)$", stripped)
    content = m.group(1) if m else stripped

    # Top header form: "Something (Assembly) @ ..."
    if "(Assembly)" in content and "@" in content and "=>" not in content:
        name = content.split("(Assembly)")[0].strip()
        base = normalize_instance_suffix(name)
        if base.startswith("Circular_"):
            return None, None
        return base, "assembly"

    # Skip Circular_* containers
    lead = content.split("=>")[0].split("(")[0].strip()
    if lead.startswith("Circular_"):
        return None, None

    if "=> Assembly" in content:
        name = content.split("=> Assembly")[0].strip()
        return normalize_instance_suffix(name), "assembly"

    if "=> Body" in content or "=> Part" in content:
        name = content.split("=>")[0].strip()
        return normalize_instance_suffix(name), "part"

    if "(" in content and ")" in content:
        name = content.split("(")[0].strip()
        return normalize_instance_suffix(name), "part"

    return None, None

# ---------------- Parse tree ----------------

def parse_tree(lines):
    assembly_children_direct = defaultdict(Counter)   # asm -> Counter(item -> count); direct children only
    assembly_children_assemblies = defaultdict(Counter)  # asm -> Counter(subasm -> count)
    item_kinds = {}  # item -> 'assembly'/'part'
    stack = []       # stack of (assembly_name, level)

    for ln in lines:
        if not ln.strip():
            continue
        lvl = compute_level(ln)
        name, kind = extract_name_and_type(ln)

        # pop to current level
        while stack and stack[-1][1] >= lvl:
            stack.pop()

        if name is None:
            continue

        # record kind (prefer 'assembly' if both ever seen)
        if name in item_kinds:
            if item_kinds[name] != "assembly" and kind == "assembly":
                item_kinds[name] = "assembly"
        else:
            item_kinds[name] = kind or "part"

        if kind == "assembly":
            if stack:
                parent = stack[-1][0]
                assembly_children_direct[parent][name] += 1
                assembly_children_assemblies[parent][name] += 1
            stack.append((name, lvl))
        else:
            if stack:
                parent = stack[-1][0]
                assembly_children_direct[parent][name] += 1

    all_assemblies = sorted(
        set(assembly_children_direct.keys()) |
        {n for n,k in item_kinds.items() if k == "assembly"}
    )
    return assembly_children_direct, assembly_children_assemblies, item_kinds, all_assemblies

# ---------------- Build tables ----------------

def build_direct_children_df(assembly_children_direct, item_kinds, all_assemblies):
    all_items = sorted(item_kinds.keys())
    rows = []
    for item in all_items:
        row = {"Item": item, "Kind": item_kinds.get(item, "part")}
        for asm in all_assemblies:
            row[asm] = assembly_children_direct[asm].get(item, 0)
        rows.append(row)
    df = pd.DataFrame(rows)
    df["_k"] = df["Kind"].map({"assembly": 0, "part": 1}).fillna(1)
    df = df.sort_values(["_k", "Item"]).drop(columns=["_k"]).reset_index(drop=True)
    return df

def build_rollup_parts_df(assembly_children_direct, assembly_children_assemblies, item_kinds, all_assemblies):
    # direct parts only
    assembly_direct_parts = {
        asm: Counter({it:c for it,c in ctr.items() if item_kinds.get(it) != "assembly"})
        for asm, ctr in assembly_children_direct.items()
    }

    @lru_cache(maxsize=None)
    def rollup_parts_for(asm: str) -> Counter:
        total = Counter(assembly_direct_parts.get(asm, Counter()))
        for subasm, n in assembly_children_assemblies.get(asm, Counter()).items():
            child = rollup_parts_for(subasm)
            for it, c in child.items():
                total[it] += c * n
        return total

    all_parts = sorted([n for n,k in item_kinds.items() if k == "part"])
    rows = []
    for item in all_parts:
        row = {"Item": item}
        for asm in all_assemblies:
            row[asm] = rollup_parts_for(asm).get(item, 0)
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("Item").reset_index(drop=True)
    return df

# ---------------- Save ODS (with XLSX fallback) ----------------

def save_ods(dfs, out_path_ods, out_path_xlsx):
    try:
        from odf.opendocument import OpenDocumentSpreadsheet
        from odf.table import Table, TableRow, TableCell
        from odf.text import P

        doc = OpenDocumentSpreadsheet()
        for sheet_name, df in dfs.items():
            t = Table(name=str(sheet_name)[:31])
            # header
            tr = TableRow()
            for h in df.columns:
                c = TableCell(valuetype="string"); c.addElement(P(text=str(h))); tr.addElement(c)
            t.addElement(tr)
            # rows
            for _, r in df.iterrows():
                tr = TableRow()
                for h in df.columns:
                    v = r[h]
                    if isinstance(v, (int, float)) and pd.notna(v):
                        c = TableCell(valuetype="float", value=float(v))
                    else:
                        c = TableCell(valuetype="string"); c.addElement(P(text="" if pd.isna(v) else str(v)))
                    tr.addElement(c)
                t.addElement(tr)
            doc.spreadsheet.addElement(t)
        doc.save(out_path_ods)
        return out_path_ods
    except Exception:
        # Fallback to XLSX
        with pd.ExcelWriter(out_path_xlsx, engine="openpyxl") as w:
            for name, df in dfs.items():
                df.to_excel(w, sheet_name=name, index=False)
        return out_path_xlsx

# ---------------- Main ----------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python make_assembly_matrix.py tree_19Jan2025.txt")
        sys.exit(1)
    in_path = sys.argv[1]
    with open(in_path, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh]

    direct, subasms, kinds, assemblies = parse_tree(lines)
    df_direct = build_direct_children_df(direct, kinds, assemblies)
    df_rollup = build_rollup_parts_df(direct, subasms, kinds, assemblies)

    out_ods  = os.path.join(os.path.dirname(in_path) or ".", "assembly_matrix.ods")
    out_xlsx = os.path.join(os.path.dirname(in_path) or ".", "assembly_matrix.xlsx")
    saved = save_ods({"DirectChildren": df_direct, "RollupPartsOnly": df_rollup}, out_ods, out_xlsx)

    print("Wrote:", saved)
    print("Sheets:")
    print("  - DirectChildren (parts + assemblies, direct only)")
    print("  - RollupPartsOnly (parts only, includes nested sub-assemblies)")

if __name__ == "__main__":
    main()
