# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 15:33:40 2020

@author: dconly
"""

import arcpy


scratch_gdb = arcpy.env.scratchGDB
arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

fc_in = 'parcel_data_pts_2016_1' # 'sacog_region' 'parcel_data_pts_2016'
fl_from_fc = 'fl_from_fc'


def make_fl_layer(fc, fl):
    print("making feature layer...")
    arcpy.MakeFeatureLayer_management(fc_in, fl_from_fc)

def make_fl_conditional(fc, fl):
    
    print('remaking feature layer from {} fc if feature layer exists...'.format(fc_in))
    if arcpy.Exists(fl):
        arcpy.Delete_management(fl)
    arcpy.MakeFeatureLayer_management(fc, fl)
    
# ===============================================================


make_fl_conditional(fc_in, fl_from_fc)

print("now trying same operation 2nd time in a row...")
make_fl_conditional(fc_in, fl_from_fc)
    
    


