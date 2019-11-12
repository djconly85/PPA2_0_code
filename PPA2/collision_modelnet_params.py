
# =================MODEL NETWORK PARAMETERS============================================
modlink_searchdist = 700 # in feet, might have projection-related issues in online tool--how was this resolved in PPA1?

# model freeway capclasses: general purp lanes, aux lanes, HOV lanes, HOV connectors, on-off ramps, HOV ramps, freeway-freeway connector ramps
col_capclass = "CAPCLASS"

capclasses_fwy = (1, 6, 8, 9, 16, 18, 26, 36, 46, 51, 56)
capclass_arterials = (2, 3, 4, 5, 12)
capclasses_nonroad = (7, 62, 63, 99)



col_lanemi = 'LANEMI'
col_distance = 'DISTANCE'
col_dayvmt = 'DAYVMT'
col_daycvmt = 'DAYCVMT'


# ============================COLLISION DATA PARAMETERS===========================
col_fwytag = "fwy_yn"
col_nkilled = "NUMBER_KILLED"
col_bike_ind = 'BICYCLE_ACCIDENT'
col_ped_ind = 'PEDESTRIAN_ACCIDENT'

ind_val_true = 'Y'

colln_searchdist = 50 # in feet, might have projection-related issues in online tool-how was this resolved in PPA1?
years_of_collndata = 5