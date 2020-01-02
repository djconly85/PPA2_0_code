# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 13:46:21 2019

@author: dconly
"""

import pandas as pd
import arcpy

def make_fl_conditional(fc, fl):
    if arcpy.Exists(fl):
        arcpy.Delete_management(fl)
    arcpy.MakeFeatureLayer_management(fc, fl)

def esri_field_exists(in_tbl, field_name):
    fields = [f.name for f in arcpy.ListFields(in_tbl)]
    if field_name in fields:
        return True
    else:
        return False


# make dataframe summarizing items by desired group field (e.g. trips by block group ID)
def trips_x_polygon(in_df, val_field, agg_fxn, groupby_field, case_field=None):
    
    col_sov = 'PRIVATE_AUTO'
    col_hov = 'CARPOOL'
    col_commveh = 'COMMERCIAL'
    col_tnc = 'ON_DEMAND_AUTO'
    col_walk = 'WALKING'
    col_bike = 'BICYCLE'
    col_transit = 'TRANSIT'
    
    col_tottrips = 'tot_trips'
    col_trippctlrank = 'trips_pctlrank'
    
    allmodes = [col_sov, col_hov, col_commveh, col_tnc, col_walk, col_bike, col_transit]
    
    piv = in_df.pivot_table(values=val_field, index=groupby_field, columns=case_field, 
                            aggfunc=agg_fxn)
    piv = piv.reset_index()
    
    tblmodes = [mode for mode in allmodes if mode in piv.columns]
    
    piv[col_tottrips] = piv[tblmodes].sum(axis=1)
    piv[col_trippctlrank] = piv[col_tottrips].rank(method='min', pct=True)

    return piv


def join_vals_to_polydf(in_df, groupby_field, in_poly_fc, poly_id_field):
    
    # convert numpy (pandas) datatypes to ESRI data types {numpy type: ESRI type}
    dtype_conv_dict = {'float64': 'FLOAT', 'object': 'TEXT', 'int64': 'LONG'}
    
    df_fields = list(in_df.columns) # get list of the dataframe's columns
    # df_fields.remove(groupby_field) #remove the join id field from field list
    
    df_ids = list(in_df[groupby_field]) # get list of index/ID values (e.g. block group IDs)
    
    # {dataframe column: column data type...}
    fields_dtype_dict = {col:str(in_df[col].dtype) for col in in_df.columns}
    
    in_poly_fl = "in_poly_fl"

    make_fl_conditional(in_poly_fc, in_poly_fl)
    
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
    
    # ------------------USER INPUTS----------------------------------------
    
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    
    csv_tripdata = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\Replica\ReplicaDownloads\GrantLineRoad_ThursdayFall.csv"
    
    csvcol_bgid = 'origin_blockgroup_id'  # Replica/big data block group ID column
    csvcol_mode = 'trip_primary_mode'  # Replica/big data trip mode column
    
    csvcol_valfield = 'trip_start_time' # field for which you want to aggregate values
    val_aggn_type = 'count'  # how you want to aggregate the values field (e.g. count of values, sum of values, avg, etc.)
    
    # feature class of polygons to which you'll join data to based on ID field
    fc_bg = "ReplicaTShed_SECTest"
    fc_poly_id_field = "GEOID10"
    
    join_to_fc = True

    #------------RUN SCRIPT------------------------------------
    
    df_tripdata = pd.read_csv(csv_tripdata)
    
    pivtbl = trips_x_polygon(df_tripdata, csvcol_valfield, val_aggn_type, csvcol_bgid, csvcol_mode)
    
    if join_to_fc:
        print("adding data to {} feature class...".format(fc_bg))
        join_vals_to_polydf(pivtbl, csvcol_bgid, fc_bg, fc_poly_id_field)
    