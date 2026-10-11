# Mapping from OGB-DC conventions to REopt.jl 1.0.0 inputs.
# Every REopt default that would silently change a benchmark result is overridden here,
# so the benchmark (not REopt's defaults) defines the case. Input names were checked
# against the REopt.jl 1.0.0 source on 2026-10-11.

const KWH_PER_MMBTU = 293.0711          # 1 MMBtu = 293.0711 kWh
const LB_PER_KG = 2.204623

"""
Natural gas in REopt's Generator.

REopt's Generator is written for diesel and counts fuel in gallons. We redefine one
"gallon" as one MMBtu (HHV). Then fuel_cost_per_gallon is \$/MMBtu,
annual_fuel_consumption_gal is MMBtu/yr, and the emissions factor is lb CO2 per MMBtu.
"""
function gas_generator(; max_kw, installed_cost_per_kw, om_cost_per_kw, om_cost_per_kwh,
                         heat_rate_mmbtu_per_mwh, fuel_usd_per_mmbtu, min_turn_down_fraction,
                         kgco2_per_mmbtu, analysis_years)
    eff = 3.412142 / heat_rate_mmbtu_per_mwh          # HHV electric efficiency
    Dict(
        "max_kw" => max_kw,
        "installed_cost_per_kw" => installed_cost_per_kw,
        "om_cost_per_kw" => om_cost_per_kw,
        "om_cost_per_kwh" => om_cost_per_kwh,
        "fuel_higher_heating_value_kwh_per_gal" => KWH_PER_MMBTU,
        "fuel_cost_per_gallon" => fuel_usd_per_mmbtu,
        "electric_efficiency_full_load" => eff,
        "electric_efficiency_half_load" => eff,        # constant heat rate -> no fuel intercept
        "min_turn_down_fraction" => min_turn_down_fraction,   # applies to the WHOLE fleet (one aggregate unit)
        "emissions_factor_lb_CO2_per_gal" => kgco2_per_mmbtu * LB_PER_KG,
        "only_runs_during_grid_outage" => false,
        # Off-grid default replaces generators in year 10 at full capital cost. Not in the spec.
        "replacement_year" => analysis_years,
        "replace_cost_per_kw" => 0.0,
    )
end

"""
Battery with a fixed duration and a target round-trip efficiency.
REopt's defaults cap power at 100 MW and energy at 1 GWh, which would silently
constrain L2/L3, and use a ~90 % round trip and 20 % minimum SOC.
"""
function battery(; installed_cost_per_kw, installed_cost_per_kwh, om_cost_per_kw,
                   duration_h, roundtrip_efficiency, soc_min, analysis_years)
    conv = 0.96                                         # inverter = rectifier efficiency
    # REopt has no ElectricStorage.om_cost_per_kw; fixed O&M is a fraction of total installed
    # cost (kW part + kWh part). With a fixed duration the conversion is exact:
    #   om_per_kw * kW == frac * (cost_kw * kW + cost_kwh * duration_h * kW)
    om_fraction = om_cost_per_kw / (installed_cost_per_kw + installed_cost_per_kwh * duration_h)
    Dict(
        "max_kw" => 1.0e7, "max_kwh" => 1.0e8,
        "min_duration_hours" => duration_h, "max_duration_hours" => duration_h,
        "installed_cost_per_kw" => installed_cost_per_kw,
        "installed_cost_per_kwh" => installed_cost_per_kwh,
        "om_cost_fraction_of_installed_cost" => om_fraction,
        "inverter_efficiency_fraction" => conv,
        "rectifier_efficiency_fraction" => conv,
        "internal_efficiency_fraction" => roundtrip_efficiency / conv^2,
        "soc_min_fraction" => soc_min,
        "replace_cost_per_kw" => 0.0, "replace_cost_per_kwh" => 0.0,
        "inverter_replacement_year" => analysis_years, "battery_replacement_year" => analysis_years,
    )
end

"Policy-neutral real-terms financials from cases.yaml: no tax, no escalation."
financial(; discount_rate, analysis_years) = Dict(
    "offtaker_discount_rate_fraction" => discount_rate,
    "owner_discount_rate_fraction" => discount_rate,
    "offtaker_tax_rate_fraction" => 0.0, "owner_tax_rate_fraction" => 0.0,
    "analysis_years" => analysis_years,
    "om_cost_escalation_rate_fraction" => 0.0,
    "generator_fuel_cost_escalation_rate_fraction" => 0.0,
    "elec_cost_escalation_rate_fraction" => 0.0,
)

"Single-threaded, seeded HiGHS so a rerun lands on the same solution (cases.yaml: solver)."
function configure_highs!(m; threads=1, random_seed=1234, mip_rel_gap=1e-5, time_limit_s=3600.0)
    set_optimizer_attribute(m, "threads", threads)
    set_optimizer_attribute(m, "random_seed", random_seed)
    set_optimizer_attribute(m, "mip_rel_gap", mip_rel_gap)
    set_optimizer_attribute(m, "time_limit", Float64(time_limit_s))
    set_optimizer_attribute(m, "output_flag", false)
    m
end

"Capital recovery factor."
crf(r, n) = r * (1 + r)^n / ((1 + r)^n - 1)
