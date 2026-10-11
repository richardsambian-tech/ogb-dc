#!/usr/bin/env python3
"""Expand cases.yaml into the flat 180-row case list (cases_expanded.csv).

Usage:  python scripts/expand_cases.py [--out results/cases_expanded.csv] [--subset ci]
        --subset ci writes only the 6 cases in verification.ci_subset (default out: results/cases_ci.csv)
Exits non-zero if the grid does not contain exactly 3 x 12 x 5 = 180 cases.
"""
import argparse, csv, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load_spec(path=ROOT / "cases.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def expand(spec):
    rows = []
    for L in spec["loads"]["items"]:
        for S in spec["sites"]["items"]:
            for A in spec["architectures"]["items"]:
                rows.append({
                    "case_id": f'{L["id"]}-{S["id"]}-{A["id"]}',
                    "load_id": L["id"], "facility_mw": L["facility_mw"],
                    "site_id": S["id"], "site_name": S["name"], "state": S["state"],
                    "lat": S["lat"], "lon": S["lon"],
                    "arch_id": A["id"], "arch_name": A["name"],
                    "components": "+".join(A["components"]),
                    "benchmark_year": spec["time"]["benchmark_year"],
                })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--subset", choices=["ci"], default=None)
    a = ap.parse_args()
    a.out = a.out or ROOT / "results" / ("cases_ci.csv" if a.subset else "cases_expanded.csv")
    spec = load_spec()
    rows = expand(spec)
    nL, nS, nA = (len(spec[k]["items"]) for k in ("loads", "sites", "architectures"))
    expected = nL * nS * nA
    ids = [r["case_id"] for r in rows]
    assert len(set(ids)) == len(ids), "duplicate case IDs"
    for cid in spec["verification"]["ci_subset"]:
        assert cid in ids, f"ci_subset case {cid} not in grid"
    if len(rows) != 180:
        print(f"WARNING: expected 180 cases, got {len(rows)}", file=sys.stderr); sys.exit(1)
    if a.subset == "ci":
        keep = set(spec["verification"]["ci_subset"])
        rows = [r for r in rows if r["case_id"] in keep]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    label = "ci subset" if a.subset else f"{nL} loads x {nS} sites x {nA} architectures"
    print(f"{len(rows)} cases ({label}) -> {a.out}")

if __name__ == "__main__":
    main()
