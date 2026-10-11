"""Write small synthetic SAM weather files so profile code can be tested without API keys.

These are NOT benchmark data. They only exercise file parsing, units and value ranges.
"""
import math
from pathlib import Path


def solar_csv(path: Path, lat=35.22, lon=-101.83, year=2012):
    """Crude clear-sky-like SAM CSV, hourly, UTC, 8760 rows (no 29 Feb)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    lines = ["Source,Location ID,City,State,Country,Latitude,Longitude,Time Zone,Elevation",
             f"Synthetic,0,Test,TX,USA,{lat},{lon},0,1000",
             "Year,Month,Day,Hour,Minute,GHI,DNI,DHI,Temperature,Wind Speed"]
    doy = 0
    for m, nd in enumerate(days, 1):
        for d in range(1, nd + 1):
            doy += 1
            decl = math.radians(23.45) * math.sin(2 * math.pi * (284 + doy) / 365)
            for h in range(24):
                solar_time = h + 0.5 + lon / 15.0           # UTC -> local solar time
                ha = math.radians(15 * (solar_time - 12))
                sin_el = (math.sin(math.radians(lat)) * math.sin(decl)
                          + math.cos(math.radians(lat)) * math.cos(decl) * math.cos(ha))
                s = max(sin_el, 0.0)
                dni = 900 * s ** 0.3 if s > 0.02 else 0.0
                dhi = 100 * s if s > 0 else 0.0
                ghi = dni * s + dhi
                lines.append(f"{year},{m},{d},{h},30,{ghi:.1f},{dni:.1f},{dhi:.1f},20,3")
    path.write_text("\n".join(lines) + "\n")
    return path


def wind_srw(path: Path, lat=35.22, lon=-101.83, year=2012, mean_speed=8.5):
    """SAM .srw with a smooth diurnal/seasonal wind speed around mean_speed at 100 m."""
    lines = [f"0,Test,TX,USA,{year},{lat},{lon},1000,1,8760",
             "Synthetic wind for unit tests",
             "Temperature,Pressure,Speed,Direction",
             "C,atm,m/s,degrees",
             "100,100,100,100"]
    for i in range(8760):
        v = mean_speed * (1 + 0.35 * math.sin(2 * math.pi * i / 24) + 0.2 * math.sin(2 * math.pi * i / 8760))
        lines.append(f"15,0.9,{max(v, 0):.2f},180")
    path.write_text("\n".join(lines) + "\n")
    return path
