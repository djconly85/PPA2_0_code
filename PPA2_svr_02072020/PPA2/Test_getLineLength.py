# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 13:26:51 2020

@author: dconly
"""

import arcpy

line_fc = arcpy.GetParameterAsText(0)

line_len = 0

with arcpy.da.SearchCursor(line_fc, "SHAPE@LENGTH") as cur:
    for row in cur:
        line_len += row[0]
        
line_len = round(line_len / 5280, 2) # get miles
     
out_msg = "Your Line is {} miles long".format(line_len)
arcpy.SetParameterAsText(1, out_msg)

