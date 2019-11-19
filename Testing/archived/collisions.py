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


def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df


def get_model_link_sums(fl_model_links, project_type):
    import collision_modelnet_params as p
    # load model links, selected to be near project, into a dataframe
    link_data_cols = [p.col_capclass, p.col_lanemi, p.col_dayvmt]
    output_data_cols = [p.col_dayvmt]
    df_linkdata = esri_object_to_df(fl_model_links, link_data_cols)

    # filter out to only include data that are on the road type of the project (i.e., arterial v. freeway)
    if project_type == 'Freeway':
        df_linkdata = df_linkdata.loc[df_linkdata[p.col_capclass].isin(p.capclasses_fwy)]
    else:
        df_linkdata = df_linkdata.loc[df_linkdata[p.col_capclass].isin(p.capclass_arterials)]

    out_dict = {col: df_linkdata[col].sum() for col in output_data_cols}
    return out_dict


def get_collision_data(fl_project, project_type, fl_model_links, fl_colln_pts):
    import collision_modelnet_params as p
    # get model network DAYVMT
    arcpy.SelectLayerByLocation_management(fl_model_links, 'HAVE_THEIR_CENTER_IN', fl_project, p.modlink_searchdist)
    print("Aggregating modeled VMT...")
    vmt_dict = get_model_link_sums(fl_model_links, project_type)
    dayvmt = vmt_dict[p.col_dayvmt]

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

    pct_fatal = fatal_collns / total_collns if total_collns > 0 else 0
    pct_bikeped = bikeped_collns / total_collns if total_collns > 0 else 0

    # collisions per million VMT (MVMT) = avg annual collisions / (modeled daily VMT * 320 days(?)) * 1,000,000
    avg_ann_collisions = total_collns / p.years_of_collndata
    colln_rate_per_vmt = avg_ann_collisions / (dayvmt * 320) * 1000000 if dayvmt > 0 else 0

    out_dict = {"TOTAL_COLLISIONS":total_collns, "COLLISIONS_PER_MVMT":colln_rate_per_vmt,
                "PCT_FATAL_COLLISIONS":pct_fatal, "PCT_BIKEPED_COLLISIONS":pct_bikeped,
                "FATAL_COLLISIONS":fatal_collns, "BIKE_PED_COLLISIONS":bikeped_collns}

    return out_dict


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    collision_fc = 'Collisions2014to2018fwytag'
    model_link_fc = 'model_links_2016'
    proj_type = 'Freeway'

    proj_fl = 'proj_fl'
    collision_fl = 'collision_fl'
    modlink_fl = 'modlink_fl'

    fc_fl_dict = {proj_line_fc: proj_fl, collision_fc: collision_fl, model_link_fc: modlink_fl}

    for k, v in fc_fl_dict.items():
        arcpy.MakeFeatureLayer_management(k, v)

    output = get_collision_data(proj_fl, proj_type, modlink_fl, collision_fl)

    print(output)