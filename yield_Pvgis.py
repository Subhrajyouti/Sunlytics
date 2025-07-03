import pvlib
import pandas as pd
import matplotlib.pyplot as plt

from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
from pvlib.iotools import get_pvgis_tmy

# 1. Read lat, lon
lat, lon = map(float, input("Enter latitude, longitude: ").split(','))

# 2. Fetch PVGIS TMY (handle 2- or 4-return signatures)
try:
    tmy_data, months_sel, inputs, metadata = get_pvgis_tmy(
        latitude=lat, longitude=lon, outputformat='csv'
    )
    elevation = float(inputs.get('elevation', 0))
except ValueError:
    tmy_data, metadata = get_pvgis_tmy(
        latitude=lat, longitude=lon, outputformat='csv'
    )
    elevation = float(
        metadata.get('meta', {}).get('elevation')
        or metadata.get('inputs', {}).get('elevation')
        or metadata.get('elevation', 0)
    )

# 3. Build Location
location = Location(lat, lon, tz='Asia/Calcutta', altitude=elevation)

# 4. Temperature model params
temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']

# 5. Retrieve SAM libraries
sandia = pvlib.pvsystem.retrieve_sam('SandiaMod')
cec    = pvlib.pvsystem.retrieve_sam('CECInverter')

# 6. Auto-select a ~500 Wp module (compute STC = V_mp_ref × I_mp_ref)
stc = sandia.loc['V_mp_ref'] * sandia.loc['I_mp_ref']
mod_cands = stc[(stc >= 450) & (stc <= 550)].index
if not len(mod_cands):
    raise RuntimeError("No Sandia module in 450–550 Wp range")
mod_name = mod_cands[0]
module   = sandia[mod_name]
print(f"Selected module: {mod_name} @ {stc[mod_name]:.0f} Wp")

# 7. Auto-select a ~3 kW inverter (CEC “Paco”)
pac = cec.loc['Paco']
inv_cands = pac[(pac >= 2500) & (pac <= 3500)].index
if not len(inv_cands):
    raise RuntimeError("No CEC inverter in 2.5–3.5 kW range")
inv_name = inv_cands[0]
inverter = cec[inv_name]
print(f"Selected inverter: {inv_name} @ {pac[inv_name]:.0f} W")

# 8. Define PVSystem: 2 modules in series, 1 string per inverter
system = PVSystem(
    surface_tilt=25,
    surface_azimuth=180,
    module_parameters=module,
    inverter_parameters=inverter,
    temperature_model_parameters=temp_params,
    modules_per_string=2,
    strings_per_inverter=1
)

# 9. Run the simulation
mc = ModelChain(system, location)
mc.run_model(tmy_data)

# 10. Compute specific annual yield (kWh/kWp)
ac = mc.results.ac
annual_wh    = ac.sum()
capacity_kwp = stc[mod_name] * system.modules_per_string / 1000.0
specific_yield = annual_wh / 1000.0 / capacity_kwp

print(f"\nLocation: {lat:.6f}, {lon:.6f} @ {elevation:.1f} m")
print(f"Specific annual yield: {specific_yield:.0f} kWh/kWp")

# 11. Plot hourly AC output
ac.plot(figsize=(14, 6))
plt.ylabel('AC power (W)')
plt.title(f'Hourly AC Output @ {lat:.4f}, {lon:.4f}')
plt.tight_layout()
plt.show()
