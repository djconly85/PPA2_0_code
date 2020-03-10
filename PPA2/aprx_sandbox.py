# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 10:21:04 2020

@author: DConly
"""
import csv

import arcpy



def build_configs(mapimg_configs_csv):
    in_csv = mapimg_configs_csv
    p_map = "MapName" # map that layout and image are derived from
    p_layout = "MapLayout" # layout that will be made into image
    p_where = "SQL" # background data layer (e.g. collision heat layer)
    p_projline = "ProjLineLayer"
    
    out_config_list = []
    
    with open(in_csv, 'r') as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            v_map = row[p_map]
            v_layout = row[p_layout]
            v_projline = row[p_projline]
            v_where = row[p_where]
            
            out_config_row = [v_map, v_layout, v_projline, v_where]
            out_config_list.append(out_config_row)
    
    return out_config_list
    
  
aprx_file = r'\\arcserver-svr\D\PPA_v2_SVR\PPA2_GIS_SVR\PPA2_GIS_SVR.aprx'
map_config_csv = r"\\arcserver-svr\D\PPA_v2_SVR\PPA2\Input_Template\CSV\map_img_config.csv"


aprx_obj = aprx = arcpy.mp.ArcGISProject(aprx_file)

maps_aprx = [l.name for l in aprx.listMaps()]
layouts_aprx = [l.name for l in aprx.listLayouts()]
layers_aprx = {m.name:[l.name for l in m.listLayouts()] for m in aprx.listMaps()}

configs = build_configs(map_config_csv)
