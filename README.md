# OGB-DC: Off-Grid Benchmark for Data Center Power

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.TODO.svg)](https://doi.org/10.5281/zenodo.TODO) <!-- minted at v0.1 -->

A fixed set of reference cases for self-supplied (off-grid) data-center power:
**3 load sizes x 12 U.S. sites x 5 supply architectures = 180 cases**, from gas-only
to solar + wind + battery + hydrogen-capable turbines. All inputs come from open
federal sources (NLR Electricity ATB, NSRDB, WIND Toolkit, EIA fuel prices) and are
frozen with SHA-256 hashes and a dataset DOI so that anyone can run their own model
on the same cases and report results in the same template.

Outputs per case: **cost (LCOE, NPV), unserved energy, emissions, peak gas burn.**

| Release | Date | Contents |
|---|---|---|
| v0.1 | Dec 2026 | Frozen inputs, case definitions, preliminary results from the reference model |
| v1.0 | Mar 2027 | Final cases, dataset DOI, results DOI, cross-model comparison, paper |

## Repository layout

```
cases.yaml                 single source of truth: loads, sites, architectures, outputs, tolerances
SPEC.md                    human-readable specification and open decisions
data/frozen/               frozen inputs + MANIFEST.sha256 (never edited in place; new version = new DOI)
data/raw/                  API downloads before freezing (git-ignored)
profiles/                  PySAM per-unit PV and wind capacity-factor profiles
results/results_template.csv   the template every participating model fills in
results/results_schema.json    column definitions and units
results/v0.1/              committed reference results for clean-run comparison
scripts/                   expand_cases, fetch_resources, make_profiles, verify_manifest, compare_results
julia/                     REopt.jl environment (Project.toml + Manifest.toml)
docs/decisions/            architecture decision records (ADR), incl. the 30 Nov PyPSA decision
VERIFICATION_LOG.md        every clean-run reproduction, dated and signed
```

## Quick start (clean run)

```bash
git clone https://github.com/<org>/ogb-dc && cd ogb-dc
python -m venv .venv && source .venv/bin/activate
pip install -e .                      # pinned in pyproject.toml / requirements.lock
make verify-data                      # hashes in data/frozen must match MANIFEST.sha256
make cases                            # expands cases.yaml -> results/cases_expanded.csv (180 rows)
make profiles                         # PySAM PV + wind profiles for every site-year
make solve                            # reference model over all cases -> results/<run>/results.csv
make compare REF=results/v0.1/results.csv NEW=results/<run>/results.csv
```

Fetching resource data from scratch (only needed to rebuild `data/frozen`):

```bash
export NLR_DEVELOPER_API_KEY=...  NLR_DEVELOPER_EMAIL=...   # free key at developer.nlr.gov
export EIA_API_KEY=...                                       # free key at api.eia.gov
make fetch && make freeze
```

## Submitting results from your own model

1. Run the 180 cases in `results/cases_expanded.csv` using only inputs from `data/frozen/`.
2. Fill `results/results_template.csv`; keep the provenance header rows.
3. Open a pull request adding `results/community/<model>_<version>.csv`.

## Toolchain pins

| Tool | Version | Role |
|---|---|---|
| nlr-pysam | 8.0.0 | resource -> production profiles (PVWatts v8, Windpower) |
| REopt.jl | 1.0.0 | sizing and dispatch, architectures A1-A4 (A5 pending ADR-0001) |
| PyPSA | 1.4.0 | candidate reference model; go/no-go 30 Nov 2026 (ADR-0001) |
| HiGHS | pinned via lockfiles | open-source LP/MILP solver |

## Citation

See `CITATION.cff`. Cite the code DOI, the dataset DOI, and (from v1.0) the results DOI.

## License

Code: MIT (`LICENSE`). Data and documentation: CC-BY-4.0 (`LICENSE-DATA`).
Upstream data remain subject to their original terms (NLR ATB disclaimer, NSRDB/WIND Toolkit, EIA).
