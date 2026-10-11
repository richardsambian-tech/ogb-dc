# Verification log

Rule: nothing is tagged or merged to `main` until the lead developer has reproduced it from a fresh clone
using only committed lockfiles and `data/frozen`. Claude drafts code and tests; this log records the human check.

| Date (UTC) | Git SHA | Dataset version | Machine / OS | Scope | `make verify-data` | `make compare` | Verified by | Notes |
|---|---|---|---|---|---|---|---|---|
| 2026-10-11 | c336b86 | none (placeholder costs) | Windows 11, Julia 1.13.1, Python 3.13.16 | Stage 2: unit tests (7 passed) + REopt smoke test L1-TXA-A1 | n/a (no frozen data yet) | n/a (smoke test compared to hand calc: all within 1e-4) | RKS | REopt 1.0.0 + HiGHS 1.26.0 pinned in julia/Manifest.toml. Unserved energy exactly at allowance (43.8 MWh); see D13, D18. |