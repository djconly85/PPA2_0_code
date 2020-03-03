"""
Name: ReplicaDataSummary_latest.py
Purpose: 
    1 - create GIS polygon representing the "trip shed" for a given project, based on Replica trip data table
    2 - run PPA ILUT and land use analyses on trip shed polygon, using parcel-level ILUT data
    3 - Generate summary table of mode split and trip purpose split for trips using the project segment
        
          
Author: Darren Conly
Last Updated: 3/1/2020
Updated by: <name>
Copyright:   (c) SACOG
Python Version: 3.x
"""
import os
import datetime as dt
import pdb

import pandas as pd
import arcpy
import openpyxl

import ppa_utils as utils
import ppa_input_params as params
import bigdata_tripshed as tripshed

    


# get PPA buffer data for trip shed
class TripShedAnalysis(object):
    
    def __init__(self, project_name, in_data_files, data_fields, tripdata_val_field, tripdata_agg_fxn, tripdata_groupby_field,
                   in_poly_fc, out_poly_fc_raw, out_poly_fc_filled, poly_id_field, filler_poly_fc, analysis_years, 
                   tripdata_case_fields, run_full_report=False, xlsx_template_path=None):
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
        self.project_name = project_name
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
        self.xlsx_template = xlsx_template_path
        
        # hard-coded args
        self.df_col_trip_pct = 'pct_of_trips'
        self.col_tottrips = 'tot_trips'
        self.col_trippctlrank = 'trips_pctlrank'
        self.pct_cutoff = 0.8 # sort by descending percent of trips, then sum until this percent of total trips is added.
        #excel workbook tabs that have output fields you want to preserve. You'll left join these to output data dfs
        self.ws_tshed_data = 'df_tshed_data'
        self.ws_trip_modes = 'df_trip_modes'
        self.ws_trip_purposes = 'df_trip_purposes'
        self.xlsx_out_dir = arcpy.env.scratchFolder
        xlsx_out = '{}_TripShedAnalysis_{}.xlsx'.format(proj_name, timesufx)
        self.xlsx_out = os.path.join(self.xlsx_out_dir, xlsx_out)
        
        
        # derived/calculated args
        self.df_data = self.make_tripdata_df()
        # self.df_grouped_data = self.summarize_tripdf(self.tripdata_groupby_field, self.tripdata_val_field, self.tripdata_agg_fxn)
        
        
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
    
    
    def summarize_tripdf(self, groupby_field, val_field, agg_fxn):
        '''taking dataframe in_df, summarize by user-specified agg_fxn (e.g. average, count, sum, etc.)
        by the user-specified groupby_field (e.g. for trip data, could be mode, origin block group ID, etc.)'''
        in_df = self.make_tripdata_df()
        
        df_gb = in_df.groupby(groupby_field)[val_field].agg(agg_fxn)
        df_gb = pd.DataFrame(df_gb).rename(columns={'{}'.format(val_field): '{}'.format(self.col_tottrips)})
        df_gb['category'] = groupby_field
        
        df_gb['pct'] = df_gb[self.col_tottrips] / df_gb[self.col_tottrips].sum()
        
        df_gb = df_gb.reset_index()
        
        return df_gb
    
    
    def get_poly_data(self, categ_cols=[]): # in_df, val_field, agg_fxn, groupby_field, categ_cols=[], case_field=None
        '''make dataframe summarizing items by desired polygon ID field (e.g. trips by block group ID), which will be the rows in output table.
        The categ_cols argument specifies what you want the columns to be (e.g., trips by mode, by purpose, etc.)
        '''
        
        val_field = self.tripdata_val_field
        groupby_field = self.tripdata_groupby_field
        agg_fxn = self.tripdata_agg_fxn
        
        in_df = self.make_tripdata_df()
        
        # totals, not cased by anything
        piv_tot = in_df.pivot_table(values=val_field, index=groupby_field, aggfunc=agg_fxn).reset_index()
        piv_tot = piv_tot.rename(columns={val_field: self.col_tottrips})
        
        #return table grouped by poly id with columns for each category (e.g. modes, trip purposes)
        if len(self.tripdata_case_fields) > 0:
            for f in enumerate(self.tripdata_case_fields):
                case_type = f[1]
                idx = f[0]
                if idx == 0:
                    piv_out = in_df.pivot_table(values=val_field, index=groupby_field, 
                                            columns=[case_type], aggfunc=agg_fxn).reset_index()
                else:
                    piv2 = in_df.pivot_table(values=val_field, index=groupby_field, 
                                            columns=[case_type], aggfunc=agg_fxn).reset_index()
                    
                    # if a column exists in two different case types (e.g. "commercial" is both a veh mode and trip purpose)
                    # then add a tag to differentiate it
                    for col in piv2.columns:
                        if col in piv_out.columns and col != groupby_field:
                            piv2 = piv2.rename(columns={col:'{}_{}'.format(col, idx)})
                    
                    piv_out = piv_out.merge(piv2, on=groupby_field)
            
            piv_final = piv_out.merge(piv_tot, on=groupby_field)

        # add col showing percent of total trips starting in each poly        
        piv_final[self.df_col_trip_pct] = piv_final[self.col_tottrips] / piv_final[self.col_tottrips].sum()  # pct of total trips from each poly
        
        # percentile rank of each poly in terms of how many trips it produces
        # e.g., 100th percentile means the poly makes more trips than any of the other polys
        piv_final[self.col_trippctlrank] = piv_final[self.col_tottrips].rank(method='min', pct=True)
        
    
        return piv_final
    
    
    def filter_cumulpct(self):
        '''filter input polygon set to only retrieve polygons that capture some majority share (cutoff share, e.g., 90%)of the total trips
        but selected in descending order of how many trips were created.'''
        in_df = self.get_poly_data()
        
        df_sorted = in_df.sort_values(self.df_col_trip_pct, ascending=False)
        
        col_cumsumpct = 'cumul_sum'
        df_sorted[col_cumsumpct] = df_sorted[self.df_col_trip_pct].cumsum()
        
        df_out = df_sorted[df_sorted[col_cumsumpct] <= self.pct_cutoff]
        
        return df_out
    
    
    # poly creation process should probably be made into a CLASS and complete these basic steps:


    def create_raw_tripshed_poly(self, in_df):
        print("creating raw tripshed polygon...")
        in_poly_fc = self.in_poly_fc
        out_poly_fc = self.out_poly_fc_raw
        poly_id_field = self.poly_id_field
        # in_df = self.summarize_tripdf()
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
    
    def tag_if_joined_cursor(self, fc_in, fields):
        with arcpy.da.UpdateCursor(fc_in, fields) as cur:
            for row in cur:
                if row[0]:
                    row[1] = 1
                else: row[1] = 0
                cur.updateRow(row)
    
    def make_filled_tripshed_poly(self, in_df):
        '''Fills in gaps in trip shed polygon to ensure area includes empty areas that, if developed,
        would fall in the link trip shed. 
        
        Key steps:
            1 - create raw trip shed polygon based on whatever poly IDs are within the raw downloaded trip table
            2 - join this raw polygon set to a "full" poly file (e.g. all block groups in region)
            3 - tag polys in the trip shed
            4 - spatial select non-trip-shed polys that share a line segment with trip shed polys
            5 - from those spatially selected polygons, remove from the selection if they are above a certain area (area_threshold_ft2 variable)
            6 - For remaining selected non-trip-shed polys, tag them as being in the trip shed
            7 - Export this expanded set of trip-shed polys to temporary FC
            8 - Intersect this temporary FC with a "filler" FC that is one feature representing the whole region. This creates a "union FC"
                with polys that fill in the holes of the expanded poly temp FC
            9 - Select all but the largest features in the "union FC" and merge them with the expanded trip shed poly FC. This fills in the holes
                that may still exist in the expanded polyFC. Result is expanded poly FC with no "holes" in the trip shed.
            '''
        
        
        print("filling in gaps in trip shed polygon...")
        full_poly_fc = self.in_poly_fc
        raw_tripshed_fc = self.out_poly_fc_raw
        filler_fc = self.filler_poly_fc
        
        scratch_gdb = arcpy.env.scratchGDB
        
        self.create_raw_tripshed_poly(in_df)  # Make trip shed polygon

        
        fl_full_poly = 'fl_full_poly'
        fl_tripshed = 'fl_tripshed'
        
        utils.make_fl_conditional(full_poly_fc, fl_full_poly)
        utils.make_fl_conditional(raw_tripshed_fc, fl_tripshed)
        
        # attribute join raw trip shed FC to full set of polygons FC
        arcpy.AddJoin_management(fl_full_poly, self.poly_id_field, fl_tripshed, self.poly_id_field)
        
        # save joined fc as temp fc to scratch GDB
        temp_joined_fc = 'TEMP_joinedpoly_fc'
        temp_joined_fc_path = os.path.join(scratch_gdb, temp_joined_fc)
        
            
        if arcpy.Exists(temp_joined_fc_path): arcpy.Delete_management(temp_joined_fc_path)
        arcpy.FeatureClassToFeatureClass_conversion(fl_full_poly, scratch_gdb, temp_joined_fc)
        
        temp_joined_fl = 'temp_joined_fl'
        utils.make_fl_conditional(temp_joined_fc_path, temp_joined_fl)
        
        # add field to joined FC indicating 1/0 if it's part of trip shed. default zero. 1 if there's a join match
        fld_tripshedind = "TripShed"
        arcpy.AddField_management(temp_joined_fl, fld_tripshedind, "SHORT")
        
        self.tag_if_joined_cursor(temp_joined_fl, [self.col_tottrips, fld_tripshedind])
        
        # spatial select features that share a line with raw trip shed
        raw_tripshed_fl = 'raw_tripshed_fl'
        utils.make_fl_conditional(raw_tripshed_fc, raw_tripshed_fl)
        
        arcpy.SelectLayerByLocation_management(temp_joined_fl, "SHARE_A_LINE_SEGMENT_WITH", raw_tripshed_fl)
        
        # subselect where not part of original raw trip shed, but yes shares line segment w raw shed, and area < 20,000 ft2 (avoid large rural block groups)
        area_threshold_ft2 = 15000000
        fld_shape_area = "Shape_Area"
        sql1 = "{} <= {} AND {} = 0".format(fld_shape_area, area_threshold_ft2, fld_tripshedind)
        # pdb.set_trace()
        arcpy.SelectLayerByAttribute_management(temp_joined_fl, "SUBSET_SELECTION", sql1)
            
        # then update the 1/0 field indicating if it's part of trip shed
        with arcpy.da.UpdateCursor(temp_joined_fl, [fld_tripshedind]) as cur:
            for row in cur:
                row[0] = 1
                cur.updateRow(row)
        
        # new selection of all polygons where trip shed flag = 1, then export that as temporary FC
        sql2 = "{} = 1".format(fld_tripshedind)
        arcpy.SelectLayerByAttribute_management(temp_joined_fl, "NEW_SELECTION", sql2)
        
        temp_fc_step2 = "TEMP_joinedpolyfc_step2"
        temp_fc_step2_path = os.path.join(scratch_gdb, temp_fc_step2)
        if arcpy.Exists(temp_fc_step2_path): arcpy.Delete_management(temp_fc_step2_path)
        arcpy.FeatureClassToFeatureClass_conversion(temp_joined_fl, scratch_gdb, temp_fc_step2)
        
        
        # Union whole region polygon with expanded "step2" trip shed
        temp_union_fc = "TEMP_poly_union_fc"
        temp_union_fc_path = os.path.join(scratch_gdb, temp_union_fc)
        temp_union_fl = 'temp_union_fl' 
        
        if arcpy.Exists(temp_union_fc_path): arcpy.Delete_management(temp_union_fc_path)
        arcpy.Union_analysis([temp_fc_step2_path, filler_fc], temp_union_fc_path)
        utils.make_fl_conditional(temp_union_fc_path, temp_union_fl)
        
        # From union result, select where tripshed joined FID = -1 (parts of the region polygon that fall outside of the tripshed polygon)
        fld_fid = 'FID_{}'.format(temp_fc_step2)
        sql3 = "{} = -1".format(fld_fid)
        # pdb.set_trace()
        arcpy.SelectLayerByAttribute_management(temp_union_fl, "NEW_SELECTION", sql3)
        
        # Run singlepart-to-multipart, which makes as separate polygons
        temp_singleprt_polys_fc = "TEMP_singlepart_fillerpolys"
        temp_singleprt_polys_fc_path = os.path.join(scratch_gdb, temp_singleprt_polys_fc)
        temp_singleprt_polys_fl = 'temp_singleprt_polys_fl'
        
        if arcpy.Exists(temp_singleprt_polys_fc_path): arcpy.Delete_management(temp_singleprt_polys_fc_path)
        arcpy.MultipartToSinglepart_management(temp_union_fl, temp_singleprt_polys_fc_path)
        utils.make_fl_conditional(temp_singleprt_polys_fc_path, temp_singleprt_polys_fl)
        
        
        # From the multipart, select all but the geographically largest polygon and union to the block-group file
        # doing this will make it so you only get the "hole filler" pieces
        values = []
        with arcpy.da.SearchCursor(temp_singleprt_polys_fc_path, ["SHAPE@AREA"]) as cur:
            for row in cur:
                values.append(row[0])
                
        largest_poly_area = max(values)
        
        sql = "{} < {}".format(fld_shape_area, largest_poly_area)
        arcpy.SelectLayerByAttribute_management(temp_singleprt_polys_fl, "NEW_SELECTION", sql)
        

        # Merge the "hole fillers" with the expanded trip shed (i.e., raw trip shed + "share a line segment" polys added to it).
        # Result will be block group trip shed, with the holes filled in with non-block-group “hole filler” polygons       
        if arcpy.Exists(self.out_poly_fc_filled): arcpy.Delete_management(self.out_poly_fc_filled)
        arcpy.Merge_management([temp_fc_step2_path, temp_singleprt_polys_fl], self.out_poly_fc_filled)
        
        for fc in [temp_joined_fc_path, temp_fc_step2_path, temp_union_fc_path, temp_singleprt_polys_fc_path]:
            try:
                arcpy.Delete_management(fc)
            except:
                continue
            
    def overwrite_df_to_xlsx(self, workbk, sheet, in_df, unused=0, start_row=0, start_col=0):  # why does there need to be an argument?
        '''Writes pandas dataframe <in_df_ to <tab_name> sheet of <xlsx_template> excel workbook.'''
        in_df = in_df.reset_index()
        df_records = in_df.to_records(index=False)
        
        # get header row for output
        out_header_list = [list(in_df.columns)]  # get header row for output
        
        out_data_list = [list(i) for i in df_records]  # get output data rows
    
        comb_out_list = out_header_list + out_data_list
    
        ws = workbk[sheet]
        for i, row in enumerate(comb_out_list):
            for j, val in enumerate(row):
                cell = ws.cell(row=(start_row + (i + 1)), column=(start_col + (j + 1)))
                if (cell):
                    cell.value = val
        
    def join2xl_import_template(self, template_xlsx, template_sheet, in_df, indf_join_col, joincolidx=0):
        '''takes in import tab of destination Excel sheet, then left joins to desired output dataframe to ensure that
        output CSV has same rows every time, even if data frame that you're joining doesn't
        have all records'''
        df_template = pd.read_excel(template_xlsx, template_sheet)
        df_template = pd.DataFrame(df_template[df_template.columns[joincolidx]]) # get rid of all columns except for data items column
        # df_template = df_template.set_index(df_template.columns[joincolidx]) # set data items column to be the index
        
        df_out = df_template.merge(in_df, how='left', left_on=df_template.columns[joincolidx], right_on = indf_join_col) \
            .set_index(df_template.columns[joincolidx])
        
        return df_out
  
    def make_trip_shed_report(self):
        
        
        # summarize by polygon and whatever case value
        "aggregating Replica trip data for each polygon within trip shed..."
        df_linktripsummary = pd.DataFrame()
        
        for f in tripdata_case_fields:
            df = self.summarize_tripdf(f, self.tripdata_val_field, self.tripdata_agg_fxn)
            df_linktripsummary = df_linktripsummary.append(df)
    
        # filter out block groups that don't meet inclusion criteria (remove polys that have few trips, but keep enough polys to capture X percent of all trips)
        #e.g., setting cutoff=0.9 means that, in descending order of trip production, block groups will be included until 90% of trips are accounted for.
        df_outdata = self.filter_cumulpct()
    
        # make new polygon feature class with trip data
        self.make_filled_tripshed_poly(df_outdata)
        
        # get PPA buffer data for trip shed (including all ILUT data, etc.)
        if self.run_full_report and self.xlsx_template:
            print("\nsummarizing PPA metrics for trip shed polygon...")
            df_tsheddata = tripshed.get_tripshed_data(self.out_poly_fc_filled, params.ptype_area_agg, 
                                                      self.analysis_years, params.aggvals_csv, base_dict={})
            df_tsheddata = df_tsheddata.reset_index()
            df_tshed_data_out = self.join2xl_import_template(self.xlsx_template, self.ws_tshed_data, df_tsheddata, df_tsheddata.columns[0])
            del df_tshed_data_out['index']

            df_trip_modes = df_linktripsummary.loc[df_linktripsummary['category'] == csvcol_mode]
            df_trip_modes_out = self.join2xl_import_template(self.xlsx_template, self.ws_trip_modes, df_trip_modes, csvcol_mode)
            
            df_trip_purposes = df_linktripsummary.loc[df_linktripsummary['category'] == csvcol_purpose]
            df_trip_purposes_out = self.join2xl_import_template(self.xlsx_template, self.ws_trip_purposes, df_trip_purposes, csvcol_purpose)
            
            
            # dict_out = {df_tshed_data_out: self.ws_tshed_data, df_trip_modes_out: self.ws_trip_modes, df_trip_purposes_out: self.ws_trip_purposes}
            dict_out = {self.ws_tshed_data: df_tshed_data_out, self.ws_trip_modes: df_trip_modes_out, self.ws_trip_purposes: df_trip_purposes_out}

            # overwrite the import tab sheets
            wb = openpyxl.load_workbook(self.xlsx_template)
            for ws, df in dict_out.items():
                self.overwrite_df_to_xlsx(wb, ws, df)
            
            #then save as output excel file
            wb.save(self.xlsx_out)
            wb.close()
            
            print("Success! output Excel Summary - {}".format(self.xlsx_out))

        else:
            return 'trip shed report not run'


