'''
#--------------------------------
# Name:PPA_getNPMRDSdata.py
# Purpose: Get distance-weighted average speed from NPMRDS data for PPA project,
#          
#           
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: <version>
#--------------------------------

Sample projects used: CAL20466, SAC25062
'''
import os
import re
import datetime as dt
import time

import arcpy
#from arcgis.features import SpatialDataFrame
import pandas as pd

import ppa_input_params as p

arcpy.env.overwriteOutput = True

dateSuffix = str(dt.date.today().strftime('%m%d%Y'))



#====================FUNCTIONS==========================================

def esri_object_to_df(in_esri_obj, esri_obj_fields, index_field=None):
    data_rows = []
    with arcpy.da.SearchCursor(in_esri_obj, esri_obj_fields) as cur:
        for row in cur:
            out_row = list(row)
            data_rows.append(out_row)

    out_df = pd.DataFrame(data_rows, index=index_field, columns=esri_obj_fields)
    return out_df

def conflate_tmc2projline(fl_proj, dirxn_list, tmc_dir_field,
                          fl_tmcs_buffd, speed_data_fields):

    out_row_dict = {}
    
    #get length of project
    fld_shp_len = "SHAPE@LENGTH"
    fld_totprojlen = "proj_length_ft"
    
    with arcpy.da.SearchCursor(fl_proj, fld_shp_len) as cur:
        for row in cur:
            out_row_dict[fld_totprojlen] = row[0]
    
    for direcn in dirxn_list:
        # https://support.esri.com/en/technical-article/000012699
        
        # temporary files
        temp_intersctpts = "temp_intersectpoints"
        temp_intrsctpt_singlpt = "temp_intrsctpt_singlpt" # converted from multipoint to single point (1 pt per feature)
        temp_splitprojlines = "temp_splitprojlines" # fc of project line split up to match TMC buffer extents
        temp_splitproj_w_tmcdata = "temp_splitproj_w_tmcdata" # fc of split project lines with TMC data on them
        
        fl_splitprojlines = "fl_splitprojlines"
        fl_splitproj_w_tmcdata = "fl_splitproj_w_tmcdata"
        
        # get TMCs whose buffers intersect the project line
        arcpy.SelectLayerByLocation_management(fl_tmcs_buffd, "INTERSECT", fl_proj)
        
        # select TMCs that intersect the project and are in indicated direction
        sql_sel_tmcxdir = "{} = '{}'".format(tmc_dir_field, direcn)
        arcpy.SelectLayerByAttribute_management(fl_tmcs_buffd, "SUBSET_SELECTION", sql_sel_tmcxdir)
        
        #split the project line at the boundaries of the TMC buffer, creating points where project line intersects TMC buffer boundaries
        arcpy.Intersect_analysis([fl_proj, fl_tmcs_buffd],temp_intersctpts,"","","POINT")
        arcpy.MultipartToSinglepart_management (temp_intersctpts, temp_intrsctpt_singlpt)
        
        #split project line into pieces at points where it intersects buffer, with 10ft tolerance
        #(not sure why 10ft tolerance needed but it is, zero tolerance results in some not splitting)
        arcpy.SplitLineAtPoint_management(fl_proj, temp_intrsctpt_singlpt,
                                          temp_splitprojlines, "10 Feet")
        arcpy.MakeFeatureLayer_management(temp_splitprojlines, fl_splitprojlines)
        
        #get TMC speeds onto each piece of the split project line via spatial join
        arcpy.SpatialJoin_analysis(temp_splitprojlines, fl_tmcs_buffd, temp_splitproj_w_tmcdata,
                                   "JOIN_ONE_TO_ONE", "KEEP_ALL", "#", "HAVE_THEIR_CENTER_IN", "30 Feet")
                                   
        #convert to fl and select records where "check field" col val is not none
        arcpy.MakeFeatureLayer_management(temp_splitproj_w_tmcdata, fl_splitproj_w_tmcdata)
        
        check_field = speed_data_fields[0] #choose first speed value field for checking--if it's null, then don't include those rows in aggregation
        sql_notnull = "{} IS NOT NULL".format(check_field)
        arcpy.SelectLayerByAttribute_management(fl_splitproj_w_tmcdata, "NEW_SELECTION", sql_notnull)
        
        #convert the selected records into a numpy array then a pandas dataframe
        flds_df = [fld_shp_len] + speed_data_fields
        df_spddata = esri_object_to_df(fl_splitproj_w_tmcdata, flds_df)

        # remove project pieces with no speed data so their distance isn't included in weighting
        df_spddata = df_spddata.loc[pd.notnull(df_spddata[speed_data_fields[0]])].astype(float)
        
        dir_len = df_spddata[fld_shp_len].sum() #sum of lengths of project segments that intersect TMCs in the specified direction
        out_row_dict["{}_calc_len".format(direcn)] = dir_len #"calc" length because it may not be same as project length
        
        #get distance-weighted average value for each speed/congestion field
        #for PHED or hours of delay, will want to get dist-weighted SUM; for speed/reliability, want dist-weighted AVG
        #ideally this would be a dict of {<field>:<aggregation method>}
        for field in speed_data_fields:
            fielddir = "{}{}".format(direcn, field)  # add direction tag to field names
            try: #wgtd avg = sum(piece's data * piece's len)/(sum of all piece lengths)
                avg_data_val = (df_spddata[field]*df_spddata[fld_shp_len]).sum() \
                                / df_spddata[fld_shp_len].sum()

                out_row_dict[fielddir] = avg_data_val
            except ZeroDivisionError:
                out_row_dict[fielddir] = df_spddata[field].mean() #if no length, just return mean speed? Maybe instead just return 'no data avaialble'? Or -1 to keep as int?
                continue

    #cleanup
    fcs_to_delete = [temp_intersctpts, temp_intrsctpt_singlpt, temp_splitprojlines, temp_splitproj_w_tmcdata]
    for fc in fcs_to_delete:
        arcpy.Delete_management(fc)
    return pd.DataFrame([out_row_dict])
    
    
