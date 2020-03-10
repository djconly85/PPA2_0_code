import sys 
import os 
import arcpy

C_OK = 'ok'
#..Testing aprx: D:\10Data\SACOG_PPA\SACOGPPA\SACOGPPA.aprx 
#..Testing Data: D:\10Data\SACOG_PPA\SACOGPPA\PPAData.gdb
#  args: D:\10Data\SACOG_PPA\SACOGPPA\SACOGPPA.aprx  "layers,project1line,OBJECTID>0;layers1,project3lines,OBJECTID=2"  JPG
#  
#json_config = {
#    {"layers": {"name" : "layers", "mapframe" : "layers", "layout" : "layers", "zoom_to_layer" : "project1line", "where" : ""}
#    }     
#}

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

def printPath(path):
    print_path = path.replace("\\\\","\\")
    print(print_path)
    arcpy.AddMessage(print_path)
    return print_path 

class PrintConfig(object):
    def __init__(self, s_print_config):
        l_print_config = s_print_config.split(",")
        self.MapFrame = l_print_config[0]                     # map/mapframe name
        self.Layout = "layout_{}".format(l_print_config[0])   # layout name
        n_elements = len(l_print_config)
        if(n_elements>1):
            self.Layer = l_print_config[1]    #..layerName used to for zoomto (control ext)
        else:
            self.Layer = ""
        if(n_elements>2):
            self.Where = l_print_config[2]    #..where to get features in the layer.
        else:
            self.Where = ""

        self.OutputImageName = "{}.jpg".format(self.MapFrame)

def exportmap(path_to_aprx, print_configs, image_format = "jpg", out_path = None):
    ok = C_OK
    out_images = ""
    try:
        if(out_path==None):
            out_path = arcpy.env.scratchFolder
        aprx = arcpy.mp.ArcGISProject(path_to_aprx)
        # print_config = "mapframe, zoomtolayer, where"
        arcpy.AddMessage(print_configs)
        print_configs = print_configs.split(";") 
        l_print_configs = []
        for s_print_config in print_configs:
            print_config = PrintConfig(s_print_config)
            l_print_configs.append(print_config)
        
        for print_config in l_print_configs:
            try:
                lyt = aprx.listLayouts(print_config.Layout)[0]
                map = aprx.listMaps(print_config.MapFrame)[0]
                if(print_config.Layer!=""):
                    try:
                        lyr = map.listLayers(print_config.Layer)[0]
                        fl = "fl{}".format(int(time.clock()))
                        if(arcpy.Exists(fl)): 
                            try:
                                arcpy.Delete_management(fl)
                            except:
                                pass 
                        arcpy.MakeFeatureLayer_management(lyr, fl, where_clause=print_config.Where)
                        arcpy.AddMessage("{} {}".format(arcpy.GetCount_management(fl)[0], print_config.Where))
                        ext = ""
                        with arcpy.da.SearchCursor(fl, ["Shape@"]) as rows:
                            for row in rows:
                                geom = row[0]
                                ext = geom.extent
                                break
                        if(ext!=""):
                            mf = lyt.listElements('MAPFRAME_ELEMENT')[0]
                            mf.camera.setExtent(ext)
                            mf.panToExtent(ext)
                    except:
                        msg = "{}, {}".format(arcpy.GetMessages(2), trace())
                        arcpy.AddMessage(msg)
                out_file = os.path.join(out_path, print_config.OutputImageName)
                if(os.path.exists(out_file)):
                    try:
                        os.remove(out_file)
                    except:
                        pass 
                arcpy.AddMessage("output image: {}".format(out_file))
                lyt.exportToJPEG(out_file)
                if(out_images==""):
                    out_images = out_file
                else:
                    out_images = "{};{}".format(out_images, out_file)
            except:
                msg = "{}, {}".format(arcpy.GetMessages(2), trace())
                arcpy.AddMessage(msg)

        t_returns = (ok, out_images)        

    except:
        msg = "{}, {}".format(arcpy.GetMessages(2), trace())
        arcpy.AddWarning(msg)
        tr = (msg,)


    return t_returns 


if (__name__ == '__main__'):
    print_configs = "layers,project1line,OBJECTID>0;layers1,project3lines,OBJECTID=2"
    aprx_path = arcpy.GetParameterAsText(0)
    print_configs = arcpy.GetParameterAsText(1)
    out_iamge_path = arcpy.GetParameterAsText(2)
    
    t_returns = exportmap(aprx_path, print_configs, "jpg")
    if(t_returns[0]==C_OK):
        arcpy.SetParameterAsText(3, t_returns[1])
    #where = "DateCreated = date '2/10/2020 12:00:00'"
