"""
The ``basic_example`` module shows a simple usage of the hydropowerlib.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
import os
import pandas as pd
import glob


try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

from git_repos.hydropowerlib.hydropowerlib import modelchain
from git_repos.hydropowerlib.hydropowerlib import hydropower_plant as hpp

logging.getLogger().setLevel(logging.INFO)

dV_file='dV_Raon.csv'
dV_Raon = pd.read_csv(dV_file, index_col='date', parse_dates=True, infer_datetime_format=True)

dV_hist_Raon=pd.DataFrame()
dV_hist_folder='dV_hist_Raon'
dV_hist_path =os.path.join(os.path.dirname(__file__),dV_hist_folder)
filenames = glob.glob(dV_hist_path + "/*.csv")
for file in filenames:
    df = pd.read_csv(file, index_col='date', parse_dates=True, infer_datetime_format=True)
    dV_hist_Raon = dV_hist_Raon.append(df)

print(dV_hist_Raon)
# Definition of the hydropower plant
hydro_Raon = hpp.HydropowerPlant(id='HydroRaon',dV_n= 12,h_n=4.23,P_n=400000,turb_num=1,turb_type='Kaplan')

# Definition of the modelchain
mc_hpp_raon = modelchain.Modelchain(HPP=hydro_Raon,dV=dV_Raon,dV_hist=dV_hist_Raon)

# Run model
mc_hpp_raon.run_model()
hydro_Raon.power_output

# Plot turbine power output
if plt:
    hydro_Raon.power_output.plot(legend=True, label='Example')
    dV_Raon.plot(legend=True, label='dV')
    plt.show()
else:
    print(hydro_Raon.power_output)

output_april=hydro_Raon.power_output.loc['2017-04-12 00:00:00':'2017-04-30 23:00:00']
print(output_april.sum())
output_may=hydro_Raon.power_output.loc['2017-05-01 00:00:00':'2017-05-31 23:00:00']
print(output_may.sum())
print(hydro_Raon.P_n)
logging.info('Done!')
