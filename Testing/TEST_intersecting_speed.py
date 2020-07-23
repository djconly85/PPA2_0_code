# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 08:36:28 2020

@author: dconly
Purpose: see if pre-selecting parcels around project prior to doing
intersect will make the intersecting process go faster

"""
import arcpy
import os

gdb = 
proj_fc = 
parcel_polys = 


fl_proj = "fl_proj"
fl_pcls = "fl_pcls"

arcpy.MakeFeatureLayer_management

#test 1 - pre-select first, then do intersect
arcpy.SelectLayerByLocation_management()


#test 2 - don't do pre-selection; just do intersect


