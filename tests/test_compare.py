"""compare_results.py must read files that start with '# provenance' lines."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compare_results as cr

HEAD = "# model_name=REopt\n# git_sha=abc\ncase_id,lcoe_usd_per_mwh,npv_cost_usd,unserved_energy_mwh,unserved_energy_fraction,co2_tonnes_per_year,peak_gas_burn_mmbtu_per_h,status\n"


def write(p, rows):
    p.write_text(HEAD + "\n".join(rows) + "\n"); return str(p)


def test_template_parses():
    prov, rows = cr.read_results(ROOT / "results/results_template.csv")
    assert "model_name" in prov and len(rows) == 180


def test_identical_files_pass(tmp_path):
    f = write(tmp_path / "a.csv", ["L1-TXA-A1,80,1e9,0,0,1e5,400,optimal", "L1-TXA-A5,,,,,,,not_run"])
    assert cr.main([f, f]) == 0


def test_drift_beyond_tolerance_fails(tmp_path):
    a = write(tmp_path / "a.csv", ["L1-TXA-A1,80,1e9,0,0,1e5,400,optimal"])
    b = write(tmp_path / "b.csv", ["L1-TXA-A1,81,1e9,0,0,1e5,400,optimal"])   # LCOE +1.25 %
    assert cr.main([a, b]) == 1


def test_missing_case_fails(tmp_path):
    a = write(tmp_path / "a.csv", ["L1-TXA-A1,80,1e9,0,0,1e5,400,optimal"])
    b = write(tmp_path / "b.csv", ["L1-TXA-A2,80,1e9,0,0,1e5,400,optimal"])
    assert cr.main([a, b]) == 1
