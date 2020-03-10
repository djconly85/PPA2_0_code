# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 14:28:03 2020

@author: DConly
"""
import datetime as dt

import arcpy
import os
import sys


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


def append_proj_to_master_fc(project_fc, proj_attributes_dict, master_fc):
    '''Takes project line and appends it to master line feature class with all lines users have entered'''
    arcpy.AddMessage("Archiving project line geometry...")
    #get geometry of user-drawn input line
    try:
        fld_shape = "SHAPE@"
        geoms = []
        with arcpy.da.SearchCursor(project_fc, fld_shape) as cur:
            for row in cur:
                geoms.append(row[0])
        
        #make row that will be inserted into master fc
        new_row = geoms + [v for k, v in proj_attributes_dict.items()]
        
        # use insert cursor to add in appropriate project name, etc.
        fields = [fld_shape] + list(proj_attributes_dict.keys())
        
        inscur = arcpy.da.InsertCursor(master_fc, fields)
        inscur.insertRow(new_row)
        
        del inscur
        
        msg = "Completed"
        return msg
    except:
        msg = trace()
        return msg
        
    
    
if __name__ == '__main__':
    arcpy.env.workspace = r'E:\ArcGIS\PPA2_DevPortal\PPA_V2.gdb'
    
    
    projectline = arcpy.GetParameterAsText(0) #line whose attributes will be added to master FC
    proj_name = arcpy.GetParameterAsText(1)
    str_timestamp = str(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    
    master_fc = 'All_PPA_Projects2020' #master line FC that the project line will be appended to
    
    proj_field_attribs = {"ProjName": proj_name, "Sponsor": "TEST", "ProjType": "TEST", 
                          "PerfOutcomes": "All", "ADT": 0, "SpeedLmt": 999, "PCI": 0, 
                          "TimeCreated": str_timestamp, "RunSuccess": "TEST ONLY"}
    
    
    result = append_proj_to_master_fc(projectline, proj_field_attribs, master_fc)
    arcpy.SetParameterAsText(2, result)