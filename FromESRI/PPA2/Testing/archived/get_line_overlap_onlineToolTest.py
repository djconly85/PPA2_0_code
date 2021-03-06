'''
#--------------------------------
# Name:get_line_overlap.py
# Purpose: See what share of a user-input project line overlaps with another network (e.g., STAA freight line network, bike lane network, etc)
#          
#           
# Author: Darren Conly
# Last Updated: <date>
# Updated by: <name>
# Copyright:   (c) SACOG
# Python Version: <version>
#--------------------------------

Sample projects used: CAL20466, SAC25062
'''
import datetime as dt
import time

import arcpy
#from arcgis.features import SpatialDataFrame
import pandas as pd

arcpy.env.overwriteOutput = True

dateSuffix = str(dt.date.today().strftime('%m%d%Y'))



#====================FUNCTIONS==========================================


def conflate_link2projline(fl_proj, fl_links_buffd, links_desc):
    arcpy.env.workspace = arcpy.env.scratchGDB
    print('starting conflation function for {}...'.format(links_desc))

    # get length of project
    fld_shp_len = "SHAPE@LENGTH"

    project_len = 0
    with arcpy.da.SearchCursor(fl_proj, fld_shp_len) as cur:
        for row in cur:
            project_len += row[0]
        
    # temporary files
    temp_intersctpts = "temp_intersectpoints"
    temp_intrsctpt_singlpt = "temp_intrsctpt_singlpt" # converted from multipoint to single point (1 pt per feature)
    temp_splitprojlines = "temp_splitprojlines" # fc of project line split up to match link buffer extents
    temp_splitproj_w_linkdata = "temp_splitproj_w_linkdata" # fc of split project lines with link data on them

    fl_splitprojlines = "fl_splitprojlines"
    fl_splitproj_w_linkdata = "fl_splitproj_w_linkdata"

    # get links whose buffers intersect the project line
    arcpy.SelectLayerByLocation_management(fl_links_buffd, "INTERSECT", fl_proj)

    #split the project line at the boundaries of the link buffer, creating points where project line intersects link buffer boundaries
    arcpy.Intersect_analysis([fl_proj, fl_links_buffd],temp_intersctpts,"","","POINT")
    arcpy.MultipartToSinglepart_management (temp_intersctpts, temp_intrsctpt_singlpt)

    # split project line into pieces at points where it intersects buffer, with 10ft tolerance
    # (not sure why 10ft tolerance needed but it is, zero tolerance results in some not splitting)
    arcpy.SplitLineAtPoint_management(fl_proj, temp_intrsctpt_singlpt,
                                      temp_splitprojlines, "10 Feet")
    arcpy.MakeFeatureLayer_management(temp_splitprojlines, fl_splitprojlines)

    # get link speeds onto each piece of the split project line via spatial join
    arcpy.SpatialJoin_analysis(temp_splitprojlines, fl_links_buffd, temp_splitproj_w_linkdata,
                               "JOIN_ONE_TO_ONE", "KEEP_ALL", "#", "HAVE_THEIR_CENTER_IN", "30 Feet")

    # convert to fl and select records where "check field" col val is not none
    arcpy.MakeFeatureLayer_management(temp_splitproj_w_linkdata, fl_splitproj_w_linkdata)

    #return total project length, project length that overlaps input line network, and pct
    join_count = "Join_Count"
    link_overlap_dist = 0
    with arcpy.da.SearchCursor(fl_splitproj_w_linkdata, [fld_shp_len, join_count]) as cur:
        for row in cur:
            if row[1] > 0:
                link_overlap_dist += row[0]
            else:
                continue

    overlap_pct = link_overlap_dist / project_len
    
    links_desc = links_desc.replace(" ","_")
    out_dict = {'project_length': project_len, 'overlap with {}'.format(links_desc): link_overlap_dist,
                'pct_proj_{}'.format(links_desc): overlap_pct}

    # cleanup
    fcs_to_delete = [temp_intersctpts, temp_intrsctpt_singlpt, temp_splitprojlines, temp_splitproj_w_linkdata]
    for fc in fcs_to_delete:
        arcpy.Delete_management(fc)

    return out_dict


def get_line_overlap(fl_projline, fc_network_lines, links_desc):
    arcpy.env.workspace = arcpy.env.scratchGDB
    arcpy.OverwriteOutput = True
    SEARCH_DIST_FT = 100
    LINKBUFF_DIST_FT = 90

    # make feature layer from speed data feature class
    fl_network_lines = "fl_network_lines"
    arcpy.MakeFeatureLayer_management(fc_network_lines, fl_network_lines)

    # make flat-ended buffers around links that intersect project
    arcpy.SelectLayerByLocation_management(fl_network_lines, "WITHIN_A_DISTANCE", fl_projline, SEARCH_DIST_FT, "NEW_SELECTION")

    # create temporar buffer layer, flat-tipped, around links; will be used to split project lines
    temp_linkbuff = "TEMP_linkbuff_4projsplit"
    fl_link_buff = "fl_link_buff"
    arcpy.Buffer_analysis(fl_network_lines, temp_linkbuff, LINKBUFF_DIST_FT, "FULL", "FLAT")
    arcpy.MakeFeatureLayer_management(temp_linkbuff, fl_link_buff)

    # get dict of data
    projdata_dict = conflate_link2projline(fl_projline, fl_link_buff, links_desc)

    return projdata_dict


# =====================RUN SCRIPT===========================
if __name__ == '__main__':
    start_time = time.time()

    #arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb'

    project_line = arcpy.GetParameterAsText(0) # "test_project_STAA_partialOverlap" #  #"NPMRDS_confl_testseg_seconn"
    proj_name = arcpy.GetParameterAsText(1) # "TestProj" #  #"TestProj"
    proj_type = arcpy.GetParameterAsText(2) # "Arterial" #  #"Freeway"
    link_fc = r'https://services.sacog.org/hosting/rest/services/Hosted/BikeRte_C1_C2_C4_2017/FeatureServer/0' # r'I:\Projects\Darren\PPA_V2_GIS\scratch.gdb\BikeRte_C1_C2_C4_2017' #network of lines whose overlap with the project you want to get (e.g., truck routes, bike paths, etc.
    links_description = "BikeC1C2C4"

    # make feature layers of NPMRDS and project line
    fl_project = "fl_project"
    arcpy.MakeFeatureLayer_management(project_line, fl_project)

    arcpy.OverwriteOutput = True
    projdata = get_line_overlap(fl_project, link_fc, links_description)
    arcpy.AddMessage(projdata)
    

        
    

