# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 11:12:02 2020

@author: dconly
"""

import os
import time 
import gc
import xlwings as xw
import shutil

import arcpy 
try:
    import arcpy.mapping as mp 
except:
    import arcpy.mp as mp 

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


def excel2pdf(in_xlsx, out_pdf, sheets_to_print):
    msg = out_pdf
    wb = None
    try:
        out_folder = arcpy.env.scratchFolder 
        ddt = time.clock()
        xw.App.visible = True

        (name, ext) = os.path.splitext(in_xlsx)    # returns tuple(<full file path up to and including name without file extn>, <.file extn>)
        print_xlsx = "{}{}{}".format(name, int(time.clock()), ext)
        if(os.path.exists(print_xlsx)):
            os.remove(print_xlsx)
        arcpy.AddMessage("OUTPUT XLSX FILE - {}".format(print_xlsx))
        shutil.copy2(in_xlsx, print_xlsx)
        wb = xw.Book(print_xlsx)
        #for s in wb.sheets:
        #    if(s.name.lower() in sheets_to_print)==False:
        #        wb.sheets[s].delete()

        msg = "{}".format(in_xlsx)
        #wb = xw.Book(in_xlsx)
        l_sheets_pdf = []
        for s in sheets_to_print:
            try:
                sheet_to_print = wb.sheets[s]
                sheet_pdf = os.path.join(out_folder, "{}.pdf".format(s))
                if(os.path.exists(sheet_pdf)):
                    os.remove(sheet_pdf)
                sheet_to_print.api.ExportAsFixedFormat(0, sheet_pdf)
                l_sheets_pdf.append(sheet_pdf)
            except:
                msg = "{}\n{}".format(msg, trace())
                arcpy.AddMessage(msg)
                
        #wb.api.ExportAsFixedFormat(0, out_pdf)
        n_pdfs = len(l_sheets_pdf)
        if(n_pdfs==1):
            shutil.copy2(sheet_pdf, out_pdf)
            #out_pdf = sheet_pdf
            pdfs = sheet_pdf

        elif(n_pdfs>1):
            final_pdf = mp.PDFDocumentCreate(out_pdf)
            for pdf in l_sheets_pdf:
                final_pdf.appendPages(pdf)
            pdfs = ";".join(l_sheets_pdf)
            final_pdf.saveAndClose()
      
        msg = "output={}, ds={:0.3f}s  \n[{}]".format(out_pdf, time.clock()-ddt, pdfs)           
        arcpy.AddMessage(msg)
    except:
        msg = "{}\n{}".format(msg, trace())
        arcpy.AddMessage(msg)
    finally:
        if(wb!=None):
            wb.close()
            del wb 

        ddt = time.clock()
        n=gc.collect()
        arcpy.AddMessage("{} objects cleaned by gc.collect(), dds={:0.3f}s".format(n, time.clock()-ddt))

    return msg  

if __name__=='__main__':
    #D:\Projects\ApProjects\SACOGPPA\docs\PPA_test_project_offNPMRDSNet_01132020_1103.xlsx test.pdf    
    input_excel = arcpy.GetParameterAsText(0) #input Excel
    out_name = arcpy.GetParameterAsText(1) #output PDF
    out_file = os.path.join(arcpy.env.scratchFolder, out_name)
    sheets_to_print = ['import', 'charts_pg1','charts_pg2']
    #sheets_to_print = ['charts_pg2']
    msg = excel2pdf(input_excel, out_file, sheets_to_print)
    arcpy.SetParameterAsText(2, out_file)
    arcpy.SetParameterAsText(3, msg)

