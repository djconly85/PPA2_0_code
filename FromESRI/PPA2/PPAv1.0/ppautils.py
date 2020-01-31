import os
import time 

import arcpy

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

# decorator  @zye 2017/09/02
def showTime(orgfunc):
    import time
    def wrapper(*args, **kwargs):
        t1 = time.time()
        rslt = orgfunc(*args, **kwargs)
        t2 = time.time() - t1
        sMsg = "{} run in {:0.4f} s.".format(orgfunc.__name__, t2)
        arcpy.AddMessage(sMsg)
        print(sMsg)
        return rslt 
    return wrapper

#..Add try/except to all the functions...zye 

#get list of unique project IDs
# if just do a select projects or all identified in center line layer
def getItemList(inLayer,item_id_col,AllItems,specItemsList):
    #.. Rewrite the following codes with arcpy.da.SearchCursor  #..zye
	if AllItems:
		inList = []
		aCursor = arcpy.SearchCursor(inLayer)
		cTypeDic = {}
		for aRow in aCursor:
			aCode = aRow.getValue(item_id_col)
			cTypeDic[aCode] = 1
		inList = cTypeDic.keys()
		del aCursor
	else:
		inList = specItemsList
	return inList
	
#@showTime
def bufferArea(layer2buffer, bufferName, distance, 
				sideType = "FULL", endType = "ROUND", 
				dissolveType = "ALL"):
	tempBuf1 = "in_memory/" + bufferName
	distanceField = str(distance) + " Feet"

	arcpy.Buffer_analysis(layer2buffer, 
							tempBuf1, 
							distanceField , 
							sideType, 
							endType, 
							dissolveType,
							"")
	
	#return buffer area in acres
	buff_acres = 0
	with arcpy.da.SearchCursor(tempBuf1,"SHAPE@AREA") as buffCursor:
		for poly in buffCursor:
			polyShape = poly[0]
			buff_acres += polyShape*2.29568e-5 #convert from square feet to acres
		
	return str(buff_acres)	


#summarize parcel layer features
#trim_location = whether to trim the summary to the selection_lyr geometry	
#@showTime
def	pointSum(inPointlLayer,varList,bufDist, selection_lyr, 
			trim_location = True, bufType="WITHIN_A_DISTANCE"):
	if trim_location:
		arcpy.SelectLayerByLocation_management(inPointlLayer, 
											bufType,
											selection_lyr,
											bufDist)
											
	
	#If there are no points in the buffer (e.g., no collisions on segment, no parcels, etc.),
	#still add those columns, but make them = 0
	file_len = arcpy.GetCount_management(inPointlLayer)
	file_len = int(file_len.getOutput(0))
	
	sum_dict = {}
	order_dict = {}
	
	#return rows of selected input layer features
	with arcpy.da.SearchCursor(inPointlLayer,varList) as aCursor:
		fields = aCursor.fields
		
		for i in range(1,len(fields)+1):
			aVarName = fields[i-1]
			order_dict[i] = aVarName #{0:"ACRES",1:"POP",...}
		
		if file_len == 0:
			for field in fields:
					sum_dict[field] = 0
		else:
			for i in aCursor:
				for field in aCursor.fields: #for each field...
					val = i[aCursor.fields.index(field)]
					if val is None:
						val = 0 #set to zero if null value
					if sum_dict.get(field) is None:
						sum_dict[field] = val
					else:
						pre_sum = sum_dict[field]
						new_sum = pre_sum + val
						sum_dict[field] = new_sum
				
	keys_sort = sorted(order_dict.keys())
	for i in keys_sort:
		if i == 1:
			outstr = str(sum_dict[order_dict[i]])
		else:
			outstr = outstr + ',' + str(sum_dict[order_dict[i]])
	return outstr

#for calculating model buffer metrics 
def modelBuffCalc(data_layer,fields,roadtype_sql):
	VMT = 0
	CVMT = 0
	LANEMI = 0
	ROUTEMI = 0
	with arcpy.da.SearchCursor(data_layer,fields,roadtype_sql) as inCursor:
		for segment in inCursor:
			VMT += segment[0]
			CVMT += segment[1]
			LANEMI += segment[2]
			ROUTEMI += segment[3] #TENTATIVE--CURRENTLY IS BIDIRECTIONAL DISTANCE, 
													#NOT CENTERLINE
	
	outString = str(VMT) + ',' + str(CVMT) + ',' + str(LANEMI) + ',' + str(ROUTEMI)
	return outString

#@showTime
def transitEvents(inSelectionLayer, bufDist, count_col = "COUNT_OBJECTID", inTransitLayer = "inGTFS_lyr",
					selection_type = "WITHIN_A_DISTANCE"):
					

	arcpy.SelectLayerByLocation_management(inTransitLayer, 
												selection_type,
												inSelectionLayer, 
												bufDist)
												
	stopLocns = 0
	stopEvents = 0
	with arcpy.da.SearchCursor(inTransitLayer,[count_col]) as aCursor:
		for aCur in aCursor:
			stopLocns += 1
			stopEvents += aCur[0]

	stringGTFS = str(stopLocns) + ',' + str(stopEvents)
	return stringGTFS
	
#@showTime
def collisionSummary(selectionLayer,bufDist, collisionSumCols, 
					collisions = "inTIMS_lyr",
					selection_type = "WITHIN_A_DISTANCE"):
			
	fwy_colln = 0
	nfwy_colln = 0
	fwyfatal_colln = 0
	nfwyfatal_colln = 0
	
	arcpy.SelectLayerByLocation_management(collisions, 
											selection_type,
											selectionLayer, 
											bufDist)

	with arcpy.da.SearchCursor(collisions,["KILLED","fwy_yn"])	as aCursor:
		for aCur in aCursor:
			fatal_ind = aCur[0] #KILLED column
			if aCur[1] == 1: #fwy_yn column
				if fatal_ind > 0: #if fatal, add to both "total" and "fatal" count
					fwyfatal_colln += 1 #otherwise, count just in "total" count
					fwy_colln += 1
				else:
					fwy_colln += 1 
			else:
				if fatal_ind > 0:
					nfwyfatal_colln += 1
					nfwy_colln += 1
				else:
					nfwy_colln += 1

	stringTIMSCounts = str(fwy_colln) + "," \
					+ str(nfwy_colln) + "," \
					 + str(fwyfatal_colln) + "," \
					 + str(nfwyfatal_colln)
	
	
	stringTIMSSums = pointSum(collisions,collisionSumCols,bufDist,
								selectionLayer)
	stringTIMS = stringTIMSCounts + ',' + stringTIMSSums
	
	return stringTIMS