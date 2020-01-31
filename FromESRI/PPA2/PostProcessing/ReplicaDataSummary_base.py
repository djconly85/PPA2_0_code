# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 13:46:21 2019

@author: dconly
"""

import pandas as pd
import arcpy

def esri_field_exists(in_tbl, field_name):
    fields = [f.name for f in arcpy.ListFields(in_tbl)]
    
    if field_name in fields:
        return True
    else:
        return False

# make dataframe summarizing items by desired group field (e.g. trips by block group ID)
def trips_x_polygon(in_df, val_field, agg_fxn, groupby_field, case_field=None):
    piv = in_df.pivot_table(values=val_field, index=groupby_field, columns=case_field, 
                            aggfunc=agg_fxn)
    piv = piv.reset_index()
    return piv

def join_vals_to_polydf(in_df, groupby_field, in_poly_fc, poly_id_field):
    
    #convert numpy (pandas) datatypes to ESRI data types {numpy type: ESRI type}
    dtype_conv_dict = {'float64':'FLOAT', 'object':'TEXT','int64':'LONG'}
    
    df_fields = list(in_df.columns) # get list of the dataframe's columns
    #df_fields.remove(groupby_field) #remove the join id field from field list
    
    df_ids = list(in_df[groupby_field]) # get list of index/ID values (e.g. block group IDs)
    
    # {dataframe column: column data type...}
    fields_dtype_dict = {col:str(in_df[col].dtype) for col in in_df.columns}
    
    in_poly_fl = "in_poly_fl"
    
    if arcpy.Exists(in_poly_fl):
        arcpy.Delete_management(in_poly_fl)
        arcpy.MakeFeatureLayer_management(in_poly_fc, in_poly_fl)
    else:
        arcpy.MakeFeatureLayer_management(in_poly_fc, in_poly_fl)
    
    for field in df_fields:
        print("adding {} column and data...".format(field))
        field_vals = list(in_df[field]) # get list of values for desired field
        fld_dict = dict(zip(df_ids, field_vals))
        
        fdtype_numpy = fields_dtype_dict[field]
        fdtype_esri = dtype_conv_dict[fdtype_numpy]
        
        # add a field, if needed, to the polygon feature class for the values being added
        if esri_field_exists(in_poly_fl, field):
            pass
        else:
            arcpy.AddField_management(in_poly_fl, field, fdtype_esri)
            
        # populate the field with the appropriate values
        with arcpy.da.UpdateCursor(in_poly_fl, [poly_id_field, field]) as cur:
            for row in cur:
                join_id = row[0]
                if fld_dict.get(join_id) is None:
                    pass
                else:
                    row[1] = fld_dict[join_id]
                    cur.updateRow(row)
        
        

if __name__ == '__main__':
    
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb'
    csv_tripdata = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\Replica\ReplicaDownloads\GrantLineRoad_ThursdayFall.csv"
    
    value_field = 'trip_start_time'
    val_aggn_type = 'count'
    
    fc_bg = "BlockGroups2010"
    bg_poly_id_field = "GEOID10"

    col_bgid = 'origin_blockgroup_id'
    mode_col = 'trip_primary_mode'
    
    df_tripdata = pd.read_csv(csv_tripdata)
    
    pivtbl = trips_x_polygon(df_tripdata, value_field, val_aggn_type, col_bgid, mode_col)
    
    print("adding data to {} feature class...".format(fc_bg))
    join_vals_to_polydf(pivtbl, col_bgid, fc_bg, bg_poly_id_field)
    