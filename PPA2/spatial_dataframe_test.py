# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 15:03:38 2020

@author: dconly

PURPOSE:
    Compares speed for loading an ESRI object to a pandas dataframe for following methods:
        Method 1 - feature class > feature layer > 2-dimensional list > dataframe (non-spatial)
        Method 2 - feature class > spatial dataframe using ESRI's GeoAccessor'
        
RESULTS:
    Method 1 (using searchcursor) is faster:
        about 10x faster for a small feature class (548 features)
        a little more than 2x faster for a larer (57,700 features) feature class


https://developers.arcgis.com/python/guide/introduction-to-the-spatially-enabled-dataframe/
"""

import os, time

import arcpy
import pandas as pd
# from arcgis.features import SpatialDataFrame
from arcgis.features import GeoAccessor, GeoSeriesAccessor


in_fc = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\parcel_data_pts_2016'
in_fc_small = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\Collisions2014to2018fwytag'

load_searchcursor = True
#==================================


fl = "fl"
if arcpy.Exists(fl): arcpy.Delete_management(fl)
arcpy.MakeFeatureLayer_management(in_fc, fl)

sql = 'EJ_2018 = 1'
arcpy.SelectLayerByAttribute_management(fl, "NEW_SELECTION", sql)



fl_small = "fl_small"
if arcpy.Exists(fl_small): arcpy.Delete_management(fl_small)
arcpy.MakeFeatureLayer_management(in_fc_small, fl_small)


def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    '''converts esri gdb table, feature class, feature layer, or SHP to pandas dataframe'''
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df



#time test to put into pandas df using searchcursor
if load_searchcursor:
    print("loading via search cursor...")
    st = time.clock()
    fields = [f.name for f in arcpy.ListFields(fl_small)]
    df_from_searchcur = esri_object_to_df(fl_small, fields, index_field=None)
    
    runsec_searchcursor = time.clock() - st
    
    df_from_searchcur # clean up memory




#time test to load to spatial dataframe using arcpy's spatial dataframe
print("loading by spatial df loader...")
st2 = time.clock()
df_from_spatialdf = pd.DataFrame.spatial.from_featureclass(in_fc_small)

runsec_sdfloader = time.clock() - st2

print(f"searchcursor took {runsec_searchcursor} secs to load\n" \
      f"spatial df loader took {runsec_sdfloader} seconds")