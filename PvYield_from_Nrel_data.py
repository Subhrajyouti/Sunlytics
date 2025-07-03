import pvlib
import pandas as pd
import matplotlib.pyplot as plt

from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

# 1) Read TMY data from CSV, using the first column as datetime index
tmy = pd.read_csv(
    "output.csv",
    index_col=0,       # <— first column (whatever its name) becomes the index
    parse_dates=True   # <— parse that index as dates
)

# 2) Set up location & system
location = Location(
    latitude=26.44389328962254,
    longitude=91.4078747873579,
    tz="Asia/Calcutta",
    altitude=50
)

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

system = PVSystem(
    surface_tilt=45,
    surface_azimuth=180,
    module_parameters=module_params,
    inverter_parameters=inverter_params,
    modules_per_string=2,
    temperature_model_parameters=temp_params
)

mc = ModelChain(
    system,
    location,
    dc_model="pvwatts",
    ac_model="pvwatts",
    aoi_model="ashrae"
)

# 3) Run the model
mc.run_model(tmy)

# 4) Extract AC power (W) and plot
ac = mc.results.ac
ac.plot(figsize=(16, 6))
plt.ylabel("AC power (W)")
plt.title("Hourly AC Power")
plt.show()

# 5) Compute total energy yield in kWh
total_kwh = ac.sum() / 1000.0
print(f"Total annual yield: {total_kwh:.1f} kWh")
