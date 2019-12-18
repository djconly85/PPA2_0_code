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
import time

import pandas as pd
import swifter
import arcpy


col_k12_enr = 'SUM_ENR_K12_propl'
col_empret = 'SUM_EMPRET_propl'
col_emptot = 'SUM_EMPTOT_propl'
col_empsvc = 
col_empfood = 
col_parkac = 


def get_wtd_idx(x, facs, params_df):
    output = 0
    
    for fac in facs:
        fac_ratio = fac
        fac_ratio = '{}_ratio'.format(fac)
        fac_out = x[fac_ratio] * params_df.loc[fac]['weight']
        output += fac_out
    
    return output

if __name__ == '__main__':
    #output csv for testing
    out_csv = r'C:\Users\dconly\PPA_TEMPFILES\test_mixindex_out{}.csv'.format(int(time.time()))
    
    #weighting values {land use:[optimal ratio per household, weight given to that ratio]}
    wgts_sacog_standard = [[col_k12_enr, 0.392079056, 0.2],
             [col_empret, 0.148253453, 0.4],
             [col_emptot, 1.085980023, 0.05],
             [col_empsvc, 0.133409274, 0.1],
             [col_empfood, 0.097047321, 0.2],
             [col_parkac, 0.269931832, 0.05]
             ]
    
    
    col_hh = 'SUM_HH_hh_propl'
    input_cols_sacog_standard = ['SUM_EMPTOT_propl', 'SUM_ENR_K12_propl',
           'SUM_EMPRET_propl']
    
    input_cols_all = ['SUM_EMPTOT_propl', 'SUM_ENR_K12_propl',
           'SUM_EMPRET_propl', 'SUM_EMPSVC_propl', 'SUM_EMPFOOD_propl']
    
    
    arcpy.env.workspace = r'Q:\SACSIM19\Integration Data Summary\ILUT GIS\ILUT GIS.gdb'
    
    fc_poly_in = 'hex_ILUT20190925ilut_combined2016_22_2'
    
    #=====================================================================
    
    col_mix_idx = "MIX_IDX_2016"
    mix_calc_cols = ['lu_fac', 'bal_ratio_per_hh', 'weight']
    
    lu_params_df = pd.DataFrame(wgts_sacog_standard, columns = mix_calc_cols) \
    .set_index(mix_calc_cols[0])
    
    #make spatial pandas data frame from input layer
    sdf_poly = pd.DataFrame.spatial.from_featureclass(fc_poly_in)
    
    #calculate ideal balance numbers, then ratios of actual vs. ideal balance.
    for col in input_cols_sacog_standard:
    #    print(col)
    #    print(wgts_sacog_standard[col][0])
    #    print(sdf_poly[col])
        
        bal_col = "{}_bal".format(col)
        sdf_poly.loc[sdf_poly[col_hh] != 0, bal_col] = sdf_poly[col] * lu_params_df.loc[col][0]
        
        #set to -1 if no HHs in polygon, for "balance number" columns
        sdf_poly.fillna(-1)
        
        ratio_col = "{}_ratio".format(col)
        
        #if balance value > actual value, return actual value / balance value
        sdf_poly.loc[(sdf_poly[col_hh] != 0) & (sdf_poly[bal_col] > sdf_poly[col]), ratio_col] = sdf_poly[col] / sdf_poly[bal_col]
        
        #if balance value < actual value, return balance value / actual value
        sdf_poly.loc[(sdf_poly[col_hh] != 0) & (sdf_poly[bal_col] < sdf_poly[col]), ratio_col] = sdf_poly[bal_col] / sdf_poly[col]
        
        # NOTE! - if balance value is zero, then a null value will be returned for when calculating actual/balance
        
    #set to -1 if no HHs in polygon, for ratio columns
    sdf_poly.fillna(-1)
    
    #sdf_poly.to_csv(out_csv)
    
    #calculate mix index
    sdf_poly[col_mix_idx] = sdf_poly.swifter.apply(lambda x: get_wtd_idx(x, input_cols_sacog_standard, lu_params_df))


    
    
    
    

