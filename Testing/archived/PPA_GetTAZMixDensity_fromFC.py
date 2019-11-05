# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 15:38:16 2019

@author: dconly
"""
#import re
import datetime as dt
import pandas as pd
#import arcpy
from arcgis.features import SpatialDataFrame as SDF

dt_suffix = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))

fc_parcels = r"I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\TEST_parcels_for_mixIndex_point2"

out_csv = r'I:\Projects\Darren\PPA_V2_GIS\CSV\Simpson_div_idx_x_taz{}.csv'.format(dt_suffix)
csv_lutypes_lookup = r"I:\Projects\Darren\PPA_V2_GIS\CSV\lutypes_lookup.csv"

col_taz = 'TAZ07'
col_netarea = 'GISAc'
col_lutype = 'LUTYPE'
col_lutype_rev = 'LUTYPE_rev'

excl_lutypes = 'EXCLUDE'

cols = [col_taz, col_netarea, col_lutype]


sdf_parcel = SDF.from_featureclass(fc_parcels)

df_x_taz_and_type = sdf_parcel.groupby([col_taz, col_lutype])[col_netarea].sum() #total TAZ area x land use type

dfpp = df_x_taz_and_type.reset_index()

#lookup of land use type sto consolidate similar land use types
df_lutypes_lookup = pd.read_csv(csv_lutypes_lookup)

dfpp = dfpp.merge(df_lutypes_lookup, on = col_lutype)

#pivot: cols = land use types, rows = TAZ IDs, values = total net acres of that land use on that TAZ
df_pivot = dfpp.pivot_table(values = col_netarea, index = col_taz, columns = col_lutype_rev, fill_value = 0)

#total area in each TAZ
df_sumarea_x_taz = df_pivot.sum(axis = 1)

#percent of each TAZ that is each land use type
df_sumdiv = df_pivot.div(df_sumarea_x_taz, axis = 0)

#square of the percents
df_sumdiv_square = df_sumdiv.applymap(lambda x: x **2)

#sum of squares by each taz. 0 = homogeneous land use, 1 = completely mixed (using Simpson Diversity Index)
df_dividx = df_sumdiv_square.sum(axis = 1)

df_dividx = pd.DataFrame(df_dividx)

df_dividx.reset_index() \
        .rename(columns = {0:'SimpDivIdx'})

df_dividx['SimpDivIdx'] = df_dividx['SimpDivIdx'].apply(lambda x: 1 - x)

df_final = df_pivot.merge(df_dividx, on = col_taz)

df_final.to_csv(out_csv, index = False, header = True)