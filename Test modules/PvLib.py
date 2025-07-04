import pvlib
import pandas as pd
import matplotlib.pyplot as plt

from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS


location = Location(latitude=26.44389328962254,longitude= 91.4078747873579,tz='Asia/Calcutta',altitude=50)
temperature_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
waaree_ahnay_550 = {
    'pdc0': 550,               # Nominal power at STC (W)
    'gamma_pdc': -0.0025,      # Temperature coefficient of power (%/°C → W/W/°C)
    'V_oc_ref': 49.85,         # Open-circuit voltage (Voc, V)
    'I_sc_ref': 13.94,         # Short-circuit current (Isc, A)
    'V_mp_ref': 41.80,         # Voltage at max power (Vmp, V)
    'I_mp_ref': 13.16,         # Current at max power (Imp, A)
    'alpha_sc': 0.0040,        # Temp coefficient of Isc (0.40%/°C = 0.0040)
    'beta_oc': -0.0029,        # Temp coefficient of Voc (–0.29%/°C = –0.0029)
    'cells_in_series': 144,    # 144 half-cut cells = 72 full cells
    'temp_ref': 25  ,           # Standard test condition temperature (°C)
    
}

waaree_ahnay_550['K'] = 0.05  # Typical for modern AR-coated glass

inverter_havels =  {
    'paco': 3000,
    'pdc0': 3000 # Match this to your module's 'pdc0'
}



system = PVSystem(surface_tilt=45,surface_azimuth=180,
                  module_parameters=waaree_ahnay_550,
                  inverter_parameters=inverter_havels,
                  modules_per_string=2,
                  temperature_model_parameters=temperature_parameters)
modelchain = ModelChain(system, location, 
                        dc_model='pvwatts', 
                        ac_model='pvwatts',
                        aoi_model='ashrae' )

tmy=pd.read_csv("output.csv")

modelchain.run_model(tmy)
modelchain.results.ac.plot(figsize=(16,9))
plt.show()