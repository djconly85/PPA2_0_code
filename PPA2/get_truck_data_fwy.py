


import arcpy
import pandas as pd

import ppa_input_params as p
import npmrds_data_conflation as ndc

def get_wtdavg_truckdata(in_df, col_name):
    len_cols = ['{}_calc_len'.format(dirn) for dirn in p.directions_tmc]
    val_cols = ['{}{}'.format(dirn, col_name) for dirn in p.directions_tmc]

    wtd_dict = dict(zip(len_cols, val_cols))

    wtd_val_sum = 0
    dist_sum = 0

    for dirlen, dirval in wtd_dict.items():
        dir_val2 = 0 if pd.isnull(in_df[dirval][0]) else in_df[dirval][0]
        dir_wtdval = in_df[dirlen][0] * dir_val2
        wtd_val_sum += dir_wtdval
        dist_sum += in_df[dirlen][0]

    return wtd_val_sum / dist_sum




def get_tmc_truck_data(fl_projline, str_project_type):

    arcpy.OverwriteOutput = True

    # make feature layer from speed data feature class
    fl_speed_data = "fl_speed_data"
    arcpy.MakeFeatureLayer_management(p.fc_speed_data, fl_speed_data)

    # make flat-ended buffers around TMCs that intersect project
    arcpy.SelectLayerByLocation_management(fl_speed_data, "WITHIN_A_DISTANCE", fl_projline, p.tmc_select_srchdist, "NEW_SELECTION")
    if str_project_type == 'Freeway':
        sql = "{} IN {}".format(p.col_roadtype, p.roadtypes_fwy)
        arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)
    else:
        sql = "{} NOT IN {}".format(p.col_roadtype, p.roadtypes_fwy)
        arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)

    # create temporar buffer layer, flat-tipped, around TMCs; will be used to split project lines
    temp_tmcbuff = "TEMP_tmcbuff_4projsplit"
    fl_tmc_buff = "fl_tmc_buff"
    arcpy.Buffer_analysis(fl_speed_data, temp_tmcbuff, p.tmc_buff_dist_ft, "FULL", "FLAT")
    arcpy.MakeFeatureLayer_management(temp_tmcbuff, fl_tmc_buff)

    # get "full" table with data for all directions
    projdata_df = ndc.conflate_tmc2projline(fl_projline, p.directions_tmc, p.col_tmcdir, fl_tmc_buff, p.flds_truck_data)

    out_dict = {}
    for col in p.flds_truck_data:
        output_val = get_wtdavg_truckdata(projdata_df, col)
        out_dict["{}_proj"] = output_val
        
    return out_dict




    # trim down table to only include outputs for directions that are "on the segment",
    # i.e., that have most overlap with segment
    # out_dict = ndc.simplify_outputs(projdata_df, 'proj_length_ft')[0]
    #
    # print(out_dict)
    # return out_dict

if __name__ == '__main__':

    workspace = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb'
    arcpy.env.workspace = workspace

    project_line = "PPA_test_fwyproj"  # arcpy.GetParameterAsText(0) #"NPMRDS_confl_testseg_seconn"
    proj_type = "Freeway"  # arcpy.GetParameterAsText(2) #"Freeway"

    # make feature layers of NPMRDS and project line
    fl_project = "fl_project"
    arcpy.MakeFeatureLayer_management(project_line, fl_project)

    output_dict = get_tmc_truck_data(fl_project, proj_type)
    print(output_dict)