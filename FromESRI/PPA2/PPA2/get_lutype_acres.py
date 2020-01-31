#--------------------------------
# Name:get_lutype_acres.py
# Purpose: Based on parcel polygon intersection with buffer around project segment, get % of acres near project that are of specific land use type
#           This version of script calculates the percent based on on-parcel acres (i.e., the total acreage excludes water/rights of way)
#
# Author: Darren Conly
# Last Updated: 12/30/2019
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
#--------------------------------

import arcpy

import ppa_input_params as p
import ppa_utils as utils


def get_lutype_acreage(fc_project, projtyp, fc_poly_parcels, lutype):
    arcpy.AddMessage("Estimating {} acres near project...".format(lutype))

    fl_parcels = "fl_parcel"
    fl_project = "fl_project"

    for fc, fl in {fc_project: fl_project, fc_poly_parcels: fl_parcels}.items():
        utils.make_fl_conditional(fc, fl)
        # if arcpy.Exists(fl):
        #     arcpy.Delete_management(fl)
        #     arcpy.MakeFeatureLayer_management(fc, fl)
        # else:
        #     arcpy.MakeFeatureLayer_management(fc, fl)

    # create temporary buffer IF the input project fc is a line. If it's a polygon, then don't make separate buffer
    if projtyp == p.ptype_area_agg:
        fc_buff = fc_project
    else:
        buff_dist = p.ilut_sum_buffdist  # distance in feet
        fc_buff = r"memory\temp_buff_qmi"
        arcpy.Buffer_analysis(fl_project, fc_buff, buff_dist)

    fl_buff = "fl_buff"
    arcpy.MakeFeatureLayer_management(fc_buff, fl_buff)

    """
    # calculate buffer area, inclusive of water bodies and rights of way
    buff_area_ft2 = 0
    with arcpy.da.SearchCursor(fl_buff, ["SHAPE@AREA"]) as cur:
        for row in cur:
            buff_area_ft2 += row[0]
    buff_acre = buff_area_ft2 / p.ft2acre  # convert from ft2 to acres. may need to adjust for projection-related issues. See PPA1 for more info
    """

    # create intersect layer of buffer with parcels of selected LUTYPE
    fc_intersect = r"memory\temp_intersect"
    arcpy.Intersect_analysis([fl_buff, fl_parcels], fc_intersect, "ALL", "", "INPUT")

    # calculate total area on parcels within buffer (excluding water and rights of way)
    fl_intersect = "fl_intersect"
    arcpy.MakeFeatureLayer_management(fc_intersect, fl_intersect)

    # get total acres within intersect polygons
    pclarea_inbuff_ft2 = 0  # total on-parcel acres within buffer
    lutype_intersect_ft2 = 0  # total acres of specified land use type within buffer
    with arcpy.da.SearchCursor(fl_intersect, ["SHAPE@AREA", p.col_lutype]) as cur:
        for row in cur:
            pclarea_inbuff_ft2 += row[0]
            if row[1] == lutype:
                lutype_intersect_ft2 += row[0]

    # get share of on-parcel land within buffer that is of specified land use type
    pct_lutype = lutype_intersect_ft2 / pclarea_inbuff_ft2 if pclarea_inbuff_ft2 > 0 else 0

    # convert to acres
    buff_acre = pclarea_inbuff_ft2 / p.ft2acre
    lutype_intersect_acres = lutype_intersect_ft2 / p.ft2acre

    [arcpy.Delete_management(item) for item in [fl_parcels, fl_project, fl_buff, fc_intersect, fl_intersect]]
    
    # delete temp buffer feature class only if it's not the same as the project FC
    if fc_buff != fc_project:
        arcpy.Delete_management(fc_buff)

    return {'total_net_pcl_acres': buff_acre, 'net_{}_acres'.format(lutype): lutype_intersect_acres,
            'pct_{}_inbuff'.format(lutype): pct_lutype}


if __name__ == '__main__':
    import ppa_input_params as p
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    parcel_featclass = p.parcel_poly_fc  # 'parcel_data_polys_2016'
    project_featclass = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_sr51riverXing'
    lutype = 'Agriculture'

    out_pcl_data = get_lutype_acreage(project_featclass, parcel_featclass, p.lutype_ag)
    print(out_pcl_data)

    # NOT 11/22/2019 - THIS IS GETTING AS PCT OF BUFFER AREA, NOT DEVELOPABLE ON-PARCEL ACRES! SHOULD FIX

