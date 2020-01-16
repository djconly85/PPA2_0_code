# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 10:25:02 2020

@author: dconly


https://openpyxl.readthedocs.io/en/stable/usage.html
"""
import os
import datetime as dt

import openpyxl
from openpyxl.drawing.image import Image

working_dir = r'C:\TEMP_OUTPUT\Testing'

xlsx_test_in = 'Test_XLSX_output01162020_1042.xlsx'
sheet_to_print = 'charts_pg1' # for now, will just be single output sheet that has full report on it. Ideally could split into different tabs.



img_file = 'test_map_img.png'


def insert_image(workbook_obj, sheet_name, rownum, col_letter, img_file):
    ws = wb[sheet_to_print]
    cell = '{}{}'.format(col_letter, rownum) # will be where upper left corner of image placed
    img_obj = Image(img_file)
    ws.add_image(img_obj, cell)

# -----------------------------------------------
time_sufx = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))
xlsx_out = 'Test_XLSX_output01162020_1042.xlsx'  # 'Test_XLSX_output{}.xlsx'.format(time_sufx)

os.chdir(working_dir)

wb = openpyxl.load_workbook(xlsx_test_in)

insert_image(wb, sheet_to_print, 103, "B", img_file)
wb.save(xlsx_out)



