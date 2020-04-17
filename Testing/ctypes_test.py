# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 09:53:57 2020

@author: DConly
"""

import sys
import arcpy


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


def get_proj_ctype(in_project_fc, commtypes_fc):
    '''Get project community type, based on which community type has most spatial overlap with project'''
    
    temp_intersect_fc = r'memory/temp_intersect_fc'
    arcpy.Intersect_analysis([in_project_fc, commtypes_fc], temp_intersect_fc, "ALL", 
                             0, "LINE")
    
    len_field = 'SHAPE@LENGTH'
    ctype_field = 'comm_type_ppa'
    fields = ['OBJECTID', len_field, ctype_field]
    
    ctype_dist_dict = {}
    with arcpy.da.SearchCursor(temp_intersect_fc, fields) as cur:
        for row in cur:
            ctype = row[fields.index(ctype_field)]
            seg_len = row[fields.index(len_field)]
            
            if ctype_dist_dict.get(ctype) is None:
                ctype_dist_dict[ctype] = seg_len
            else:
                ctype_dist_dict[ctype] += seg_len
    arcpy.AddMessage(ctype_dist_dict)
          
    try:
        maxval = max([v for k, v in ctype_dist_dict.items()])
        output_str = [k for k, v in ctype_dist_dict.items() if v == maxval][0]
    except:
        output_str = trace()
    
    return output_str




if __name__ == '__main__':
    arcpy.env.workspace = S

    proj_line_fc = arcpy.GetParameterAsText(0)
    community_types_fc = 'comm_type_jurspec_dissolve'
    proj_type = "Line project"

    output = get_proj_ctype(proj_line_fc, community_types_fc)
    arcpy.SetParameterAsText(1, output)