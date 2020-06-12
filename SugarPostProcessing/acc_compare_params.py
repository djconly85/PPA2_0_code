# Esri start of added imports
import sys, os, arcpy
# Esri end of added imports

# Esri start of added variables
g_ESRI_variable_1 = '\\\\arcserver-svr\\D\\PPA_v2_SVR'
# Esri end of added variables

"""
Name: ppa_input_params.py
Purpose: Stores all input parameter values for SACOG Project Performance Assessment Tool v2.0 Sugar post-processor
        
          
Author: Darren Conly
Last Updated: 3/2020
Updated by: <name>
Copyright:   (c) SACOG
Python Version: 3.x
"""

# ========================================INPUT DATA LAYERS===================================================== 
server_folder = g_ESRI_variable_1

fgdb = os.path.join(server_folder, r"PPA2_GIS_SVR\owner_PPA.sde")  # os.path.join(server_folder, gdb_name)

# input feature classes
accdata_fc = 'Sugar_access_data_latest' # sugar accessibility polygon data

proj_line_template_fc = 'Project_Line_Template' # has symbology that the project line will use.
all_projects_fc = "All_PPA_Projects2020"


# project type
ptype_fwy = 'Freeway'
ptype_arterial = 'Arterial or Transit Expansion'
ptype_sgr = 'Complete Street or State of Good Repair'
ptype_commdesign = "Community Design"
ptype_area_agg = 'AreaAvg' # e.g., regional average, community type avg


# ===================================OUTPUT TEMPLATE DATA=========================================================


msg_ok = "C_OK" # message that returns if utils script executes correctly.
msg_fail = "Run_Failed"

# ===================================CONVERSION FACTORS=========================================================
ft2acre = 43560 # convert square feet to acres
ft2mile = 5280
# ===================================ACCESSIBILITY PARAMETERS=========================================================

# Accessibility columns
col_geoid = "bgid"
col_acc_ej_ind = "PPA_EJ2018"
col_pop = "population"

col_walk_alljob = 'WALKDESTSalljob'
col_bike_alljob = 'BIKEDESTSalljob'
col_drive_alljob = 'AUTODESTSalljob'
col_transit_alljob = 'TRANDESTSalljob'
col_walk_lowincjob = 'WALKDESTSlowjobs'
col_bike_lowincjob = 'BIKEDESTSlowjobs'
col_drive_lowincjob = 'AUTODESTSlowjobs'
col_transit_lowincjob = 'TRANDESTSlowjob'
col_walk_edu = 'WALKDESTSedu'
col_bike_edu = 'BIKEDESTSedu'
col_drive_edu = 'AUTODESTSedu'
col_transit_edu = 'TRANDESTSedu'
col_walk_poi = 'WALKDESTSpoi2'
col_bike_poi = 'BIKEDESTSpoi2'
col_drive_poi = 'AUTODESTSpoi2'
col_transit_poi = 'TRANDESTSpoi2'

acc_cols = [col_walk_alljob, col_bike_alljob, col_drive_alljob, col_transit_alljob, col_walk_edu, col_bike_edu,
            col_drive_edu, col_transit_edu, col_walk_poi, col_bike_poi, col_drive_poi, col_transit_poi]

acc_cols_ej = [col_walk_alljob, col_bike_alljob, col_drive_alljob, col_transit_alljob, col_walk_lowincjob,
               col_bike_lowincjob, col_drive_lowincjob, col_transit_lowincjob, col_walk_edu, col_bike_edu,
               col_drive_edu, col_transit_edu, col_walk_poi, col_bike_poi, col_drive_poi, col_transit_poi]



bg_search_dist = 300 # feet away from project line that you'll tag block groups in

#===========================================================




