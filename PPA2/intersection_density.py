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

def intersection_density(fl_project, fl_intersxns):
    # create temporary buffer
    buff_dist = 1320 # distance in feet
    fc_buff = r"memory\temp_buff_qmi"
    arcpy.Buffer_analysis(fl_project, fc_buff, buff_dist)

    fl_buff = "fl_buff"
    arcpy.MakeFeatureLayer_management(fc_buff, fl_buff)

    # calculate buffer area
    buff_area_ft2 = 0
    with arcpy.da.SearchCursor(fl_buff, ["SHAPE@AREA"]) as cur:
        for row in cur:
            buff_area_ft2 += row[0]

    buff_acre = buff_area_ft2 / 43560  # convert from ft2 to acres. may need to adjust for projection-related issues. See PPA1 for more info

    # get count of transit stops within buffer
    arcpy.SelectLayerByLocation_management(fl_intersxns, "INTERSECT", fl_buff, 0, "NEW_SELECTION")

    intsxn_34 = 0
    col_link_cnt = "LINKS"

    with arcpy.da.SearchCursor(fl_intersxns, [col_link_cnt]) as cur:
        for row in cur:
            if row[0] > 2:
                intsxn_34 += 1

    intersxns_per_acre = intsxn_34 / buff_acre if buff_acre > 0 else 0

    return {"Intersxn_34_per_acre": intersxns_per_acre}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    intersxns_fc = 'intersections_2016'

    fl_projline = "fl_projline"
    fl_intersxn = "fl_trnstp"

    arcpy.MakeFeatureLayer_management(proj_line_fc, fl_projline)
    arcpy.MakeFeatureLayer_management(intersxns_fc, fl_intersxn)

    output = intersection_density(fl_projline, fl_intersxn)
    print(output)
