# Stage-2 smoke test: does REopt.jl 1.0.0 solve one off-grid OGB-DC case, and does it agree
# with a hand calculation?
#
#   julia --project=julia julia/smoke_test.jl
#
# Case: L1-TXA-A1 (50 MW flat facility load, Amarillo, gas turbines only), benchmark year 2012.
#
# !!! The cost and price numbers below are SMOKE-TEST PLACEHOLDERS, not benchmark inputs. !!!
# They exist only to check the plumbing. Real values come from the frozen ATB 2025 / EIA files.
#
# Why gas-only first: with a flat load and a constant heat rate the optimal answer can be worked
# out by hand, so any disagreement points to a mapping error rather than to the optimizer.

using REopt, JuMP, HiGHS, CSV, DataFrames, Dates
include(joinpath(@__DIR__, "ogb_mapping.jl"))

# ---- case inputs (from cases.yaml where they exist) -----------------------------------------
const LOAD_KW        = 50_000.0     # loads.L1.facility_mw
const LAT, LON       = 35.22, -101.83   # sites.TXA
const MIN_LOAD_MET   = 0.9999       # constraints.reliability: 1 - max_unserved_energy_fraction
const DISCOUNT, YEARS = 0.07, 25    # financials
const KGCO2          = 53.06        # resources.emissions_factors.natural_gas_kgco2_per_mmbtu
const MIN_TURNDOWN   = 0.30         # technologies.gas_turbine.min_load_fraction

# ---- placeholders (NOT benchmark values) ----------------------------------------------------
const CAPEX_PER_KW   = 1300.0       # $/kW
const FOM_PER_KW     = 20.0         # $/kW-yr
const VOM_PER_KWH    = 0.005        # $/kWh  (= $5/MWh)
const HEAT_RATE      = 9.9          # MMBtu/MWh, HHV
const GAS_PRICE      = 3.50         # $/MMBtu

scenario = Dict(
    "Settings" => Dict("off_grid_flag" => true, "add_soc_incentive" => false, "solver_name" => "HiGHS"),
    "Site" => Dict("latitude" => LAT, "longitude" => LON),
    "ElectricLoad" => Dict(
        "loads_kw" => fill(LOAD_KW, 8760),
        "year" => 2012,
        "min_load_met_annual_fraction" => MIN_LOAD_MET,
        # REopt off-grid default holds 10 % operating reserve every hour. The spec handles
        # redundancy as N+1 after the solve instead, so reserves are off here (SPEC D14).
        "operating_reserve_required_fraction" => 0.0,
    ),
    "Financial" => financial(discount_rate=DISCOUNT, analysis_years=YEARS),
    "Generator" => gas_generator(max_kw=2 * LOAD_KW, installed_cost_per_kw=CAPEX_PER_KW,
        om_cost_per_kw=FOM_PER_KW, om_cost_per_kwh=VOM_PER_KWH, heat_rate_mmbtu_per_mwh=HEAT_RATE,
        fuel_usd_per_mmbtu=GAS_PRICE, min_turn_down_fraction=MIN_TURNDOWN,
        kgco2_per_mmbtu=KGCO2, analysis_years=YEARS),
    # A1 is gas-only. PV, Wind and ElectricStorage are simply left out: REopt then builds none.
    # (Including "PV" with max_kw = 0 would still make REopt call the PVWatts web API.)
)

m = configure_highs!(Model(HiGHS.Optimizer))
t0 = time()
r = run_reopt(m, scenario)
solve_s = time() - t0

