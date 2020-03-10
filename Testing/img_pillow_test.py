# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 08:20:40 2020

@author: DConly
"""



import arcpy

img_file = "E:\ArcGIS\PPA2_DevPortal\Tests\Capture.JPG"

def trace():
    import sys, traceback, inspect
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # script name + line number
    line = tbinfo.split(", ")[1]
    filename = inspect.getfile(inspect.currentframe())
    # Get Python syntax error
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror

try:
    from openpyxl.drawing.image import Image
    img_obj = Image(img_file)
    msg = "successfully imported Image from openpyxl. No Pillow-related errors"
except:
    msg = trace()
    
arcpy.SetParameterAsText(0, msg)