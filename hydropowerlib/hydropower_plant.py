"""
The ``hydropower_plant`` module contains the class HydropowerPlant that implements
a run-of-the-river hydropower plant in the hydropowerlib and functions needed for the modelling of a
hydropower plant.

"""

import pandas as pd
import logging
import sys
import os
import numpy as np

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"


class HydropowerPlant(object):
    r"""
    Defines a standard set of hydropower plant attributes.

    Parameters
    ----------
    turbine_type : string
        Type of the turbine.
        Use get_turbine_types() to see a list of all turbines for which
        efficiency curve data is provided.
    Q_n : float
        Nominal water flow entering the plant in m3/s.
    H_n : float
        Nominal head of water in m.
    W_n : float
        Nominal water level leaving the plant in m.
    Q_rest : float
        Part of the water flow that cannot be used (fish ladder, compulsory minimal water flow leaving the plant...)
    eta_turb_values : pandas.DataFrame
        Efficiency of the turbine depending on partial load.
        The indices of the DataFrame are the corresponding partial loads of the
        efficiency curve, the efficiency values are listed in
        the column 'eta_turb'. Default: None.
    turbine_parameters : pandas.DataFrame
        Parameters to calculate the efficiency of the turbine
    eta_gen : float
        Efficiency of the generator.
    latitude : float
        Latitude of the plant (to calculate g)


    Attributes
    ----------
    turbine_type : string
        Type of the turbine.
        Use get_turbine_types() to see a list of all turbines for which
        efficiency curve data is provided.
    Q_n : float
        Nominal water flow entering the plant in m3/s.
    H_n : float
        Nominal head of water in m.
    W_n : float
        Nominal water level leaving the plant in m.
    Q_rest : float
        Part of the water flow that cannot be used (fish ladder, compulsory minimal water flow leaving the plant...)
    eta_turb_values : pandas.DataFrame
        Efficiency of the turbine depending on partial load.
        The indices of the DataFrame are the corresponding partial loads of the
        efficiency curve, the efficiency values are listed in
        the column 'eta_turb'. Default: None.
    turbine_parameters : pandas.DataFrame
        Parameters to calculate the efficiency of the turbine
    eta_gen : float
        Efficiency of the generator.
    latitude : float
        Latitude of the plant (to calculate g)        
    power_output : pandas.Series
        The calculated power output of the wind turbine.

    Examples
    --------
    >>> from hydropowerlib.hydropowerlib import hydropower_plant
    >>> example_plant = {
    ...    'H_n': 4.23,
    ...    'Q_n': 12,
    ...    'W_n': 2,
    ...    'turbine_type': 'Kaplan'}
    >>> example = hydropower_plant.HydropowerPlant(**example_plant)
    >>> print(example.Q_n)
    12

    """

    def __init__(self, Q_n, H_n, W_n, Q_rest, eta_gen, turbine_type=None, eta_turb_values=None,
                 turbine_parameters = None,latitude=None):

        self.turbine_type = turbine_type
        self.Q_n = Q_n
        self.H_n = H_n
        self.W_n = W_n
        self.Q_rest = Q_rest
        self.eta_turb_values = eta_turb_values
        self.turbine_parameters = turbine_parameters
        self.eta_gen = eta_gen
        self.latitude=latitude


        self.power_output = None

        if self.turbine_type is None :
            self.fetch_turbine_type()

        if self.eta_turb_values is None and self.turbine_parameters is None:
            self.turbine_parameters=self.fetch_turbine_data()


    def fetch_turbine_data(self):
        r"""
        Fetches data of the requested hydropower turbine.

        Method fetches the nominal efficiency, minimum load, as well as parameters to calculate the efficiency curve from a data file provided along with the hydropowerlib.

        Examples
        --------
        >>> from hydropowerlib.hydropowerlib import hydropower_plant
        >>> example_plant = {
        ...    'H_n': 4.23,
        ...    'Q_n': 12,
        ...    'W_n': 2,
        ...    'turbine_type': 'Kaplan'}
        >>> example = hydropower_plant.HydropowerPlant(**example_plant)
        >>> print(example.turbine_parameters.eta_nom[0])
        0.423


        """

        def restructure_data():
            df = read_turbine_data(filename=filename)
            hpp_df = df[df.type == self.turbine_type]
            if hpp_df.shape[0] == 0:
                pd.set_option('display.max_rows', len(df))
                logging.info('Possible types: \n{0}'.format(df.type))
                pd.reset_option('display.max_rows')
                sys.exit('Cannot find the turbine type: {0}'.format(
                    self.turbine_type))

            return hpp_df
        filename='turbine_type.csv'
        return restructure_data()

    def fetch_turbine_type(self):
        r"""
        Fetches type of the requested hydropower turbine by situating it on a H_n/Q_n characteristic diagram of different turbines.
        The characteristic zones of each turbine are polygons in a Q_n / H_n plan and are defined by their angles.
        The list of angles for each type of turbine is given in "data/charac_diagrams.csv" and is based on https://de.wikipedia.org/wiki/Wasserturbine#/media/File:Kennfeld.PNG
        :return: 
        """

        def ccw(A, B, C):
            r"""
            Function to check if three points are called counterclockwise or clockwise
            Based on http://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
            :param A: [float, float]
            Coordinates of the first point
            :param B: [float, float]
            Coordinates of the second point
            :param C: [float, float]
            Coordinates of the third point
            :return: 
            True if A, B and C are in counterclockwise order
            False if A, B and C are in clockwise order
            """
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


        def intersec(A, B, C):
            r"""
            Function to determine if the half line defined as y=yA and x>=xA crosses the [BC[ segment
            Based on http://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
            :param A: [float, float]
            :param B: [float, float]
            :param C: [float, float]
            :return: bool
            """
            if B == C:
                # if [BC] is a point
                return False
            else:
                if B[1] == C[1]:
                    # if [BC[ is horizontal
                    # the segment and the horizontal half-line are parallel and never cross
                    # (overlapping is not considered an intersection here)
                    return False
                elif A[1] == B[1] and A[0] <= B[0]:
                    # in order not to count twice an intersection on an angle of the polygon,
                    # only the segment [BC[ is considered
                    return True
                elif A[1] == C[1]:
                    return False
                else:
                    # define a point on the horizontal half-line starting in A
                    # check if the two segments intersect
                    D = (max(B[0], C[0]) + 1, A[1])
                    return ccw(A, C, B) != ccw(D, C, B) and ccw(A, D, C) != ccw(A, D, B)

        df = pd.read_csv('data/charac_diagrams.csv', index_col=0)
        turbine_types = []
        charac_diagrams = pd.DataFrame()

        for col in df.columns:
            turbine_type = col[:len(col) - 3]
            if turbine_type not in turbine_types:
                turbine_types.append(turbine_type)
                charac_diagrams[turbine_type] = ""
            for i in df.index:
                if col[-2:] == 'Qn':
                    charac_diagrams.at[i, turbine_type] = df.loc[i, col]
                elif col[-2:] == 'Hn':
                    charac_diagrams.at[i, turbine_type] = [charac_diagrams.loc[i, turbine_type], df.loc[i, col]]

        for turbine_type in turbine_types:
            intersections = 0
            for i in charac_diagrams.index:
                if i == len(charac_diagrams.index):
                    if intersec([self.Q_n,self.H_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[1, turbine_type]):
                        intersections = intersections + 1
                else:
                    if (charac_diagrams.loc[i + 1, turbine_type])[0] != (charac_diagrams.loc[i + 1, turbine_type])[0] or \
                                    (charac_diagrams.loc[i + 1, turbine_type])[1] != (charac_diagrams.loc[i + 1, turbine_type])[1]:
                        if intersec([self.Q_n,self.H_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[1, turbine_type]):
                            intersections = intersections + 1
                        break
                    else:
                        if intersec([self.Q_n,self.H_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[i + 1, turbine_type]):
                            intersections = intersections + 1
            if intersections % 2 != 0:
                self.turbine_type=turbine_type
                break
        if self.turbine_type is None:
            logging.info('Turbine type could not be defined')
            sys.exit()

def read_turbine_data(**kwargs):
    r"""
    Fetches turbine nominal efficiency, minimal load and parameters to calculate the efficiency curve from a file.

    The data file is provided along with the hydropowerlib and are located in
    the directory hydropowerlib/data.

    Other Parameters
    ----------------
    datapath : string, optional
        Path where the data file is stored. Default: './data'
    filename : string, optional
        Name of data file. Default: 'turbine_types.csv'

    Returns
    -------
    pandas.DataFrame
        Power coefficient curve values or power curve values with the
        corresponding wind speeds as indices.

    """
    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.dirname(__file__), 'data')

    if 'filename' not in kwargs:
        kwargs['filename'] = 'turbine_type.csv'

    df = pd.read_csv(os.path.join(kwargs['datapath'], kwargs['filename']),
                     index_col=0)
    return df


def get_turbine_types(print_out=True, **kwargs):
    r"""
    Get the names of all possible turbine types for which the parameters are provided in the data files in
    the directory hydropowerlib/data.

    Parameters
    ----------
    print_out : boolean
        Directly prints the list of types if set to True. Default: True

    Examples
    --------
    >>> from hydropowerlib.hydropowerlib import hydropower_plant
    >>> valid_types_df = hydropower_plant.get_turbine_types(print_out=False)
    >>> print(valid_types_df.iloc[5])
    turbine_type    Kaplan
    eta_nom         0.895
    Name: 5, dtype: object

    """
    df = read_turbine_data(**kwargs)

    if print_out:
        pd.set_option('display.max_rows', len(df))
        print(df[['type', 'eta_nom']])
        pd.reset_option('display.max_rows')
    return df[['type', 'eta_nom']]