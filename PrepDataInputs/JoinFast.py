import arcpy

arcpy.env.workspace = r'I:\Projects\Darren\PPA_V2_GIS\PPA_V2.gdb'
arcpy.OverwriteOutput = True

left_table = 'pcl_w_mixindex_1mi_11042019' #can be feature class or table
right_table = 'parcel_mixindex_halfmi_11052019' #can be feature class or table

join_key_field_left = 'PARCELID' #case sensitive!
join_key_field_right = 'parcelid'
field_to_calc = 'mix_index_halfmi'
field_to_calc_dtype = "FLOAT" #FLOAT, TEXT, SHORT, or LONG

print("loading values from right-side table into dict...")
halfmi_dict = {}

fields_right = [f.name for f in arcpy.ListFields(right_table)]
fields_left = [f.name for f in arcpy.ListFields(left_table)]

with arcpy.da.SearchCursor(right_table, fields_right) as cur:
    for row in cur:
        pclid = row[fields_right.index(join_key_field_right)]
        mixval = row[fields_right.index(field_to_calc)]
        halfmi_dict[pclid] = mixval


print("updating...")
if field_to_calc not in fields_left:
    arcpy.AddField_management(left_table,field_to_calc, field_to_calc_dtype)

with arcpy.da.UpdateCursor(left_table, fields_left) as cur:
    for row in cur:
        pclid = row[fields_left.index(join_key_field_left)]
        if halfmi_dict.get(pclid) is not None:
            row[fields_left.index(field_to_calc)] = halfmi_dict[pclid]
            cur.updateRow(row)
        else:
            continue
