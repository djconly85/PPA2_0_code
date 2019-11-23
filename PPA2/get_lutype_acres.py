#--------------------------------
# Name:get_lutype_acres.py
# Purpose: Based on parcel polygon intersection with buffer around project segment, get % of acres near project that are of specific land use type
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
#--------------------------------

import arcpy

def get_lutype_acreage(fc_project, fc_poly_parcels, lutype):
    arcpy.AddMessage("Estimating {} acres near project...".format(lutype))

    fl_parcels = "fl_parcel"
    fl_project = "fl_project"
    arcpy.MakeFeatureLayer_management(fc_poly_parcels, fl_parcels)
    arcpy.MakeFeatureLayer_management(fc_project, fl_project)

    # create temporary buffer
    buff_dist = 2640  # distance in feet
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

    # select only parcels of desired land use type (lutype)
    col_lutype = "LUTYPE16"
    sql_lutype = "{} = '{}'".format(col_lutype, lutype)
    arcpy.SelectLayerByAttribute_management(fl_parcels, "NEW_SELECTION", sql_lutype)

    # create intersect layer of buffer with parcels of selected LUTYPE
    fc_intersect = r"memory\temp_intersect"
    arcpy.Intersect_analysis([fl_buff, fl_parcels], fc_intersect, "ONLY_FID", "", "INPUT")

    fl_intersect = "fl_intersect"
    arcpy.MakeFeatureLayer_management(fc_intersect, fl_intersect)

    # get total acres within intersect polygons
    lutype_intersect_ft2 = 0
    with arcpy.da.SearchCursor(fl_intersect, "SHAPE@AREA") as cur:
        for row in cur:
            lutype_intersect_ft2 += row[0]

    lutype_intersect_acres = lutype_intersect_ft2 / 43560  # convert to acres
    pct_lutype = lutype_intersect_acres / buff_acre if buff_acre > 0 else 0

    [arcpy.Delete_management(item) for item in [fl_parcels, fl_project, fc_buff, fl_buff, fc_intersect, fl_intersect]]

    return {'total_buff_acres': buff_acre, '{}_acres'.format(lutype): lutype_intersect_acres,
            'pct_{}_in_buff'.format(lutype): pct_lutype}



if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    parcel_featclass = 'parcels_w_urbanization'
    project_featclass = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    lutype = 'Agriculture'

    out_pcl_data = get_lutype_acreage(project_featclass, parcel_featclass, lutype)
    print(out_pcl_data)

    # NOT 11/22/2019 - THIS IS GETTING AS PCT OF BUFFER AREA, NOT DEVELOPABLE ON-PARCEL ACRES! SHOULD FIX

