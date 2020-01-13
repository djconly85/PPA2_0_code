'''
https://stackoverflow.com/questions/16683376/print-chosen-worksheets-in-excel-files-to-pdf-in-python

more on the win32com module - 
    Official documentation - https://docs.microsoft.com/en-us/visualstudio/vsto/excel-object-model-overview?redirectedfrom=MSDN&view=vs-2019
    https://lazywinadmin.com/2014/03/powershell-read-excel-file-using-com.html?m=1
    https://pbpython.com/windows-com.html
'''


import os
import win32com.client


if __name__ == '__main__':
    wkg_dir = r'Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\PPA2\ProjectValCSVs'
    os.chdir(wkg_dir)

    xlsx_name = 'PPA_test_project_sr51riverXing_01132020_0805.xlsx'
    xlsx_path = os.path.join(wkg_dir, xlsx_name)

    path_to_pdf = os.path.join(wkg_dir, 'sample.pdf')

    excel_app_obj = win32com.client.Dispatch("Excel.Application")
    excel_app_obj.Visible = False

    wb = excel_app_obj.Workbooks.Open(xlsx_path)
    ws_index_list = [2,3] #say you want to print these sheets

    wb.WorkSheets(ws_index_list).Select()

    wb.ActiveSheet.ExportAsFixedFormat(0, path_to_pdf)

