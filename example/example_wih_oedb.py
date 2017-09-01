"""
The ``basic_example`` module shows a simple usage of the hydropowerlib.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
import os
import pandas as pd
from oemof import db


try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

from git_repos.hydropowerlib.hydropowerlib import modelchain
from git_repos.hydropowerlib.hydropowerlib import hydropower_plant as hpp

logging.getLogger().setLevel(logging.INFO)

if __name__ == '__main__':
    conn_oedb = db.connection(section='oedb')

    sql_read = """
    WITH plants AS (SELECT reg.id,reg.start_up_date, reg.electrical_capacity, reg_dp.dp_geom, reg_dp.nam 
    FROM supply.ego_renewable_power_plants_germany_hydro_mview reg, supply.fred_dp_res_powerplant_hydro_on_river_mview reg_dp
    WHERE reg.id=reg_dp.id) 

    WITH p_w AS (SELECT DISTINCT ON (plants.id) plants.id, plants.start_up_date, plants.electrical_capacity, plants.dp_geom, plants.nam, watergap.gid
    FROM plants, hydrolib.watergap_geoms watergap
    WHERE st_dwithin(st_transform(plants.dp_geom,3035), st_transform(watergap.geom,3035), 10000)
    ORDER BY plants.id, st_distance(st_transform(plants.dp_geom,3035), st_transform(watergap.geom,3035)))        
    """
    #TO BE CONTINUED
    df = pd.read_sql(sql_read, con)

    try:
        read_and_plot(conn_oedb)
    finally:
        conn_oedb.close()
    print(time.time)
    logger.info('...database connections closed...')
    logger.info('...script successfully executed in {:.2f} seconds. Goodbye!'
        .format(time.time() - start_time))


def read_river_data(filename, datetime_column='Unnamed: 0',
                      **kwargs):
    r"""
    Fetches weather data from a file.

    The files are located in the example folder of the windpowerlib.

    Parameters
    ----------
    filename : string
        Filename of the weather data file.
    datetime_column : string
        Name of the datetime column of the weather DataFrame.

    Other Parameters
    ----------------
    datapath : string, optional
        Path where the weather data file is stored.
        Default: 'windpowerlib/example'.

    Returns
    -------
    pandas.DataFrame
        Contains weather data time series.

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.split(
            os.path.dirname(__file__))[0], 'example')

    file = os.path.join(kwargs['datapath'], filename)
    df = pd.read_csv(file)
    return df.set_index(pd.to_datetime(df[datetime_column])).tz_localize(
        'UTC').tz_convert('Europe/Berlin').drop(datetime_column, 1)

# Read weather data from csv
river_data = read_river_data('river_raon.csv')

# Specifications of the hydropower plant
hydro_Raon = {
    'H_n': 4.23,
    'Q_n': 12,
    'W_n': 0.8,
    'P_n':400000,
    'turb_num':1,
    'eta_gen':0.95}


# Initialize HydropowerPlant objects
hpp_ex = hpp.HydropowerPlant(**hydro_Raon)
print(hpp_ex.turbine_type)
print(hpp_ex.Q_n)


# Specifications of the modelchain data
modelchain_data = {
    'g_model': 'default',
    'rho_model': 'default'}

# Calculate turbine power output
mc_hpp_ex = modelchain.Modelchain(hpp_ex, **modelchain_data).run_model(
    river_data)
hpp_ex.power_output = mc_hpp_ex.power_output

# Plot turbine power output
if plt:
    hpp_ex.power_output.plot(legend=True, label='Example')
    plt.show()
else:
    print(hpp_ex.power_output)

# Plot power (coefficient) curves
if plt:
    if hpp_ex.eta_turb_values is not None:
        hpp_ex.eta_turb_values.plot(style='*', title='Example')
        plt.show()
else:
    if hpp_ex.eta_turb_values is not None:
        print("The efficency value with a normalized waterflow of 0,6: {0}".format(
            hpp_ex.eta_turb_values.eta_turb[0.6]))

print(hpp_ex.power_output)
output_april=hpp_ex.power_output.loc['2017-04-12 00:00:00':'2017-04-30 23:00:00']
print(output_april.sum())
output_may=hpp_ex.power_output.loc['2017-05-01 00:00:00':'2017-05-31 23:00:00']
print(output_may.sum())

logging.info('Done!')
