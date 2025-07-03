import sys
import requests
import pandas as pd
import matplotlib.pyplot as plt
from urllib.parse import urlencode

from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

API_KEY = "fKumsKDJAjMChPzyFgdd1QFU2L8Js8Pqn7BdfzUo"
EMAIL   = "mahantasubhra243@gmail.com"
BASE_CSV = "https://developer.nrel.gov/api/nsrdb/v2/solar/himawari-tmy-download.csv"

def download_himawari_tmy(lat: float, lon: float,
                         tmy_version: str = "tmy-2020",
                         interval: int = 60,
                         attributes: str = "air_temperature,ghi,dni,dhi,wind_speed"
                         ) -> pd.DataFrame:
    """Download & return an hourly TMY DataFrame for the given point."""
    wkt = f"POINT({lon} {lat})"
    params = {
        "api_key":    API_KEY,
        "email":      EMAIL,
        "wkt":        wkt,
        "names":      tmy_version,
        "attributes": attributes,
        "utc":        "false",
        "leap_day":   "false",
        "interval":   str(interval)
    }
    url = BASE_CSV + "?" + urlencode(params)

    # Read & display metadata
    meta = pd.read_csv(url, nrows=1)
    elev = meta.get("Elevation", [None])[0]
    print(f"Location elevation: {elev} m")

    # Download the data (skip the two metadata lines)
    df = pd.read_csv(url, skiprows=2)

    # Build a proper DateTimeIndex
    year_str = tmy_version.split("-", 1)[-1]
    idx = pd.date_range(start=f"1/1/{year_str} 00:00",
                        periods=len(df),
                        freq=f"{interval}Min")
    df.index = idx

    # Normalize column names: strip, lowercase, replace spaces
    df.columns = (df.columns
                    .str.strip()
                    .str.lower()
                    .str.replace(" ", "_", regex=False))

    # Rename temperature to temp_air for pvlib
    if "temperature" in df.columns:
        df.rename(columns={"temperature": "temp_air"}, inplace=True)

    print(f"Downloaded TMY DataFrame: {df.shape[0]} rows, {df.shape[1]} vars")
    return df

def main():
    raw = input("Enter latitude, longitude (e.g. 26.4441636772774, 91.40806653548296): ").strip()
    try:
        lat_str, lon_str = [x.strip() for x in raw.split(",")]
        lat, lon = float(lat_str), float(lon_str)
    except Exception:
        print("Invalid format. Please enter: <latitude>, <longitude>")
        sys.exit(1)

    # 1) Download TMY into DataFrame
    tmy = download_himawari_tmy(lat, lon, tmy_version="tmy-2020", interval=60)

    # 2) Set up pvlib location & system
    location = Location(latitude=lat,
                        longitude=lon,
                        tz="Asia/Calcutta",
                        altitude=location_elev if (location_elev := tmy.index[0].tzinfo) else 50)

    temp_params = TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]

    module_params = {
        "pdc0": 550,
        "gamma_pdc": -0.0025,
        "V_oc_ref": 49.85,
        "I_sc_ref": 13.94,
        "V_mp_ref": 41.80,
        "I_mp_ref": 13.16,
        "alpha_sc": 0.0040,
        "beta_oc": -0.0029,
        "cells_in_series": 144,
        "temp_ref": 25,
        "K": 0.05
    }

    inverter_params = {
        "paco": 3000,
        "pdc0": 3300
    }

    system = PVSystem(surface_tilt=45,
                      surface_azimuth=180,
                      module_parameters=module_params,
                      inverter_parameters=inverter_params,
                      modules_per_string=6,
                      temperature_model_parameters=temp_params)

    mc = ModelChain(system,
                    location,
                    dc_model="pvwatts",
                    ac_model="pvwatts",
                    aoi_model="ashrae")

    # 3) Run the simulation
    mc.run_model(tmy)

    # 4) Plot hourly AC power
    ac = mc.results.ac
    ac.plot(figsize=(14, 6))
    plt.ylabel("AC Power (W)")
    plt.title("Hourly AC Power Yield")
    plt.show()

    # 5) Print total annual yield
    total_kwh = ac.sum() / 1000.0
    print(f"Total annual yield at ({lat}, {lon}): {total_kwh:.1f} kWh")

if __name__ == "__main__":
    main()
