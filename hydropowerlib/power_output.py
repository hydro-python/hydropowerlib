"""
The ``power_output`` module contains functions to calculate the power output
of a hydropower plant.

"""

import numpy as np
import pandas as pd


__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"


def output_from_eta_values(Q, W, hpp,rho,g):
    r"""
    Calculates the turbine power output using the given efficiency curve.

    This function is carried out when the parameter `eta_turb_values` of an
    instance of the :class:`~.modelchain.Modelchain` class
    has been filled in

    Parameters
    ----------
    Q : pandas.Series or array
        Water flow in m3/s.
    W : pandas.Series or array
        Water level in m.
    hpp : instance of the :class:`~.hydropower_plant.HydropowerPlant` class
        Specifications of the hydropower plant
    rho : float
        Density of water in kg/m³.
    g : float
        Acceleration of gravity in m/s2.    


    Returns
    -------
    pandas.Series
        Electrical power output of the hydropower plant in W.

    Notes
    -----
    The following equation is used [1]_:

    .. math:: P=\eta_{turbine}\cdot\eta_{generator}\cdot g\cdot\rho_{water}\cdot min(Q,Q_{n})\cdot(H_{n}+W_{n}-W) 


    with:
        P: power [W], :math:`\rho_{water}`: density [kg/m³], g: standard gravity [m/s2],
        Q: water flow [m3/s], W: water level [m], Q_{n}: nominal water flow [m3/s], W_{n}:n ominal water level [m], 
	H_{n}: nominal head of water [m], \eta_{turbine}: efficiency of the turbine [], \eta_{generator}: efficiency of the generator []

    It is assumed that the efficiency for water flows above the maximum
    water flow given in the efficiency curve is the nominal efficiency 
    (the water surplus will be drained over the dam and impact the water head and thus the power output)

    References
    ----------
    .. [1] Quaschning, V.: "Regenerative Energiesysteme". 9. Auflage, München,
            Hanser, 2015, page 333


    """

    load = Q/hpp.Q_n
    power_output = pd.Series('',index=load.index,name='feedin_hydropower_plant')
    eta_turb = np.interp(load, hpp.eta_turb_values.index, hpp.eta_turb_values.eta,
                          left=0, right=0)
    for timestep in load.index:
        power_output[timestep] = eta_turb[load[timestep]] * hpp.eta_gen * g * rho * min(Q[timestep],hpp.Q_n) * (hpp.H_n+hpp.W_n-W[timestep])

    # Set index for time series
    try:
        series_index = Q.index
    except AttributeError:
        series_index = range(1, len(power_output)+1)
    power_output = pd.Series(data=power_output, index=series_index,
                             name='feedin_hydropower_plant')
    return power_output


def output_from_parameters(Q, W, hpp,rho,g):
    r"""
    Calculates the turbine power output using turbine efficiency values calculated from parameters.

    This function is carried out when the parameter `eta_turb_values` of an
    instance of the :class:`~.modelchain.Modelchain` class
    has not been filled in

    Parameters
    ----------
    Q : pandas.Series or array
        Water flow in m3/s.
    W : pandas.Series or array
        Water level in m.
    hpp : instance of the :class:`~.hydropower_plant.HydropowerPlant` class
        Specifications of the hydropower plant
    rho : float
        Density of water in kg/m³.
    g : float
        Acceleration of gravity in m/s2.   

    Returns
    -------
    power_output : pandas.Series
        Electrical power output of the hydropower plant in W.

    Notes
    -------
    It is assumed that the efficiency for water flows above the maximum
    water flow given in the efficiency curve is the nominal efficiency 
    (the water surplus will be drained over the dam and impact the water head and thus the power output)

    See :py:func:`output_from_eta_values` for further information on how the power values
    are calculated

    """

    load = Q/hpp.Q_n
    power_output = pd.Series('',index=load.index,name='feedin_hydropower_plant')
    for timestep in load.index:
        if load[timestep]<hpp.turbine_parameters["load_min"][0]:
            eta_turb=0
            power_output[timestep] = eta_turb * hpp.eta_gen * g * rho* min(Q[timestep], hpp.Q_n) * (hpp.H_n + hpp.W_n - W[timestep])
        elif load[timestep]>=1:
            eta_turb=hpp.turbine_parameters["eta_n"][0]
            power_output[timestep] = eta_turb * hpp.eta_gen * g * rho* min(Q[timestep], hpp.Q_n) * (
            hpp.H_n + hpp.W_n - W[timestep])
        else:
            eta_turb=(load[timestep]-hpp.turbine_parameters["load_min"][0])/(hpp.turbine_parameters["a1"][0]+hpp.turbine_parameters["a2"][0]*(load[timestep]-hpp.turbine_parameters["load_min"][0])+hpp.turbine_parameters["a3"][0]*(load[timestep]-hpp.turbine_parameters["load_min"][0])*(load[timestep]-hpp.turbine_parameters["load_min"][0]))
        power_output[timestep] = eta_turb * hpp.eta_gen * g * rho* min(Q[timestep], hpp.Q_n) * (
        hpp.H_n + hpp.W_n - W[timestep])
    #power_output = eta_turb*hpp.eta_gen*g*rho*min(Q,hpp.Q_n)*(hpp.H_n+hpp.W_n-W)
    # Set index for time series

    return power_output

