PY ?= python
REF ?= results/v0.1/results.csv
NEW ?= results/latest/results.csv

.PHONY: cases fetch freeze verify-data profiles solve compare ci-subset test julia-setup smoke clean

cases:            ## expand cases.yaml -> results/cases_expanded.csv (must be 180 rows)
	$(PY) scripts/expand_cases.py

fetch:            ## download NSRDB + WIND Toolkit files into data/raw (needs NLR_DEVELOPER_API_KEY)
	$(PY) scripts/fetch_resources.py

freeze:           ## copy raw downloads into data/frozen and (re)write MANIFEST.sha256
	mkdir -p data/frozen/solar data/frozen/wind
	cp data/raw/solar/*.csv data/frozen/solar/ && cp data/raw/wind/*.srw data/frozen/wind/
	$(PY) scripts/verify_manifest.py --write

verify-data:      ## check every frozen file against MANIFEST.sha256
	$(PY) scripts/verify_manifest.py

profiles: verify-data   ## PySAM per-unit PV and wind profiles
	$(PY) scripts/make_profiles.py

solve: cases profiles   ## reference model over all cases
	mkdir -p results/latest
	julia --project=julia julia/run_reopt.jl results/cases_expanded.csv $(NEW)

compare:          ## diff a fresh run against the committed reference within cases.yaml tolerances
	$(PY) scripts/compare_results.py $(REF) $(NEW)

ci-subset:        ## write the 6-case subset (cases.yaml: verification.ci_subset) -> results/cases_ci.csv
	$(PY) scripts/expand_cases.py --subset ci
	@echo "solving the subset is wired in once julia/run_reopt.jl maps all of A1-A4 (stage 3)"

test:             ## unit tests: profile units/ranges, results parsing (no API keys needed)
	$(PY) -m pytest -q tests

julia-setup:      ## install the pinned Julia environment and write julia/Manifest.toml (commit it)
	julia --project=julia -e 'using Pkg; Pkg.instantiate(); Pkg.status()'

smoke:            ## stage-2 check: REopt.jl solves L1-TXA-A1 and matches the hand calculation
	julia --project=julia julia/smoke_test.jl

clean:
	rm -rf results/latest results/smoke profiles/*.csv
