.. currentmodule:: hydropowerlib


Classes
=========

.. autosummary::
   :toctree: temp/

   hydropower_plant.HydropowerPlant
   modelchain.Modelchain

   

Hydropower plant data
====================

Functions and methods to obtain the nominal power as well as 
power curve or power coefficient curve needed by the :py:class:`~hydropower_plant.HydropowerPlant` class.


.. autosummary::
   :toctree: temp/

   hydropower_plant.HydropowerPlant.fetch_turbine_data
   hydropower_plant.get_turbine_types
   hydropower_plant.read_turbine_data


Power output
==============

Functions for calculating power output of an hydropower plant.

.. autosummary::
   :toctree: temp/

   power_output.output_from_parameters
   power_output.output_from_eta_values


Modelchain
==============

Creating a Modelchain object.

.. autosummary::
   :toctree: temp/

   modelchain.Modelchain

Running the modelchain.

.. autosummary::
   :toctree: temp/

   modelchain.Modelchain.run_model

Methods of the Modelchain object.

.. autosummary::
   :toctree: temp/

   modelchain.Modelchain.rho
   modelchain.Modelchain.g
   modelchain.Modelchain.turbine_power_output