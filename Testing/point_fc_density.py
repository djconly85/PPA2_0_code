# --------------------------------
# Name: transit_svc_measure.py
# Purpose: Get point density (i.e. points per acre)
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

def point_density(fc_project, fc_points, project_type, buffdist, metric_desc):
    arcpy.AddMessage("calculating {}...".format(metric_desc))

    fl_project = "fl_projline"
    fl_points = "fl_trnstp"

    arcpy.MakeFeatureLayer_management(fc_project, fl_project)
    arcpy.MakeFeatureLayer_management(fc_points, fl_points)

    # analysis area. If project is line or point, then it's a buffer around the line/point.
    # If it's a polygon (e.g. ctype or region), then no buffer and analysis area is that within the input polygon
    if project_type == p.ptype_area_agg:
        fc_buff = fc_project
    else:
        fc_buff = r"memory\temp_buff_qmi"
        arcpy.Buffer_analysis(fl_project, fc_buff, buffdist)

    fl_buff = "fl_buff"
    arcpy.MakeFeatureLayer_management(fc_buff, fl_buff)

    # calculate buffer area
    buff_area_ft2 = 0
    with arcpy.da.SearchCursor(fl_buff, ["SHAPE@AREA"]) as cur:
        for row in cur:
            buff_area_ft2 += row[0]

    buff_acre = buff_area_ft2 / 43560  # convert from ft2 to acres. may need to adjust for projection-related issues. See PPA1 for more info

    # get count of transit stops within buffer
    arcpy.SelectLayerByLocation_management(fl_points, "INTERSECT", fl_buff, 0, "NEW_SELECTION")

    pntcnt = 0
    col_link_cnt = "LINKS"

    with arcpy.da.SearchCursor(fl_points, [col_link_cnt]) as cur:
        for row in cur:
            if row[0] > 2:
                pntcnt += 1

    pts_per_acre = pntcnt / buff_acre if buff_acre > 0 else 0

    return {metric_desc: pts_per_acre}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_STAA_partialOverlap'
    intersxns_fc = 'intersections_2016'
    transit_stops_fc =
    proj_type = p.ptype_sgr

    output = point_density(proj_line_fc, intersxns_fc, proj_type)
    print(output)
