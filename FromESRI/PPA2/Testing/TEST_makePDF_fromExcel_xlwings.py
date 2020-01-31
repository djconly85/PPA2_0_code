# -*- coding: utf-8 -*-
"""
Use xlwings to convert Excel file to PDF

TROUBLESHOOTING:
    Error - AttributeError: module 'win32com.gen_py.00020813-0000-0000-C000-000000000046x0x1x9' has no attribute 'CLSIDToClassMap'
        Solution - import win32com, then enter  print(win32com.__gen_path__), which will give you folder path.
            Delete the folder at the end of the folder path.
"""

import os
import gc
import datetime as dt

import xlwings as xw

working_dir = r'C:\TEMP_OUTPUT\Testing'

xlsx_test_in = 'Test_XLSX_input.xlsx'
sheets_to_print = ['charts_pg1'] # for now, will just be single output sheet that has full report on it. Ideally could split into different tabs.


# -----------------------------------------------
time_sufx = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))

os.chdir(working_dir)

# load excel workbook
xw.App.visible = False  # make sure that workbook doesn't visibly open
wb = xw.Book(xlsx_test_in)

#select desired sheets
for s in sheets_to_print:
    out_sheet = wb.sheets[s]
    out_sheet.api.ExportAsFixedFormat(0, os.path.join(working_dir, "{}.pdf".format(s)))

wb.close()
gc.collect()


