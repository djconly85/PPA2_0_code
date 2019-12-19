# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 12:57:40 2019

@author: dconly
"""

import os, pandas as pd, arcpy
import PPA2_master_ctypes_byfy as polyagg

arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'



base_year = 2016
future_year = 2016
trip_shed_in = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\ReplicaTShed_SECTest'
case_col = 'OBJECTID'


df_base = polyagg.get_ppa_agg_data(trip_shed_in, case_col, base_year, future_year, test_run=False)

df_base_t = df_base.T

