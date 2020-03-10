# --------------------------------
# Name:get_buff_netmiles.py
# Purpose: get total network and bikeway miles within specified buffer of project, get % of those that are bikeways
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------

import arcpy

import ppa_utils as utils
import ppa_input_params as params


def netmiles_in_buffer(fc_project, fc_network, project_type):

    # if project is polygon, then use polygon. If line or point, then make polygon as buffer around line/point.
    if project_type == params.ptype_area_agg:
        fc_poly_buff = fc_project
    else:
        fc_poly_buff = r"memory\temp_buff_qmi"
        arcpy.Buffer_analysis(fc_project, fc_poly_buff, params.bikeway_buff)

    fl_poly = "fl_buff"

    if arcpy.Exists(fl_poly): arcpy.Delete_management(fl_poly)
    arcpy.MakeFeatureLayer_management(fc_poly_buff, fl_poly)    

    # if not arcpy.Exists(fl_poly):
    #     utils.make_fl_conditional(fc_poly_buff, fl_poly)

    temp_intersect_fc = r"memory\temp_intersect_fc"

    #run intersect of network lines against buffer
    arcpy.Intersect_analysis([fc_network, fc_poly_buff], temp_intersect_fc)

    # get total mileage of network lines-buffer intersection fc
    net_len = 0
    with arcpy.da.SearchCursor(temp_intersect_fc, "SHAPE@LENGTH") as cur:
        for row in cur:
            net_len += row[0]

    arcpy.Delete_management(temp_intersect_fc)

    if fc_poly_buff != fc_project:
        arcpy.Delete_management(fc_poly_buff)
    return net_len


def get_bikeway_mileage_share(project_fc, proj_type):
    arcpy.AddMessage("calculating share of centerline miles near project that are bikeways...")

    centerline_miles = netmiles_in_buffer(project_fc, params.reg_centerline_fc, proj_type)
    bikeway_miles = netmiles_in_buffer(project_fc, params.reg_bikeway_fc, proj_type)

    share_bikeways = bikeway_miles / centerline_miles

    return {"pct_roadmi_bikeways": share_bikeways}

'''
if __name__ == '__main__':
    arcpy.env.workspace = None

    project = None

    test_dict = get_bikeway_mileage_share(project, params.ptype_sgr)

    print(test_dict)
    '''