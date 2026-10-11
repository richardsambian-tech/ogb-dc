# Stage 2 runbook: first end-to-end checks (target: done by 17 Oct 2026)

Each step has a pass condition. Record the result of each in `VERIFICATION_LOG.md`.

## 1. Python unit tests (no API keys)
    pip install -e ".[dev]"
    make test
Pass: `7 passed`. These prove the profile-unit fixes and the results parser on synthetic weather.

## 2. Julia environment
    make julia-setup            # installs REopt 1.0.0, JuMP, HiGHS; writes julia/Manifest.toml
Pass: `Pkg.status()` lists REopt v1.0.0. Commit `julia/Manifest.toml`.

## 3. REopt smoke test (placeholder costs)
    make smoke
Pass: every row of the comparison table has rel diff below ~2e-4, status optimal,
unserved energy within the allowance. Expected hand-calculation values:

| quantity | expected |
|---|---|
| gas capacity | ~50 MW |
| annual gas | ~4,335,766 MMBtu |
| lifecycle cost | ~279,017,628 USD |
| LCOE | ~54.67 USD/MWh |
| CO2 | ~230,056 t/yr |
| peak gas burn | ~495 MMBtu/h |

If LCC is off by a round factor, suspect a REopt default not yet overridden in `julia/ogb_mapping.jl`
(replacement year, tax, escalation). If REopt errors on an input name, check it against the
REopt.jl 1.0.0 docs and fix `ogb_mapping.jl`.

## 4. One real weather pull: TXA, 2012
    export NLR_DEVELOPER_API_KEY=...  NLR_DEVELOPER_EMAIL=...
    # temporarily limit fetch to one site-year, or let it run and stop after TXA 2012
    make fetch
    mkdir -p data/frozen/solar data/frozen/wind
    cp data/raw/solar/TXA_2012.csv data/frozen/solar/ && cp data/raw/wind/TXA_2012.srw data/frozen/wind/
    python scripts/make_profiles.py --sites TXA --years 2012
Pass: PV CF roughly 25-30 % (per kW_dc, 1-axis tracking, Amarillo); wind CF roughly 35-45 % at 100 m
with 10 % wake loss. Do not run `make freeze` yet: the dataset is frozen only after D4 and D15 close.

## 5. Close spec decisions D1-D3, D5, D10 and tag `v0.0.1-spec`.
