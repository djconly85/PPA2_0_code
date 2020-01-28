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

import ppa_input_params as params
import ppa_utils as utils


def get_poly_area(poly_fl):
    buff_area_ft2 = 0
    with arcpy.da.SearchCursor(poly_fl, ["SHAPE@AREA"]) as cur:
        for row in cur:
            buff_area_ft2 += row[0]

    buff_acre = buff_area_ft2 / params.ft2acre  # convert from ft2 to acres. may need to adjust for projection-related issues. See PPA1 for more info
    return buff_acre

def transit_svc_density(fc_project, fc_trnstops, project_type):

    arcpy.AddMessage("calculating transit service density...")
    fl_project = "fl_projline"
    fl_trnstops = "fl_trnstp"

    utils.make_fl_conditional(fc_project, fl_project)
    utils.make_fl_conditional(fc_trnstops, fl_trnstops)
    # analysis area. If project is line or point, then it's a buffer around the line/point.
    # If it's a polygon (e.g. ctype or region), then no buffer and analysis area is that within the input polygon
    if project_type == params.ptype_area_agg:
        fc_buff = fc_project
    else:
        params.intersxn_dens_buff
        fc_buff = r"memory\temp_buff_qmi"
        arcpy.Buffer_analysis(fl_project, fc_buff, params.trn_buff_dist)

    fl_buff = "fl_buff"
    utils.make_fl_conditional(fc_buff, fl_buff)

    # calculate buffer area
    buff_acres = get_poly_area(fl_buff)

    # get count of transit stops within buffer
    arcpy.SelectLayerByLocation_management(fl_trnstops, "INTERSECT", fl_buff, 0, "NEW_SELECTION")

    transit_veh_events = 0

    with arcpy.da.SearchCursor(fl_trnstops, [params.col_transit_events]) as cur:
        for row in cur:
            vehstops = row[0] if row[0] is not None else 0
            transit_veh_events += vehstops

    trnstops_per_acre = transit_veh_events / buff_acres if buff_acres > 0 else 0

    return {"TrnVehStop_Acre": trnstops_per_acre}


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    proj_line_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_urbancore'
    trnstops_fc = 'transit_stoplocn_w_eventcount_2016'
    ptype = params.ptype_arterial

    output = transit_svc_density(proj_line_fc, trnstops_fc, ptype)
    print(output)
