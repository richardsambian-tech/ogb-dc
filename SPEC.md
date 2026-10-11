# OGB-DC Specification v0.1 (DRAFT)

Status: draft, 10 Oct 2026. Target: tag `v0.0.1-spec` by 17 Oct 2026.
Machine-readable twin: `cases.yaml`. If the two disagree, `cases.yaml` wins and this file is wrong.

## 1. Purpose

Provide a fixed, open, reproducible set of cases on which any energy-system model can be run
and compared for self-supplied data-center power. The benchmark fixes the *questions* and
the *inputs*; it does not fix the model.

## 2. Case grid

- Loads: L1 50 MW, L2 200 MW, L3 500 MW facility load, flat, PUE 1.20.
- Sites: 12 U.S. locations (see `cases.yaml: sites`).
- Architectures: A1 gas-only; A2 gas + battery; A3 gas + PV + battery; A4 gas + PV + wind + battery;
  A5 PV + wind + battery + electrolyzer + H2 storage + H2-capable turbine.
- Case ID: `{load}-{site}-{arch}`, e.g. `L2-IAD-A4`. Total 180.

## 3. Time basis

Hourly, UTC, no leap day (8760 h). Weather years 2007-2013; v0.1 solves the single benchmark year 2012;
v1.0 adds multi-year runs.

## 4. Inputs (frozen)

| Layer | Source | Vintage |
|---|---|---|
| Technology cost/performance | NLR Electricity ATB | 2025 v1, files dated 2026-08-27, Moderate scenario, 2030 cost year |
| Solar resource | NSRDB PSM, hourly | 2007-2013, 12 points |
| Wind resource | WIND Toolkit, 100 m hub, SRW | 2007-2013, 12 points |
| Fuel | EIA state natural-gas prices (industrial) | base year 2025, band 0.5x-1.5x |
| Emissions factors | EPA stationary combustion | see `cases.yaml` |
| Financials | policy-neutral: 7 % real, 25 yr, no tax/ITC/PTC, carbon price 0 | — |

## 5. Constraints

Reliability is a hard constraint: unserved energy <= 0.01 % of annual load. Gas turbines carry N+1
redundancy applied after sizing. No land or interconnection limits in v0.1.

## 6. Required outputs

`lcoe_usd_per_mwh`, `npv_cost_usd`, `unserved_energy_mwh`, `unserved_energy_fraction`,
`co2_tonnes_per_year`, `peak_gas_burn_mmbtu_per_h`, plus provenance header fields.
See `results/results_schema.json`.

## 7. Open decisions (close before `v0.0.1-spec` unless a later date is given)

| # | Decision | Proposed default | Owner | Due |
|---|---|---|---|---|
| D1 | Load sizes and PUE | 50/200/500 MW, PUE 1.20, flat | RKS | 17 Oct |
| D2 | Final 12 sites and exact grid-point coordinates | list in `cases.yaml` | RKS | 17 Oct |
| D3 | Gas unit type for A1-A4 (simple cycle vs combined cycle at L3) | simple cycle, aeroderivative | RKS | 17 Oct |
| D4 | Weather years (2007-2013 WTK overlap vs WTK-LED newer years) | 2007-2013 | RKS | 24 Oct |
| D5 | Reliability: hard constraint vs reported; threshold | hard, 0.01 % | RKS | 17 Oct |
| D6 | A5 hydrogen sourcing: on-site only vs purchased H2; gas backup allowed? | on-site only, gas backup allowed | RKS | 24 Oct |
| D7 | Electrolyzer / H2 storage cost source (not in ATB) | DOE Hydrogen Program record (TBD) | RKS | 31 Oct |
| D8 | ATB scenario and cost year | Moderate, 2030 | RKS | 24 Oct |
| D9 | PyPSA go/no-go | see ADR-0001 | RKS | 30 Nov |
| D10 | PV tilt with 1-axis tracking: `tilt_deg: latitude` contradicts `array_type: 2` (tracker axes are usually horizontal) | tilt 0 | RKS | 17 Oct |
| D11 | Dollar-year basis: ATB 2025 dollar year, EIA nominal 2025 prices and `currency_year: 2024` must be put on one basis | state the deflator series and convert everything to one year | RKS | 24 Oct |
| D12 | N+1: gas unit size (needed to add "one unit"), and whether the N+1 capital cost is inside LCOE/NPV | include in LCOE/NPV; unit size from ATB reference CT | RKS | 24 Oct |
| D13 | Solver determinism and tolerances: MILP gap vs 0.1 % tolerance; `unserved_energy_mwh: abs 0.0` is tighter than LP feasibility noise | threads 1, seed fixed, `mip_rel_gap` 1e-5 (now in `cases.yaml: solver`); unserved tolerance abs 1 MWh | RKS | 24 Oct |
| D14 | Operating reserves: REopt off-grid default holds 10 % reserve every hour; spec is silent | 0 % (redundancy handled by N+1), stated explicitly for all models | RKS | 24 Oct |
| D15 | Wind losses beyond wake: PySAM defaults silently add ~16 %; now zeroed and exposed as `other_losses_pct` (0 for now) | align with ATB 2025 land-based wind loss assumption | RKS | 24 Oct |
| D16 | Gas fleet representation: REopt models all turbines as one aggregate unit, so `min_load_fraction` 0.30 applies to the whole fleet, not per unit | accept for v0.1, document as a model difference; PyPSA could commit units individually | RKS | 30 Nov |
| D17 | EIA series IDs in `cases.yaml` use the API v1 form (`NG.N3035TX3.A`); API v2 uses a route plus a series facet, and some state industrial prices are withheld | rewrite as v2 route + facet; define a fallback for withheld years | RKS | 31 Oct |

## 8. Verification

Every number in a tagged release must have been reproduced from a fresh clone using only committed
lockfiles and `data/frozen`. See `VERIFICATION_LOG.md` and `make compare`.
