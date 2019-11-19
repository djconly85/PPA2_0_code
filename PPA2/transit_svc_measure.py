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

import ppa_input_params as p


def transit_svc_density(fc_project, fc_trnstops):
    fl_project = "fl_projline"
    fl_trnstops = "fl_trnstp"

    arcpy.MakeFeatureLayer_management(fc_project, fl_project)
    arcpy.MakeFeatureLayer_management(fc_trnstops, fl_trnstops)

    # create temporary buffer
    fc_buff = r"memory\temp_buff_qmi"
    arcpy.Buffer_analysis(fl_project, fc_buff, p.trn_buff_dist)

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

    with arcpy.da.SearchCursor(fl_trnstops, [p.col_transit_events]) as cur:
        for row in cur:
            vehstops = row[0] if row[0] is not None else 0
            transit_veh_events += vehstops

    trnstops_per_acre = transit_veh_events / buff_acre if buff_acre > 0 else 0

    return {"TrnVehStop_Acre": trnstops_per_acre}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    trnstops_fc = 'transit_stoplocn_w_eventcount_2016'

    output = transit_svc_density(proj_line_fc, trnstops_fc)
    print(output)
