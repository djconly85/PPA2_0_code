
# =================MODEL NETWORK PARAMETERS============================================
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