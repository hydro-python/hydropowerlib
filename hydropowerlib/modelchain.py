"""
The ``modelchain`` module contains functions and classes of the
hydropowerlib. This module makes it easy to get started with the hydropowerlib
and demonstrates standard ways to use the library.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
import sys
from hydropowerlib.hydropowerlib import power_output


class Modelchain(object):
    r"""Model to determine the output of a hydropower plant

    Parameters
    ----------
    hydropower_plant : HydropowerPlant
        A :class:`~.hydropower_plant.HydropowerPlant` object representing the hydropower
        plant.
    rho_model : string
        Parameter to define which model to use to calculate the density of water in the turbine. 
        Valid options are 'default' and 'from_temp'.
        Default: 'default'.
    g_model : string 
        Parameter to define which model to use to calculate the acceleration of gravity. 
        Valid options are 'default' and 'from_lat'.
        Default: 'default'.


    Attributes
    ----------
    hydropower_plant : HydropowerPlant
        A :class:`~.hydropower_plant.HydropowerPlant` object representing the hydropower
        plant.
    rho_model : string
        Parameter to define which model to use to calculate the density of water in the turbine. 
        Valid options are 'default' and 'from_temp'.
        Default: 'default'.
    g_model : string 
        Parameter to define which model to use to calculate the acceleration of gravity. 
        Valid options are 'default' and 'from_lat'.
        Default: 'default'.       
    power_output : pandas.Series
        Electrical power output of the hydropower plant in W.

    Examples
    --------
    >>> from hydropowerlib.hydropowerlib import modelchain
    >>> from hydropowerlib.hydropowerlib import hydropower_plant
    >>> example_plant = {
    ...    'H_n': 4.23,
    ...    'Q_n': 12,
    ...    'W_n': 2,
    ...    'turbine_type': 'Kaplan'}
    >>> example = hydropower_plant.HydropowerPlant(**example_plant)
    >>> modelchain_data = {'g_model': default,'rho_model': default}
    >>> example_md = modelchain.Modelchain(example, **modelchain_data)
    >>> print(example.H_n)
    4.23

    """

    def __init__(self, hydropower_plant,
                 g_model='default',
                 rho_model='default'):

        self.hydropower_plant = hydropower_plant
        self.g_model = g_model
        self.rho_model = rho_model
        self.power_output = None

    def rho(self, river_data):
        r"""
        
        Calculates the density of water in the turbine.

        The density is calculated using the method specified by the parameter
        `rho_model`. 

        Parameters
        ----------
        river_data : DataFrame or Dictionary
            Containing columns or keys with timeseries for temperature
            `temp_water` in K 

        Returns
        -------
        rho : float
            Density of water in kg/m³ at the location.

        """

        if self.rho_model is 'default':
            return 1000
        elif self.rho_model is 'from_temp':
            # Check if temperature data is available.
            if 'temp_water' not in river_data:
                logging.info('Missing values: the river data file does not have a water temperature column. Please use the default setting for the water density')
                sys.exit()
            else:
                # Calculate rho from water temperature
                return 1005
        else:
            logging.info(
                'The model used for water density does not exist. Possible values are default or from_temp ')
            sys.exit()


    def g(self):
        if self.g_model is 'default':
            return 9.81
        elif self.g_model is 'from_lat':
            # Check if latitude is available.
            if self.hydropower_plant.latitude is None:
                logging.info('Missing value: you did not enter the latitude of the hydropower plant. Please use the default setting for the gravitational acceleration')
                sys.exit()
            else:
                # Calculate g from latitude
                return 9.3
        else:
            logging.info(
                'The model used for gravity acceleration does not exist. Possible values are default or from_lat ')
            sys.exit()

    def turbine_power_output(self, Q, W,rho,g):
        r"""
        Calculates the power output of the hydropower plant.

        Parameters
        ----------
        Q : pandas.Series or array
            Flow of the river in m3/s.F
        W : pandas:Series or array
            Water level in m.
        rho : pandas.Series or array
            Density of water in kg/m³.
        g : float
            Acceleration of gravity in m/s2.

        Returns
        -------
        output : pandas.Series
            Electrical power in W of the hydropower plant.

        """

        if self.hydropower_plant.eta_turb_values is None:
            if self.hydropower_plant.turbine_type is None:
                logging.info(
                    'You have to specify either the turbine type or provide efficiency values. Use get_turbine_types for available turbine types.')
                sys.exit()
            else:
                # calculate from Quaschning
                output=power_output.output_from_parameters(Q,W,self.hydropower_plant,rho,g)
        else:
            # calculate from csv file
            output=power_output.output_from_eta_values(Q,W,self.hydropower_plant,rho,g)

        return output

    def run_model(self, river_data):
        r"""
        Runs the model.

        Parameters
        ----------
        river_data : DataFrame or Dictionary
            Containing columns or keys with the timeseries for river data
            water flow `Q` in m3/s , water level 'W' in m, temperature
            `T` in K.

        Returns
        -------
        self

        """
        Q=river_data['Q'];
        W=river_data['W']
        g = self.g()
        rho = self.rho(river_data)
        self.power_output = self.turbine_power_output(Q,W,rho,g)
        return self
