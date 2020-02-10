# --------------------------------
# Name: PPA2_masterTest.py
# Purpose: testing master script to call can combine all PPA modules
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import datetime as dt
import os

import arcpy
import pandas as pd

import ppa_input_params as params
import accessibility_calcs as acc
import collisions as coll
import complete_street_score as cs
import get_buff_netmiles as bnmi
import get_line_overlap as linex
import get_lutype_acres as luac
import get_truck_data_fwy as truck_fwy
import intersection_density as intsxn
import landuse_buff_calcs as lu_pt_buff
import link_occup_data as link_occ
import mix_index_for_project as mixidx
import npmrds_data_conflation as npmrds
import transit_svc_measure as trnsvc
import urbanization_metrics as urbn
import ppa_utils as utils


# Pandas orient values need to be up here so that publishing process does not assign wrong variable.
# must be global variable
df_orient_val = 'index'


def get_proj_ctype(in_project_fc, commtypes_fc):
    '''Get project community type, based on which community type has most spatial overlap with project'''
    
    temp_intersect_fc = r'memory/temp_intersect_fc'
    arcpy.Intersect_analysis([in_project_fc, commtypes_fc], temp_intersect_fc, "ALL", 
                             0, "LINE")
    
    len_field = 'SHAPE@LENGTH'
    fields = ['OBJECTID', len_field, params.col_ctype]
    df_intersect = utils.esri_object_to_df(temp_intersect_fc, fields)
    
    proj_ctype = list(df_intersect[df_intersect[len_field] == max(df_intersect[len_field])][ params.col_ctype])[0]
    
    return proj_ctype

def get_proj_len(in_project_fc):
    tot_len = 0
    
    with arcpy.da.SearchCursor(in_project_fc, "SHAPE@LENGTH") as cur:
        for row in cur:
            tot_len += row[0]
            
    len_mi = tot_len / params.ft2mile
    return len_mi

def get_singleyr_data(fc_project, projtyp, adt, posted_speedlim, out_dict={}):
    
    pcl_pt_fc = params.parcel_pt_fc_yr(2016)
    pcl_poly_fc = params.parcel_poly_fc_yr(2016)
    
    accdata = acc.get_acc_data(fc_project, params.accdata_fc, projtyp, get_ej=False)
    
    collision_data = coll.get_collision_data(fc_project, projtyp, params.collisions_fc, adt)

    complete_street_score = {'complete_street_score': -1} if projtyp == params.ptype_fwy else \
        cs.complete_streets_idx(pcl_pt_fc, fc_project, projtyp, posted_speedlim, params.trn_svc_fc)
        
    truck_route_pct = {'pct_proj_STAATruckRoutes': 1} if projtyp == params.ptype_fwy else \
        linex.get_line_overlap(fc_project, params.freight_route_fc, params.freight_route_fc) # all freeways are STAA truck routes
        
    ag_acres = luac.get_lutype_acreage(fc_project, projtyp, pcl_poly_fc, params.lutype_ag)
    
    pct_adt_truck = {"pct_truck_aadt": -1} if projtyp != params.ptype_fwy else truck_fwy.get_tmc_truck_data(fc_project, projtyp)
    
    intersxn_data = intsxn.intersection_density(fc_project, params.intersections_base_fc, projtyp)
    
    npmrds_data = npmrds.get_npmrds_data(fc_project, projtyp)
    
    transit_data = trnsvc.transit_svc_density(fc_project, params.trn_svc_fc, projtyp)
    
    bikeway_data = bnmi.get_bikeway_mileage_share(fc_project, params.ptype_sgr)
    
    infill_status = urbn.projarea_infill_status(fc_project, params.comm_types_fc)
    
    
    # total job + du density (base year only, for state-of-good-repair proj eval only)
    job_du_dens = lu_pt_buff.point_sum_density(pcl_pt_fc, fc_project, projtyp, 
                                               [ params.col_emptot, params.col_du], params.ilut_sum_buffdist)
    comb_du_dens = sum(list(job_du_dens.values()))
    job_du_dens['job_du_perNetAcre'] = comb_du_dens

    # get EJ data
    ej_data = lu_pt_buff.point_sum(pcl_pt_fc, fc_project, projtyp, [ params.col_pop_ilut],
                                            params.ilut_sum_buffdist, params.col_ej_ind, case_excs_list=[])
    
    ej_flag_dict = {0: "Pop_NonEJArea", 1: "Pop_EJArea"}  # rename keys from 0/1 to more human-readable names
    ej_data = utils.rename_dict_keys(ej_data, ej_flag_dict)
    ej_data["Pct_PopEJArea"] = ej_data["Pop_EJArea"] / sum(list(ej_data.values()))
    
    accdata_ej = acc.get_acc_data(fc_project, params.accdata_fc, projtyp, get_ej=True)  # EJ accessibility data
    ej_data.update(accdata_ej)
    

    # for base dict, add items that only have a base year value (no future year values)
    for d in [accdata, collision_data, complete_street_score, truck_route_pct, pct_adt_truck, ag_acres, intersxn_data,
              npmrds_data, transit_data, bikeway_data, infill_status, job_du_dens, ej_data]:
        out_dict_base.update(d)

    outdf = pd.DataFrame.from_dict(out_dict_base, orient=df_orient_val)
    
    return outdf

