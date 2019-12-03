# --------------------------------
# Name:collisions.py
# Purpose: calculate collision data for PPA tool.
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import pandas as pd
import arcpy

import ppa_input_params as p


def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df


def link_vehocc(row):
    total_veh_vol = row[p.col_dayvehvol]
    vol_sov = row[p.col_sovvol]
    vol_hov2 = row[p.col_hov2vol]
    vol_hov3 = row[p.col_hov3vol]

    return (vol_sov + vol_hov2 * p.fac_hov2 + vol_hov3 * p.fac_hov3) / total_veh_vol


def get_wtdavg_vehocc(in_df):

    col_wtdvol = 'col_wtdvol'
    in_df[col_wtdvol] = in_df.apply(lambda x: link_vehocc(x), axis = 1)

    sumprod = in_df[p.col_lanemi].dot(in_df[col_wtdvol])
    lanemi_tot = in_df[p.col_lanemi].sum()
    output_val = sumprod / lanemi_tot

    return output_val


def get_wtdavg_vehvol(in_df, col_vehtype):

    sumprod = in_df[p.col_lanemi].dot(in_df[col_vehtype]) # sum product of lanemi * volume, for the occupancy class (sov, hov2, hov3+)
    lanemi_tot = in_df[p.col_lanemi].sum()
    output_vehvol = sumprod / lanemi_tot # lanemi-weighted average volume for the occupancy class

    return output_vehvol


def get_linkoccup_data(fc_project, project_type, fc_model_links):
    arcpy.AddMessage("getting modeled vehicle occupancy data...")
    fl_project = 'proj_fl'
    fl_model_links = 'modlink_fl'

    arcpy.MakeFeatureLayer_management(fc_project, fl_project)
    arcpy.MakeFeatureLayer_management(fc_model_links, fl_model_links)

    # get model links that are on specified link type with centroid within search distance of project
    arcpy.SelectLayerByLocation_management(fl_model_links, 'HAVE_THEIR_CENTER_IN', fl_project, p.modlink_searchdist)

    # load data into dataframe then subselect only ones that are on same road type as project (e.g. fwy vs. arterial)
    df_cols = [p.col_capclass, p.col_lanemi, p.col_tranvol, p.col_dayvehvol, p.col_sovvol, p.col_hov2vol, p.col_hov3vol]
    df_linkdata = esri_object_to_df(fl_model_links, df_cols)

    if project_type == p.ptype_fwy:
        df_linkdata = df_linkdata.loc[df_linkdata[p.col_capclass].isin(p.capclasses_fwy)]
    else:
        df_linkdata = df_linkdata.loc[df_linkdata[p.col_capclass].isin(p.capclass_arterials)]

    avg_proj_trantrips = get_wtdavg_vehvol(df_linkdata, p.col_tranvol) if df_linkdata.shape[0] > 0 else 0
    avg_proj_vehocc = get_wtdavg_vehocc(df_linkdata) if df_linkdata.shape[0] > 0 else 0

    out_dict = {"avg_2way_trantrips": avg_proj_trantrips, "avg_2way_vehocc": avg_proj_vehocc}

    return out_dict


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_xmult_strt'
    model_link_fc = 'model_links_2016'
    proj_type = p.ptype_arterial

    output = get_linkoccup_data(proj_line_fc, proj_type, model_link_fc)

    print(output)