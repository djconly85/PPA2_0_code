
# Accessibility columns
col_geoid = "bgid"
col_ej_ind = "PPA_EJ2018"
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



bg_search_dist = 300 #feet away from project line that you'll tag block groups in