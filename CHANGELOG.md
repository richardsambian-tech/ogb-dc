# Changelog

All notable changes to this project are documented here. Format follows Keep a Changelog; versions follow SemVer.
Data changes are versioned separately in `data/frozen/README.md`.

## [Unreleased]
### Added
- Repository skeleton, `cases.yaml` v0.1 draft (180 cases), results template and schema.
- Scripts: expand_cases, fetch_resources, make_profiles, verify_manifest, compare_results.
- ADR-0001 (PyPSA go/no-go, due 2026-11-30) opened.

### Fixed (2026-10-11)
- `make_profiles.py`: PV capacity factor was divided by 1000 (PySAM `gen` is already kW); profiles were ~1000x too small and hidden by clipping.
- `make_profiles.py`: wind used PySAM's default 1.5 MW power curve while dividing by 3000 kW; a 3 MW curve is now built from `cases.yaml`.
- `make_profiles.py`: `wake_int_loss` is ignored for a single turbine, so the spec's 10 % wake loss was never applied; now applied via `wake_ext_loss`.
- `make_profiles.py`: PySAM's default wind losses (~16 %) were applied silently; all zeroed, spec losses only.
- `make_profiles.py`: out-of-range or wrong-length profiles now raise instead of being clipped.
- `compare_results.py`: crashed on any file with `#` provenance lines; now parses them, skips `not_run`, reports status changes.
- `julia/Project.toml`: placeholder UUIDs (REopt, project) replaced with verified ones.
- Removed committed `__pycache__` (built with Python 3.14, outside the pinned range).

### Fixed (2026-10-11, review)
- `cases.yaml`: NSRDB endpoint `psm3-2-2-download` is deprecated and no longer listed; replaced with
  `nsrdb-GOES-aggregated-v4-0-0-download` (PSM v4 aggregated, 4 km, 1998 onwards).
- `julia/ogb_mapping.jl`: `ElectricStorage.om_cost_per_kw` is not a REopt.jl input; mapped to
  `om_cost_fraction_of_installed_cost` (exact under the fixed battery duration).

### Added (2026-10-11)
- `tests/` with synthetic weather files: regression tests for every fix above (`make test`, also in CI).
- `julia/ogb_mapping.jl`: OGB-DC -> REopt.jl 1.0.0 mapping that overrides defaults which would change results
  (off-grid generator replacement in year 10, 100 MW / 1 GWh battery caps, 90 % round trip, 20 % SOC floor,
  26 % tax, cost escalation, 10 % operating reserve, SOC incentive in the objective). Natural gas mapped as "1 gallon = 1 MMBtu".
- `julia/smoke_test.jl` (`make smoke`): solves L1-TXA-A1 with placeholder costs and compares to a hand calculation.
- `cases.yaml`: `solver` section; wind `rotor_diameter_m`, `power_curve`, `other_losses_pct` (all proposed).
- `make ci-subset` writes the 6-case list; SPEC open decisions D10-D17.

## [0.1.0] - 2026-12-TBD
_Inputs frozen; results preliminary._
