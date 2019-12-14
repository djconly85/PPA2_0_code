# --------------------------------
# Name:urbanization_metrics.py
# Purpose: (1) categorize project as infill, greenfield, or spanning infill + greenfield areas
#          (2) calculate loss of natural resources (acres of ag + forest + open space)
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------

import arcpy

import get_lutype_acres as luta
import ppa_input_params as p

# get list of ctypes that a project passes through. "infill" if ctype = is established or corridor; greenfield if not
def projarea_infill_status(fc_project, comm_types_fc):
    arcpy.AddMessage("Determining project greenfield/infill status...")
    temp_intersect_fc = r"memory/temp_intersect_fc"

    arcpy.Intersect_analysis([fc_project, comm_types_fc], temp_intersect_fc)

    proj_len_infill = 0
    proj_len_greenfield = 0

    with arcpy.da.SearchCursor(temp_intersect_fc, [p.col_ctype_2, "SHAPE@LENGTH"]) as cur:
        for row in cur:
            if row[0] in p.ctypes_infill:
                proj_len_infill += row[1]
            else:
                proj_len_greenfield += row[1]

    pct_infill = proj_len_infill / (proj_len_infill + proj_len_greenfield)
    if pct_infill >= p.threshold_val:
        category = "Infill project"
    elif pct_infill < (1-p.threshold_val):
        category = "Greenfield project"
    else:
        category = "Project spans both infill and greenfield areas"

    return {"Project's use of existing assets": category}

def nat_resources(fc_project, fc_pcl_poly, year): #NOTE - this is year dependent!
    nat_resource_ac = 0
    for lutype in p.lutypes_nat_resources:
        lutype_ac_dict = luta.get_lutype_acreage(fc_project, fc_pcl_poly, lutype)
        nat_resource_ac += lutype_ac_dict['{}_acres'.format(lutype)]

    return {"nat_resource_acres{}".format(year): nat_resource_ac}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    # input fc of parcel data--must be polygons!
    in_pcl_base_fc = p.parcel_poly_fc
    # in_pcl_future_tbl =
    # in_ctypes_fc =

    # input line project for basing spatial selection
    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_SEConnector'
    an_year = 2016

    #out_gfield_dict = projarea_infill_status(project_fc, p.comm_types_fc)
    # out_natacres_dict = nat_resources(project_fc, in_pcl_base_fc, an_year)
    #
    # #print(out_gfield_dict)
    # print(out_natacres_dict)

    infill_status_dict = projarea_infill_status(project_fc, p.comm_types_fc)
    print(infill_status_dict)