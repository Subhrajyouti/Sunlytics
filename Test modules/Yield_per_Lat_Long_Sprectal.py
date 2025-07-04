#!/usr/bin/env python3
"""
dynamic_spectral_yield.py

Fetch NREL Spectral On-demand data for one point/year, compute
plane‐of‐array irradiance, then run a PVWatts ModelChain to
estimate annual AC yield per kWp.
"""

import sys
import io
import requests
import pandas as pd
from urllib.parse import urlencode

from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

API_KEY = "fKumsKDJAjMChPzyFgdd1QFU2L8Js8Pqn7BdfzUo"
EMAIL   = "mahantasubhra243@gmail.com"

BASE_URL = (
    "https://developer.nrel.gov/api/nsrdb_api/solar/"
    "spectral_ondemand_download.json"
)

MODULE_PARAMS = {
    "pdc0": 550, "gamma_pdc": -0.0025,
    "V_oc_ref": 49.85, "I_sc_ref": 13.94,
    "V_mp_ref": 41.80, "I_mp_ref": 13.16,
    "alpha_sc": 0.0040, "beta_oc": -0.0029,
    "cells_in_series": 144, "temp_ref": 25, "K": 0.05
}
INVERTER_PARAMS = {"paco": 3000, "pdc0": 3000}


def fetch_spectral(params: dict) -> pd.DataFrame:
    """Submit the request, handle JSON ack vs CSV response."""
    url = BASE_URL + "?" + urlencode(params)
    print("\n▶ Request URL:\n", url, "\n")
    resp = requests.get(url)
    ctype = resp.headers.get("Content-Type", "")

    # JSON acknowledgement (async)
    if "application/json" in ctype:
        j = resp.json()
        if j.get("errors"):
            print("❌ API Errors:", j["errors"])
            sys.exit(1)
        print("ℹ️  NREL response:", j["outputs"]["message"])
        print("→ Download link will arrive by email.")
        sys.exit(0)

    # Otherwise assume we got CSV text back
    df = pd.read_csv(io.StringIO(resp.text))
    print(f"  • received CSV: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


def main():
    # 1) Inputs & Validation
    try:
        lat, lon = map(float, input("Enter lat, lon (e.g. 26.44, 91.41): ").split(","))
        year     = int(input("Enter year (2017–2024): ").strip())
    except:
        print("Invalid location or year format."); sys.exit(1)

    equip = input("System type? [fixed_tilt / one_axis]: ").strip()
    if equip not in ("fixed_tilt", "one_axis"):
        print("Must be 'fixed_tilt' or 'one_axis'."); sys.exit(1)

    # only request tilt/angle if fixed_tilt
    tilt = angle = None
    if equip == "fixed_tilt":
        try:
            tilt  = float(input("Enter panel tilt (0–90°): ").strip())
            angle = float(input("Enter panel azimuth (0=N, 90=E… 0–359.9): ").strip())
        except:
            print("Invalid tilt/angle."); sys.exit(1)
        # enforce bounds
        if not (0 <= tilt <= 90):
            print("Tilt must be between 0 and 90∘."); sys.exit(1)
        if not (0 <= angle < 360):
            print("Azimuth must be between 0 and 359.9∘."); sys.exit(1)

    # 2) Build params dict
    params = {
        "api_key":   API_KEY,
        "wkt":       f"POINT({lon} {lat})",
        "names":     year,
        "equipment": equip,
        "email":     EMAIL,
        "full_name": "Subhrajyoti Mahanta",
        "affiliation":"My Organization",
        "reason":    "yield+calc",
        "mailing_list":"false"
    }
    if equip == "fixed_tilt":
        params.update({"tilt": tilt, "angle": angle})

    # 3) Fetch spectral data
    spec = fetch_spectral(params)

    # 4) Build hourly index
    idx = pd.date_range(start=f"1/1/{year} 00:00",
                        periods=len(spec), freq="60Min")
    spec.index = idx

    # 5) Drop all metadata columns
    drop_keys = {c.lower() for c in [
        "source","location id","city","state","country","latitude","longitude",
        "time zone","elevation","local time zone","year","month","day",
        "hour","minute"
    ]}
    spec.drop(columns=[c for c in spec.columns if c.lower() in drop_keys],
              inplace=True)

    # 6) Sum narrow bands → POA global [W/m²]
    spec["poa_global"] = spec.sum(axis=1)

    # 7) Run pvlib ModelChain
    location    = Location(lat, lon, tz="Asia/Calcutta", altitude=50)
    temp_pars   = TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]
    system      = PVSystem(
        surface_tilt=tilt or lat,
        surface_azimuth=angle or 180,
        module_parameters=MODULE_PARAMS,
        inverter_parameters=INVERTER_PARAMS,
        modules_per_string=2,
        temperature_model_parameters=temp_pars
    )
    mc = ModelChain(system, location,
                    dc_model="pvwatts", ac_model="pvwatts", aoi_model=None)
    mc.run_model(spec[["poa_global"]])

    # 8) Report annual AC yield
    total_kwh = mc.results.ac.sum() / 1000.0
    print(f"\n→ Annual AC yield @1 kWp: {total_kwh:.1f} kWh")

    # 9) Optional CSV export
    if input("Save spectral+POA data? (y/N): ").lower()=="y":
        fn = f"spectral_{lat:.4f}_{lon:.4f}_{year}.csv"
        spec.to_csv(fn)
        print(f"Saved to {fn}")

if __name__ == "__main__":
    main()
