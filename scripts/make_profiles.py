#!/usr/bin/env python3
"""Generate per-unit PV and wind capacity-factor profiles with PySAM.

Reads frozen weather files from data/frozen/{solar,wind}; writes
profiles/{site}_{year}_pv.csv and profiles/{site}_{year}_wind.csv (8760 rows, 0..1).

Definitions (these are what every model in the benchmark consumes):
  PV   cf[h] = AC output [kW] of a 1 kW_dc system   (per kW_dc, the REopt PV convention)
  Wind cf[h] = output [kW] of one turbine / turbine rating [kW]

Deterministic: identical inputs give identical outputs; a short hash of each file is printed.
Values outside [0, 1] or a wrong length raise an error instead of being clipped, so unit
mistakes fail loudly.

Usage:
  python scripts/make_profiles.py                       # all sites x all weather years
  python scripts/make_profiles.py --sites TXA --years 2012
Install:  pip install nlr-pysam==8.0.0
"""
import argparse, hashlib, sys, warnings
from pathlib import Path
import yaml
import PySAM.Pvwattsv8 as Pvwatts
import PySAM.Windpower as Windpower

ROOT = Path(__file__).resolve().parents[1]
HOURS = 8760
TRACKING_ARRAY_TYPES = {2, 3, 4}   # PVWatts: 2 = 1-axis, 3 = backtracking, 4 = 2-axis


def check_profile(values, label):
    """Fail loudly on wrong length or out-of-range values (no silent clipping)."""
    if len(values) != HOURS:
        raise ValueError(f"{label}: expected {HOURS} hourly values, got {len(values)}")
    lo, hi = min(values), max(values)
    # PVWatts can report tiny negative night-time values (inverter tare losses): allow -1e-3.
    if lo < -1e-3 or hi > 1.0 + 1e-6:
        raise ValueError(f"{label}: capacity factor out of range [{lo:.6f}, {hi:.6f}] - check units")
    return [min(max(v, 0.0), 1.0) for v in values]   # only removes floating-point noise


def pv_profile(weather_file, lat, p):
    """Per-kW_dc hourly AC output for the PV design in cases.yaml technologies.pv."""
    pv = Pvwatts.default("PVWattsNone")
    pv.SolarResource.solar_resource_file = str(weather_file)
    pv.SystemDesign.system_capacity = 1.0            # kW_dc
    pv.SystemDesign.dc_ac_ratio = p["dc_ac_ratio"]
    if p["tilt_deg"] == "latitude":
        tilt = lat
        if p["array_type"] in TRACKING_ARRAY_TYPES:
            warnings.warn("tilt_deg=latitude with a tracking array_type: tracker axes are usually "
                          "horizontal (tilt 0). See SPEC.md open decision D10.")
    else:
        tilt = float(p["tilt_deg"])
    pv.SystemDesign.tilt = tilt
    pv.SystemDesign.azimuth = p["azimuth_deg"]
    pv.SystemDesign.losses = p["losses_pct"]
    pv.SystemDesign.array_type = p["array_type"]
    pv.execute()
    # Outputs.gen is in kW. For a 1 kW_dc system, kW output == per-unit capacity factor.
    cf = [g / pv.SystemDesign.system_capacity for g in pv.Outputs.gen]
    return check_profile(cf, f"PV {Path(weather_file).name}"), pv.Outputs.capacity_factor


def wind_profile(srw_file, w):
    """Per-unit hourly output of one turbine built from cases.yaml technologies.wind."""
    wp = Windpower.default("WindPowerNone")
    wp.Resource.wind_resource_filename = str(srw_file)
    # The default PySAM turbine is a 1.5 MW machine. Build the power curve for the turbine the
    # spec actually defines, otherwise the rating and the curve disagree.
    pc = w["power_curve"]
    wp.Turbine.calculate_powercurve(
        turbine_size=w["turbine_rating_kw"], rotor_diameter=w["rotor_diameter_m"], elevation=0,
        max_cp=pc["max_cp"], max_tip_speed=pc["max_tip_speed_m_per_s"],
        max_tip_sp_ratio=pc["max_tip_speed_ratio"], cut_in=pc["cut_in_m_per_s"],
        cut_out=pc["cut_out_m_per_s"], drive_train=pc["drive_train"])
    rating = max(wp.Turbine.wind_turbine_powercurve_powerout)
    if abs(rating - w["turbine_rating_kw"]) > 1e-6 * w["turbine_rating_kw"]:
        raise ValueError(f"power curve peak {rating} kW != turbine_rating_kw {w['turbine_rating_kw']}")
    wp.Turbine.wind_turbine_rotor_diameter = w["rotor_diameter_m"]
    wp.Turbine.wind_turbine_hub_ht = w["hub_height_m"]
    wp.Farm.system_capacity = rating
    wp.Farm.wind_farm_xCoordinates = [0]
    wp.Farm.wind_farm_yCoordinates = [0]
    wp.Farm.wind_farm_wake_model = 0                 # irrelevant for a single turbine
    # PySAM's default case silently applies ~16 % of availability/electrical/environmental losses.
    # Zero every loss category so that only the losses written in cases.yaml are applied.
    for name in wp.Losses.export():
        setattr(wp.Losses, name, 0.0)
    # wake_int_loss is NOT applied to a single-turbine farm (verified with nlr-pysam 8.0.0), so the
    # farm-level wake loss is applied through wake_ext_loss, which reaches the hourly output.
    wp.Losses.wake_ext_loss = w["wake_loss_pct"]
    wp.Losses.turb_generic_loss = w["other_losses_pct"]   # everything else, one explicit number (D15)
    wp.execute()
    cf = [g / rating for g in wp.Outputs.gen]
    return check_profile(cf, f"Wind {Path(srw_file).name}"), wp.Outputs.capacity_factor


def write(path, values):
    path.write_text("hour,cf\n" + "\n".join(f"{i},{v:.6f}" for i, v in enumerate(values)) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", nargs="*", help="site ids (default: all)")
    ap.add_argument("--years", nargs="*", type=int, help="weather years (default: all)")
    ap.add_argument("--frozen", default=ROOT / "data/frozen", type=Path)
    ap.add_argument("--out", default=ROOT / "profiles", type=Path)
    a = ap.parse_args(argv)

    spec = yaml.safe_load(open(ROOT / "cases.yaml"))
    tech, T = spec["technologies"], spec["time"]
    sites = [S for S in spec["sites"]["items"] if not a.sites or S["id"] in a.sites]
    years = a.years or T["weather_years"]
    a.out.mkdir(parents=True, exist_ok=True)
    for S in sites:
        for y in years:
            cf, annual = pv_profile(a.frozen / "solar" / f'{S["id"]}_{y}.csv', S["lat"], tech["pv"])
            print("pv  ", S["id"], y, f"CF={annual:.1f}%", write(a.out / f'{S["id"]}_{y}_pv.csv', cf))
            cf, annual = wind_profile(a.frozen / "wind" / f'{S["id"]}_{y}.srw', tech["wind"])
            print("wind", S["id"], y, f"CF={annual:.1f}%", write(a.out / f'{S["id"]}_{y}_wind.csv', cf))


if __name__ == "__main__":
    sys.exit(main())
