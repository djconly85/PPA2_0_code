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


def get_collision_data(fl_project, project_type, fl_colln_pts, project_adt):

    # get annual VMT for project segment based on user input and segment length
    df_projlen = esri_object_to_df(fl_project, ["SHAPE@LENGTH"])
    proj_len_mi = df_projlen.iloc[0][0] / 5280 # return project length in miles

    # approximate annual project VMT, assuming ADT is reflective of weekdays only, but assumes
    ann_proj_vmt = project_adt * proj_len_mi * 320

    # get collision totals
    print("Aggregating collision data...")
    arcpy.SelectLayerByLocation_management(fl_colln_pts, 'WITHIN_A_DISTANCE', fl_project, p.colln_searchdist)
    colln_cols = [p.col_fwytag, p.col_nkilled, p.col_bike_ind, p.col_ped_ind]

    df_collndata = esri_object_to_df(fl_colln_pts, colln_cols)

    # filter so that fwy collisions don't get tagged to non-freeway projects, and vice-versa
    if project_type == 'Freeway':
        df_collndata = df_collndata.loc[df_collndata[p.col_fwytag] == 1]
    else:
        df_collndata = df_collndata.loc[df_collndata[p.col_fwytag] == 0]

    total_collns = df_collndata.shape[0]
    fatal_collns = df_collndata.loc[df_collndata[p.col_nkilled] > 0].shape[0]
    bikeped_collns = df_collndata.loc[(df_collndata[p.col_bike_ind] == p.ind_val_true)
                                      | (df_collndata[p.col_ped_ind] == p.ind_val_true)].shape[0]

    bikeped_colln_clmile = bikeped_collns / proj_len_mi

    # collisions per million VMT (MVMT) = avg annual collisions / (modeled daily VMT * 320 days) * 1,000,000
    avg_ann_collisions = total_collns / p.years_of_collndata
    avg_ann_fatalcolln = fatal_collns / p.years_of_collndata

    colln_rate_per_vmt = avg_ann_collisions / ann_proj_vmt * 100000000 if ann_proj_vmt > 0 else 0
    fatalcolln_per_vmt = avg_ann_fatalcolln / ann_proj_vmt * 100000000 if ann_proj_vmt > 0 else 0

    out_dict = {"TOT_COLLISNS": total_collns, "TOT_COLLISNS_PER_100MVMT": colln_rate_per_vmt,
                "FATAL_COLLISNS": fatal_collns, "FATAL_COLLISNS_PER_100MVMT": fatalcolln_per_vmt,
                "BIKEPED_COLLISNS": bikeped_collns, "BIKEPED_COLLISNS_PER_CLMILE": bikeped_colln_clmile}

    return out_dict


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    # user-entered values
    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\ppa_testseg_urbancore'
    proj_type = 'Arterial' # 'Freeway', 'Arterial', 'State of Good Repair'
    proj_weekday_adt = 16000  # avg daily traffic, will be user-entered value

    # collision data layer
    collision_fc = 'Collisions2014to2018fwytag'

    proj_fl = 'proj_fl'
    collision_fl = 'collision_fl'

    fc_fl_dict = {proj_line_fc: proj_fl, collision_fc: collision_fl}

    for k, v in fc_fl_dict.items():
        arcpy.MakeFeatureLayer_management(k, v)

    output = get_collision_data(proj_fl, proj_type, collision_fl, proj_weekday_adt)

    print(output)