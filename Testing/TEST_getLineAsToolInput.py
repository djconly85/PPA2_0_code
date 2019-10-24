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
    
    project_lines = arcpy.GetParameterAsText(0) #supposed to be user-drawn line--use data type "Feature Set"
    proj_name = arcpy.GetParameterAsText(0) 
    
    arcpy.AddMessage([f.name for f in arcpy.ListFields(project_lines)])
    
    arcpy.AddMessage(type(project_lines))
    
    arcpy.MakeFeatureLayer_management(project_lines, "projlines_fl")
    
    with arcpy.da.SearchCursor("projlines_fl",["Name","Shape_Length"]) as cur:
        for row in cur:
            arcpy.AddMessage('{}, {}'.format(row[0], row[1]))
            
    arcpy.Delete_management(project_lines)
  