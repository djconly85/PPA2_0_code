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
import gc
import sys

import arcpy

# import ppa_input_params as params


def trace():
    import traceback, inspect
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # script name + line number
    line = tbinfo.split(", ")[1]
    filename = inspect.getfile(inspect.currentframe())
    # Get Python syntax error
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror

def get_poly_area(poly_fl):
    buff_area_ft2 = 0
    with arcpy.da.SearchCursor(poly_fl, ["SHAPE@AREA"]) as cur:
        for row in cur:
            buff_area_ft2 += row[0]

    buff_acre = buff_area_ft2 / 43560  # convert from ft2 to acres. may need to adjust for projection-related issues. See PPA1 for more info
    return buff_acre


def intersection_density(fc_project, fc_intersxns, project_type):
    try:
        arcpy.AddMessage("Calculating intersection density...")
    
        fl_project = "fl_projline"
        fl_intersxns = "fl_trnstp"
    
        if arcpy.Exists(fl_project): arcpy.Delete_management(fl_project)
        arcpy.MakeFeatureLayer_management(fc_project, fl_project)
        
        if arcpy.Exists(fl_intersxns): arcpy.Delete_management(fl_intersxns)
        arcpy.MakeFeatureLayer_management(fc_intersxns, fl_intersxns)
    
        # analysis area. If project is line or point, then it's a buffer around the line/point.
        # If it's a polygon (e.g. ctype or region), then no buffer and analysis area is that within the input polygon
        if project_type == "AGG":
            fc_buff = fc_project
        else:
            buffdist = 1320 # feet
            fc_buff = r"memory\temp_buff_qmi"
            arcpy.Buffer_analysis(fl_project, fc_buff, buffdist)
    
        fl_buff = "fl_buff"
        
        if arcpy.Exists(fl_buff): arcpy.Delete_management(fl_buff)
        arcpy.MakeFeatureLayer_management(fc_buff, fl_buff)
    
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
    
        arcpy.Delete_management(fl_intersxns)
        gc.collect()
        
        msg = "SUCCESS - intersections per acre: {}".format(intersxns_per_acre)
    except:
        msg = trace()
        
        
    return msg

    


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\ForESRI\Layers4ESRI_03172020.gdb'

    proj_line_fc = arcpy.GetParameterAsText(0)
    intersxns_fc = 'intersections_2016'
    proj_type = "Line project"

    output = intersection_density(proj_line_fc, intersxns_fc, proj_type)
    arcpy.SetParameterAsText(1, output)
