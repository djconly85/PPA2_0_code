# ========================================INPUT DATA LAYERS=====================================================
fgdb = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb' #for now, is reference only. individual scripts explicitly indicate workspace and file locations

region_fc = 'sacog_region'
fc_speed_data = 'npmrds_metrics_v7'  # r"I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\npmrds_metrics_v6_wtruck" #npmrds speed data
accdata_fc = 'Sugar_access_data_latest' # sugar accessibility polygon data
collisions_fc = 'Collisions2014to2018fwytag' # collision point data
parcel_pt_fc = "parcel_data_pts_2016" # parcel point data
parcel_poly_fc = 'parcels_w_urbanization'
trn_svc_fc = 'transit_stoplocn_w_eventcount_2016' # transit stop event data; point file
freight_route_fc = 'STAATruckRoutes' # STAA truck route lines
intersections_base_fc = 'intersections_2016'
comm_types_fc = 'comm_type_jurspecific_latest'
model_links_fc = 'model_links_2016'
reg_centerline_fc = 'RegionalCenterline_2019'
reg_bikeway_fc = 'BikeRte_C1_C2_C4_2017'

# project type
ptype_fwy = 'Freeway'
ptype_arterial = 'Arterial'
ptype_sgr = 'Complete Street or State of Good Repair'
ptype_area_agg = 'AreaAvg' # e.g., regional average, community type avg

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

# ===================================PROBE-BASED SPEED DATA (E.G. NPMRDS) PARAMETERS================================

# speed data attributes
col_ff_speed = "ff_speed"
col_congest_speed = "havg_spd_worst4hrs"
col_reliab_ampk = "lottr_ampk"
col_reliab_md = "lottr_midday"
col_reliab_pmpk = "lottr_pmpk"
col_reliab_wknd = "lottr_wknd"
col_tmcdir = "direction_signd"
col_roadtype = "f_system"  # indicates if road is freeway or not, so that data from freeways doesn't affect data on surface streets, and vice-versa
col_truckpct = "Trk_Veh_Pc"

flds_speed_data = [col_ff_speed, col_congest_speed, col_reliab_ampk, col_reliab_md, col_reliab_pmpk,
                   col_reliab_wknd]

flds_truck_data = [col_truckpct]

roadtypes_fwy = (1, 2)  # road type values corresponding to freeways
directions_tmc = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND"]

tmc_select_srchdist = 300 # units in feet. will select TMCs within this distance of project line for analysis.
tmc_buff_dist_ft = 90  # buffer distance, in feet, around the TMCs

# ===================================MODEL-BASED LAND USE  PARAMETERS==============================================

# parameters for mix index
import pandas as pd

# input columns for land use mix calculation--MUST MATCH COLNAMES IN mix_idx_params_csv
col_parcelid = 'PARCELID'
col_hh = 'HH_hh'
col_emptot = 'EMPTOT'
col_empfood = 'EMPFOOD'
col_empret = 'EMPRET'
col_empsvc = 'EMPSVC'
col_k12_enr = 'ENR_K12'

mix_index_buffdist = 5280 #feet
du_mix_buffdist = 5280 #feet
ilut_sum_buffdist = 2640 # feet

# park acreage info,
col_area_ac = 'GISAc'
col_lutype = 'LUTYPE'
lutype_parks = 'Park and/or Open Space'
col_parkac = 'PARK_AC'  # will be calc'd as GISAc if LUTYPE = park/open space LUTYPE
park_calc_dict = {'area_field': col_area_ac,
                  'lutype_field': col_lutype,
                  'park_lutype': lutype_parks,
                  'park_acres_field': col_parkac}

lutype_ag = 'Agriculture' #from LUTYPE colume for ILUT table

mix_idx_col = 'mix_index_1mi'

# by default, bal_ratio_per_hh = ratio of that land use factor per HH at the regional level, and represents "ideal" ratio
mix_calc_cols = ['lu_fac', 'bal_ratio_per_hh', 'weight']
mix_calc_vals = [[col_k12_enr, 0.392079056, 0.2],
             [col_empret, 0.148253453, 0.4],
             [col_emptot, 1.085980023, 0.05],
             [col_empsvc, 0.133409274, 0.1],
             [col_empfood, 0.097047321, 0.2],
             [col_parkac, 0.269931832, 0.05]
             ]

