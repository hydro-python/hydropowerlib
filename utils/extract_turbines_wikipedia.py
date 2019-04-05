"""
Convert turbine flow<->height polygons given as matlab code on wikipedia to geojson

Runs `octave` on the matlab code in `turbines.m` which saves the polygons to
`turbines.mat` as f.ex.:

              flow  height
PelDubble =  [0.5   110     # Source Voith / Dubbel
              30    250
              50    700
              30    1000
              5     1900
              0.5   1900];

Polygons for the turbine types Pelton, Francis and Kaplan are taken from
multiple producers and we use the union of the different turbines. All turbines
in the SVG on Wikipedia [1] are available in principle.

References
----------
[1] https://de.wikipedia.org/wiki/Datei:Kennfeld_Wasserturbinen.svg
by Jahobr 2017-01-10
"""

import sys
import geopandas as gpd
from scipy.io import loadmat
from shapely.geometry import Polygon
from shapely.ops import cascaded_union as union
from operator import itemgetter
from subprocess import run
from collections import OrderedDict

def extract_turbines_from_matlab(fnin="turbines.m", fnout="turbines.geojson"):
    if fnin.endswith(".m"):
        octavescript = fnin
        fnin = fnin[:-len(".m")] + ".mat"
        print("Running octave on {} in the hope it updates {}.".format(octavescript, fnin))
        run(["octave", octavescript], check=True)

    turbine_data = loadmat(fnin)
    def turbinepoly(*names):
        return union([Polygon(turbine_data[n]) for n in names])

    # The order is significant, since we want to use the first turbine if there are multiple matches
    turbines = gpd.GeoSeries(OrderedDict((
        ('Francis', turbinepoly("FraAndritz", "FraDubbel")),
        ('Pelton', turbinepoly("PelAndritz", "PelBieudron", "PelDubble")),
        ('Kaplan', turbinepoly("KapAndritz", "KapDubbel")),
    )))

    turbines.to_file(fnout, driver="GeoJSON")

    print("Converted phase shapes from {} for {} turbines ({}) and saved them to {}."
          .format(fnin, len(turbines), ", ".join(turbines.index), fnout))


if __name__ == "__main__":
    extract_turbines_from_matlab(*sys.argv[1:])
