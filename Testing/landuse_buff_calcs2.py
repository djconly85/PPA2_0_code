#land use buffer calcs

"""
Get following numbers within 0.5mi of project area:
    sum of jobs
    sum of dwelling units
    sum of trips (for each mode)

"""
import arcpy
import pandas as pd


def point_sum(fl_pclpt, val_fields, buff_dist, select_lyr, case_field=None, case_excs_list=[]):
    arcpy.SelectLayerByLocation_management(fl_pclpt, "WITHIN_A_DISTANCE", select_lyr, buff_dist)

    # If there are no points in the buffer (e.g., no collisions on segment, no parcels, etc.),
    # still add those columns, but make them = 0
    file_len = arcpy.GetCount_management(fl_pclpt)
    file_len = int(file_len.getOutput(0))

    if case_field is not None:
        val_fields.append(case_field)

    # load parcel data into dataframe
    rows_pcldata = []
    with arcpy.da.SearchCursor(fl_pclpt, val_fields) as cur:
        for row in cur:
            df_row = list(row)
            rows_pcldata.append(df_row)

    parcel_df = pd.DataFrame(rows_pcldata, columns = val_fields)

    if case_field is not None:
        parcel_df = parcel_df.loc[~parcel_df[case_field].isin(case_excs_list)] #exclude specified categories
        out_df = parcel_df.groupby(case_field).sum().T #get sum by category (case field)
        #NEXT ISSUE - need to figure out how to show all case types, even if no parcels with that case type within the buffer
    else:
        out_df = pd.DataFrame(parcel_df[val_fields].sum(axis=0)).T

    out_dict = out_df.to_dict('records')[0]
    print(out_dict)
    return out_dict




if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'

    # input fc of parcel data--must be points!
    in_pcl_pt_fc = "parcel_data_2016_11062019_pts"
    value_fields = ['POP_TOT', 'EMPTOT', 'EMPIND', 'PT_TOT_RES', 'SOV_TOT_RES', 'HOV_TOT_RES', 'TRN_TOT_RES', 'BIK_TOT_RES',
              'WLK_TOT_RES']

    fl_parcel = "fl_parcel"
    arcpy.MakeFeatureLayer_management(in_pcl_pt_fc, fl_parcel)

    # input line project for basing spatial selection
    project_fc = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\NPMRDS_confl_testseg'
    fl_project = "fl_project"
    arcpy.MakeFeatureLayer_management(project_fc, fl_project)

    buff_dist_ft = 2640  # distance in feet--MIGHT NEED TO BE ADJUSTED FOR WGS84--SEE OLD TOOL FOR HOW THIS WAS RESOLVED

    # get jobs, dwelling units, trips by mode within 0.5mi
    # point_sum(fl_parcel, value_fields, 2640, fl_project)

    # dwelling units by housing type within 1mi
    # point_sum(fl_parcel, ['DU_TOT'], 5280, fl_project, case_field='TYPCODE_DESC', case_excs_list=['Other'])

    # EJ population
    point_sum(fl_parcel, ['POP_TOT'], 5280, fl_project, case_field='EJ_2018')

