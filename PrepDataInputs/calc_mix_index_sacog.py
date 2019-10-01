# -*- coding: utf-8 -*-
#--------------------------------
# Name:calc_mix_index_sacog.py
# Purpose: calculate the mix index for PPA, with emphasis on measuring how
#          conducive the land use mix is to replacing drive trips with walk
   #        trips due to daily needs like retail, schools, etc. being within walk distance           

# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
#--------------------------------

import pandas as pd
import arcpy
from arcgis.features import GeoAccessor, GeoSeriesAccessor


#output csv for testing
out_csv = r'C:\Users\dconly\PPA_TEMPFILES\test_mixindex_out.csv'

#weighting values {land use:[optimal ratio per household, weight given to that ratio]}
wgts_sacog_standard = {'SUM_ENR_K12_propl':[0.5,0.4],
                       'SUM_EMPRET_propl':[0.25, 0.4],
                       'SUM_EMPTOT_propl':[1.2, 0.2]
                       }

col_hh = 'SUM_HH_hh_propl'
input_cols_sacog_standard = ['SUM_EMPTOT_propl', 'SUM_ENR_K12_propl',
       'SUM_EMPRET_propl']

input_cols_all = ['SUM_EMPTOT_propl', 'SUM_ENR_K12_propl',
       'SUM_EMPRET_propl', 'SUM_EMPSVC_propl', 'SUM_EMPFOOD_propl']


arcpy.env.workspace = r'Q:\SACSIM19\Integration Data Summary\ILUT GIS\ILUT GIS.gdb'

fc_poly_in = 'hex_ILUT20190925ilut_combined2016_22_2'

#=====================================================================


#make spatial pandas data frame from input layer
sdf_poly = pd.DataFrame.spatial.from_featureclass(fc_poly_in)

#calculate ideal balance numbers, then ratios of actual vs. ideal balance.
for col in input_cols_sacog_standard:
#    print(col)
#    print(wgts_sacog_standard[col][0])
#    print(sdf_poly[col])
    
    bal_col = "{}_bal".format(col)
    sdf_poly.loc[sdf_poly[col_hh] != 0, bal_col] = sdf_poly[col] * wgts_sacog_standard[col][0]
    
    #set to -1 if no HHs in polygon, for "balance number" columns
    sdf_poly.fillna(-1)
    
    ratio_col = "{}_ratio".format(col)
    
    #if balance value > actual value, return actual value / balance value
    sdf_poly.loc[(sdf_poly[col_hh] != 0) & (sdf_poly[bal_col] > sdf_poly[col]), ratio_col] = sdf_poly[col] / sdf_poly[bal_col]
    
    #if balance value < actual value, return balance value / actual value
    sdf_poly.loc[(sdf_poly[col_hh] != 0) & (sdf_poly[bal_col] < sdf_poly[col]), ratio_col] = sdf_poly[bal_col] / sdf_poly[col]
    
#set to -1 if no HHs in polygon, for ratio columns
sdf_poly.fillna(-1)

#sdf_poly.to_csv(out_csv)

#calculate mix index

    
    
    
    

