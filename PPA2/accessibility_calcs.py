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

import ppa_input_params as p
import ppa_utils as utils


def get_acc_data(fc_project, fc_accdata, project_type, get_ej=False):
    arcpy.AddMessage("calculating accessibility metrics...")

    fl_accdata = "fl_accdata"
    fl_project = "fl_project"

    utils.make_fl_conditional(fc_project, fl_project)
    utils.make_fl_conditional(fc_accdata, fl_accdata)

    # select polygons that intersect with the project line
    searchdist = 0 if project_type == p.ptype_area_agg else p.bg_search_dist
    arcpy.SelectLayerByLocation_management(fl_accdata, "INTERSECT", fl_project, searchdist, "NEW_SELECTION")

    # read accessibility data from selected polygons into a dataframe
    accdata_fields = [p.col_geoid, p.col_acc_ej_ind, p.col_pop] + p.acc_cols_ej
    accdata_df = utils.esri_object_to_df(fl_accdata, accdata_fields)

    # get pop-weighted accessibility values for all accessibility columns

    out_dict = {}
    if get_ej:
        for col in p.acc_cols_ej:
            col_wtd = "{}_wtd".format(col)
            col_ej_pop = "{}_EJ".format(p.col_pop)
            accdata_df[col_wtd] = accdata_df[col] * accdata_df[p.col_pop] * accdata_df[p.col_acc_ej_ind]
            accdata_df[col_ej_pop] = accdata_df[p.col_pop] * accdata_df[p.col_acc_ej_ind]
            
            tot_ej_pop = accdata_df[col_ej_pop].sum()
            
            out_wtd_acc = accdata_df[col_wtd].sum() / tot_ej_pop if tot_ej_pop > 0 else 0
            col_out_ej = "{}_EJ".format(col)
            out_dict[col_out_ej] = out_wtd_acc
    else:
        for col in p.acc_cols:
            col_wtd = "{}_wtd".format(col)
            accdata_df[col_wtd] = accdata_df[col] * accdata_df[p.col_pop]
            out_wtd_acc = accdata_df[col_wtd].sum() / accdata_df[p.col_pop].sum()
            out_dict[col] = out_wtd_acc

    return out_dict


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    arcpy.OverwriteOutput = True

    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_sr51riverXing'
    accdata_fc = 'Sugar_access_data_latest'

    out_1 = get_acc_data(project_fc, accdata_fc, p.ptype_arterial, get_ej=True)

    print(out_1)


