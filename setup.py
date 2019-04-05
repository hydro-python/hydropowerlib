import os
from setuptools import setup

from .hydropowerlib import __version__

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(name='hydropowerlib',
      version=__version__,
      description='Creating time series from hydropower plants.',
      long_description=long_description,
      url='http://github.com/hydro-python/hydropowerlib',
      author='oemof developing group',
      author_email='mail',
      license='GPLv3',
      packages=['hydropowerlib'],
      package_data={'hydropowerlib': ['data/*.csv', 'data/*.geojson']},
      install_requires=['numpy', 'pandas', 'geopandas'])
