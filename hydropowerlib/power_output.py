"""
The ``power_output`` module contains functions to calculate the power output
of a hydropower plant.

"""

import pandas as pd
import os
import logging
import sys

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"


def get_eta_g_n(P_n):
    r"""
    Calculate the nominal efficiency of the generator based on the nominal power of the plant
    Source : "Wahl, Dimensionierung und Abnahme einer Kleinturbine" from PACER
    :param P_n: float
    :return: 
    float
    """
    if P_n < 1000:
        eta_g_n = 80
    elif P_n < 5000:
        eta_g_n = 80 + (P_n - 1000) / 1000 * 5 / 4
    elif P_n < 20000:
        eta_g_n = 85 + (P_n - 5000) / 1000 * 5 / 15
    elif P_n < 100000:
        eta_g_n = 90 + (P_n - 20000) / 1000 * 5 / 80
    else:
        eta_g_n = 95
    return (eta_g_n / 100)


def get_turb_param(turb_type, file_turb_eff):
    r"""
    Gets the parameters to calculate the turbine efficiency
    :param turb_type: string
    Type of turbine
    :param file_turb_eff: string
    csv file storing the efficiency parameters. File has to be in data folder
    :return: 
    pd.DataFrame
    """
    try:
        df = pd.read_csv(os.path.join(os.path.join(os.path.dirname(__file__), 'data'), file_turb_eff), index_col=0)
    except IOError:
        logging.info(
            'No file %s in data folder' % file_turb_eff)
        sys.exit()
    hpp_df = df[df.type == turb_type]
    if hpp_df.shape[0] == 0:
        pd.set_option('display.max_rows', len(df))
        logging.info('Possible types: \n{0}'.format(df.type))
        pd.reset_option('display.max_rows')
        sys.exit('Turbine type %s is not in file %s' % (turb_type, file_turb_eff))
    return hpp_df


def get_eta_gen(load, eta_g_n):
    r"""
    Get efficiency of generator based on the part load and the nominal efficiency.
    Source : "Wahl, Dimensionierung und Abnahme einer Kleinturbine" from PACER
    :param load: float
    :param eta_g_n: float
    :return: 
    float
    """
    if load < 0.1:
        eta_g = 0.85 * eta_g_n
    elif load < 0.25:
        eta_g = (0.85 + (load - 0.1) * 0.1 / 0.15) * eta_g_n
    elif load < 50:
        eta_g = (0.95 + (load - 0.25) * 0.05 / 0.25) * eta_g_n
    else:
        eta_g = eta_g_n
    return eta_g


def run(hpp, dV, file_turb_eff):
    r"""
    Calculates the plant power output.

    Parameters
    ----------
    hpp : instance of the :class:`~.hydropower_plant.HydropowerPlant` class
        Specifications of the hydropower plant
    dV : pandas.Series
        Water flow in m3/s.

    Returns
    -------
    pandas.Series
        Electrical power output of the hydropower plant in W.

    Notes
    -----
    The following equation is used [1]_:

    .. math:: P=\eta_{turbine}\cdot\eta_{generator}\cdot g\cdot\rho_{water}\cdot min(dV,dV_{n})\cdot h_{n}


    with:
        P: power [W], :math:`\rho_{water}`: density [kg/m³], g: standard gravity [m/s2],
        dV: water flow [m3/s], :math:`dV_{n}`: nominal water flow [m3/s],
        :math:`h_{n}`: nominal head of water [m], :math:`\eta_{turbine}`: efficiency of the turbine [],
        :math:`\eta_{generator}`: efficiency of the generator []

    It is assumed that the efficiency for water flows above the maximum
    water flow given in the efficiency curve is the nominal efficiency
    (the water surplus will be drained over the dam)

    References
    ----------
    .. [1] Quaschning, V.: "Regenerative Energiesysteme". 9. Auflage, München,
           Hanser, 2015, page 333


    """

    load = pd.Series(data=dV.dV.values / hpp.dV_n, index=dV.index)
    power_output = pd.Series('', index=dV.index, name='feedin_hydropower_plant')
    eta_g_n = get_eta_g_n(hpp.P_n)
    turbine_parameters = get_turb_param(hpp.turb_type, file_turb_eff)

    for timestep in dV.index:
        if load[timestep] < turbine_parameters.load_min.values[0]:
            power_output[timestep] = 0
        elif load[timestep] >= 1:
            power_output[timestep] = hpp.P_n
        else:
            eta_turb = (load[timestep] - turbine_parameters.load_min.values[0]) / (
            turbine_parameters.a1.values[0] + turbine_parameters.a2.values[0] * (
            load[timestep] - turbine_parameters.load_min.values[0]) + turbine_parameters.a3.values[0] * (
            load[timestep] - turbine_parameters.load_min.values[0]) * (load[timestep] - turbine_parameters.load_min.values[0]))
            eta_gen = get_eta_gen(load[timestep], eta_g_n)
            power_output[timestep] = eta_turb * eta_gen * 9.81 * 1000 * dV.dV[timestep] * hpp.h_n

    return power_output

