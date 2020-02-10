import arcpy
import pandas as pd
import openpyxl
import xlwings as xw

#

data = r"\\arcserver-svr\D\PPA_v2_SVR\PPA_V2.gdb\sacog_region"
data_layer = "datalayer"
file = r"\\arcserver-svr\D\PPA_v2_SVR\PPA2\TestingScript.py"

if(__name__=='__main__'):
    t = arcpy.GetParameterAsText(0) 
    if(arcpy.Exists(data_layer)): arcpy.Delete_management(data_layer) 
    arcpy.MakeFeatureLayer_management(data, data_layer) 
    n = arcpy.GetCount_management(data_layer)[0]
    
    msg = "data:\n{}\n{}".format(data, file) 
    
    msg = "{}\n{} has {} features".format(msg, data, n)
    l = []
    with open(file, 'r') as in_file:
        l = in_file.readlines()
    msg = "{}\n{}".format(msg, l)

    arcpy.AddMessage(msg)    
    arcpy.SetParameterAsText(1, msg) 
