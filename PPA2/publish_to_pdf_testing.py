# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 14:15:41 2020

@author: dconly
"""
import time
import os

import arcpy
import pandas as pd
# import openpyxl

import ppa_utils as utils
import ppa_input_params as params

proj_fc = arcpy.GetParameterAsText(0)  
xlt_in = r"\\arcserver-svr\D\PPA_v2_SVR\PPA2\Input_Template\XLSX\PPA_Template_ArterialExp.xlsx"
csv_in = r"\\arcserver-svr\D\PPA_v2_SVR\Tests\sample_ppa_raw_output.csv"
proj_type = params.ptype_arterial

out_dir = arcpy.env.scratchFolder
xl_out = os.path.join(out_dir,"OutputTest{}.xlsx".format(int(time.clock())))



df_test = pd.read_csv(csv_in, index_col='data_item')

sheets_to_pdf = ['1ReduceVMT', '3Multimodal']


output = utils.Publish(df_test, xlt_in, params.xlsx_import_sheet, xl_out, proj_fc, proj_type, xlsheets_to_pdf=sheets_to_pdf, 
                 proj_name='UnnamedProject')

print('making PDF...')
results = output.make_pdf()

arcpy.SetParameterAsText(1, results[1])
arcpy.SetParameterAsText(2, results[2])

# print(results[0])
# print(results[1])
    
