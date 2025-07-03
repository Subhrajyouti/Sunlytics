import sys
import requests
import pandas as pd
from urllib.parse import urlencode

API_KEY = "fKumsKDJAjMChPzyFgdd1QFU2L8Js8Pqn7BdfzUo"
EMAIL   = "mahantasubhra243@gmail.com"
BASE_CSV = "https://developer.nrel.gov/api/nsrdb/v2/solar/himawari-tmy-download.csv"

def download_himawari_tmy(lat: float, lon: float,
                         tmy_version: str = "tmy-2020",
                         interval: int = 60,
                         attributes: str = "air_temperature,ghi,dni,dhi,wind_speed") -> pd.DataFrame:
    """Download & return a clean hourly DataFrame for the given point."""
    wkt = f"POINT({lon} {lat})"
    params = {
        "api_key":      API_KEY,
        "email":        EMAIL,
        "wkt":          wkt,
        "names":        tmy_version,   
        "attributes":   attributes,
        "utc":          "false",
        "leap_day":     "false",
        "interval":     str(interval)
    }
    url = BASE_CSV + "?" + urlencode(params)

    # Read metadata
    meta = pd.read_csv(url, nrows=1)
    tz   = meta.get("Local Time Zone", ["UTC"])[0]
    elev = meta.get("Elevation", [None])[0]
    print(f"Metadata → Time Zone: {tz}, Elevation: {elev} m")

    # Read data, skipping the 2 metadata lines
    df = pd.read_csv(url, skiprows=2)

    # Build a proper DateTimeIndex
    year_str = tmy_version.split("-",1)[-1]  # e.g. "2020"
    periods  = len(df)
    freq     = f"{interval}Min"
    idx      = pd.date_range(start=f"1/1/{year_str} 00:00", periods=periods, freq=freq)
    df.index = idx

    # Drop any leftover time-columns
    for col in ["Year","Month","Day","Hour","Minute"]:
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    print(f"Loaded TMY DataFrame with shape {df.shape}")
    return df

def main():
    raw = input("Enter latitude, longitude (e.g. 26.4441636772774, 91.40806653548296): ").strip()
    try:
        lat_str, lon_str = [x.strip() for x in raw.split(",")]
        lat = float(lat_str)
        lon = float(lon_str)
    except Exception:
        print("Invalid format. Please enter as: <latitude>, <longitude>")
        sys.exit(1)

    df = download_himawari_tmy(lat, lon, tmy_version="tmy-2020", interval=60)
 
    df.to_csv("output.csv", sep=',', encoding='utf-8', index=True)

if __name__ == "__main__":
    main()
