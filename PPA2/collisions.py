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

#for aggregate, polygon-based avgs (e.g., community type, whole region), use model for VMT; for
#project, the VMT will be based on combo of project length and user-entered ADT for project
def get_model_link_sums(fc_polygon, fc_model_links):

    fl_polygon = "fl_polygon"
    fl_model_links = "fl_model_links"
    arcpy.MakeFeatureLayer_management(fc_polygon, fl_polygon)
    arcpy.MakeFeatureLayer_management(fc_model_links, fl_model_links)

    # select model links whose centroid is within the polygon area
    arcpy.SelectLayerByLocation_management(fl_model_links, "HAVE_THEIR_CENTER_IN", fl_polygon)

    link_data_cols = [p.col_capclass, p.col_distance, p.col_lanemi, p.col_dayvmt]
    output_data_cols = [p.col_dayvmt, p.col_distance]

    # load model links, selected to be near project, into a dataframe
    df_linkdata = esri_object_to_df(fl_model_links, link_data_cols)

    # get total VMT for links within the area
    out_dict = {col: df_linkdata[col].sum() for col in output_data_cols}
    return out_dict

# get centerline miles within project area or aggregation geography (community type, entire region, etc)
def get_centerline_miles(selection_poly_fc, centerline_fc):
    fl_selection_poly = "fl_selection_poly"
    fl_centerline = "fl_centerline"

    arcpy.MakeFeatureLayer_management(selection_poly_fc, fl_selection_poly)
    arcpy.MakeFeatureLayer_management(centerline_fc, fl_centerline)

    arcpy.SelectLayerByLocation_management(fl_centerline, "HAVE_THEIR_CENTER_IN", fl_selection_poly)

    cline_miles = 0
    with arcpy.da.SearchCursor(fl_centerline, "SHAPE@LENGTH") as cur:
        for row in cur:
            cline_miles += row[0]

    return cline_miles / p.ft2mile


def get_collision_data(fc_project, project_type, fc_colln_pts, project_adt):

    print("Aggregating collision data...")
    fl_project = 'proj_fl'
    fl_colln_pts = 'collision_fl'

    arcpy.MakeFeatureLayer_management(fc_project, fl_project)
    arcpy.MakeFeatureLayer_management(fc_colln_pts, fl_colln_pts)

    # if for project segment, get annual VMT for project segment based on user input and segment length
    df_projlen = esri_object_to_df(fl_project, ["SHAPE@LENGTH"])
    proj_len_mi = df_projlen.iloc[0][0] / p.ft2mile  # return project length in miles

    # for aggregate, polygon-based avgs (e.g., community type, whole region), use model for VMT; for
    # project, the VMT will be based on combo of project length and user-entered ADT for project
    # approximate annual project VMT, assuming ADT is reflective of weekdays only, but assumes
    if project_type == p.ptype_area_agg:
        vmt_dict = get_model_link_sums(fc_project, p.model_links_fc)
        dayvmt = vmt_dict[p.col_dayvmt]
        ann_proj_vmt = dayvmt * 320
        proj_len_mi = get_centerline_miles(fc_project, p.reg_centerline_fc)
    else:
        ann_proj_vmt = project_adt * proj_len_mi * 320

    # get collision totals
    searchdist = 0 if project_type == p.ptype_area_agg else p.colln_searchdist
    arcpy.SelectLayerByLocation_management(fl_colln_pts, 'WITHIN_A_DISTANCE', fl_project, searchdist)
    colln_cols = [p.col_fwytag, p.col_nkilled, p.col_bike_ind, p.col_ped_ind]

    df_collndata = esri_object_to_df(fl_colln_pts, colln_cols)

    # filter so that fwy collisions don't get tagged to non-freeway projects, and vice-versa
    if project_type == p.ptype_fwy:
        df_collndata = df_collndata.loc[df_collndata[p.col_fwytag] == 1]
    elif project_type == p.ptype_area_agg:
        pass  # for aggregating at polygon level, like region or community type, we want all collisions on all roads
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
    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    proj_type = 'Freeway' # 'Freeway', 'Arterial', 'State of Good Repair'
    proj_weekday_adt = 16000  # avg daily traffic, will be user-entered value

    # collision data layer
    collision_fc = 'Collisions2014to2018fwytag'

    output = get_collision_data(proj_line_fc, proj_type, collision_fc, proj_weekday_adt)

    print(output)