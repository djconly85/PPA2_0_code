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

def get_poly_avg(input_poly_fc):
    accdata = acc.get_acc_data(input_poly_fc, p.accdata_fc, get_ej=False)
    collision_data = coll.get_collision_data(input_poly_fc, project_type, p.collisions_fc, adt)

    out_dict = {}
    for d in [accdata, collision_data]:
        out_dict.update(d)

    return out_dict

if __name__ == '__main__':
    start_time = time.time()
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    arcpy.OverwriteOutput = True

    # fc of community type polygons
    ctype_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\testproj_causeway_fwy'

    # fl_ctype = 'fl_ctype'
    # arcpy.MakeFeatureLayer_management(ctype_fc, fl_ctype)

    # loop through each feature in ctype fc, make a temp fc of it, run the calcs on that fc
    # get list of ctypes to search/loop through
    ctypes_list = []
    master_out_dict = {}
    with arcpy.da.SearchCursor(ctype_fc, [p.col_ctype]) as cur:
        for row in cur:
            ctypes_list.append(row[0])

    # for each ctype, select polygon feature from cytpes fc and export to temporary single feature fc
    for ctype in ctypes_list:
        temp_poly_fc = 'TEMP_ctype_fc'

        sql = "{} = '{}'".format(p.col_ctype, ctype)
        # arcpy.SelectLayerByAttribute_management(fl_ctype, "NEW_SELECTION", sql)
        arcpy.FeatureClassToFeatureClass_conversion(ctype_fc, 'memory', temp_poly_fc, sql)

        # on that temp fc, run the PPA tools, but SET BUFFER DISTANCES TO ZERO SOMEHOW
        # this will return a dict with all numbers for that ctype
        poly_dict = get_poly_avg(temp_poly_fc)
        master_out_dict.update(poly_dict)
        # for all keys in the output dict, add a tag to the key value to indicate community type
        # append it to a master dict

    print(master_out_dict)

    #outputs for calling functions


    complete_street_score = {'complete_street_score': -1} if project_type == p.ptype_fwy else \
        cs.complete_streets_idx(p.parcel_pt_fc, project_fc, project_speedlim, p.trn_svc_fc)
    truck_route_pct = {'pct_proj_STAATruckRoutes': 1} if project_type == p.ptype_fwy else \
        linex.get_line_overlap(project_fc, p.freight_route_fc, p.freight_route_fc) # all freeways are STAA truck routes
    ag_acres = luac.get_lutype_acreage(project_fc, p.parcel_poly_fc, p.lutype_ag)
    pct_adt_truck = {"pct_truck_aadt": -1} if project_type != p.ptype_fwy else truck_fwy.get_tmc_truck_data(project_fc, project_type)
    intersxn_data = intsxn.intersection_density(project_fc, p.intersections_base_fc)

    # outputs that use both base year and future year values--MIGHT WANT TO MAKE SEPARATE SCRIPT
    #lu_pt_data = lu_pt_buff.point_sum(p.parcel_pt_fc, val_fields, buff_dist, fc_project, case_field=None, case_excs_list=[])



    print(pd.DataFrame.from_dict(out_dict, orient='index'))


