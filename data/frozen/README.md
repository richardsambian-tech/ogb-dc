# Frozen input dataset

**Dataset version:** 0.1 (not yet frozen) — **Dataset DOI:** 10.5281/zenodo.TODO

"Frozen" means: (1) every file is listed with its SHA-256 in `MANIFEST.sha256`; (2) the same files are
deposited on Zenodo as a dataset record separate from the code; (3) any change creates a new dataset
version and DOI, recorded below. Files here are never edited in place.

| Layer | Files | Source (URL, retrieval date) |
|---|---|---|
| Technology cost & performance | `atb/2025_v1_Workbook_08-27-2026.xlsx`, `atb/2025_v1_Model_Parameters_08-27-2026.csv`, `atb/atb2025_extract.csv` | https://data.openei.org/submissions/8759 — retrieved TODO |
| Solar resource | `solar/{site}_{year}.csv` (SAM CSV, hourly, UTC) | NSRDB via developer.nlr.gov — retrieved TODO |
| Wind resource | `wind/{site}_{year}.srw` (SAM SRW, 100 m) | WIND Toolkit via developer.nlr.gov — retrieved TODO |
| Fuel prices | `fuel/eia_gas_prices_by_state.csv` | EIA API v2, series per `cases.yaml` — retrieved TODO |
| Emissions factors | `emissions/factors.csv` | EPA GHG Emission Factors Hub — vintage TODO |
| Site grid points | `site_gridpoints.csv` | coordinates actually returned by NSRDB / WTK for each site |

## Dataset version history

| Version | Date | DOI | Change |
|---|---|---|---|
| 0.1 | 2026-10-TBD | TODO | initial freeze |
