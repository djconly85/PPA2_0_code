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

import pdb

import arcpy
#from arcgis.features import SpatialDataFrame
import pandas as pd

arcpy.env.overwriteOutput = True

dateSuffix = str(dt.date.today().strftime('%m%d%Y'))



#====================FUNCTIONS==========================================


def conflate_tmc2projline(fl_project, fld_proj_name, proj_name, dirxn_list, tmc_dir_field, 
                          fl_tmcs_buffd, speed_data_fields, out_rows):
    
    print("getting data for {}...".format(proj_name))
    arcpy.AddMessage("getting data for {}...".format(proj_name))
    
    fld_shp_len = "SHAPE@LENGTH"
    fld_totprojlen = "proj_length_ft"
     
    out_row_dict = {"ID":proj_name}
    
    with arcpy.da.SearchCursor(fl_project, fld_shp_len) as cur:
        for row in cur:
            out_row_dict[fld_totprojlen] = row[0]
    
    for direcn in dirxn_list:
        #https://support.esri.com/en/technical-article/000012699
        
        
        #temporary files
        temp_intersctpts = "temp_intersectpoints"
        temp_intrsctpt_singlpt = "temp_intrsctpt_singlpt" #converted from multipoint to single point (1 point per feature)
        temp_splitprojlines = "temp_splitprojlines" #fc of project line split up to match TMC buffer extents
        temp_splitproj_w_tmcdata = "temp_splitproj_w_tmcdata" #fc of split project lines with TMC data on them
        
        fl_splitprojlines = "fl_splitprojlines"
        fl_splitproj_w_tmcdata = "fl_splitproj_w_tmcdata"
        
        #get TMCs whose buffers intersect the project line
        arcpy.SelectLayerByLocation_management(fl_tmcs_buffd, "INTERSECT", fl_project)
        
        #select TMCs that intersect the project and are in indicated direction
        sql_sel_tmcxdir = "{} = '{}'".format(tmc_dir_field, direcn)
        arcpy.SelectLayerByAttribute_management(fl_tmcs_buffd, "SUBSET_SELECTION", sql_sel_tmcxdir)
        
        #for reasonableness checking--correct TMCs getting selected?
        #tmc_cnt = arcpy.GetCount_management(fl_tmcs_buffd)
        #print("{} {}B TMCs selected".format(tmc_cnt, direcn))
        
        #split the project line at the boundaries of the TMC buffer, creating points where project line intersects TMC buffer boundaries
        arcpy.Intersect_analysis([fl_project, fl_tmcs_buffd],temp_intersctpts,"","","POINT")
        arcpy.MultipartToSinglepart_management (temp_intersctpts, temp_intrsctpt_singlpt)
        
        #split project line into pieces at points where it intersects buffer, with 10ft tolerance
        #(not sure why 10ft tolerance needed but it is, zero tolerance results in some not splitting)
        arcpy.SplitLineAtPoint_management(fl_project, temp_intrsctpt_singlpt,
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
        flds_df = [fld_proj_name, fld_shp_len] + speed_data_fields                     
        npa_spddata = arcpy.da.FeatureClassToNumPyArray(fl_splitproj_w_tmcdata, flds_df)
        df_spddata = pd.DataFrame(npa_spddata)
        df_spddata = df_spddata.loc[pd.notnull(df_spddata[speed_data_fields[0]])] #remove project pieces with no speed data so their distance isn't included in weighting        
        
        dir_len = df_spddata[fld_shp_len].sum() #sum of lengths of project segments that intersect TMCs in the specified direction
        out_row_dict["{}_calc_len".format(direcn)] = dir_len #"calc" length because it may not be same as project length
        
        #get distance-weighted average value for each speed/congestion field
        #for PHED or hours of delay, will want to get dist-weighted SUM; for speed/reliability, want dist-weighted AVG
        #ideally this would be a dict of {<field>:<aggregation method>}
        for field in speed_data_fields:
            try: #wgtd avg = sum(piece's data * piece's len)/(sum of all piece lengths)
                avg_data_val = (df_spddata[field]*df_spddata[fld_shp_len]).sum() \
                                / df_spddata[fld_shp_len].sum()
                
                fielddir = "{}{}".format(direcn, field) #add direction tag to field names
                out_row_dict[fielddir] = avg_data_val
            except ZeroDivisionError:
                out_row_dict[fielddir] = df_spddata[field].mean() #if no length, just return mean speed? Maybe instead just return 'no data avaialble'? Or -1 to keep as int?
                continue
    out_rows.append(out_row_dict)
    
    #cleanup
    fcs_to_delete = [temp_intersctpts, temp_intrsctpt_singlpt, temp_splitprojlines, temp_splitproj_w_tmcdata]
    for fc in fcs_to_delete:
        arcpy.Delete_management(fc)
    
    
def simplify_outputs(in_df, proj_len_col, proj_id_col):
    
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
    
    #pdb.set_trace()
    maxdir = max_len_col[:max_len_col.find(dirlen_suffix)] #direction name without '_calc_len' suffix
    secdir = secndmax_col[:secndmax_col.find(dirlen_suffix)]
    
    print(maxdir, secdir)
    
    outcols_max = [c for c in in_df.columns if re.match(maxdir, c)]
    outcols_sec = [c for c in in_df.columns if re.match(secdir, c)]
    
    outcols = [proj_id_col] + outcols_max + outcols_sec
    
    return in_df[outcols]
        
#=====================RUN SCRIPT===========================
if __name__ == '__main__':
    start_time = time.time()
    
    workspace = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb'
    arcpy.env.workspace = workspace
    
    output_dir = r'I:\Projects\Darren\PPA_V2_GIS\Temp\Script Test Outputs'
    
    project_line = "NPMRDS_confl_testseg_seconn"  #arcpy.GetParameterAsText(0) #
    proj_name =  "TestProj" #arcpy.GetParameterAsText(1) #
    proj_type = "Freeway"
    
    #NPMRDS data parameters -- consider putting all of these into a separate "config" python script
    speed_data = r"I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\npmrds_metrics_v6"
    ff_speed = "ff_speed"
    congest_speed = "havg_spd_worst4hrs"
    reliab_ampk = "lottr_ampk"
    
    fld_tmcdir = "direction_signd"
    
    #might want to make dict to enable working with multiple direction formats (e.g., {"N":"NORTHBOUND", "S":"SOUTHBOUND"...} etc.)
    directions_tmc = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND"] #can modify this depending on what directions you want to consider
    
    #------------------no more user input below here, at least normally---------------
    flds_speed_data = [ff_speed, congest_speed, reliab_ampk] #'avspd_3p6p','congn_6a9a','congn_3p6p'
    
    #create temporar buffer layer, flat-tipped, around TMCs; will be used to split project lines
    temp_tmcbuff = "TEMP_tmcbuff_4projsplit2"
    buff_dist_ft = 90 #buffer distance, in feet, around the TMCs
    
    #select TMCs that intersect project lines
    fl_project = "fl_project"
    fld_proj_len = "proj_len"
    fld_proj_name = "proj_name"
    
    fl_speed_data = "fl_speed_data"
    fl_tmc_buff = "fl_tmc_buff"
    
    #add fields for project length and name
    arcpy.AddField_management(project_line,fld_proj_len,"FLOAT")
    arcpy.AddField_management(project_line,fld_proj_name,"TEXT")
    
    #make feature layers of NPMRDS and project line
    arcpy.MakeFeatureLayer_management(project_line, fl_project)
    arcpy.MakeFeatureLayer_management(speed_data, fl_speed_data)
    
    #populate the length and name fields
    calc_add_len = "!shape.length@feet!"
    calc_set_proj_name = "'{}'".format(proj_name)
    
    arcpy.CalculateField_management(project_line, fld_proj_len, calc_add_len, "PYTHON")
    arcpy.CalculateField_management(project_line, fld_proj_name, calc_set_proj_name, "PYTHON")
    
    #make flat-ended buffers around TMCs that intersect project
    arcpy.SelectLayerByLocation_management(fl_speed_data, "WITHIN_A_DISTANCE", fl_project, 300, "NEW_SELECTION")
    arcpy.Buffer_analysis(fl_speed_data, temp_tmcbuff, buff_dist_ft, "FULL", "FLAT")
    arcpy.MakeFeatureLayer_management(temp_tmcbuff, fl_tmc_buff)
    
    out_rows = []
    
    #in theory this should only be one project line, but want to keep flexible in case
    #we want batch version in future.
    conflate_tmc2projline(fl_project, fld_proj_name, proj_name, directions_tmc, fld_tmcdir, 
                                  fl_tmc_buff, flds_speed_data, out_rows)
        
    df_projdata = pd.DataFrame(out_rows)
    
    out_df = simplify_outputs(df_projdata, 'proj_length_ft','ID')
    #out_df.iloc[0].to_dict() will write to dict in {field:value} format--might be good for ESRI CSV
    
    output_tstamp = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))
    output_csv = os.path.join(output_dir,"projlin_conflation_{}.csv".format(output_tstamp))
    arcpy.AddMessage("writing to {}...".format(output_csv))
    
    out_df.to_csv(output_csv, index = False)
    
    #NEXT STEP = join dataframe to project feature class, then look at map and do reasonableness check
    #also, how to quickly mention and bypass projects that don't intersect TMCs?
    #also, define a logical column order for the DF before doing join
    elapsed_time = round((time.time() - start_time)/60,1)
    print("Success! Time elapsed: {} minutes".format(elapsed_time))    
    
        
        
    

