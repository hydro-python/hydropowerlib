"""
The ``modelchain`` module contains functions and classes of the
hydropowerlib. This module makes it easy to get started with the hydropowerlib
and demonstrates standard ways to use the library.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
import sys
import os
import pandas as pd
import numpy as np
import datetime
from git_repos.hydropowerlib.hydropowerlib import power_output


class Modelchain(object):
    r"""Model to determine the output of a hydropower plant

    Parameters
    ----------
    HPP : HydropowerPlant
        A :class:`~.hydropower_plant.HydropowerPlant` object representing the hydropower
        plant.
    dV : pandas.DataFrame
        Containing DateTime index and column with water flow `dV` in m3/s over the period to simulate
    dV_hist : pandas.DataFrame
        Containing DateTime index and column with water flow `dV` in m3/s over several past years.
        Used to extrapolate the missing values about the plant.
    file_turb_eff : string 
        Name of the file containing parameters about the turbine efficiency.
    file_turb_graph : 
        Name of the file containing the characteristic diagrams.

    Attributes
    ----------
    HPP : HydropowerPlant
        A :class:`~.hydropower_plant.HydropowerPlant` object representing the hydropower
        plant.
    dV : pandas.DataFrame
        Containing DateTime index and column with water flow `dV` in m3/s over the period to simulate
    dV_hist : pandas.DataFrame
        Containing DateTime index and column with water flow `dV` in m3/s over several past years.
        Used to extrapolate the missing values about the plant.
    file_turb_eff : string 
        Name of the file containing parameters about the turbine efficiency.
    file_turb_graph : 
        Name of the file containing the characteristic diagrams.

    Examples
    --------
    >>> from hydropowerlib.hydropowerlib import modelchain
    >>> from hydropowerlib.hydropowerlib import hydropower_plant
    >>> example_plant = {
    ...    'H_n': 4.23,
    ...    'Q_n': 12,
    ...    'turbine_type': 'Kaplan'}
    >>> example = hydropower_plant.HydropowerPlant(**example_plant)
    >>> modelchain_data = {'dV': df_runoff,'dV_hist': df_dV_hist}
    >>> example_md = modelchain.Modelchain(example, **modelchain_data)
    >>> print(example.H_n)
    4.23

    """

    def __init__(self, HPP,dV,dV_hist=None,file_turb_eff='turbine_type.csv',file_turb_graph='charac_diagrams.csv'):

        self.HPP = HPP
        self.dV=dV
        self.dV_hist = dV_hist
        self.file_turb_eff = file_turb_eff
        self.file_turb_graph = file_turb_graph

        if self.check_feasibility() is False:
            logging.info(
                'The input data is not sufficient for plant %s' %self.HPP.id)
            sys.exit()

        if self.HPP.dV_rest is None :
            HPP.dV_rest=self.get_dV_rest()

        if self.HPP.dV_n is None:
            HPP.dV_n = self.get_dV_n()

        if self.HPP.P_n is None:
            HPP.P_n = self.get_P_n()

        if self.HPP.h_n is None:
            HPP.h_n = self.get_h_n()

        if self.HPP.turb_type is None:
            HPP.turb_type = self.get_turb_type()


    def check_feasibility(self):
        r"""
        Test if the input data is sufficient to simulate the plant.
        The simulation is feasible if two parameters among (dV_n, h_n and P_n) are known. 
        If dV_n is not known, it can be extrapolated from dv_hist
        The logical expression verifying the feasibility is (h_n and P_n) or ((h_n or P_n) and (dV_hist or dV_n))
        :return: 
        boolean : True if sufficient
        """
        return (((self.HPP.h_n is not None) and (self.HPP.P_n is not None)) or (((self.HPP.h_n is not None) or (self.HPP.P_n is not None)) and (( self.dV_hist is not None) or (self.HPP.dV_n is not None))))


    def get_dV_rest(self):
        r"""
        Get value for dV_rest. dV_rest is calculated from the mean flow duration curve over several years.
        The mean flow duration curve is obtained through dV_hist. If dV_hist is not given, dV_rest is set to 0.
         Source for calculation of dV_rest : "Wahl, Dimensionierung und Abnahme einer Kleinturbine" from PACER
        :return:
        float
        """
        if self.dV_hist is None :
            return 0
        else :
            recent=self.dV_hist.sort_index().iloc[self.dV_hist.count()-1].index[0]
            try:
                ten_years = datetime.datetime(recent.year - 10, recent.month, recent.day)+datetime.timedelta(days=1)
            except ValueError:
                ten_years = datetime.datetime(recent.year - 10, recent.month, recent.day - 1)+datetime.timedelta(days=1)
            dV_ten_years=self.dV_hist.sort_index().loc[ten_years:recent]
            dV_mean = dV_ten_years.groupby([dV_ten_years.index.month, dV_ten_years.index.day]).mean()
            mean_year = pd.Series(dV_mean['dV'].values, index=np.arange(1, 367, 1))
            mean_fdc = pd.Series(mean_year.sort_values(ascending=False).values, index=mean_year.index)
            dV_347 = mean_fdc.loc[347]
            if dV_347 < 0.06:
                return 0.05
            elif dV_347 < 0.16:
                return 0.05 + (dV_347 - 0.6) * 8 / 10
            elif dV_347 < 0.5:
                return 0.130 + (dV_347 - 0.5) * 4.4 / 10
            elif dV_347 < 2.5:
                return 0.28 + (dV_347 - 0.13) * 31 / 100
            elif dV_347 < 10:
                return 0.9 + (dV_347 - 2.5) * 21.3 / 100
            elif dV_347 < 60:
                return 2.5 + (dV_347 - 10) * 150 / 1000
            else:
                return 10


    def get_dV_n(self):
        r"""
        Get value for dV_n, the nominal water flow through the turbine. 
        If P_n and h_n are known, dV_n is calculated through equation P_n=h_n*dV_n*g*rho*eta_g_n*eta_t_n
        Where g=9.81 m/s², rho=1000 kg/m³, eta_g_n (nominal generator efficiency)=0.95 and 
        eta_t_n (nominal turbine efficiency)=0.9
        Otherwise dV_n is calculated from the flow duration curve over several years, after subtracting dV_rest.
        It is the water flow reached or exceeded 20% of the time.
        :return: 
        float
        """
        if self.HPP.h_n is not None and self.HPP.P_n is not None:
            return self.HPP.P_n/(self.HPP.h_n*9.81*1000*0.9*0.95)
        else:
            fdc = pd.Series(self.dV_hist.sort_values(by='dV', ascending=False).dV.values - self.HPP.dV_rest,
                        index=np.arange(1, 100, 99 / self.dV_hist.count()))
            return np.interp(20,fdc.index,fdc.values)


    def get_P_n(self):
        r"""
        Get value for P_n through equation P_n=h_n*dV_n*g*rho*eta_g_n*eta_t_n
        Where g=9.81 m/s², rho=1000 kg/m³
        eta_g_n (nominal generator efficiency)=0.95 and eta_t_n (nominal turbine efficiency)=0.9
        :return: 
        float
        """
        return self.HPP.h_n*self.HPP.dV_n*9.81*1000*0.9*0.95


    def get_h_n(self):
        r"""
        Get value for h_n through equation P_n=h_n*dV_n*g*rho*eta_g_n*eta_t_n
        Where g=9.81 m/s², rho=1000 kg/m³
        eta_g_n (nominal generator efficiency)=0.95 and eta_t_n (nominal turbine efficiency)=0.9
        :return: 
        float
        """
        return self.HPP.P_n/(self.HPP.dV_n*9.81*1000*0.9*0.95)


    def get_turb_type(self):
        r"""
        Fetches type of the requested hydropower turbine by situating it on a h_n/dV_n characteristic diagram of different turbines.
        The characteristic zones of each turbine are polygons in a dV_n / h_n plan and are defined by their angles.
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

        try:
            df = pd.read_csv(os.path.join(os.path.join(os.path.dirname(__file__), 'data'), self.file_turb_graph),index_col=0)
        except IOError:
            logging.info(
                'No file %s in data folder' %self.file_turb_graph)
            sys.exit()
        turbine_types = []
        charac_diagrams = pd.DataFrame()

        for col in df.columns:
            turbine_type = col.split('_')[0]
            if turbine_type not in turbine_types:
                turbine_types.append(turbine_type)
                charac_diagrams[turbine_type] = ""
            for i in df.index:
                if col.split('_')[1] == 'dV':
                    charac_diagrams.at[i, turbine_type] = df.loc[i, col]
                elif col.split('_')[1] == 'h':
                    charac_diagrams.at[i, turbine_type] = [charac_diagrams.loc[i, turbine_type], df.loc[i, col]]

        for turbine_type in turbine_types:
            intersections = 0
            for i in charac_diagrams.index:
                if i == len(charac_diagrams.index):
                    if intersec([self.HPP.dV_n/self.HPP.turb_num,self.HPP.h_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[1, turbine_type]):
                        intersections = intersections + 1
                else:
                    if (charac_diagrams.loc[i + 1, turbine_type])[0] != (charac_diagrams.loc[i + 1, turbine_type])[0] or (charac_diagrams.loc[i + 1, turbine_type])[1] != (charac_diagrams.loc[i + 1, turbine_type])[1]:
                        if intersec([self.HPP.dV_n/self.HPP.turb_num,self.HPP.h_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[1, turbine_type]):
                            intersections = intersections + 1
                        break
                    else:
                        if intersec([self.HPP.dV_n/self.HPP.turb_num,self.HPP.h_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[i + 1, turbine_type]):
                            intersections = intersections + 1
            if intersections % 2 != 0:
                return turbine_type
                break

        logging.info('Turbine type could not be defined for plant %s. Dummy type used' %self.HPP.id)
        return 'dummy'


    def run_model(self):
        r"""
        Runs the model
        :return: 
        pandas.DataFrame
        """

        self.HPP.power_output = power_output.run(self.HPP, self.dV-self.HPP.dV_rest,self.file_turb_eff)
