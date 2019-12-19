# --------------------------------
# Name: transit_svc_measure.py
# Purpose: Get count of intersection density per acre
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import arcpy

import ppa_input_params as p

def make_fl_conditional(fc, fl):
    if arcpy.Exists(fl):
        arcpy.Delete_management(fl)
    arcpy.MakeFeatureLayer_management(fc, fl)

def get_poly_area(poly_fl):
    buff_area_ft2 = 0
    with arcpy.da.SearchCursor(poly_fl, ["SHAPE@AREA"]) as cur:
        for row in cur:
            buff_area_ft2 += row[0]

    buff_acre = buff_area_ft2 / p.ft2acre  # convert from ft2 to acres. may need to adjust for projection-related issues. See PPA1 for more info
    return buff_acre


def intersection_density(fc_project, fc_intersxns, project_type):
    arcpy.AddMessage("calculating intersection density...")

    fl_project = "fl_projline"
    fl_intersxns = "fl_trnstp"

    make_fl_conditional(fc_project, fl_project)
    make_fl_conditional(fc_intersxns, fl_intersxns)

    # analysis area. If project is line or point, then it's a buffer around the line/point.
    # If it's a polygon (e.g. ctype or region), then no buffer and analysis area is that within the input polygon
    if project_type == p.ptype_area_agg:
        fc_buff = fc_project
    else:
        p.intersxn_dens_buff
        fc_buff = r"memory\temp_buff_qmi"
        arcpy.Buffer_analysis(fl_project, fc_buff, p.intersxn_dens_buff)

    fl_buff = "fl_buff"
    make_fl_conditional(fc_buff, fl_buff)

    buff_acres = get_poly_area(fl_buff)

    # get count of transit stops within buffer
    arcpy.SelectLayerByLocation_management(fl_intersxns, "INTERSECT", fl_buff, 0, "NEW_SELECTION")

    intsxn_34 = 0
    col_link_cnt = "LINKS"

    with arcpy.da.SearchCursor(fl_intersxns, [col_link_cnt]) as cur:
        for row in cur:
            if row[0] > 2:
                intsxn_34 += 1

    intersxns_per_acre = intsxn_34 / buff_acres if buff_acres > 0 else 0

    return {"Intersxn_34_per_acre": intersxns_per_acre}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_STAA_partialOverlap'
    intersxns_fc = 'intersections_2016'
    proj_type = p.ptype_sgr

    output = intersection_density(proj_line_fc, intersxns_fc, proj_type)
    print(output)
