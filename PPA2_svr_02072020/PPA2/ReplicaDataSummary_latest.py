# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 13:46:21 2019

@author: dconly
"""
import os
import datetime as dt

import pandas as pd
import arcpy

import ppa_input_params as params
import ppa_utils as utils


# get PPA buffer data for trip shed
class TripShedAnalysis(object):
    
    def __init__(self, in_data_files, data_fields, tripdata_val_field, tripdata_agg_fxn, tripdata_groupby_field,
                   in_poly_fc, out_poly_fc_raw, out_poly_fc_filled, poly_id_field, filler_poly_fc, analysis_years, tripdata_case_fields, run_full_report=False):
        '''

        Parameters
        ----------
        in_data_files : TYPE = comma-delimited text or CSV
            DESCRIPTION = raw input trip data tables with origin and destination block group/TAZ ID columns
        data_fields : TYPE = fields to use in in_data_files
            DESCRIPTION. = fields with the relevant information for making trips-by-polygon ID summary table
        tripdata_val_field : TYPE = pandas dataframe field name
            DESCRIPTION. = field whose values we want (e.g. count of trip IDs, sum of trip distances, average of trip travel times, etc.)
        tripdata_agg_fxn : TYPE = string
            DESCRIPTION. = type of pandas aggregation function to apply to tripdata_val_field
        tripdata_groupby_field : TYPE = pandas dataframe field name
            DESCRIPTION. Group by this field to get the rows of the aggregated trip data (e.g. trips by block group ID, TAZ, etc.)
        in_poly_fc : TYPE = ESRI feature class
            DESCRIPTION. Polygons that you want to group trips into (e.g. TAZs, block group IDs, etc)
        out_poly_fc_raw : TYPE = ESRI feature class
            DESCRIPTION. trip shed polygon, raw with any holes if no trips originated in that area
        out_poly_fc_filled = trip shed polygon with holes filled
        poly_id_field : TYPE = ESRI feature class
            DESCRIPTION. final trip shed polygon used as analysis area
        filler_poly_fc : TYPE = ESRI feature class
            DESCRIPTION. polygon used to fill holes in initial trip shed polygon (usually single-feature SACOG region polygon)
        analysis_years : TYPE = list of integer years
            DESCRIPTION. years for which ILUT analyses for parcel-level demographic data will be run
        tripdata_case_fields : TYPE list of field names
            DESCRIPTION. fields in raw trip data for which you want columns made in pivot table (e.g. for trip counts by purpose, mode)
        run_full_report : TYPE, optional boolean flag
            DESCRIPTION. The default is False. Set to true if you want full ILUT demographic analyses run. False means just the trip shed polygon is made

        Returns
        -------
        None.

        '''
        
        # user-entered params
        self.in_data_files = in_data_files
        self.data_fields = data_fields
        self.tripdata_val_field = tripdata_val_field
        self.tripdata_agg_fxn = tripdata_agg_fxn
        self.tripdata_groupby_field = tripdata_groupby_field
        self.in_poly_fc = in_poly_fc
        self.out_poly_fc_raw = out_poly_fc_raw
        self.out_poly_fc_filled = out_poly_fc_filled
        self.poly_id_field = poly_id_field
        self.filler_poly_fc = filler_poly_fc
        self.analysis_years = analysis_years
        self.tripdata_case_fields = tripdata_case_fields
        self.run_full_report = run_full_report
        
        # hard-coded args
        self.df_col_trip_pct = 'pct_of_trips'
        self.col_tottrips = 'tot_trips'
        self.col_trippctlrank = 'trips_pctlrank'
        self.pct_cutoff = 0.8 # sort by descending percent of trips, then sum until this percent of total trips is added.
        
        # derived/calculated args
        self.df_data = self.make_tripdata_df()
        self.df_grouped_data = self.summarize_tripdf()
        
        
    def make_tripdata_df(self):
        '''Read in one or more CSVs containing raw trip data and make a pandas dataframe from them'''
    
        if len(self.in_data_files) == 1:
            out_df = pd.read_csv(self.in_data_files[0])
        else:
            out_df = pd.read_csv(self.in_data_files[0])
            for file in self.in_data_files[1:]:
                out_df2 = pd.read_csv(file, usecols=self.data_fields)
                out_df = out_df.append(out_df2)
        
        return out_df
    
    
    def summarize_tripdf(self):
        '''taking dataframe in_df, summarize by user-specified agg_fxn (e.g. average, count, sum, etc.)
        by the user-specified groupby_field (e.g. for trip data, could be mode, origin block group ID, etc.)'''
        in_df = self.make_tripdata_df()
        groupby_field = self.tripdata_groupby_field
        val_field = self.tripdata_val_field
        agg_fxn = self.tripdata_agg_fxn
        
        df_gb = in_df.groupby(groupby_field)[val_field].agg(agg_fxn)
        df_gb = pd.DataFrame(df_gb).rename(columns={'{}'.format(val_field): '{}'.format(agg_fxn)})
        df_gb['category'] = groupby_field
        
        df_gb['pct'] = df_gb[agg_fxn] / df_gb[agg_fxn].sum()
        
        df_gb = df_gb.reset_index()
        
        return df_gb
    
    
    def get_poly_data(self, categ_cols=[]): # in_df, val_field, agg_fxn, groupby_field, categ_cols=[], case_field=None
        '''make dataframe summarizing items by desired polygon ID field (e.g. trips by block group ID), which will be the rows in output table.
        The categ_cols argument specifies what you want the columns to be (e.g., trips by mode, by purpose, etc.)
        '''
        
        val_field = self.tripdata_val_field
        
        in_df = self.make_tripdata_df()
        
        piv = in_df.pivot_table(values=val_field, index=self.tripdata_groupby_field, 
                                columns=self.tripdata_case_fields, aggfunc=self.tripdata_agg_fxn) \
            .reset_index()
        
        # option to break out trips in each poly by some category (e.g., mode or purpose)
        if len(categ_cols) > 0:
            tblmodes = [col for col in categ_cols if col in piv.columns]
            
            piv[self.col_tottrips] = piv[tblmodes].sum(axis=1)  # count of trips in each poly
        else:
            piv = piv.rename(columns={val_field: self.col_tottrips}) # or just give total trips from each poly
        
        piv[self.col_pcttrips] = piv[self.col_tottrips] / piv[self.col_tottrips].sum()  # pct of total trips from each poly
        
        # percentile rank of each poly in terms of how many trips it produces
        # e.g., 100th percentile means the poly makes more trips than any of the other polys
        piv[self.col_trippctlrank] = piv[self.col_tottrips].rank(method='min', pct=True)
    
        return piv
    
    
    def filter_cumulpct(self):
        '''filter input polygon set to only retrieve polygons that capture some majority share (cutoff share, e.g., 90%)of the total trips
        but selected in descending order of how many trips were created.'''
        in_df = self.get_poly_data()
        
        df_sorted = in_df.sort_values(self.col_pcttrips, ascending=False)
        
        col_cumsumpct = 'cumul_sum'
        df_sorted[col_cumsumpct] = df_sorted[self.col_pcttrips].cumsum()
        
        df_out = df_sorted[df_sorted[col_cumsumpct] <= self.pct_cutoff]
        
        return df_out
    
    
    # poly creation process should probably be made into a CLASS and complete these basic steps:


    def create_raw_tripshed_poly(self):
        print("creating raw tripshed polygon...")
        in_poly_fc = self.in_poly_fc
        out_poly_fc = self.out_poly_fc_raw
        poly_id_field = self.poly_id_field
        in_df = self.summarize_tripdf()
        df_grouby_field = self.tripdata_groupby_field
        
        # convert numpy (pandas) datatypes to ESRI data types {numpy type: ESRI type}
        dtype_conv_dict = {'float64': 'FLOAT', 'object': 'TEXT', 'int64': 'LONG', 
                           'String': 'TEXT', 'OID': 'LONG', 'Single': 'DOUBLE', 
                           'Integer': 'LONG'}
        
        #make copy of base input poly fc that only has features whose IDs are in the dataframe
        fl_input_polys = 'fl_input_polys'
        utils.make_fl_conditional(in_poly_fc, fl_input_polys)
        
        df_ids = tuple(in_df[df_grouby_field])
        
        sql = "{} IN {}".format(poly_id_field, df_ids)
        arcpy.SelectLayerByAttribute_management(fl_input_polys, "NEW_SELECTION", sql)
        
        arcpy.CopyFeatures_management(fl_input_polys, out_poly_fc)
    
        # add dataframe fields to the trip shed polygon set
                
        #dict of {field: field data type} for input dataframe
        fields_dtype_dict = {col:str(in_df[col].dtype) for col in in_df.columns}
        
        # populate those fields with the dataframe data
        for field in fields_dtype_dict.keys():
            print("adding {} column and data...".format(field))
            field_vals = list(in_df[field]) # get list of values for desired field
            fld_dict = dict(zip(df_ids, field_vals))
            
            fdtype_numpy = fields_dtype_dict[field]
            fdtype_esri = dtype_conv_dict[fdtype_numpy]
            
            # add a field, if needed, to the polygon feature class for the values being added
            if utils.esri_field_exists(out_poly_fc, field):
                pass
            else:
                arcpy.AddField_management(out_poly_fc, field, fdtype_esri)
                
            # populate the field with the appropriate values
            with arcpy.da.UpdateCursor(out_poly_fc, [poly_id_field, field]) as cur:
                for row in cur:
                    join_id = row[0]
                    if fld_dict.get(join_id) is None:
                        pass
                    else:
                        row[1] = fld_dict[join_id]
                        cur.updateRow(row)
    
    def tag_if_joined_cursor(fc_in, fields):
        with arcpy.da.UpdateCursor(fc_in, fields) as cur:
            for row in cur:
                if row[0]:
                    row[1] = 1
                else: row[1] = 0
                cur.updateRow(row)
    
    def make_filled_tripshed_poly(self):
        print("filling in gaps in trip shed polygon...")
        full_poly_fc = self.in_poly_fc
        raw_tripshed_fc = self.out_poly_fc_raw
        filler_fc = self.filler_poly_fc
        
        scratch_gdb = arcpy.env.scratchGDB
        
        
        self.create_raw_tripshed_poly()  # Make trip shed polygon
        print(raw_tripshed_fc)
        print(arcpy.Exists(raw_tripshed_fc))
        
        
        # attribute join raw trip shed FC to full set of polygons FC
        arcpy.AddJoin_management(full_poly_fc, self.poly_id_field, raw_tripshed_fc, self.poly_id_field)
        
        # save joined fc as temp fc to scratch GDB
        temp_joined_fc = 'TEMP_joinedpoly_fc'
        temp_joined_fc_path = r'{}\{}'.format(scratch_gdb, temp_joined_fc)
        arcpy.FeatureClassToFeatureClass_conversion(full_poly_fc, scratch_gdb, temp_joined_fc)
        
        # add field to joined FC indicating 1/0 if it's part of trip shed. default zero. 1 if there's a join match
        fld_tripshedind = "TripShed"
        arcpy.AddField_management(temp_joined_fc_path, fld_tripshedind, "SHORT")
        
        self.tag_if_joined_cursor(temp_joined_fc_path, [self.col_tottrips, fld_tripshedind])
        
        # spatial select features that share a line with raw trip shed
        temp_joined_fl = 'temp_joined_fl'
        raw_tripshed_fl = 'raw_tripshed_fl'
        
        utils.make_fl_conditional(temp_joined_fc_path, temp_joined_fl)
        utils.make_fl_conditional(raw_tripshed_fc, raw_tripshed_fl)
        
        arcpy.SelectLayerByLocation_management(temp_joined_fl, "SHARE_A_LINE_SEGMENT_WITH", raw_tripshed_fl)
        
        # subselect where no join match and area < 20,000 ft2 (avoid large rural block groups)
        area_threshold_ft2 = 20000
        sql1 = "'SHAPE@AREA' <= {} AND {} = 0".format(area_threshold_ft2, fld_tripshedind)
        arcpy.SelectLayerByAttribute_management(temp_joined_fl, "SUBSET_SELECTION", sql1)
            
        # then updated the 1/0 field indicating if it's part of trip shed
        self.tag_if_joined_cursor(temp_joined_fl, [self.col_tottrips, fld_tripshedind])
        
        # new selection of all polygons where trip shed flag = 1, then export that as temporary FC
        sql2 = "'{}' = 1".format(fld_tripshedind)
        arcpy.SelectLayerByAttribute_management(temp_joined_fl, "NEW_SELECTION", sql2)
        
        temp_fc_step2 = "TEMP_joinedpolyfc_step2"
        temp_fc_step2_path = r'{}\{}'.format(scratch_gdb, temp_fc_step2)
        arcpy.FeatureClassToFeatureClass_conversion(full_poly_fc, scratch_gdb, temp_fc_step2)
        
        
        # Union whole region polygon with expanded "step2" trip shed
        temp_union_fc = "TEMP_poly_union_fc"
        temp_union_fc_path = r'{}\{}'.format(scratch_gdb, temp_union_fc)
        temp_union_fl = 'temp_union_fl' 
        
        arcpy.Union([temp_fc_step2_path, filler_fc], temp_union_fc_path)
        utils.make_fl_conditional(temp_union_fc_path, temp_union_fl)
        
        # From union result, select where tripshed joined FID = -1 (parts of the region polygon that fall outside of the tripshed polygon)
        fld_fid = 'FID'
        sql3 = "'{}' = -1".format(fld_fid)
        arcpy.SelectLayerByAttribute_management(temp_union_fl, "NEW_SELECTION", sql3)
        
        # Run singlepart-to-multipart, which makes as separate polygons
        temp_singleprt_polys_fc = "TEMP_singlepart_fillerpolys"
        temp_singleprt_polys_fc_path = r'{}\{}'.format(scratch_gdb, temp_singleprt_polys_fc)
        temp_singleprt_polys_fl = 'temp_singleprt_polys_fl'
        
        arcpy.MultipartToSinglepart_management(temp_union_fl, temp_singleprt_polys_fc_path)
        utils.make_fl_conditional(temp_singleprt_polys_fc_path, temp_singleprt_polys_fl)
        
        
        # From the multipart, select all but the geographically largest polygon and union to the block-group file
        # doing this will make it so you only get the "hole filler" pieces
        values = []
        with arcpy.da.SearchCursor(temp_singleprt_polys_fc_path, ["SHAPE@AREA"]) as cur:
            for row in cur:
                values.append(row[0])
                
        largest_poly_area = max(values)
        
        sql = "'{}' < {}".format("SHAPE@AREA", largest_poly_area)
        arcpy.SelectLayerByAttribute_management(temp_singleprt_polys_fl, "NEW_SELECTION", sql)
        

        # Merge the "hole fillers" with the expanded trip shed (i.e., raw trip shed + "share a line segment" polys added to it).
        # Result will be block group trip shed, with the holes filled in with non-block-group “hole filler” polygons        
        arcpy.Merge([temp_fc_step2_path, temp_singleprt_polys_fl], self.out_poly_fc_filled)
        
                        
        
'''        # user-entered params
        self.in_data_files = in_data_files
        self.data_fields = data_fields
        self.tripdata_val_field = tripdata_val_field
        self.tripdata_agg_fxn = tripdata_agg_fxn
        self.tripdata_groupby_field = tripdata_groupby_field
        self.in_poly_fc = in_poly_fc
        self.out_poly_fc = out_poly_fc
        self.out_poly_fc_filled = out_poly_fc_filled
        self.poly_id_field = poly_id_field
        self.filler_poly_fc = filler_poly_fc
        self.analysis_years = analysis_years
        self.tripdata_case_fields = tripdata_case_fields
        self.run_full_report = run_full_report
        
        # hard-coded args
        self.df_col_trip_pct = 'pct_of_trips'
        self.col_tottrips = 'tot_trips'
        self.col_trippctlrank = 'trips_pctlrank'
        self.pct_cutoff = 0.8 # sort by descending percent of trips, then sum until this percent of total trips is added.
        
        # derived/calculated args
        self.df_data = self.make_tripdata_df()
        self.df_grouped_data = self.summarize_tripdf()
        '''
                    
'''               
    def make_trip_shed_report(self):
    
        df_col_trip_pct = self.df_col_trip_pct
        
        # import CSV trip data into dataframe
        df_tripdata = make_tripdata_df(in_tripdata_files, trip_data_fields)
        
        # get splits of trips by mode and trips by purpose
        df_linktripsummary = self.df_grouped_data
        
        for f in tripdata_case_fields[1:]:
            df_linktripsummary = df_linktripsummary.append(summarize_tripdf(df_tripdata, f, tripdata_val_field, tripdata_agg_fxn))
        
        # summarize by polygon and whatever case value
        "aggregating Replica trip data for each polygon within trip shed..."
        df_groupd_tripdata = get_poly_data(df_tripdata, tripdata_val_field, tripdata_agg_fxn, 
                                           tripdata_groupby_field, [])
    
        # filter out block groups that don't meet inclusion criteria (remove polys that have few trips, but keep enough polys to capture X percent of all trips)
        #e.g., setting cutoff=0.9 means that, in descending order of trip production, block groups will be included until 90% of trips are accounted for.
        df_outdata = filter_cumulpct(df_groupd_tripdata, df_col_trip_pct, 0.9)
    
    
        # make new polygon feature class with trip data
        create_tripshed_poly(in_poly_fc, out_poly_fc, poly_id_field, df_outdata, tripdata_groupby_field)
        print("created polygon feature class {}.".format(out_poly_fc))
        
        # get PPA buffer data for trip shed
        if run_full_report:
            print("\nsummarizing PPA metrics for trip shed polygon...")
            df_tsheddata = tripshed.get_tripshed_data(out_poly_fc, params.ptype_area_agg, analysis_years, params.aggvals_csv, base_dict={})
        
            return df_tsheddata, df_linktripsummary
        else:
            return 'trip shed report not run', 'trip shed report not run'
            '''

if __name__ == '__main__':
    
    # ------------------USER INPUTS----------------------------------------
    
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    dir_tripdata = r'C:\TEMP_OUTPUT\ReplicaDownloads\SR51_AmRiver'
    
    #community-type and region-level values for comparison to project-level values
    aggvals_csv = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\PPA2\AggValCSVs\Agg_ppa_vals01132020_0954.csv"
    
    proj_name = input('Enter project name (numbers, letters, and underscores only): ')
    
    tripdata_files = ['trips_list_SR51AmRiverNB_Mon.zip',
                      'trips_list_SR51AmRiverSB_Mon.zip']  # os.listdir(r'C:\TEMP_OUTPUT\ReplicaDownloads\SR51_AmRiver')
    
    csvcol_bgid = 'origin_blockgroup_id'  # Replica/big data block group ID column
    csvcol_mode = 'trip_primary_mode'  # Replica/big data trip mode column
    csvcol_purpose = 'travel_purpose'  # Replica/big data trip purpose column
    
    csvcol_valfield = 'trip_start_time' # field for which you want to aggregate values
    val_aggn_type = 'count'  # how you want to aggregate the values field (e.g. count of values, sum of values, avg, etc.)
    
    # feature class of polygons to which you'll join data to based on ID field
    fc_bg_in = "BlockGroups2010"
    fc_poly_id_field = "GEOID10"
    
    fc_filler = 'sacog_region'
    
    years = [2016, 2040]
    
    xlsx_template = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\Replica\Replica_Summary_Template.xlsx"
    xlsx_out_dir = r"C:\TEMP_OUTPUT\ReplicaTripShed"
    
    run_full_shed_report = False

    #------------RUN SCRIPT------------------------------------
    timesufx = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))
    os.chdir(dir_tripdata)
    
    xlsx_out = '{}_TripShedAnalysis_{}.xlsx'.format(proj_name, timesufx)
    xlsx_out = os.path.join(xlsx_out_dir, xlsx_out)
    
    #excel workbook tabs that have output fields you want to preserve. You'll left join these to output data dfs
    ws_tshed_data = 'df_tshed_data'
    ws_trip_modes = 'df_trip_modes'
    ws_trip_purposes = 'df_trip_purposes'

    fc_tripshed_out_raw = "TripShedRaw_{}{}".format(proj_name, timesufx)
    fc_tripshed_out_filled = "TripShedFilled_{}{}".format(proj_name, timesufx)
    
    trip_data_fields = ['travel_purpose', 'origin_blockgroup_id', 'destination_blockgroup_id', 
                        'trip_primary_mode', 'trip_start_time'] #fields to use from Replica trip data CSVs
    
    tripdata_case_fields = [csvcol_mode, csvcol_purpose]
    
    trip_shed = TripShedAnalysis(tripdata_files, trip_data_fields, csvcol_valfield, val_aggn_type, csvcol_bgid,
                   fc_bg_in, fc_tripshed_out_raw, fc_tripshed_out_filled, fc_poly_id_field, fc_filler, years, tripdata_case_fields, 
                   run_full_report=False)
    
    trip_shed.make_filled_tripshed_poly()
    
    
    '''
    df_tshed_data, link_trip_summary = make_trip_shed_report(tripdata_files, trip_data_fields, csvcol_valfield, val_aggn_type, csvcol_bgid,
                   fc_bg_in, fc_tripshed_out, fc_poly_id_field, years, [csvcol_mode, csvcol_purpose], run_full_shed_report)
    
    if run_full_shed_report:
        df_trip_modes = link_trip_summary.loc[link_trip_summary['category'] == csvcol_mode]
        df_trip_purposes = link_trip_summary.loc[link_trip_summary['category'] == csvcol_purpose]
        
        df_tshed_data_out = utils.join_xl_import_template(xlsx_template, ws_tshed_data, df_tshed_data)
        df_trip_modes_out = utils.join_xl_import_template(xlsx_template, ws_trip_modes, df_trip_modes)
        df_trip_purposes_out = utils.join_xl_import_template(xlsx_template, ws_trip_purposes, df_trip_purposes)
        
        # output_csv = os.path.join(xlsx_out_dir, 'PPA_TripShed_{}_{}.csv'.format(
        #     proj_name, timesufx)
        # df_tshed_data.to_csv(output_csv)  # probably not necessary to output to CSV if outputting to Excel.
        
    
        utils.overwrite_df_to_xlsx(df_tshed_data_out, xlsx_template, xlsx_out, ws_tshed_data, start_row=0, start_col=0)
        utils.overwrite_df_to_xlsx(df_trip_modes_out, xlsx_out, xlsx_out, ws_trip_modes, start_row=0, start_col=0)
        utils.overwrite_df_to_xlsx(df_trip_purposes_out, xlsx_out, xlsx_out, ws_trip_purposes, start_row=0, start_col=0)
    '''
        
    print("Success! Output Excel file is {}".format(xlsx_out))
    
    
    