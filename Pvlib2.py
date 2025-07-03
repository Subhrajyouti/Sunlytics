import pvlib
import pandas as pd
import matplotlib.pyplot as plt
from pvlib.modelchain import ModelChain
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS


location = Location(latitude=26.44389328962254,longitude= 91.4078747873579,tz='Asia/Calcutta',altitude=50)
temperature_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
modules=pvlib.pvsystem.retrieve_sam('SandiaMod')
inverter=pvlib.pvsystem.retrieve_sam('CECInverter')
waaree_ahnay_550=modules['Canadian_Solar_CS5P_220M___2009_']
inverter_havels=inverter['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
system = PVSystem(surface_tilt=45,surface_azimuth=180,
                  module_parameters=waaree_ahnay_550,
                  inverter_parameters=inverter_havels,
                  temperature_model_parameters=temperature_parameters)
modelchain = ModelChain(system,location)
times=pd.date_range(start='2025-01-01',end='2025-01-07',freq='1min',tz=location.tz)

clearsky=location.get_clearsky(times)
clearsky.plot(figsize=(16,9))
plt.show()
modelchain.run_model(clearsky)
modelchain.results.ac.plot(figsize=(16,9))
plt.show()