#!/usr/bin/env python3
"""Download NSRDB (solar) and WIND Toolkit (wind) hourly files for every site-year.

Reads cases.yaml; writes data/raw/solar/{site}_{year}.csv and data/raw/wind/{site}_{year}.srw.
Requires env vars NLR_DEVELOPER_API_KEY and NLR_DEVELOPER_EMAIL (free key: developer.nlr.gov).
Honours the CSV-endpoint rate limit (1 request/second). 12 sites x 7 years x 2 = 168 requests.
Confirm endpoint names in cases.yaml against the current NSRDB / WIND Toolkit API docs.
"""
import os, sys, time
from pathlib import Path
import requests, yaml

ROOT = Path(__file__).resolve().parents[1]
spec = yaml.safe_load(open(ROOT / "cases.yaml"))
KEY, EMAIL = os.environ.get("NLR_DEVELOPER_API_KEY"), os.environ.get("NLR_DEVELOPER_EMAIL")
if not (KEY and EMAIL):
    sys.exit("Set NLR_DEVELOPER_API_KEY and NLR_DEVELOPER_EMAIL")

sol, wnd, T = spec["resources"]["solar"], spec["resources"]["wind"], spec["time"]
utc = "true" if T["timezone"] == "UTC" else "false"
leap = "true" if T["leap_day"] else "false"

def get(url, params, dest):
    if dest.exists():
        return "cached"
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    time.sleep(1.1)
    return "ok"

for S in spec["sites"]["items"]:
    for y in T["weather_years"]:
        # Solar: SAM-format CSV, single point, single year
        d = ROOT / "data/raw/solar" / f'{S["id"]}_{y}.csv'
        st = get(f'{sol["api_base"]}/{sol["endpoint"]}.csv', {
            "api_key": KEY, "email": EMAIL, "wkt": f'POINT({S["lon"]} {S["lat"]})',
            "names": y, "interval": sol["interval_minutes"], "utc": utc, "leap_day": leap,
            "attributes": ",".join(sol["attributes"])}, d)
        print("solar", S["id"], y, st)
        # Wind: SAM .srw format
        d = ROOT / "data/raw/wind" / f'{S["id"]}_{y}.srw'
        st = get(f'{wnd["api_base"]}/{wnd["endpoint"]}', {
            "api_key": KEY, "email": EMAIL, "lat": S["lat"], "lon": S["lon"],
            "year": y, "hubheight": wnd["hub_height_m"], "utc": utc}, d)
        print("wind ", S["id"], y, st)
print("done — now run: make freeze  (copies to data/frozen and writes MANIFEST.sha256)")
