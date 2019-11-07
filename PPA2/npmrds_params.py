

#speed data attributes
fc_speed_data = r"I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\npmrds_metrics_v6"
col_ff_speed = "ff_speed"
col_congest_speed = "havg_spd_worst4hrs"
col_reliab_ampk = "lottr_ampk"
col_reliab_md = "lottr_midday"
col_reliab_pmpk = "lottr_pmpk"
col_reliab_wknd = "lottr_wknd"
col_tmcdir = "direction_signd"
col_roadtype = "f_system"  # indicates if road is freeway or not, so that data from freeways doesn't affect data on surface streets, and vice-versa

roadtypes_fwy = (1, 2)  # road type values corresponding to freeways
directions_tmc = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND"]

tmc_select_srchdist = 300 # units in feet. will select TMCs within this distance of project line for analysis.
tmc_buff_dist_ft = 90  # buffer distance, in feet, around the TMCs