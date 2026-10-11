# ADR-0001: Adopt PyPSA as a reference model?

- Status: proposed (decision due **2026-11-30**)
- Deciders: Richard K. Sambian

## Context
REopt.jl 1.0.0 is the planned reference model for A1-A4. Architecture A5 (electrolyzer -> H2 storage ->
H2-capable turbine) may not be representable natively in REopt.jl. PyPSA 1.4.0 can express A5 with
Link/Store components. The question is whether PyPSA becomes a (or the) reference model for v0.1.

## Decision criteria (fixed before the prototype runs)
| # | Criterion | Threshold |
|---|---|---|
| C1 | REopt.jl v1.0 can represent A5 natively (electrolyzer, H2 store, H2 turbine) | yes / no — documented with input names |
| C2 | PyPSA reproduces REopt LCOE on L1-TXA-A1 from identical profiles and costs | within 2 % |
| C3 | PyPSA solves L1-TXA-A5 with HiGHS | < 30 min on the development machine |
| C4 | Maintenance burden (lines of glue code, dependency count) | qualitative |

## Evidence
_To be filled from the two-case prototype (L1-TXA-A1, L1-TXA-A5) during 17-28 Nov 2026._

## Decision options
- **Go:** PyPSA is the reference model for all 180 cases; REopt.jl is the cross-check for A1-A4.
- **No-go:** REopt.jl is the reference model; A5 ships in v0.1 as defined-but-unsolved with a plan.
- **Hybrid:** REopt.jl for A1-A4, PyPSA for A5 only, with the C2 agreement table published.

## Decision
_Pending._

## Consequences
_Pending._
