# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 08:20:40 2020

@author: DConly
"""



import arcpy
import openpyxl

img_file = r"C:\Users\dconly\Desktop\testimg.JPG"
xlsx = r"C:\Users\dconly\Desktop\TestWorkbook.xlsx"
sheet = "Sheet1"
row = 1
col = "A"

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


def insert_image_xlsx(wb, sheet_name, rownum, col_letter, img_file):
    '''inserts image into specified sheet and cell within Excel workbook'''
    ws = wb[sheet_name]
    cell = '{}{}'.format(col_letter, rownum) # will be where upper left corner of image placed
    arcpy.AddMessage("About to Make Image File from {}".format(img_file))
    img_obj = Image(img_file)
    ws.add_image(img_obj, cell)

try:
    from openpyxl.drawing.image import Image
    
    wb = openpyxl.load_workbook(xlsx)
    
    insert_image_xlsx(wb, sheet, row, col, img_file)
    wb.save(xlsx)

    msg = "successfully imported Image from openpyxl and inserted to test workbook. No Pillow-related errors"
except:
    msg = trace()
    
print(msg)
    
arcpy.SetParameterAsText(0, msg)