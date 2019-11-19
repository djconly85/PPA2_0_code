# --------------------------------
# Name: complete_street_score.py
# Purpose: Calculate complete street index (CSI) for project
#           CSI = (students/acre + daily transit vehicle stops/acre + BY jobs/acre + BY du/acre)
#                  * (1-(posted speed limit - threshold speed limit)*speed penalty factor)
#
#
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: 3.x
# --------------------------------
import arcpy

import ppa_input_params as p
import landuse_buff_calcs as luc
import transit_svc_measure as ts


def complete_streets_idx(fc_pclpt, fc_project, posted_speedlim, trn_svc_dens):

    lu_facs = [p.col_area_ac, p.col_k12_enr, p.col_emptot, p.col_du]
    lu_vals = [p.col_k12_enr, p.col_emptot, p.col_du]
    lu_vals_dict = luc.point_sum(fc_pclpt, lu_facs, p.cs_buffdist, fc_project)

    #dens_score = (student_dens + trn_svc_dens + job_dens + du_dens)
    dens_score = sum([lu_vals_dict[i] / lu_vals_dict[p.col_area_ac] for i in lu_vals]) + trn_svc_dens

    csi = dens_score * (1 - (posted_speedlim - p.cs_threshold_speed) * p.cs_spd_pen_fac)

    out_dict = {'complete_strt_idx': csi}
    return out_dict

if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    # input fc of parcel data--must be points!
    in_pcl_pt_fc = "parcel_data_2016_11062019_pts"
    value_fields = [p.col_area_ac, p.col_k12_enr, p.col_emptot, p.col_du]
    posted_speedlimit = 30 # mph

    # input line project for basing spatial selection
    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    trnstops_fc = 'transit_stoplocn_w_eventcount_2016'

    # get number of transit stops
    tran_stops_dict = ts.transit_svc_density(project_fc, trnstops_fc)
    transit_svc_density = list(tran_stops_dict.values())[0]

    output_dict = complete_streets_idx(in_pcl_pt_fc, project_fc, posted_speedlimit, transit_svc_density)
    print(output_dict)