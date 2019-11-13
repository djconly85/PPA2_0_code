# --------------------------------
# Name: transit_svc_measure.py
# Purpose: Estimate transit service density near project
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import arcpy


def transit_svc_density(fl_project, fl_trnstops):
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

    buff_acre = buff_area_ft2 / 43560  # may need to adjust for projection-related issues. See PPA1 for more info

    # get count of transit stops within buffer
    arcpy.SelectLayerByLocation_management(fl_trnstops, "INTERSECT", fl_buff, 0, "NEW_SELECTION")

    transit_veh_events = 0
    col_transit_events = "COUNT_trip_id"

    with arcpy.da.SearchCursor(fl_trnstops, [col_transit_events]) as cur:
        for row in cur:
            transit_veh_events += row[0]

    trnstops_per_acre = transit_veh_events / buff_acre if buff_acre > 0 else 0

    return {"TrnVehStop_Acre": trnstops_per_acre}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    trnstops_fc = 'transit_stoplocn_w_eventcount_2016'

    fl_projline = "fl_projline"
    fl_trnstp = "fl_trnstp"

    arcpy.MakeFeatureLayer_management(proj_line_fc, fl_projline)
    arcpy.MakeFeatureLayer_management(trnstops_fc, fl_trnstp)

    output = transit_svc_density(fl_projline, fl_trnstp)
    print(output)
