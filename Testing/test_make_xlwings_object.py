# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:58:17 2020

@author: DConly
"""
import sys
import getpass

import arcpy

import xlwings as xw

xlsx = r"\\arcserver-svr\D\PPA_v2_SVR\Tests\TestWorksheet2.xlsx"

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


arcpy.AddMessage(sys.executable)
arcpy.AddMessage(getpass.getuser())
try:
    # make excel workbook with project outputs
    xw.App.visible = True # must be set to True or else it won't work            
    wb = xw.Book(xlsx)
    wb.close()
    msg = "Success! xlwings workbook object created and closed!"
except:
    msg = trace()
    
arcpy.SetParameterAsText(0, msg)
    
    