def simplify_outputs(in_df, proj_len_col):
    dirlen_suffix = '_calc_len'
    
    proj_len = in_df[proj_len_col][0]
    
    re_lendir_col = '.*{}'.format(dirlen_suffix)
    lendir_cols = [i for i in in_df.columns if re.search(re_lendir_col, i)]
    df_lencols = in_df[lendir_cols]    
    
    max_dir_len = df_lencols.max(axis = 1)[0] # direction for which project has longest intersect with TMC. assumes just one record in the output
    
    #if there's less than 10% overlap in the 'highest overlap' direction, then say that the project is not on any TMCs (and any TMC data is from cross streets or is insufficient to represent the segment)
    if (max_dir_len / proj_len) < 0.1:
        return pd.DataFrame([-1])
    else:
        max_len_col = df_lencols.idxmax(axis = 1)[0] #return column name of direction with greatest overlap
        df_lencols2 = df_lencols.drop(max_len_col, axis = 1)
        secndmax_col = df_lencols2.idxmax(axis = 1)[0] #return col name of direction with second-most overlap (should be reverse of direction with most overlap)

    maxdir = max_len_col[:max_len_col.find(dirlen_suffix)] #direction name without '_calc_len' suffix
    secdir = secndmax_col[:secndmax_col.find(dirlen_suffix)]
    
    outcols_max = [c for c in in_df.columns if re.match(maxdir, c)]
    outcols_sec = [c for c in in_df.columns if re.match(secdir, c)]
    
    outcols = outcols_max + outcols_sec
    
    return in_df[outcols].to_dict('records')


def get_npmrds_data(fc_projline, str_project_type):
    arcpy.AddMessage("Calculating congestion and reliability metrics...")
    arcpy.OverwriteOutput = True

    fl_projline = "fl_project"
    arcpy.MakeFeatureLayer_management(fc_projline, fl_projline)

    # make feature layer from speed data feature class
    fl_speed_data = "fl_speed_data"
    arcpy.MakeFeatureLayer_management(p.fc_speed_data, fl_speed_data)

    # make flat-ended buffers around TMCs that intersect project
    arcpy.SelectLayerByLocation_management(fl_speed_data, "WITHIN_A_DISTANCE", fl_projline, p.tmc_select_srchdist, "NEW_SELECTION")
    if str_project_type == 'Freeway':
        sql = "{} IN {}".format(p.col_roadtype, p.roadtypes_fwy)
        arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)
    else:
        sql = "{} NOT IN {}".format(p.col_roadtype, p.roadtypes_fwy)
        arcpy.SelectLayerByAttribute_management(fl_speed_data, "SUBSET_SELECTION", sql)

    # create temporar buffer layer, flat-tipped, around TMCs; will be used to split project lines
    temp_tmcbuff = "TEMP_tmcbuff_4projsplit"
    fl_tmc_buff = "fl_tmc_buff"
    arcpy.Buffer_analysis(fl_speed_data, temp_tmcbuff, p.tmc_buff_dist_ft, "FULL", "FLAT")
    arcpy.MakeFeatureLayer_management(temp_tmcbuff, fl_tmc_buff)

    # get "full" table with data for all directions
    projdata_df = conflate_tmc2projline(fl_projline, p.directions_tmc, p.col_tmcdir,
                                        fl_tmc_buff, p.flds_speed_data)

    # trim down table to only include outputs for directions that are "on the segment",
    # i.e., that have most overlap with segment
    out_dict = simplify_outputs(projdata_df, 'proj_length_ft')[0]

    #cleanup
    arcpy.Delete_management(temp_tmcbuff)

    return out_dict




# =====================RUN SCRIPT===========================
if __name__ == '__main__':
    start_time = time.time()
    
    workspace = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb'
    arcpy.env.workspace = workspace

    project_line = "PPA_test_fwyproj" # arcpy.GetParameterAsText(0) #"NPMRDS_confl_testseg_seconn"
    proj_type = p.ptype_fwy # arcpy.GetParameterAsText(2) #"Freeway"

    # make feature layers of NPMRDS and project line


    get_npmrds_data(project_line, proj_type)

    elapsed_time = round((time.time() - start_time)/60, 1)
    print("Success! Time elapsed: {} minutes".format(elapsed_time))    
    

        
    

