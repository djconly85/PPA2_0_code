# -*- coding: utf-8 -*-
"""
Created on Sun Mar  1 12:41:56 2020

@author: DConly
"""


import os
import time

import openpyxl
from openpyxl.drawing.image import Image




def insert_image_xlsx(wb, sheet_name, rownum, col_letter, img_file):
    '''inserts image into specified sheet and cell within Excel workbook'''
    ws = wb[sheet_name]
    cell = '{}{}'.format(col_letter, rownum) # will be where upper left corner of image placed
    img_obj = Image(img_file)
    ws.add_image(img_obj, cell)


xlsm = r"E:\ArcGIS\PPA2_DevPortal\Tests\TestWorksheetMACRO.xlsm"
img = r"E:\ArcGIS\PPA2_DevPortal\Tests\Capture.JPG"

xlsm_out = r"E:\ArcGIS\PPA2_DevPortal\Tests\TestWorksheetMACRO_OUT{}.xlsm".format(int(time.time()))

wb = openpyxl.load_workbook(xlsm, read_only=False, keep_vba=True)


insert_image_xlsx(wb, "Sheet1", 10, "A", img)

wb.save(xlsm_out)

wb.close()
