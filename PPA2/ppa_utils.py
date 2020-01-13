# --------------------------------
# Name: utils.py
# Purpose: Provides general PPA functions that are used throughout various PPA scripts and are not specific to any one PPA script
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import win32com.client

import openpyxl
import pandas as pd
import arcpy


def make_fl_conditional(fc, fl):
    if arcpy.Exists(fl):
        arcpy.Delete_management(fl)
    arcpy.MakeFeatureLayer_management(fc, fl)


def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df


def rename_dict_keys(dict_in, new_key_dict):
    '''if dict in = {0:1} and dict out supposed to be {'zero':1}, this function renames the key accordingly per
    the new_key_dict (which for this example would be {0:'zero'}'''
    dict_out = {}
    for k, v in new_key_dict.items():
        if k in list(dict_in.keys()):
            dict_out[v] = dict_in[k]
        else:
            dict_out[v] = 0
    return dict_out


def join_csv_template(template_csv, in_df):
    '''takes in template CSV, left joins to desired output dataframe, ensure that
    output CSV has same rows every time, even if data frame that you're joining doesn't
    have all records'''
    df_template = pd.read_csv(template_csv)
    df_template = df_template.set_index(df_template.columns[0])
    
    df_out = df_template.join(in_df)
    
    return df_out


def overwrite_df_to_xlsx(in_df, xlsx_template, xlsx_out, tab_name, start_row=0, start_col=0):
    '''Writes pandas dataframe <in_df_ to <tab_name> sheet of <xlsx_template> excel workbook.'''

    df_records = in_df.to_records()
    out_header_list = [list(in_df.columns)]  # get header row for output
    out_data_list = [list(i) for i in df_records]  # get output data rows

    comb_out_list = out_header_list + out_data_list

    wb = openpyxl.load_workbook(xlsx_template)
    ws = wb[tab_name]
    for i, row in enumerate(comb_out_list):
        for j, val in enumerate(row):
            cell = ws.cell(row=(start_row + (i + 1)), column=(start_col + (j + 1)))
            if (cell):
                cell.value = val
    wb.save(xlsx_out)


def excel2pdf(in_xlsx, out_pdf):

    excel_app_obj = win32com.client.Dispatch("Excel.Application")
    excel_app_obj.Visible = False

    wb = excel_app_obj.Workbooks.Open(in_xlsx)
    ws_index_list = [2, 3]  # say you want to print these sheets

    wb.WorkSheets(ws_index_list).Select()
    wb.ActiveSheet.ExportAsFixedFormat(0, out_pdf)

