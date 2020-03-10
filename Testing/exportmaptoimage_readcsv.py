import sys 
import os 
import time
import csv

import arcpy

C_OK = 'ok'

def trace():
    import traceback, inspect
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # script name + line number
    line = tbinfo.split(", ")[1]
    filename = inspect.getfile(inspect.currentframe())
    # Get Python syntax error
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror


def build_configs(in_csv):
    p_map = "MapName" # map that layout and image are derived from
    p_layout = "MapLayout" # layout that will be made into image
    p_projlyr = "ProjLineLayer" # project line
    p_where = "SQL" # background data layer (e.g. collision heat layer)
    
    out_config_list = []
    
    with open(in_csv, 'r') as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            v_map = row[p_map]
            v_layout = row[p_layout]
            v_projlyr = row[p_projlyr]
            v_where = row[p_where]
            out_config_row = [v_map, v_layout, v_projlyr, v_where]
            out_config_list.append(out_config_row)
    
    return out_config_list

def expandExtent2D(ext, ratio):
    '''Adjust zoom extent for map of project segment
    ext = input extent object
    ratio = how you want to change extent. Ratio > 1 zooms away from project line; <1 zooms in to project line
    '''
    try:
        # spref = ext.spatialReference
        xmin = ext.XMin
        xmax = ext.XMax
        ymin = ext.YMin
        ymax = ext.YMax 
        width = ext.width
        height = ext.height
        dx = (ratio-1.0)*width/2.0 # divided by two so that diff is split evenly between opposite sides, so featur is still center of the extent
        dy = (ratio-1.0)*height/2.0
        xxmin = xmin - dx 
        xxmax = xmax + dx
        yymin = ymin - dy 
        yymax = ymax + dy
        new_ext = arcpy.Extent(xxmin, yymin, xxmax, yymax)
    except:
        new_ext = None 
    return new_ext      

class PrintConfig(object):
    '''each PrintConfig object has attributes: map frame, layer name, where clause'''
    def __init__(self, l_print_config):
        self.MapFrame = l_print_config[0]                     # map/mapframe name
        self.Layout = l_print_config[1]   # layout name
        n_elements = len(l_print_config)
        if(n_elements>1):
            self.Layer = l_print_config[2]    #..layerName used to for zoomto (control ext)
        else:
            self.Layer = ""
        if(n_elements>2):
            self.Where = l_print_config[3]    #..where to get features in the layer.
        else:
            self.Where = ""

        self.OutputImageName = "{}.jpg".format(self.MapFrame)

def exportmap(path_to_aprx, config_csv, project_fc):
    
    server_folder = 'E:\\ArcGIS\\PPA2_DevPortal'
    regd = os.path.join(server_folder, 'PPA_V2.gdb') #this was manually added after publishing! Is FGDB holding master FC with all project lines in it.
    proj_line_template_fc = os.path.join(regd, 'Project_Line_Template') # FC that has project line in it.
    all_projects_fc = os.path.join(regd, "All_PPA_Projects2020")
    
    arcpy.env.overwriteOutput = True
    ok = C_OK
    out_images = ""
    try:
        out_path = arcpy.env.scratchFolder
        arcpy.AddMessage(path_to_aprx)
        aprx = arcpy.mp.ArcGISProject(path_to_aprx)
        # print_config = "mapframe, zoomtolayer, where"
        l_print_configs = build_configs(config_csv)
        
        o_print_configs = []
        
        for l_print_config in l_print_configs:
            o_print_config = PrintConfig(l_print_config) #converts list vals into attributes of PrintConfig object ('o')
            o_print_configs.append(o_print_config)
            
            
        #insert process to overwrite display layer and append to master. This will update in all layouts using the display layer
        arcpy.AddMessage(os.path.abspath(proj_line_template_fc))
        
        arcpy.DeleteFeatures_management(proj_line_template_fc) # delete whatever features were in the display layer
        featcnt = arcpy.GetCount_management(proj_line_template_fc)[0]
        arcpy.AddMessage("after deleting, there are {} features in {}".format(featcnt, proj_line_template_fc))
        
        arcpy.Append_management([project_fc], proj_line_template_fc) # then replace those features with those from user-drawn line
        
        for print_config in o_print_configs:
            arcpy.AddMessage(print_config.Layout)
            try:
                
                lyt = aprx.listLayouts(print_config.Layout)[0]
                map = aprx.listMaps(print_config.MapFrame)[0]
                if(print_config.Layer!=""): # if there's a layer
                    try:
                        lyr = map.listLayers(print_config.Layer)[0]
                        fl = "fl{}".format(int(time.clock()))
                        if(arcpy.Exists(fl)): 
                            try:
                                arcpy.Delete_management(fl)
                            except:
                                pass 
                        arcpy.MakeFeatureLayer_management(lyr, fl, where_clause=print_config.Where) #make feature layer of project line
                        # arcpy.AddMessage("{} {}".format(arcpy.GetCount_management(fl)[0], print_config.Where))
                        ext = ""
                        with arcpy.da.SearchCursor(fl, ["Shape@"]) as rows:
                            for row in rows:
                                geom = row[0]
                                ext = geom.extent
                                
                                ext_ratio = 1.33
                                ext_zoom = expandExtent2D(ext, ext_ratio)
                                break
                        if ext_zoom != "": #zoom to project line feature
                            mf = lyt.listElements('MAPFRAME_ELEMENT')[0]
                            mf.camera.setExtent(ext_zoom)
                            mf.panToExtent(ext_zoom)
                    except:
                        msg = "{}, {}".format(arcpy.GetMessages(2), trace())
                        arcpy.AddMessage(msg)
                out_file = os.path.join(out_path, print_config.OutputImageName)
                if(os.path.exists(out_file)):
                    try:
                        os.remove(out_file)
                    except:
                        pass 
                lyt.exportToJPEG(out_file) # after zooming in, export the layout to a JPG
                if(out_images==""):
                    out_images = out_file
                else:
                    out_images = "{};{}".format(out_images, out_file) # make semicolon-delim'd list of output JPEGs
            except:
                msg = "{}, {}".format(arcpy.GetMessages(2), trace())
                arcpy.AddMessage(msg)

        t_returns = (ok, out_images)        

    except:
        msg = "{}, {}".format(arcpy.GetMessages(2), trace())
        arcpy.AddWarning(msg)
        t_returns = (msg,)


    return t_returns 


if (__name__ == '__main__'):
    fc_in = arcpy.GetParameterAsText(0)
    
    print_configs = "layers,project1line,OBJECTID>0;layers1,project3lines,OBJECTID=2"
    aprx_path = r"E:\ArcGIS\PPA2_DevPortal\PPA2_GIS_SVR\PPA2_GIS_SVR.aprx"  # r"\\arcserver-svr\D\PPA_v2_SVR\PPA2_GIS_SVR\PPA2_GIS_SVR.aprx"

    
    mapimg_configs_csv = r"\\arcserver-svr\D\PPA_v2_SVR\PPA2\Input_Template\CSV\map_img_config_TEST.csv"
    
    arcpy.AddMessage("updated {}".format(int(time.time())))
    t_returns = exportmap(aprx_path, mapimg_configs_csv, fc_in)
    if(t_returns[0]==C_OK):
        arcpy.SetParameterAsText(1, t_returns[1])
    #where = "DateCreated = date '2/10/2020 12:00:00'"
