#land use buffer calcs

"""
Get following numbers within 0.5mi of project area:
    sum of jobs
    sum of dwelling units
    sum of trips (for each mode)

"""
import os

import arcpy
import pandas as pd



def point_sum(fc_pclpt, fc_project, val_fields, buffdist=2640, case_field=None, case_excs_list=[]):
    
    arcpy.AddMessage("aggregating land use data...")
    fl_parcel = "fl_parcel"
    arcpy.MakeFeatureLayer_management(fc_pclpt, fl_parcel)
    fl_project = "fl_project"
    arcpy.MakeFeatureLayer_management(fc_project, fl_project)
    
#    #synch projection of project line to fc
#    arcpy.AddMessage(arcpy.Describe(fl_parcel).spatialReference.name)
#    
#    arcpy.DefineProjection_management(fl_project, sr_parcels)
#    
#    arcpy.AddMessage(arcpy.Describe(fl_parcel).spatialReference.name)

    buff_dist = buffdist
    arcpy.SelectLayerByLocation_management(fl_parcel, "WITHIN_A_DISTANCE", fl_project, buff_dist)

    # If there are no points in the buffer (e.g., no collisions on segment, no parcels, etc.),
    # still add those columns, but make them = 0
    file_len = arcpy.GetCount_management(fl_parcel)
    file_len = int(file_len.getOutput(0))

    if case_field is not None:
        val_fields.append(case_field)

    # load parcel data into dataframe
    rows_pcldata = []
    with arcpy.da.SearchCursor(fl_parcel, val_fields) as cur:
        for row in cur:
            df_row = list(row)
            rows_pcldata.append(df_row)

    parcel_df = pd.DataFrame(rows_pcldata, columns = val_fields)

    if case_field is not None:
        parcel_df = parcel_df.loc[~parcel_df[case_field].isin(case_excs_list)] #exclude specified categories
        out_df = parcel_df.groupby(case_field).sum().T # get sum by category (case field)
        # NEXT ISSUE - need to figure out how to show all case types, even if no parcels with that case type within the buffer
    else:
        out_df = pd.DataFrame(parcel_df[val_fields].sum(axis=0)).T

    out_dict = out_df.to_dict('records')[0]

    return out_dict


if __name__ == '__main__':
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    output_space = r'C:\TEMP_OUTPUT'  # arcpy.env.scratchFolder
    output_txt = 'PPA_test_output.txt'

    # input fc of parcel data--must be points!
    in_pcl_pt_fc = r'https://services.sacog.org/hosting/rest/services/Hosted/parcel_data_pts_2016_ElDoradoTest/FeatureServer/0?' \
                    'token=KRoiSh6dNpAtlCUgV76z5u-6QL23j4VnbkfTan_THZ-qwNBZsj6BF8pIVDedu3PfGyTLkcaxKPkmwPROia1H5qTjPiugT2D7ty6TnIPyrxG7oGFYRtg0XCa86wbHcuOZtbdj2MlErby7wHR8e6UyHv0TG-62T0pRiFznejtGOIvZtTcEhG6DnWVIteZ5ylOyoIj3QRXtMpYexweWytfspLBTpDGyy6mZIBvPXAFxnaQ.' # arcpy.GetParameterAsText(0)
    value_fields = arcpy.GetParameterAsText(0)
    project_fc = arcpy.GetParameterAsText(1)
    
    value_fields = value_fields.split(';')
    
    dict_out = point_sum(in_pcl_pt_fc, project_fc, value_fields)
    
    out_txt = os.path.join(output_space, output_txt)
    
    arcpy.SetParameterAsText(2, out_txt)
    with open(out_txt,'w') as fout:
        for k, v in dict_out.items():
            lineout = '{}: {}'.format(k, v)
            fout.write(lineout)
    
    arcpy.AddMessage(dict_out)
    arcpy.AddMessage('printed to {}'.format(out_txt))
