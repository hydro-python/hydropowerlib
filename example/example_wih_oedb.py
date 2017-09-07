"""
The ``basic_example`` module shows a simple usage of the hydropowerlib.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
import os
import pandas as pd
from oemof import db
import numpy as np


try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

from git_repos.hydropowerlib.hydropowerlib import modelchain
from git_repos.hydropowerlib.hydropowerlib import hydropower_plant as hpp

logging.getLogger().setLevel(logging.INFO)


conn_oedb = db.connection(section='oedb')

try:
    # Get power plants in Thuringe with their id, electrical capacity, location, start-up date, and the id of the raster cell containing the modeled runoff
    sql_read = """
    WITH reg_TH AS (SELECT reg_on_wg.id, reg_on_wg.dp_geom, reg_on_wg.wg_id
    FROM supply.fred_dp_res_powerplant_hydro_on_wg_mview reg_on_wg, orig_vg250.vg250_2_lan bl
    WHERE st_contains(st_TRANSFORM(bl.geom,3035),ST_TRANSFORM(reg_on_wg.dp_geom,3035)) AND bl.gen='Thüringen')
    SELECT reg_TH.id,reg_TH.wg_id, reg.electrical_capacity
    FROM reg_TH, supply.ego_renewable_power_plants_germany_hydro_mview reg
    WHERE reg_TH.id=reg.id
    """
    plant_reg = pd.read_sql(sql_read, conn_oedb)

    # Feel free to chage this to try another year
    year_to_simulate=2009

    # Counts the plants simulated = the plants for which runoff data from the year to simulate was available
    plants_with_ts=0

    # Sums the energy of all plants
    energy=0

    # DataFrame of all plants
    plants_df=pd.DataFrame(columns=['P_n','dV_n','h_n','dV_rest','turb_type','simu','power_output'])
    plants_df=plants_df.astype(dtype={'P_n':float,'dV_n':float,'h_n':float,'dV_rest':float,'turb_type':str,'simu':bool,'power_output':pd.Series})

    for i in plant_reg.index:
        # Read the runoff time series of the raster cell in which the plant is (one time series per year)
        sql_read= """SELECT year, time_series FROM hydrolib.watergap_runoff
        WHERE geom_id=%s """ %plant_reg.loc[i,'wg_id']
        discharge=pd.read_sql(sql_read, conn_oedb)

        simu=False

        # Remove empty 2/29 cell on leap years (no leap years in watergap) and concatenate in one time series over several years
        ts_df=pd.DataFrame(columns=['dV'])
        for j in discharge.index:
            index_temp1=pd.date_range('1/1/%s'%discharge.loc[j,'year'], periods=59, freq='D')
            index_temp2=pd.date_range('3/1/%s'%discharge.loc[j,'year'], periods=306, freq='D')
            index_temp=index_temp1.append(index_temp2)
            discharge_temp=np.asarray(discharge.loc[j, 'time_series'])
            discharge_temp=discharge_temp[~np.isnan(discharge_temp)]
            ts_df=ts_df.append(pd.DataFrame(index=index_temp,data={'dV':discharge_temp}))
            # If the raster cell has modeled runoff data for the year to simulate, simulation of this plant is possible
            if discharge.loc[j,'year']==year_to_simulate:
                plants_with_ts=plants_with_ts+1
                power_outputs=pd.DataFrame(index=index_temp)
                simu=True
        if simu==True:
            # Define the HydropowerPlant object and the ModelChain object based on available data
            my_hpp=hpp.HydropowerPlant(P_n=plant_reg.loc[i,'electrical_capacity']*1000,id=plant_reg.loc[i,'id'])
            my_mc=modelchain.Modelchain(HPP=my_hpp,dV=ts_df.loc[ts_df.index.year==year_to_simulate,:],dV_hist=ts_df)
            my_mc.run_model()
            power_outputs[plant_reg.loc[i,'id']]=my_hpp.power_output
            energy=energy+(my_hpp.power_output.sum()*24)
            plants_df.loc[my_hpp.id] = {'P_n': my_hpp.P_n, 'dV_n': my_hpp.dV_n, 'h_n': my_hpp.h_n, 'dV_rest': my_hpp.dV_rest,
                                     'turb_type': my_hpp.turb_type, 'simu': simu,
                                     'power_output': my_hpp.power_output.values}
        else:
            plants_df.loc[plant_reg.loc[i,'id']] = {'P_n': plant_reg.loc[i,'electrical_capacity']*1000, 'dV_n': None, 'h_n': None,
                                        'dV_rest': None, 'turb_type': None, 'simu': simu, 'power_output': None}

    logging.info('\t%d from %d plants simulated \n\t\t\tEnergy produced : %d GWh' %(plants_with_ts,len(plants_df.index),energy/1000000000))
    #plants_df.to_csv('example_oedb.csv', index=True)
finally:
    conn_oedb.close()