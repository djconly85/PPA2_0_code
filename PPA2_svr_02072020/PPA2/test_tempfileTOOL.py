'''
#--------------------------------
# Name:get_line_overlap.py
# Purpose: See what share of a user-input project line overlaps with another network (e.g., STAA freight line network, bike lane network, etc)
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
import sys

import arcpy

arcpy.env.overwriteOutput = True

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

def doWork(in_fc):
    msg = "default msg"
    try:
        # MUST USE os.path.join, not r"\{}..." to specify file path, or else it won't work online.
        temp_fc = os.path.join(arcpy.env.scratchGDB, "TempBuff")  # r"{}\TEMPbuff".format(arcpy.env.scratchGDB) 
        temp_fc_copy = os.path.join(arcpy.env.scratchGDB, "TempBuffCOPY")
        temp_fl = "temp_fl"

        if arcpy.Exists(temp_fc):
            arcpy.AddMessage("Need to delete existing FC: {}".format(arcpy.Exists(temp_fc)))
            arcpy.Delete_management(temp_fc)
        
        arcpy.Buffer_analysis(in_fc, temp_fc, 100, "FULL", "FLAT")
        output_exists = arcpy.Exists(temp_fc)
        
        msg_exists = "{} buffer output exists? {}".format(temp_fc, output_exists)
        arcpy.AddMessage(msg_exists)

        arcpy.CopyFeatures_management(temp_fc, temp_fc_copy)
        copy_exists = arcpy.Exists(temp_fc_copy)
        
        msg_copy_exists = "{} buffer output exists? {}".format(temp_fc_copy, copy_exists)
        arcpy.AddMessage(msg_copy_exists)

        try:
            arcpy.MakeFeatureLayer_management(temp_fc, temp_fl)
            cnt = arcpy.GetCount_management(temp_fl)[0]
        
            msg = "{} features in {}".format(cnt, temp_fc)
        except:
            msg = arcpy.AddMessage(str(arcpy.GetMessages(2)))
            arcpy.MakeFeatureLayer_management(temp_fc_copy, temp_fl)
            msg = "{}\nMakeFeature {} from {} OK".format(msg, temp_fl, temp_fc_copy)

        arcpy.Delete_management(temp_fc)
    except:
        msg = "inExcept \n{}\n{}\n\n{}".format(msg, arcpy.GetMessages(2), trace())
        
    return msg
        
    
# =====================RUN SCRIPT===========================

if __name__ == '__main__':
    start_time = "2/4/2020 11:21am"
    arcpy.AddMessage("code updated: {}".format(start_time))
    arcpy.OverwriteOutput = True

    arcpy.env.workspace = r'\\arcserver-svr\D\PPA_v2_SVR\PPA_V2.gdb'
    
    in_fc = arcpy.GetParameterAsText(0)

# =================================================================

    msg = doWork(in_fc)

    arcpy.SetParameterAsText(1, msg)

   
    

        
    

