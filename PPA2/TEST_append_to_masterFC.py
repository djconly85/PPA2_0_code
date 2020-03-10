# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 14:27:32 2020

@author: DConly
"""
import datetime as dt

import arcpy

import ppa_input_params as params


def append_proj_to_master_fc(project_fc, proj_attributes_dict, master_fc):
    '''Takes project line and appends it to master line feature class with all lines users have entered    
    '''
    arcpy.AddMessage("Archiving project line geometry...")
    #get geometry of user-drawn input line
    fld_shape = "SHAPE@"
    geoms = []
    with arcpy.da.SearchCursor(project_fc, fld_shape) as cur:
        for row in cur:
            geoms.append(row[0])
    
    #make row that will be inserted into master fc
    geom = geoms[0] 
    new_row = geoms + [v for k, v in proj_attributes_dict.items()]
    
    # use insert cursor to add in appropriate project name, etc.
    fields = [fld_shape] + list(proj_attributes_dict.keys())
    
    cur = arcpy.da.InsertCursor(master_fc, fields)
    cur.insertRow(new_row)
    
    
if __name__ == '__main__':
    p_fc = arcpy.GetParameterAsText(0)
    
    start_time = dt.datetime.now()
    str_timestamp = str(start_time.strftime('%Y-%m-%d %H:%M:%S'))
    
    attrs_dict = {"ProjName": "TEST", "Sponsor": "TEST", "ProjType": "TEST", 
                          "PerfOutcomes": '1;2;3', "ADT": 23000, "SpeedLmt": 45, "PCI": 70, 
                          "TimeCreated": str_timestamp, "RunSuccess": "test only"}
    
    try:
        append_proj_to_master_fc(p_fc, attrs_dict, params.all_projects_fc)
        arcpy.AddMessage("Success!")
    except:
        "Fail!"