# ---- extract in benchmark units --------------------------------------------------------------
status      = r["status"]
gen_kw      = r["Generator"]["size_kw"]
fuel_mmbtu  = r["Generator"]["annual_fuel_consumption_gal"]        # "gal" == MMBtu by construction
gen_series  = r["Generator"]["electric_to_load_series_kw"]
load_met    = r["ElectricLoad"]["offgrid_load_met_fraction"]
lcc         = r["Financial"]["lcc"]
annual_mwh  = LOAD_KW * 8760 / 1000
served_mwh  = annual_mwh * load_met
unserved    = annual_mwh - served_mwh
lcoe        = lcc * crf(DISCOUNT, YEARS) / served_mwh
co2_t       = fuel_mmbtu * KGCO2 / 1000
peak_burn   = maximum(gen_series) / 1000 * HEAT_RATE

# ---- hand calculation (what the answer must be) ----------------------------------------------
# Flat load, constant heat rate: build ~load, run flat out; the 0.01 % unserved allowance can shave
# at most 0.01 % off size and energy, so expect agreement to ~0.02 %.
h_energy = annual_mwh * MIN_LOAD_MET
h_fuel   = h_energy * HEAT_RATE
h_annual = LOAD_KW * FOM_PER_KW + h_energy * 1000 * VOM_PER_KWH + h_fuel * GAS_PRICE
h_lcc    = LOAD_KW * CAPEX_PER_KW + h_annual * (1 - (1 + DISCOUNT)^-YEARS) / DISCOUNT
h_lcoe   = h_lcc * crf(DISCOUNT, YEARS) / h_energy

println("\nOGB-DC smoke test  L1-TXA-A1  (placeholder costs)  status = $status  solve = $(round(solve_s, digits=1)) s\n")
println(rpad("quantity", 30), rpad("REopt", 18), rpad("hand calc", 18), "rel diff")
for (name, a, b) in [("gas capacity [MW]", gen_kw / 1000, LOAD_KW / 1000),
                     ("annual gas [MMBtu]", fuel_mmbtu, h_fuel),
                     ("lifecycle cost [USD]", lcc, h_lcc),
                     ("LCOE [USD/MWh]", lcoe, h_lcoe),
                     ("CO2 [t/yr]", co2_t, h_fuel * KGCO2 / 1000),
                     ("peak gas burn [MMBtu/h]", peak_burn, LOAD_KW / 1000 * HEAT_RATE)]
    println(rpad(name, 30), rpad(round(a, sigdigits=8), 18), rpad(round(b, sigdigits=8), 18),
            round(abs(a - b) / abs(b), sigdigits=3))
end
println("\nunserved energy: $(round(unserved, digits=3)) MWh  (allowance $(round(annual_mwh * (1 - MIN_LOAD_MET), digits=3)) MWh)")
println("N+1 redundancy is NOT included above (post-solve rule, unit size still open: SPEC D12).")

# ---- write a template-shaped row so make compare can be exercised ---------------------------
out = joinpath(@__DIR__, "..", "results", "smoke", "L1-TXA-A1.csv")
mkpath(dirname(out))
open(out, "w") do io
    println(io, "# model_name=REopt.jl")
    println(io, "# model_version=", pkgversion(REopt))
    println(io, "# solver_name=HiGHS")
    println(io, "# solver_version=", pkgversion(HiGHS))
    sha = try strip(read(`git rev-parse --short HEAD`, String)) catch; "not-a-git-checkout" end
    println(io, "# git_sha=", sha)
    println(io, "# dataset_doi=PLACEHOLDER-COSTS")
    println(io, "# run_timestamp_utc=", Dates.format(now(UTC), "yyyy-mm-ddTHH:MM:SSZ"))
    println(io, "case_id,lcoe_usd_per_mwh,npv_cost_usd,unserved_energy_mwh,unserved_energy_fraction,co2_tonnes_per_year,peak_gas_burn_mmbtu_per_h,gas_capacity_mw,annual_gas_mmbtu,solve_time_s,status")
    println(io, join(["L1-TXA-A1", lcoe, lcc, unserved, unserved / annual_mwh, co2_t, peak_burn,
                      gen_kw / 1000, fuel_mmbtu, solve_s, lowercase(string(status))], ","))
end
println("wrote $out")
