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
#import swifter
import arcpy

import ppa_input_params as p
import ppa_utils as utils

# =============FUNCTIONS=============================================


def make_summary_df(in_fl, input_cols,  landuse_cols, col_hh, park_calc_dict):

    # load into dataframe
    parcel_df = utils.esri_object_to_df(in_fl, input_cols)

    col_parkac = park_calc_dict['park_acres_field']
    col_lutype = park_calc_dict['lutype_field']
    lutype_parks = park_calc_dict['park_lutype']
    col_area_ac = park_calc_dict['area_field']

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
        

def calc_mix_index(in_df, params_df, hh_col, lu_factor_cols, mix_idx_col):
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
    in_df[mix_idx_col] = in_df.apply(lambda x: get_wtd_idx(x, lu_facs, params_df), axis = 1)
        
    #in_df[mix_idx_col] = in_df.swifter.apply(lambda x: get_wtd_idx(x, lu_facs, params_df), axis = 1)
    
    return in_df


def get_mix_idx(fc_parcel, fc_project, project_type):
    arcpy.AddMessage("calculating mix index...")

    fl_parcel = "fl_parcel"
    fl_project = "fl_project"

    utils.make_fl_conditional(fc_parcel, fl_parcel)
    utils.make_fl_conditional(fc_project, fl_project)

    in_cols = [p.col_parcelid, p.col_hh, p.col_k12_enr, p.col_emptot, p.col_empfood,
               p.col_empret, p.col_empsvc, p.col_area_ac, p.col_lutype]

    lu_fac_cols = [p.col_k12_enr, p.col_emptot, p.col_empfood, p.col_empret, p.col_empsvc, p.col_parkac]
    # make parcel feature layer

    buffer_dist = 0 if project_type == p.ptype_area_agg else p.mix_index_buffdist
    arcpy.SelectLayerByLocation_management(fl_parcel, "WITHIN_A_DISTANCE", fl_project, buffer_dist, "NEW_SELECTION")

    summ_df = make_summary_df(fl_parcel, in_cols, lu_fac_cols, p.col_hh, p.park_calc_dict)

    out_df = calc_mix_index(summ_df, p.params_df, p.col_hh, lu_fac_cols, p.mix_idx_col)

    # if you want to make CSV.
    #out_df[[col_hh, mix_idx_col]].to_csv(out_csv, index = False)
    #print("Done! Output CSV: {}".format(out_csv))

    out_val = out_df[p.mix_idx_col][0]
    return {p.mix_idx_col: out_val}

# ===============================SCRIPT=================================================


if __name__ == '__main__':
    
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    
    # input fc of parcel data--must be points!
    in_pcl_pt_fc = "parcel_data_pts_2016"

    # input line project for basing spatial selection
    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_urbancore'

    buff_dist_ft = p.mix_index_buffdist  # distance in feet--MIGHT NEED TO BE ADJUSTED FOR WGS 84--SEE OLD TOOL FOR HOW THIS WAS RESOLVED

    out_dict = get_mix_idx(in_pcl_pt_fc, project_fc, p.ptype_arterial)

    print(out_dict)
    
    

