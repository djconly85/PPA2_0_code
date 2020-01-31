'''
https://stackoverflow.com/questions/16683376/print-chosen-worksheets-in-excel-files-to-pdf-in-python

more on the win32com module - 
    Official documentation - https://docs.microsoft.com/en-us/visualstudio/vsto/excel-object-model-overview?redirectedfrom=MSDN&view=vs-2019
    https://lazywinadmin.com/2014/03/powershell-read-excel-file-using-com.html?m=1
    https://pbpython.com/windows-com.html
'''


import os
import win32com.client


def excel2pdf(in_xlsx, out_pdf, sheets_to_pdf_list):

    excel_app_obj = win32com.client.Dispatch("Excel.Application")  # creates object for interacting with Excel files
    
    # Settings so that the targeted Excel template workbook does not visibly open when you activate it.
    excel_app_obj.Visible = False 
    # excel_app_obj.ScreenUpdating = False
    # excel_app_obj.DisplayAlerts = False
    # excel_app_obj.EnableEvents = False

    wb = excel_app_obj.Workbooks.Open(in_xlsx)  # open a specific Excel workbook (XLSX file)
    
    # indicate which sheets you want to open
    ws_index_list = sheets_to_pdf_list  # ws_index_list = [2, 3]  # say you want to print these sheets

    wb.WorkSheets(ws_index_list).Select()
    wb.ActiveSheet.ExportAsFixedFormat(0, out_pdf)
    
    excel_app_obj.Quit()

if __name__ == '__main__':
    wkg_dir = r'Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\PPA2\ProjectValCSVs'
    os.chdir(wkg_dir)

    xlsx_name = 'PPA_test_project_offNPMRDSNet_01132020_1103.xlsx'
    xlsx_path = os.path.join(wkg_dir, xlsx_name)

    path_to_pdf = os.path.join(wkg_dir, 'sample.pdf')
    
    #excel2pdf(xlsx_path, path_to_pdf, ['charts_pg1', 'charts_pg2'])    
    
    excel_app_obj = win32com.client.Dispatch("Excel.Application") # win32com.client.Dispatch("Excel.Application")
    excel_app_obj.Visible = False

    wb = excel_app_obj.Workbooks.Open(xlsx_path)
    ws_index_list = [2,3] #say you want to print these sheets

    wb.Worksheets(['charts_pg1', 'charts_pg2']).Select()

    wb.ActiveSheet.ExportAsFixedFormat(0, path_to_pdf)
    
    excel_app_obj.Quit()

