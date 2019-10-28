'''
#--------------------------------
# Name:PPA_getNPMRDSdata.py
# Purpose: Get distance-weighted average speed from NPMRDS data for PPA project,
#          
#           
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: <version>
#--------------------------------

https://pro.arcgis.com/en/pro-app/arcpy/classes/parameter.htm

Sample projects used: CAL20466, SAC25062
'''
import os
import arcpy
#from arcgis.features import SpatialDataFrame
import datetime
import time
import pandas as pd

arcpy.env.overwriteOutput = True

dateSuffix = str(datetime.date.today().strftime('%m%d%Y'))



#====================FUNCTIONS==========================================

    
#=====================RUN SCRIPT===========================
if __name__ == '__main__':
    start_time = time.time()
    
    workspace = r'P:\NPMRDS data\NPMRDS_GIS\scratch.gdb'
    arcpy.env.workspace = workspace
    
    output_dir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\PPAv2\srcpy\Testing Scripts\outputs'
    
    #supposed to be user-drawn line--use data type 
    project_line = arcpy.Parameter(name = "temp_line", displayName = "TEMP_line",
                                   direction = "Input", datatype = "GPFeatureRecordSetLayer",
                                   parameterType = "Required")
    
    arcpy.AddMessage("valueAsText: {}".format(project_line.valueAsText))
    arcpy.AddMessage("values: {}".format(project_line.values))
    arcpy.AddMessage("columns: {}".format(project_line.columns))
    
    proj_name = arcpy.GetParameterAsText(0) 
    
    arcpy.AddMessage([f.name for f in arcpy.ListFields(project_line)])
    
    arcpy.AddMessage(type(project_line))
    
    arcpy.MakeFeatureLayer_management(project_line, "projlines_fl")
    
    with arcpy.da.SearchCursor("projlines_fl",["Name","Shape_Length"]) as cur:
        for row in cur:
            arcpy.AddMessage('{}, {}'.format(row[0], row[1]))
            
    arcpy.Delete_management(project_line)
  