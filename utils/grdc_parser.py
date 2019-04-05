"""
Encode GRDC station data into a tabular format requested by Geesthacht for them
to determine which grid cell to use for loading from their mean river flow
"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import numpy as np
import pandas as pd
import geopandas as gpd
import fiona
from shapely.geometry import Point
import os

# Maps HydroBASINS number of the most downstream sink of rivers to their counterparts in HD-Model
RIVER_MAP = {
    2040023010: 8,  # 'RHINE RIVER'
    2040026060: 10, # 'ODER RIVER'
    2040024170: 12, # 'ELBE RIVER'
    2030008490: 14, # 'DANUBE RIVER'
    2060023600: 19, # 'EMS RIVER'
    2060023940: 21  # 'WESER RIVER'
}

HYDRO_BASINS_DATA_PATH_TEMPLATE = os.path.join(
    'data',
    'HydroBasins',
    'hybas_eu_lev01-12_v1c',
    'hybas_eu_lev{}_v1c.shp'
)

def load_feature(shpfn, **selector):
    with fiona.open(shpfn) as fin:
        def is_match(x):
            return all(x[k] == v for k, v in selector.items())
        try:
            return next((x for x in fin if is_match(x["properties"])))
        except StopIteration:
            raise KeyError(f"Selector {selector} did not find any matching feature.")

def load_hydrobasins_feature(hybas_id, hydrobasins_data_path_template=HYDRO_BASINS_DATA_PATH_TEMPLATE):
    level = str(hybas_id)[1:3]
    return load_feature(hydrobasins_data_path_template.format(level), HYBAS_ID=hybas_id)

def load_hydrobasins_cover(river_map=RIVER_MAP, hydrobasins_data_path_template=HYDRO_BASINS_DATA_PATH_TEMPLATE):
    features = [load_hydrobasins_feature(i, hydrobasins_data_path_template) for i in river_map.keys()]
    return gpd.GeoDataFrame.from_features(features).set_index(pd.Index(river_map.values(), name="GEESTHACHT_ID"))

def format_station_file(
        station_fname='grdc_formatted.txt',
        grdc=None,
        grdc_path='data/grdc_stations.xlsx',
        country_code='DE',
        hydrobasins_cover=None,
        hydrobasins_river_map=RIVER_MAP,
        hydrobasins_data_path_template=HYDRO_BASINS_DATA_PATH_TEMPLATE,
):

    if hydrobasins_cover is None:
        hydrobasins_cover = load_hydrobasins_cover(hydrobasins_river_map, hydrobasins_data_path_template)

    if grdc is None:
        # load the grdc data
        grdc = pd.read_excel(grdc_path, na_values=[-999])

    if country_code is not None:
        # select data from a country only
        grdc = grdc.loc[grdc.country == country_code]

    def find_river_idx(point):
        idx = hydrobasins_cover.index[hydrobasins_cover.contains(point)]
        if idx.empty:
            return -1
        elif len(idx) > 1:
            print(f"{point.xy} in more than one basin: {list(hydrobasins_cover.index[contains_b])}")
        else:
            return idx[0]

    river_idx = grdc[["long", "lat"]].apply(Point, axis=1).map(find_river_idx)

    formatted_grdc = pd.DataFrame({
        'GRDC-No.': grdc.grdc_no,
        'Cat.': river_idx,
        'Longitude': grdc.long,
        'Latitude': grdc.lat,
        'ilon': 0,
        'ilat': 0,
        'HD5 Area': 0,
        'Obs. Area': grdc.area,
        'Station': grdc.station
    })

    # save the formatted grdc station file to a fixed with file
    header = "GRDC-No. Cat. Longitude  Latitude  ilon ilat HD5 Area  Obs. Area Station\n"
    fmt = ' %i %4d % 9.4f % 9.4f %5d %4d %8.f. %8.f. %1s'
    np.savetxt(station_fname, formatted_grdc.values, fmt=fmt, header=header, comments="")


if __name__ == '__main__':
    format_station_file()
