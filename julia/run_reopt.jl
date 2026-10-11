# Reference-model driver (REopt.jl 1.0.0) for architectures A1-A4.  STAGE 3 - not yet complete.
# Run `make smoke` first: julia/smoke_test.jl proves the mapping on one case.
# When filled in, build every scenario with the helpers in julia/ogb_mapping.jl so REopt's
# defaults never leak into benchmark results.
# Usage: julia --project=julia julia/run_reopt.jl results/cases_expanded.csv results/<run>/results.csv
# Reads PySAM profiles from profiles/ so every model sees identical resource data.
using REopt, JuMP, HiGHS, CSV, DataFrames, JSON

cases_path, out_path = ARGS[1], ARGS[2]
cases = CSV.read(cases_path, DataFrame)

function build_scenario(row)
    # TODO: map cases.yaml -> REopt inputs (off-grid, Generator, ElectricStorage, PV, Wind,
    # production_factor_series from profiles/{site}_{year}_{pv,wind}.csv).
    Dict("Site" => Dict("latitude" => row.lat, "longitude" => row.lon),
         "Settings" => Dict("off_grid_flag" => true),
         "ElectricLoad" => Dict("loads_kw" => fill(row.facility_mw * 1000.0, 8760)))
end

results = DataFrame()
for row in eachrow(cases)
    occursin("electrolyzer", row.components) && continue   # A5 handled per ADR-0001
    m = Model(HiGHS.Optimizer)
    r = run_reopt(m, build_scenario(row))
    # TODO: extract lcoe, npv, unserved energy, emissions, peak gas burn into the template columns
    push!(results, (case_id = row.case_id,), cols = :union)
end
CSV.write(out_path, results)