params_df = pd.DataFrame(mix_calc_vals, columns = mix_calc_cols) \
    .set_index(mix_calc_cols[0])

# ---------parameters for summary land use data ---------------------

# other ILUT columns used
col_pop_ilut = 'POP_TOT'
col_ej_ind = "EJ_2018"
col_empind = 'EMPIND'
col_persntrip_res = 'PT_TOT_RES'
col_sovtrip_res = 'SOV_TOT_RES'
col_hovtrip_res = 'HOV_TOT_RES'
col_trntrip_res = 'TRN_TOT_RES'
col_biketrip_res = 'BIK_TOT_RES'
col_walktrip_res = 'WLK_TOT_RES'
col_du = 'DU_TOT'



# ===================================MODEL NETWORK PARAMETERS==============================================

modlink_searchdist = 700 # in feet, might have projection-related issues in online tool--how was this resolved in PPA1?

# model freeway capclasses: general purp lanes, aux lanes, HOV lanes, HOV connectors, on-off ramps, HOV ramps, freeway-freeway connector ramps
col_capclass = "CAPCLASS"

capclasses_fwy = (1, 8, 51, 56) # freeway gen purpose, aux, and HOV lanes
capclasses_ramps = (6, 16, 18, 26, 36, 46) # onramps, offramps, freeway-freeway connectors, HOV onramp meter byp lanes, metered onramp lanes
capclass_arterials = (2, 3, 4, 5, 12)
capclasses_nonroad = (7, 62, 63, 99)

col_lanemi = 'LANEMI'
col_distance = 'DISTANCE'
col_dayvmt = 'DAYVMT'
col_daycvmt = 'DAYCVMT'
col_tranvol = 'TOT_TRNVOL'
col_dayvehvol = 'DYV'
col_sovvol = 'DYV_DA'
col_hov2vol = 'DYV_SD2'
col_hov3vol = 'DYV_SD3'

# occupancy factors for shared vehicles
fac_hov2 = 2 # HOV2 = 2 people per veh
fac_hov3 = 1/0.3 # inverse of 0.3, which is factor for converting HOV3+ person trips into vehicle trips


# ============================COLLISION DATA PARAMETERS===========================
col_fwytag = "fwy_yn"
col_nkilled = "NUMBER_KILLED"
col_bike_ind = 'BICYCLE_ACCIDENT'
col_ped_ind = 'PEDESTRIAN_ACCIDENT'

ind_val_true = 'Y'

colln_searchdist = 75 # in feet, might have projection-related issues in online tool-how was this resolved in PPA1?
years_of_collndata = 5

# ============================TRANSIT SERVICE DENSITY PARAMETERS===========================
trn_buff_dist = 1320 # feet, search distance for transit stops from project line
col_transit_events = "COUNT_trip_id" #if transit feature class is point file dissolved by stop location, this
                                    #col is number of times per day that transit vehicle served each stop



# ============================COMPLETE STREETS INDEX PARAMETERS===========================

# CSI = (students/acre + daily transit vehicle stops/acre + BY jobs/acre + BY du/acre)
#                  * (1-(posted speed limit - threshold speed limit)*speed penalty factor)

cs_buffdist = 2640 # feet
cs_lu_facs = [col_area_ac, col_k12_enr, col_emptot, col_du]

cs_threshold_speed = 40 # MPH
cs_spd_pen_fac = 0.04 # speed penalty factor

intersxn_dens_buff = 1320 # distance in feet
bikeway_buff = 1320 # distance in feet

# ============================URBANIZATION PARAMETERS===========================

#params for determining if project is in greenfield or infill area
col_ctype = 'comm_type'
col_ctype_2 = 'comm_type_ppa'
ctypes_infill = ['Established', 'Corridor']
threshold_val = 0.9  # if more than 90% of project length is in greenfield, then project is greenfield vice-versa for infill

#for measuring loss in acres of natural resources within project area (nat resources = forest, parks, ag land)
buff_nat_resources = 2640 #feet. Is area of consideration when measuring acres of natural resources lost within project area.
lutypes_nat_resources = ['Forest', 'Agriculture', ]

