#!/usr/bin/env python3
"""Check (or write, with --write) SHA-256 hashes for every file under data/frozen/."""
import hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FROZEN, MANIFEST = ROOT / "data/frozen", ROOT / "data/frozen/MANIFEST.sha256"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(): return sorted(p for p in FROZEN.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256" and p.name != "README.md")

if "--write" in sys.argv:
    MANIFEST.write_text("".join(f"{sha(p)}  {p.relative_to(FROZEN)}\n" for p in files()))
    print(f"wrote {MANIFEST} ({len(files())} files)"); sys.exit(0)

expected = {l.split("  ", 1)[1].strip(): l.split("  ", 1)[0] for l in MANIFEST.read_text().splitlines() if l.strip()}
bad = [str(p.relative_to(FROZEN)) for p in files() if expected.get(str(p.relative_to(FROZEN))) != sha(p)]
missing = [k for k in expected if not (FROZEN / k).exists()]
if bad or missing:
    print("MANIFEST MISMATCH\n  changed/unlisted:", bad, "\n  missing:", missing); sys.exit(1)
print(f"frozen dataset verified: {len(expected)} files match MANIFEST.sha256")
