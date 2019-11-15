# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from dbfread import DBF
import pandas as pd
import swifter


year = 2040

in_dbf = r"I:\Projects\Darren\PPA_V2_GIS\SACSIM Model Data\trans.link.all_{}.dbf".format(year)

out_csv = r'I:\Projects\Darren\PPA_V2_GIS\SACSIM Model Data\transit_linkvol_{}.csv'.format(year)

col_anode = 'A'
col_bnode = 'B'

grouby_cons_col = '{}_{}'.format(col_anode, col_bnode)

val_cols = ['VOL', 'REV_VOL']
# ---------------------------------------------------------

dbf = DBF(in_dbf)
df_data = pd.DataFrame(dbf)

input_cols = [col_anode, col_bnode] + val_cols

df_data = df_data[input_cols]

df_data[grouby_cons_col] = df_data[col_anode].map(str) + '_' + df_data[col_bnode].map(str) 

#df_data[grouby_cons_col] = df_data.swifter.apply(lambda x: '{}_{}'.format(x[group_cols[0]], x[group_cols[1]]), axis = 1)

val_cols.append(grouby_cons_col)

df_summed = df_data[val_cols].groupby([grouby_cons_col]).sum().reset_index()
df_summed[val_cols].to_csv(out_csv, index = False)
print('success!')