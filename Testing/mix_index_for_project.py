# -*- coding: utf-8 -*-
#--------------------------------
# Name:calc_mix_index_sacog.py
# Purpose: calculate the mix index for PPA, with emphasis on measuring how
#          conducive the land use mix is to replacing drive trips with walk
   #        trips due to daily needs like retail, schools, etc. being within walk distance           

# Author: Darren Conly
# Last Updated: 11/2019
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------

import time

import pandas as pd
import swifter
import arcpy
# from arcgis.features import GeoAccessor, GeoSeriesAccessor


# =============FUNCTIONS=============================================

def make_summary_df(in_fl, input_cols,  landuse_cols, col_hh, park_calc_dict):
    out_rows = []
    with arcpy.da.SearchCursor(in_fl, input_cols) as cur:
        for row in cur:
            out_row = list(row)
            out_rows.append(out_row)

    parcel_df = pd.DataFrame(out_rows, columns = input_cols)
    col_parkac = park_calc_dict['park_acres_field']
    col_lutype = park_calc_dict['lutype_field']
    lutype_parks = park_calc_dict['park_lutype']
    col_area_ac = park_calc_dict['area']

    # add col for park acres, set to total parcel acres where land use type is parks/open space land use type
    parcel_df.loc[(parcel_df[col_lutype] == lutype_parks), col_parkac] = parcel_df[col_area_ac]

    cols = landuse_cols + [col_hh]
    out_df = pd.DataFrame(parcel_df[cols].sum(axis = 0)).T

    return out_df


def get_wtd_idx(x, facs, params_df):
    output = 0
    
    for fac in facs:
        fac_ratio = '{}_ratio'.format(fac)
        fac_out = x[fac_ratio] * params_df.loc[fac]['weight']
        output += fac_out
    
    return output
        

def calc_mix_index(in_df, params_csv, hh_col, lu_factor_cols):
    
    params_df = pd.read_csv(params_csv, index_col = 'lu_fac')
    
    lu_facs = params_df.index
    
    for fac in lu_facs:
        
        # add column for the "ideal", or "balanced" ratio of that land use to HHs
        bal_col = "{}_bal".format(fac) 
        in_df.loc[in_df[hh_col] != 0, bal_col] = in_df[hh_col] * params_df.loc[fac]['bal_ratio_per_hh']
        
        # if no HH, set bal_col = -1
        in_df.fillna(-1)
        
        ratio_col = "{}_ratio".format(fac)
        
        # if balance value > actual value, return actual value / balance value
        in_df.loc[(in_df[hh_col] != 0) & (in_df[bal_col] > in_df[fac]), ratio_col] = in_df[fac] / in_df[bal_col]
    
        # if balance value < actual value, return balance value / actual value
        in_df.loc[(in_df[hh_col] != 0) & (in_df[bal_col] < in_df[fac]), ratio_col] = in_df[bal_col] / in_df[fac]
        
        # if no HH, set ratio col = -1
        in_df.fillna(-1)
        
    in_df['mix_index_1mi'] = in_df.swifter.apply(lambda x: get_wtd_idx(x, lu_facs, params_df), axis = 1)
    
    return in_df


def do_work(in_fl, out_csv, params_csv, input_cols, landuse_cols, col_hh, park_calc_dict):
    summ_df = make_summary_df(in_fl, input_cols, landuse_cols, col_hh, park_calc_dict)

    out_df = calc_mix_index(summ_df, params_csv, col_hh, landuse_cols)

    out_df[[col_hh, 'mix_index_1mi']].to_csv(out_csv, index = False)
    print("Done! Output CSV: {}".format(out_csv))

# ===============================SCRIPT=================================================


if __name__ == '__main__':
    
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    
    # input fc of parcel data--must be points!
    in_pcl_pt_fc = "parcel_data_2016_11052019_pts"

    # input line project for basing spatial selection
    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg_seconn'

    buff_dist_ft = 5280 # distance in feet--MIGHT NEED TO BE ADJUSTED FOR WGS 84--SEE OLD TOOL FOR HOW THIS WAS RESOLVED
    
    # weighting values {land use:[optimal ratio per household, weight given to that ratio]}
    mix_idx_params_csv = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\Testing\mix_idx_params.csv"
    
    # output csv for testing
    output_id = int(round(time.time(), 0))
    out_csv = r'C:\Users\dconly\PPA_TEMPFILES\test_mixindex_out{}.csv'.format(output_id)

    # input columns--MUST MATCH COLNAMES IN mix_idx_params_csv
    col_parcelid = 'PARCELID'
    col_hh = 'HH_hh'
    # col_stugrd = 'stugrd_2'
    # col_stuhgh = 'stuhgh_2'
    col_emptot = 'EMPTOT'
    col_empfood = 'EMPFOOD'
    col_empret = 'EMPRET'
    col_empsvc = 'EMPSVC'
    col_k12_enr = 'ENR_K12'

    # park acreage info
    col_area_ac = 'GISAc'
    col_lutype = 'LUTYPE'
    lutype_parks = 'Park and/or Open Space'
    col_parkac = 'PARK_AC' # will be calc'd as GISAc if LUTYPE = park/open space LUTYPE

    # =====================================================================

    fl_parcel = "fl_parcel"

    arcpy.MakeFeatureLayer_management(in_pcl_pt_fc, fl_parcel)
    arcpy.SelectLayerByLocation_management(fl_parcel, "WITHIN_A_DISTANCE", project_fc, buff_dist_ft, "NEW_SELECTION")

    in_cols = [col_parcelid, col_hh, col_k12_enr, col_emptot, col_empfood,
               col_empret, col_empsvc, col_area_ac, col_lutype]

    lu_fac_cols = [col_k12_enr, col_emptot, col_empfood, col_empret, col_empsvc, col_parkac]

    park_calc_dict = {'area': col_area_ac,
                      'lutype_field': col_lutype,
                      'park_lutype': lutype_parks,
                      'park_acres_field': col_parkac}

    do_work(fl_parcel, out_csv, mix_idx_params_csv, in_cols, lu_fac_cols, col_hh, park_calc_dict)

    
    
    

