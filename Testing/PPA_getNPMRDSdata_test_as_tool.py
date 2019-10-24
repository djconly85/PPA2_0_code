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
import arcpy
#from arcgis.features import SpatialDataFrame
import datetime
import time
import pandas as pd

arcpy.env.overwriteOutput = True

dateSuffix = str(datetime.date.today().strftime('%m%d%Y'))



#====================FUNCTIONS==========================================


def conflate_tmc2projline(fl_projects, project_id, proj_id_col, dir_list, tmc_dir_field, 
                          fl_tmcs_buffd, speed_data_fields, out_rows):
    print("getting data for {}...".format(project_id))
    #output_diss_fc = "outputSpdData_{}".format(project)
    
    fld_shp_len = "SHAPE@LENGTH"
    fld_totprojlen = "proj_length_ft"
    
    #select project line
    sql_sel_proj = "{} = '{}'".format(proj_id_col, project_id)
    arcpy.SelectLayerByAttribute_management(fl_projects, "NEW_SELECTION", sql_sel_proj)
     
    out_row_dict = {"ID":project_id}
    
    with arcpy.da.SearchCursor(fl_projects, fld_shp_len) as cur:
        for row in cur:
            out_row_dict[fld_totprojlen] = row[0]
    
    for direcn in dir_list:
        #https://support.esri.com/en/technical-article/000012699
        
        
        #temporary files
        temp_intersctpts = "temp_intersectpoints"
        temp_intrsctpt_singlpt = "temp_intrsctpt_singlpt" #converted from multipoint to single point (1 point per feature)
        temp_splitprojlines = "temp_splitprojlines" #fc of project line split up to match TMC buffer extents
        temp_splitproj_w_tmcdata = "temp_splitproj_w_tmcdata" #fc of split project lines with TMC data on them
        
        fl_splitprojlines = "fl_splitprojlines"
        fl_splitproj_w_tmcdata = "fl_splitproj_w_tmcdata"
        
        #get TMCs whose buffers intersect the project line
        arcpy.SelectLayerByLocation_management(fl_tmcs_buffd, "INTERSECT", fl_projects)
        
        #select TMCs that intersect the project and are in indicated direction
        sql_sel_tmcxdir = "{} = '{}'".format(tmc_dir_field, direcn)
        arcpy.SelectLayerByAttribute_management(fl_tmcs_buffd, "SUBSET_SELECTION", sql_sel_tmcxdir)
        
        #for reasonableness checking--correct TMCs getting selected?
        #tmc_cnt = arcpy.GetCount_management(fl_tmcs_buffd)
        #print("{} {}B TMCs selected".format(tmc_cnt, direcn))
        
        #split the project line at the boundaries of the TMC buffer, creating points where project line intersects TMC buffer boundaries
        arcpy.Intersect_analysis([fl_projects, fl_tmcs_buffd],temp_intersctpts,"","","POINT")
        arcpy.MultipartToSinglepart_management (temp_intersctpts, temp_intrsctpt_singlpt)
        
        #split project line into pieces at points where it intersects buffer, with 10ft tolerance
        #(not sure why 10ft tolerance needed but it is, zero tolerance results in some not splitting)
        arcpy.SplitLineAtPoint_management(fl_projects, temp_intrsctpt_singlpt,
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
        flds_df = [proj_id_col, fld_shp_len] + speed_data_fields                     
        npa_spddata = arcpy.da.FeatureClassToNumPyArray(fl_splitproj_w_tmcdata, flds_df)
        df_spddata = pd.DataFrame(npa_spddata)
        df_spddata = df_spddata.loc[pd.notnull(df_spddata[speed_data_fields[0]])] #remove project pieces with no speed data so their distance isn't included in weighting        
        
        dir_len = df_spddata[fld_shp_len].sum() #sum of lengths of project segments that intersect TMCs in the specified direction
        out_row_dict["{}B_calc_len".format(direcn)] = dir_len #"calc" length because it may not be same as project length
        
        #get distance-weighted average value for each speed/congestion field
        #for PHED or hours of delay, will want to get dist-weighted SUM; for speed/reliability, want dist-weighted AVG
        #ideally this would be a dict of {<field>:<aggregation method>}
        for field in speed_data_fields:
            try: #wgtd avg = sum(piece's data * piece's len)/(sum of all piece lengths)
                avg_data_val = (df_spddata[field]*df_spddata[fld_shp_len]).sum() \
                                / df_spddata[fld_shp_len].sum()
                
                fielddir = "{}B{}".format(direcn, field) #add direction tag to field names
                out_row_dict[fielddir] = avg_data_val
            except ZeroDivisionError:
                out_row_dict[fielddir] = df_spddata[field].mean()
                continue
    out_rows.append(out_row_dict)
    
    #cleanup
    fcs_to_delete = [temp_intersctpts, temp_intrsctpt_singlpt, temp_splitprojlines, temp_splitproj_w_tmcdata]
    for fc in fcs_to_delete:
        arcpy.Delete_management(fc)
    
#=====================RUN SCRIPT===========================
if __name__ == '__main__':
    start_time = time.time()
    
    workspace = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb'
    arcpy.env.workspace = workspace
    
    output_dir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\PPAv2\srcpy\Testing Scripts\outputs'
    
    project_line = arcpy.GetParameterAsText(0) #r"P:\NPMRDS data\NPMRDS_GIS\scratch.gdb\TEMP_projects_for_npmrdsConflation"
    proj_name = arcpy.GetParameterAsText(1) 
    
    #NPMRDS data parameters -- consider putting all of these into a separate "config" python script
    speed_data = r"I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\npmrds_metrics_v4"
    ff_speed = "ff_speed"
    congest_speed = "havg_spd_worst4hrs"
    reliab_ampk = "lottr_ampk"
    
    fld_tmcdir = "direction"
    directions_tmc = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND"] #can modify this depending on what directions you want to consider
    
    #------------------no more user input below here, at least normally---------------
    flds_speed_data = [ff_speed, congest_speed, reliab_ampk] #'avspd_3p6p','congn_6a9a','congn_3p6p'
    
    #create temporar buffer layer, flat-tipped, around TMCs; will be used to split project lines
    temp_tmcbuff = "TEMP_tmcbuff_4projsplit2"
    buff_dist_ft = 60 #buffer distance, in feet, around the TMCs
    
    #select TMCs that intersect project lines
    fl_projects = "fl_projects"
    fld_proj_len = "proj_len"
    
    fl_speed_data = "fl_speed_data"
    fl_tmc_buff = "fl_tmc_buff"
    
    #mak
    arcpy.MakeFeatureLayer_management(project_line, fl_projects)
    arcpy.MakeFeatureLayer_management(speed_data, fl_speed_data)
    
    #add field that has project's length in it
    arcpy.AddField_management(project_line,fld_proj_len,"FLOAT")
    
    calc_add_len = "!shape.length@feet!"
    arcpy.CalculateField_management(project_line, fld_proj_len, calc_add_len, "PYTHON")
    
    #make flat-ended buffers around TMCs
    arcpy.Buffer_analysis(fl_speed_data, temp_tmcbuff, buff_dist_ft, "FULL", "FLAT")
    arcpy.MakeFeatureLayer_management(temp_tmcbuff, fl_tmc_buff)
    
    out_rows = []
    
    #in theory this should only be one project line, but want to keep flexible in case
    #we want batch version in future.
    for line in fl_projects:
        conflate_tmc2projline(fl_projects, line, proj_name, directions_tmc, fld_tmcdir, 
                                  fl_tmc_buff, flds_speed_data, out_rows)
        
    df_projdata = pd.DataFrame(out_rows)
    
    output_csv = os.path.join(output_dir,"projlin_conflation_test1.csv")
    arcpy.AddMessage("writing to {}...".format(output_csv))
    
    df_projdata.to_csv(output_csv, index = False)
    
    #NEXT STEP = join dataframe to project feature class, then look at map and do reasonableness check
    #also, how to quickly mention and bypass projects that don't intersect TMCs?
    #also, define a logical column order for the DF before doing join
    elapsed_time = round((time.time() - start_time)/60,1)
    print("Success! Time elapsed: {} minutes".format(elapsed_time))    
    
        
        
    

