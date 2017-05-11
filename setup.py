import os
from setuptools import setup
from hydropowerlib import __version__

setup(name='hydropowerlib',
      version=__version__,
      description='Creating time series from hydropower plants.',
      url='http://github.com/hydro-python/hydropowerlib',
      author='oemof developing group',
      author_email='mail',
      license=None,
      packages=['hydropowerlib'],
      package_data={
          'hydropowerlib': [os.path.join('data', '*.csv')]},
      zip_safe=False,
      install_requires=['numpy >= 1.7.0',
                        'pandas >= 0.13.1'])