if __name__ == '__main__':
    
    # ------------------USER INPUTS----------------------------------------
    
    arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
    
    dir_tripdata = r'C:\TEMP_OUTPUT\ReplicaDownloads'
    tripdata_files = ['trips_listGrantLineNOJacksonThu.zip']  # os.listdir(r'C:\TEMP_OUTPUT\ReplicaDownloads\SR51_AmRiver')
    csvcol_bgid = 'origin_blockgroup_id'  # Replica/big data block group ID column
    csvcol_mode = 'trip_primary_mode'  # Replica/big data trip mode column
    csvcol_purpose = 'travel_purpose'  # Replica/big data trip purpose column
    csvcol_valfield = 'trip_start_time' # field for which you want to aggregate values
    val_aggn_type = 'count'  # how you want to aggregate the values field (e.g. count of values, sum of values, avg, etc.)
    
    #community-type and region-level values for comparison to project-level values
    aggvals_csv = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\PPA2_0_code\PPA2\Input_Template\CSV\Agg_ppa_vals02042020_0825.csv"
    
    # feature class of polygons to which you'll join data to based on ID field
    fc_bg_in = "BlockGroups2010"
    fc_poly_id_field = "GEOID10"
    
    fc_filler = 'sacog_region' # to fill in "holes" left over in trip shed
    
    years = [2016, 2040] # analysis years for ILUT data
    
    xlsx_template = r"Q:\ProjectLevelPerformanceAssessment\PPAv2\Replica\Replica_Summary_Template.xlsx"
    xlsx_out_dir = r"C:\TEMP_OUTPUT\ReplicaTripShed"
    
    
    run_full_shed_report = True

    #------------RUN SCRIPT------------------------------------
    proj_name = input('Enter project name (numbers, letters, and underscores only): ')
    
    timesufx = str(dt.datetime.now().strftime('%m%d%Y_%H%M'))
    os.chdir(dir_tripdata)
    

    fc_tripshed_out_raw = "TripShedRaw_{}{}".format(proj_name, timesufx)
    fc_tripshed_out_filled = "TripShedFilled_{}{}".format(proj_name, timesufx)
    
    trip_data_fields = ['travel_purpose', 'origin_blockgroup_id', 'destination_blockgroup_id', 
                        'trip_primary_mode', 'trip_start_time'] #fields to use from Replica trip data CSVs
    
    tripdata_case_fields = [csvcol_mode, csvcol_purpose]
    
    trip_shed = TripShedAnalysis(proj_name, tripdata_files, trip_data_fields, csvcol_valfield, val_aggn_type, csvcol_bgid,
                   fc_bg_in, fc_tripshed_out_raw, fc_tripshed_out_filled, fc_poly_id_field, fc_filler, years, tripdata_case_fields, 
                   run_full_shed_report, xlsx_template)
    
    outputs = trip_shed.make_trip_shed_report()
    
    
        
    
    
    
    