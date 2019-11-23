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
import time

import arcpy
import pandas as pd

import ppa_input_params as p
import accessibility_calcs as acc
import collisions as coll
import complete_street_score as cs
import get_line_overlap as linex
import get_lutype_acres as luac
import get_truck_data_fwy as truck_fwy
import intersection_density as intsxn
import landuse_buff_calcs as lu_pt_buff
import link_occup_data as link_occ
import mix_index_for_project as mixidx
import npmrds_data_conflation as npmrds

import transit_svc_measure as trn_svc

if __name__ == '__main__':
    start_time = time.time()
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    arcpy.OverwriteOutput = True

    #project data
    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\testproj_causeway_fwy'
    project_type = p.ptype_fwy
    adt = 17000
    project_speedlim = 30

    #outputs for calling functions
    accdata = acc.get_acc_data(project_fc, p.accdata_fc, get_ej=False)
    collision_data = coll.get_collision_data(project_fc, project_type, p.collisions_fc, adt)
    complete_street_score = {'complete_street_score': -1} if project_type == p.ptype_fwy else \
        cs.complete_streets_idx(p.parcel_pt_fc, project_fc, project_speedlim, p.trn_svc_fc)
    truck_route_pct = {'pct_proj_STAATruckRoutes': 1} if project_type == p.ptype_fwy else \
        linex.get_line_overlap(project_fc, p.freight_route_fc, p.freight_route_fc) # all freeways are STAA truck routes
    ag_acres = luac.get_lutype_acreage(project_fc, p.parcel_poly_fc, p.lutype_ag)
    pct_adt_truck = {"pct_truck_aadt": -1} if project_type != p.ptype_fwy else truck_fwy.get_tmc_truck_data(project_fc, project_type)
    intersxn_data = intsxn.intersection_density(project_fc, p.intersections_base_fc)

    # outputs that use both base year and future year values--MIGHT WANT TO MAKE SEPARATE SCRIPT
    #lu_pt_data = lu_pt_buff.point_sum(p.parcel_pt_fc, val_fields, buff_dist, fc_project, case_field=None, case_excs_list=[])

    out_dict = {}
    for d in [accdata, collision_data, complete_street_score, truck_route_pct, pct_adt_truck, intersxn_data]:
        out_dict.update(d)

    print(pd.DataFrame.from_dict(out_dict, orient = 'index'))

