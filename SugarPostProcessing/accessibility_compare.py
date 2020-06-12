# Esri start of added imports
import sys, os
# Esri end of added imports

# Esri start of added variables
g_ESRI_variable_1 = 'fl_accdata'
g_ESRI_variable_2 = 'fl_project'
# Esri end of added variables

# --------------------------------
# Name: accessibility_compare.py
# Purpose: does before-after comparison of accessibility measures
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import time
import arcpy
import pandas as pd
import pdb

import sugarcomp_params as params
import sugarcomp_utils as utils

class accessCompare(object):
    def __init__(self, fc_project, fc_accdata_pre, fc_accdata_post, project_type, get_ej=False):
        self.fc_project = fc_project
        self.project_type = project_type
        self.get_ej = get_ej
        self.fc_accdata_pre = fc_accdata_pre
        self.fc_accdata_post = fc_accdata_post
        self.col_geoid = "blockid10"
        
        
    def get_acc_data(self, fc_accdata):
        '''Calculate average accessibility to selected destination types for all
        polygons that either intersect the project line or are within a community type polygon.
        Average accessibility is weighted by each polygon's population.'''
        
        arcpy.AddMessage("Calculating accessibility metrics...")
        
        sufx = int(time.clock()) + 1
        fl_accdata = os.path.join(arcpy.env.scratchGDB,'fl_accdata{}'.format(sufx))
        fl_project = g_ESRI_variable_2
    
        if arcpy.Exists(fl_project): arcpy.Delete_management(fl_project)
        arcpy.MakeFeatureLayer_management(self.fc_project, fl_project)
    
        if arcpy.Exists(fl_accdata): arcpy.Delete_management(fl_accdata)
        arcpy.MakeFeatureLayer_management(fc_accdata, fl_accdata)
    
        # select polygons that intersect with the project line
        searchdist = 0 if self.project_type == params.ptype_area_agg else params.bg_search_dist
        arcpy.SelectLayerByLocation_management(fl_accdata, "INTERSECT", fl_project, searchdist, "NEW_SELECTION")
    
        # read accessibility data from selected polygons into a dataframe
        accdata_fields_all = [self.col_geoid, params.col_acc_ej_ind, params.col_pop] + params.acc_cols_ej
        fl_accdata_fields = [f.name for f in arcpy.ListFields(fl_accdata)]
        accdata_fields_used = [f for f in accdata_fields_all if f in fl_accdata_fields]
        
        accdata_df = utils.esri_object_to_df(fl_accdata, accdata_fields_used)
    
        # get pop-weighted accessibility values for all accessibility columns
    
        out_dict = {}
        if self.get_ej: # if for enviro justice population, weight by population for EJ polygons only.
            for col in params.acc_cols_ej:
                if col in accdata_df.columns:
                    col_wtd = "{}_wtd".format(col)
                    col_ej_pop = "{}_EJ".format(params.col_pop)
                    accdata_df[col_wtd] = accdata_df[col] * accdata_df[params.col_pop] * accdata_df[params.col_acc_ej_ind]
                    accdata_df[col_ej_pop] = accdata_df[params.col_pop] * accdata_df[params.col_acc_ej_ind]
                    
                    tot_ej_pop = accdata_df[col_ej_pop].sum()
                    
                    out_wtd_acc = accdata_df[col_wtd].sum() / tot_ej_pop if tot_ej_pop > 0 else 0
                    col_out_ej = "{}_EJ".format(col)
                    out_dict[col_out_ej] = out_wtd_acc
                else:
                    continue
        else:
            for col in params.acc_cols:
                if col in accdata_df.columns:
                    col_wtd = "{}_wtd".format(col)
                    accdata_df[col_wtd] = accdata_df[col] * accdata_df[params.col_pop]
                    out_wtd_acc = accdata_df[col_wtd].sum() / accdata_df[params.col_pop].sum()
                    out_dict[col] = out_wtd_acc
                else:
                    continue
    
        colname = 'PreProject' if fc_accdata == self.fc_accdata_pre else 'PostProject' 
    
        out_df = pd.DataFrame(pd.Series(out_dict, index=out_dict.keys())) \
                .rename(columns={0:colname})
        
        # pdb.set_trace()
        
        return out_df
    
    
    def make_compare_table(self):
        print("running for base scenario...")
        base_df = self.get_acc_data(self.fc_accdata_pre)
        
        for scenario in [self.fc_accdata_post]:  #written as list to potentially make expandable in future (e.g. more than just "pre/post project")
            print("running for {}".format(scenario))
            if scenario:    
                df2 = self.get_acc_data(scenario)
                base_df = base_df.merge(df2, how='left', left_index=True, right_index=True)
            else:
                continue
        
        return base_df
            


if __name__ == '__main__':
    '''This process will be for Sugar post-processing. It may need to be in
    a separate script, or the input accessibility FC will need to have the column names
    changed to match those specified in the parameters file.'''
    
    reports_dir = r"I:\Projects\Darren\PPA_V2_GIS\Sugar\Project Reports"
    
    fc_project_line = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\testProjSycamoreBikeBrg'  # arcpy.GetParameterAsText(0)
    fc_accessibility_data = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\Sugar_access_data_latest' # os.path.join(params.fgdb, params.accdata_fc)  # arcpy.GetParameterAsText(1)
    str_project_type = params.ptype_arterial  # arcpy.GetParameterAsText(2)
    
    fc_accessibility_data_post = r"TestSycamoreBikeBrg\SycamoreProj_NonTransit_w_decay\SycamoreWProjEdu_NonTransit.gdb\accessSycamoreWProjEdu_NonTransit"
    fc_accessibility_data_post = os.path.join(reports_dir, fc_accessibility_data_post)
    
    out_obj = accessCompare(fc_project_line, fc_accessibility_data, fc_accessibility_data_post, str_project_type, get_ej=False)
    out_df = out_obj.make_compare_table()
    print(out_df)
    
