"""Regression tests for the two make_profiles.py unit bugs fixed on 2026-10-11."""
import sys
from pathlib import Path
import pytest, yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "tests"))
import make_profiles as mp
from synthetic_weather import solar_csv, wind_srw

SPEC = yaml.safe_load(open(ROOT / "cases.yaml"))


def test_pv_profile_is_per_kw_dc(tmp_path):
    cf, annual_pct = mp.pv_profile(solar_csv(tmp_path / "s.csv"), 35.22, SPEC["technologies"]["pv"])
    assert len(cf) == 8760
    mean = sum(cf) / len(cf)
    # Old bug divided kW by 1000, giving a mean around 0.0002. A real PV profile is 0.1-0.4.
    assert 0.10 < mean < 0.40, mean
    assert max(cf) <= 1.0
    # The hourly profile and PySAM's own annual capacity factor (per kW_dc in PVWatts v8) must agree.
    assert mean == pytest.approx(annual_pct / 100, rel=0.02)


def test_wind_profile_uses_spec_turbine(tmp_path):
    w = SPEC["technologies"]["wind"]
    cf, annual_pct = mp.wind_profile(wind_srw(tmp_path / "w.srw"), w)
    assert len(cf) == 8760
    mean = sum(cf) / len(cf)
    # Old bug: 1.5 MW default curve divided by 3000 kW capped CF at 0.5.
    assert max(cf) > 0.85, "turbine never reaches near-rated output; curve/rating mismatch?"
    assert mean == pytest.approx(annual_pct / 100, rel=0.02)
    # With only the spec's losses applied, rated output = 1 - wake - other losses.
    expected_peak = (1 - w["wake_loss_pct"] / 100) * (1 - w["other_losses_pct"] / 100)
    assert max(cf) == pytest.approx(expected_peak, rel=1e-3)


def test_out_of_range_profile_raises():
    with pytest.raises(ValueError):
        mp.check_profile([1.5] * 8760, "bad")
    with pytest.raises(ValueError):
        mp.check_profile([0.5] * 8784, "leap")
