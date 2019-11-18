
import arcpy

from PPA2 import collisions as coll2
# TO GET CTYPE AVERAGES, WILL NEED TO USE MODEL-BASED VERSION MODULE BECAUSE NEED MODELED VMT

fc_ctypes = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\comm_type_juris_latest'
fc_collisions = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb\Collisions2014to2018fwytag'


proj_type = 'Arterial' # maybe need to run separate ctype analysis for freeways
# ---------------

col_ctype = "comm_type"

fl_ctypes = 'fl_ctypes'
fl_collisions = 'fl_collisions'

arcpy.MakeFeatureLayer_management(fc_ctypes, fl_ctypes)
arcpy.MakeFeatureLayer_management(fc_collisions, fl_collisions)

list_ctypes = []
with arcpy.da.SearchCursor(fl_ctypes, col_ctype) as cur:
    for row in cur:
        list_ctypes.append(row[0])

uniq_ctypes = list(set(list_ctypes))

for ctype in uniq_ctypes:
    #select areas within that ctype
    arcpy.SelectLayerByAttribute_management(fl_ctypes, "NEW_SELECTION", "{} = '{}'".format(col_ctype, uniq_ctypes))

    output = coll2.get_collision_data(fl_ctypes, proj_type, fl_collisions, proj_weekday_adt)