def get_multiyear_data(project_fc, project_type, base_df, analysis_year):
    
    ilut_val_fields = [ params.col_pop_ilut, params.col_du, params.col_emptot, params.col_k12_enr, params.col_empind, params.col_persntrip_res] \
                  + params.ilut_ptrip_mode_fields    

    fc_pcl_pt = params.parcel_pt_fc_yr(year)
    fc_pcl_poly = params.parcel_poly_fc_yr(year)
    fc_modelhwylinks = params.model_links_fc(year)

    year_dict = {}
    # get data on pop, job, k12 totals
    # point_sum(fc_pclpt, fc_project, project_type, val_fields, buffdist, case_field=None, case_excs_list=[])
    ilut_buff_vals = lu_pt_buff.point_sum(fc_pcl_pt, project_fc, project_type, ilut_val_fields,
                                          params.ilut_sum_buffdist, case_field=None, case_excs_list=[])

    ilut_indjob_share = {"{}_jobshare".format( params.col_empind): ilut_buff_vals[ params.col_empind] / ilut_buff_vals[ params.col_emptot]}
    ilut_buff_vals.update(ilut_indjob_share)

    ilut_mode_split = {"{}_share".format(modetrp): ilut_buff_vals[modetrp] / ilut_buff_vals[ params.col_persntrip_res]
                       for modetrp in params.ilut_ptrip_mode_fields}
    ilut_buff_vals.update(ilut_mode_split)

    # cleanup to remove non-percentage mode split values, if we want to keep output CSV from getting too long.
    # for trip_numcol in params.ilut_ptrip_mode_fields: del ilut_buff_vals[trip_numcol]

    # job + du total
    job_du_tot = {"SUM_JOB_DU": ilut_buff_vals[ params.col_du] + ilut_buff_vals[ params.col_emptot]}

    # model-based vehicle occupancy
    veh_occ_data = link_occ.get_linkoccup_data(project_fc, project_type, fc_modelhwylinks)

    # land use diversity index
    mix_index_data = mixidx.get_mix_idx(fc_pcl_pt, project_fc, project_type)

    # housing type mix
    housing_mix_data = lu_pt_buff.point_sum(fc_pcl_pt, project_fc, project_type, [params.col_du], params.du_mix_buffdist,
                                            params.col_housing_type, case_excs_list=['Other'])

    # acres of "natural resources" (land use type = forest or agriculture)
    nat_resources_data = urbn.nat_resources(project_fc, project_type, fc_pcl_poly, year)

    # combine into dict
    for d in [ilut_buff_vals, job_du_tot, veh_occ_data, mix_index_data, housing_mix_data, nat_resources_data]:
        year_dict.update(d) 

    # make dict into dataframe
    df_year_out = pd.DataFrame.from_dict(year_dict, orient=df_orient_val)
    
    return df_year_out


    
