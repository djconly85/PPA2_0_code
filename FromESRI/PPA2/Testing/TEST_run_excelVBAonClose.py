# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 09:56:29 2020

@author: dconly
"""

import openpyxl


in_xlsm = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\PPA2\ProjectValCSVs\PPA_TemplateTEST_vba.xlsm"
out_xlsm = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\PPA2\ProjectValCSVs\PPA_TemplateTEST_vbaOUT.xlsm"

wb = openpyxl.load_workbook(filename=in_xlsm, read_only=False, keep_vba=True)
wb.save(out_xlsm)
wb.close()