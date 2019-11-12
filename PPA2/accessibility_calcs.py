# --------------------------------
# Name: accessibility_calcs.py
# Purpose: PPA accessibility metrics
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------

import arcpy
import pandas as pd

def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df


def get_acc_data(fl_project, fl_accdata, get_ej=False):
    print("calculating accessibility metrics for project...")
    import accessibility_params as p

    # select polygons that intersect with the project line
    arcpy.SelectLayerByLocation_management(fl_accdata, "INTERSECT", fl_project, p.bg_search_dist, "NEW_SELECTION")

    # read accessibility data from selected polygons into a dataframe
    accdata_fields = [p.col_geoid, p.col_ej_ind, p.col_pop] + p.acc_cols_ej
    accdata_df = esri_object_to_df(fl_accdata, accdata_fields)

    # get pop-weighted accessibility values for all accessibility columns

    out_dict = {}
    if get_ej:
        for col in p.acc_cols_ej:
            col_wtd = "{}_wtd".format(col)
            col_ej_pop = "{}_EJ".format(p.col_pop)
            accdata_df[col_wtd] = accdata_df[col] * accdata_df[p.col_pop] * accdata_df[p.col_ej_ind]
            accdata_df[col_ej_pop] = accdata_df[p.col_pop] * accdata_df[p.col_ej_ind]
            out_wtd_acc = accdata_df[col_wtd].sum() / accdata_df[col_ej_pop].sum()
            out_dict[col] = out_wtd_acc
    else:
        for col in p.acc_cols:
            col_wtd = "{}_wtd".format(col)
            accdata_df[col_wtd] = accdata_df[col] * accdata_df[p.col_pop]
            out_wtd_acc = accdata_df[col_wtd].sum() / accdata_df[p.col_pop].sum()
            out_dict[col] = out_wtd_acc

    print(out_dict)
    return out_dict


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    fc_project = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    fc_accdata = 'Sugar_access_data_latest'

    accdata_fl = "fl_accdata"
    project_fl = "fl_project"

    arcpy.MakeFeatureLayer_management(fc_project, project_fl)
    arcpy.MakeFeatureLayer_management(fc_accdata, accdata_fl)

    get_acc_data(project_fl, accdata_fl, get_ej=False)
    get_acc_data(project_fl, accdata_fl, get_ej=True)