if __name__ == '__main__':
    # =====================================USER/TOOLBOX INPUTS===============================================
    # project data
    project_fc = arcpy.GetParameterAsText(0) # r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\test_project_SEConnector'
    proj_name = arcpy.GetParameterAsText(1)  # os.path.basename(project_fc) # os.path.basename(project_fc)
    proj_juris = arcpy.GetParameterAsText(2) # project jurisdiction
    project_type = arcpy.GetParameterAsText(3)  # params.ptype_arterial  # params.ptype_fwy, params.ptype_arterial, or params.ptype_sgr
    performance_outcomes =  arcpy.GetParameterAsText(4) # ['Reduce VMT', 'Reduce Congestion', 'Encourage Non-SOV Travel']
    adt = int(arcpy.GetParameterAsText(5)) # avg daily traffic; user-entered value
    project_speedlim = int(arcpy.GetParameterAsText(6)) #posted speed limit; user-entered value
    pci = int(arcpy.GetParameterAsText(7))  # pavement condition index, will be user-entered value

    # =======================BEGIN SCRIPT==============================================================
    start_time = dt.datetime.now()
    
    arcpy.OverwriteOutput = True
    arcpy.env.workspace = params.fgdb
    
    analysis_years = [2016, 2040]  # which years will be used.
    time_sufx = str(dt.datetime.now().strftime('%m%d%Y%H%M'))
    
    template_xl = os.path.join(params.template_dir, params.type_template_dict[project_type])
    
    output_xl = 'PPA_{}{}.xlsx'.format(os.path.basename(proj_name), time_sufx)

    proj_len_mi = get_proj_len(project_fc)
    
    project_ctype = get_proj_ctype(project_fc, params.comm_types_fc)
    
    out_dict_base = {"project_name": proj_name, "jurisdiction": proj_juris, "project_type": project_type, 'project_aadt': adt, 'project_pci': pci,
                'project_speedlim': project_speedlim, "project_cline_len": proj_len_mi, "project_communtype": project_ctype}

    # metrics that only have base year value ------------------------------------
    outdf_base = get_singleyr_data(project_fc, project_type, adt, project_speedlim, out_dict_base)

    # ---------------------------------------------------------------------------------------------------------
    # outputs that use both base year and future year values
    for year in analysis_years:
        df_year = get_multiyear_data(project_fc, project_type, outdf_base, year)
        # if it's base year, then append values to bottom of outdf_base,
        # if it's future year, then left-join the values to the outdf.
        # table has metrics as rows; years as columns (and will also append     
        if year == min(analysis_years):
            out_df = outdf_base.rename(columns={0: 'projval_{}'.format(year)})
            df_year = df_year.rename(columns={0: 'projval_{}'.format(year)})
            out_df = out_df.append(df_year)
        else:
            df_year = df_year.rename(columns={0: 'projval_{}'.format(year)})
            out_df = out_df.join(df_year)
    
    out_df = utils.join_xl_import_template(template_xl, params.xlsx_import_sheet, out_df)

    # get community type and regional level data
    df_aggvals = pd.read_csv( params.aggvals_csv, index_col = 'Unnamed: 0')
    col_aggvals_year = 'year'
    region_headname = 'REGION'
    cols_ctype_reg = [project_ctype, region_headname]
    aggval_headers = {col: 'CommunityType' for col in df_aggvals.columns if col != region_headname}
    
    for year in analysis_years:
        df_agg_yr = df_aggvals[df_aggvals[col_aggvals_year] == year]  # filter to specific year
        df_agg_yr = df_agg_yr[cols_ctype_reg]  # only include community types for community types that project is in
        df_agg_yr = df_agg_yr.rename(columns={project_ctype: 'CommunityType'})
        df_agg_yr = df_agg_yr.rename(columns={col:'{}_{}'.format(col, year) for col in list(df_agg_yr.columns)})
        
        out_df = out_df.join(df_agg_yr)
        
    arcpy.AddMessage("Writing to XLSX and making PDF report...")
    
    # format performance outcomes into readable list for rest of script--if input was through argis toolbox
    performance_outcomes = [outcome.strip("'") for outcome in performance_outcomes.split(';')]
    
    
    if project_type == params.pytpe_commdesign:
        # for community design report, user does not choose which performance outcomes to include. all are included.
        performance_outcome_sheets = params.perf_outcomes_commdesign
    else:
        #convert user-entered perf outcomes to the corresponding excel sheet names
        performance_outcome_sheets = [ params.perf_outcomes_dict[outcome] for outcome in performance_outcomes]
    
    
    out_report = utils.Publish(out_df, template_xl, params.xlsx_import_sheet, output_xl, performance_outcome_sheets, 
                                None, proj_name) #params.map_list_csv
    
    outputs = out_report.make_pdf() # successful run returns tuple ("ok", output PDF file, output excel file)
    # if fail, returns tuple ("fail", <error message>)
        
    if outputs[0] == params.msg_ok:
        out_pdf = outputs[1]
        out_excel = outputs[2]

        arcpy.SetParameterAsText(8, out_pdf)
        arcpy.SetParameterAsText(9, out_excel)
        
        end_time = dt.datetime.now()
        delta = end_time - start_time
        mins_and_secs = divmod(delta.seconds, 60)
        arcpy.AddMessage("Success! Tool completed in {} minutes, {} seconds.".format(mins_and_secs[0], mins_and_secs[1]))
        
    else: # if making PDF fails, still return the Excel file.
        out_excel = outputs[1]
        
        arcpy.AddMessage(outputs[0]) #print error message if error.
        arcpy.SetParameterAsText(8, "NOT_AVAILABLE")
        arcpy.SetParameterAsText(9, out_excel)

    
    


