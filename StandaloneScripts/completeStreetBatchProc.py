# --------------------------------
# Name: complete_street_score.py
# Purpose: Calculate complete street index (CSI) for project, which is proxy 
#       to describe how beneficial complete streets treatments would be for the project segment.
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import datetime as dt

import arcpy

# import ppa_input_params as params
import landuse_buff_calcs as lubuff
import transit_svc_measure as ts

    
def complete_streets_idx(fc_pclpt, fc_project, project_type, posted_speedlim, transit_event_fc):
    '''Calculate complete street index (CSI) for project
        CSI = (students/acre + daily transit vehicle stops/acre + BY jobs/acre + BY du/acre) * (1-(posted speed limit - threshold speed limit)*speed penalty factor)
        '''
    col_area_ac
    col_k12_enr
    col_emptot
    col_du
    cs_buffdist
    cs_threshold_speed
    cs_spd_pen_fac
    
    
    # don't give complete street score for freeway projects or if sponsor didn't enter speed limit
    if project_type == params.ptype_fwy or posted_speedlim <= 1: 
        csi = -1
    else:
        # arcpy.AddMessage("Calculating complete street score...")
    
        # get transit service density around project
        tran_stops_dict = ts.transit_svc_density(fc_project, transit_event_fc, project_type)
        transit_svc_density = list(tran_stops_dict.values())[0]
    
        lu_fac_cols = [params.col_area_ac, params.col_k12_enr, params.col_emptot, params.col_du]
        lu_vals_cols = [params.col_k12_enr, params.col_emptot, params.col_du]
    
        # get sums of the lu_fac_cols within project buffer area
        lu_vals_dict = lubuff.point_sum(fc_pclpt, fc_project, project_type, lu_fac_cols, params.cs_buffdist)
    
        #dens_score = (student_dens + trn_svc_dens + job_dens + du_dens)
        dens_score = sum([lu_vals_dict[i] / lu_vals_dict[params.col_area_ac] for i in lu_vals_cols]) + transit_svc_density
    
        csi = dens_score * (1 - (posted_speedlim - params.cs_threshold_speed) * params.cs_spd_pen_fac)

    out_dict = {'complete_street_score': csi}
    
    return out_dict

def make_fc_with_csi(network_fc, transit_event_fc, fc_pclpt, project_type):
    
    fld_geom = "SHAPE@"
    fld_strtname = "FULLSTREET"
    fld_spd = "SPEED"
    fld_len = "SHAPE@LENGTH"
    fld_csi = "CompltStreetIdx"
    
    fields = [fld_geom, fld_strtname, fld_spd, fld_len]
    
    time_sufx = str(dt.datetime.now().strftime('%m%d%Y%H%M'))
    output_fc = "CompleteStreetMap{}".format(time_sufx)
    
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, output_fc,spatial_reference = 2226)
    
    arcpy.AddField_management(output_fc, fld_strtname, "TEXT")
    arcpy.AddField_management(output_fc, fld_spd, "SHORT")
    arcpy.AddField_management(output_fc, fld_csi, "FLOAT")
    
    inscur = arcpy.da.InsertCursor(output_fc, [fld_geom, fld_strtname, fld_spd, fld_csi])
    
    print("inserting rows...")
    with arcpy.da.SearchCursor(network_fc, fields) as cur:
        for row in cur:
            geom = row[0]
            stname = row[1]
            speedlim = row[2]
            # seglen = row[3]
            
            csi_dict = complete_streets_idx(fc_pclpt, geom, project_type, speedlim, transit_event_fc)
            csi = csi_dict['complete_street_score']
            
            ins_row = [geom, stname, speedlim, csi]
            inscur.insertRow(ins_row)
        


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    # input fc of parcel data--must be points!
    in_pcl_pt_fc = "parcel_data_2016_11062019_pts"
    value_fields = [params.col_area_ac, params.col_k12_enr, params.col_emptot, params.col_du]
    posted_speedlimit = 30 # mph
    ptype = 'Arterial'

    # input line project for basing spatial selection
    network_fc = 'ArterialCollector_2019'
    trnstops_fc = 'transit_stoplocn_w_eventcount_2016'


    # output_dict = complete_streets_idx(in_pcl_pt_fc, project_fc, ptype, posted_speedlimit, trnstops_fc)
    print(output_dict)

