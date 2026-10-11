#!/usr/bin/env python3
"""Compare a fresh results file with the committed reference using cases.yaml tolerances.

Usage: python scripts/compare_results.py results/v0.1/results.csv results/latest/results.csv

Results files start with '# key=value' provenance lines, then a normal CSV header and rows.
Cases whose reference status is not_run are skipped; a status change is reported as a mismatch.
Exit code 0 = every reference case reproduces within tolerance, 1 = mismatches, 2 = bad input.
"""
import csv, io, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def read_results(path):
    """Return (provenance dict, {case_id: row}) from a results CSV with '#' header lines."""
    provenance, body = {}, []
    for line in Path(path).read_text().splitlines():
        if line.startswith("#"):
            key, _, val = line.lstrip("#").strip().partition("=")
            if key:
                provenance[key.strip()] = val.strip()
        elif line.strip():
            body.append(line)
    if not body:
        raise ValueError(f"{path}: no CSV header found")
    rows = list(csv.DictReader(io.StringIO("\n".join(body))))
    if rows and "case_id" not in rows[0]:
        raise ValueError(f"{path}: no case_id column")
    return provenance, {r["case_id"]: r for r in rows}


def within(a, b, tol):
    if "abs" in tol:
        return abs(a - b) <= tol["abs"]
    return abs(a - b) <= tol["rel"] * max(abs(a), 1e-9)


def compare(ref, new, tolerances):
    fails, skipped = [], 0
    for cid, r in ref.items():
        n = new.get(cid)
        if n is None:
            fails.append((cid, "missing", "", "")); continue
        rs, ns = r.get("status", "").strip(), n.get("status", "").strip()
        if rs == "not_run":
            skipped += 1; continue
        if rs and ns and rs != ns:
            fails.append((cid, "status", rs, ns)); continue
        for col, tol in tolerances.items():
            try:
                a, b = float(r[col]), float(n[col])
            except (KeyError, ValueError):
                fails.append((cid, col, r.get(col, ""), n.get(col, ""))); continue
            if not within(a, b, tol):
                fails.append((cid, col, a, b))
    return fails, skipped


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print(__doc__); return 2
    tol = yaml.safe_load(open(ROOT / "cases.yaml"))["verification"]["tolerance"]
    try:
        (_, ref), (prov, new) = read_results(argv[0]), read_results(argv[1])
    except ValueError as e:
        print(f"ERROR: {e}"); return 2
    fails, skipped = compare(ref, new, tol)
    if prov:
        print("new run:", ", ".join(f"{k}={v}" for k, v in prov.items() if v))
    if fails:
        print(f"{len(fails)} mismatches ({skipped} not_run cases skipped):")
        for f in fails[:50]:
            print("  ", *f)
        return 1
    print(f"all {len(ref) - skipped} compared cases reproduce within tolerance ({skipped} not_run skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
