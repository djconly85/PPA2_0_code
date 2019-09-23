# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 15:38:16 2019

@author: dconly
"""
import re
import pandas as pd
import arcpy

in_csv = r"I:\Projects\Darren\PPA_V2_GIS\CSV\parcelsILUT2012.csv"

out_csv = r'I:\Projects\Darren\PPA_V2_GIS\CSV\out_taz_lu_x_acres.csv'

cols = ['TAZ','ACRES','OPTYPE']

df_in = pd.read_csv(in_csv, usecols = cols)

#re_res_tag = ".*Residential.*"
#
#df_in.loc(df_in['OPTYPE'].str.contains('Residential'),'OPTYPE2') = 'Residential'

df_x_taz_and_type = df_in.groupby(['TAZ','OPTYPE'])['ACRES'].sum()

dfpp = df_x_taz_and_type.reset_index()

df_pivot = dfpp.pivot_table(values = 'ACRES', index = 'TAZ', columns = 'OPTYPE', fill_value = 0)

df_pivot.to_csv(out_csv)