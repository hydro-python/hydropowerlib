"""
The ``example_with_csv`` module shows a simple usage of the hydropowerlib.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
import os
import pandas as pd
import glob


try:
    import matplotlib
    from matplotlib import pyplot as plt
    from matplotlib import dates as mdates
    matplotlib.style.use('seaborn-deep')
    matplotlib.rcParams.update({'font.size': 12})
except ImportError:
    plt = None

from hydropowerlib import modelchain, HydropowerPlant, Modelchain

logging.basicConfig(level="DEBUG")

dV_file = 'dV_Raon.csv'
dV_Raon = pd.read_csv(dV_file, index_col='date', parse_dates=True, infer_datetime_format=True).dV

dV_hist_folder = 'dV_hist_Raon'
dV_hist_path = os.path.join(os.path.dirname(__file__), dV_hist_folder)
dV_hist_Raon = []
for file in glob.glob(dV_hist_path + "/*.csv"):
    df = pd.read_csv(file, index_col='date', parse_dates=True, infer_datetime_format=True)
    dV_hist_Raon.append(df)
dV_hist_Raon = pd.concat(dV_hist_Raon).dV

# Definition of the hydropower plant
hydro_Raon = HydropowerPlant(name='HydroRaon', dV_n=12, h_n=4.23, P_n=400000, turb_num=1, turb_type='Kaplan')

# Definition of the modelchain
mc_hpp_raon = Modelchain(hpp=hydro_Raon, dV=dV_Raon, dV_hist=dV_hist_Raon)


# Run model
mc_hpp_raon.run_model()

# Get outputs of each month
output_april = hydro_Raon.power_output.loc['2017-04']
output_may = hydro_Raon.power_output.loc['2017-05']

logging.info('\tEnergy production in April : %d MWh\n\t\t\tEnergy production in May : %d MWh'%(output_april.sum()/1000000,output_may.sum()/1000000))

# Plot turbine power output
if plt:
    fig, ax = plt.subplots(1)
    plt.plot(hydro_Raon.power_output.index, hydro_Raon.power_output.values/1000)
    plt.grid(b=True, which='major', axis='y')
    plt.ylabel("Power output [kW]")
    plt.xlabel("Day")
    plt.xticks(rotation=45)
    plt.xlim('2017-04-01 00:00:00','2017-05-31 23:00:00')
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))  # to get a tick every 15 minutes
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))  # optional formatting
    plt.show()
else:
    print(hydro_Raon.power_output)

logging.info('Done!')
