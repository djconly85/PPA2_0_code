'''
Purpose - create tabular data table with PPA projects as rows and metrics as columns.
	Metrics are in excel sheet Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Spreadsheet\RawDataTableLayout.xlsx
    
	11/16/2017:
		instead of looping through projects, this script loops through place types
		and gets place type averages
	
	11/14/2017:
		attempt to replace searchcursor with da.searchcursor because supposedly
		it's much faster.

		
	11/9/2017:
		Add regional averages; possibly averages grouped by placetype
	
	10/17/2017:
	For job accessibility, will say zero jobs accessible if the project has no
	TAZ intesecting it (i.e., it's not in SACOG region).
	
	Older updates:
	See notes in Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\Old scripts\getMasterTable_multibuff_latest_10192017good.py

to run in command line:
python Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\Master Table Scripts\getMasterTable_commtypes_latest.py

to run in shell:
execfile(r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\Master Table Scripts\bikeway_fix\getMasterTable_commtypes_bikwyfix.py')
'''
import arcpy
from arcpy import env
import datetime
import time
import sys
import os
import csv

script_dir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\Master Table Scripts'
os.chdir(script_dir)

import ppa_functions1 as ppaf



arcpy.env.overwriteOutput = True



dateSuffix = str(datetime.date.today().strftime('%m%d%Y'))

#===============USER-DEFINED PARAMETERS=========================
# Specify directories
workSpace = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\PPA_layers.gdb'
arcpy.env.workspace = workSpace
accessibilityTxtDir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Accessbility Metric'
outTextDir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Spreadsheet\Region and CType Averages'

#community type inputs
commTypes = "community_type"
commTypeIdCol = "type"

#data layer inputs
centerLine = "Region_Centerline2017fwytag2"
AllParcel = "parcel_all"
JobCenter = "JobCenters"
BikewaysCurrent = "AllBikeways2015"
BikewaysFuture = "ProposedBikeways2015"
GTFSEvents = "TrnStopLocnWTrpCnt11172017"
TIMS = "Collisions2011to2016fwytag"
TAZ = "TAZ07"


# input choices
Year = 2012 #year to use for ILUT and model network data
#YEAR MUST MATCH REGION SCRIPT YEAR TOO

run_regsum = False #whether to get region-level summary
AllItems = True #whether to include all community types or not
commList = ["Corridor"]

bufferDistJC = 21120 # job center buffer distance in feet; 4 mile = 21120ft

start_time = time.time()
#============================FUNCTIONS===============================

#get list of unique project IDs
# if just do a select projects or all identified in center line layer
#==================DATA IMPORT AND PREPARATION========================

Year = str(Year)
ILUT = "parcel_" + Year
interSect = "intersections_" + Year
modelNet = "SM15_modelnet_" + Year
accessTxt = accessibilityTxtDir + "\\access_" + Year + ".csv"
outputFile = outTextDir+"\\CommTypeSum_" + Year + "_" + dateSuffix + ".csv"
	
#all-parcel file project stats
yr2char = Year[-2:]
varListAllParcel = ["acres","acres_AG_" + yr2char,"du_BO","emp_BO",
					"netACdu_" + yr2char,"netACemp_" + yr2char]
					
#ILUT
varListILUT = ["DU_TOT","POP_TOT","POP_EJ","HH_TOT_P","EMPEDU","EMPFOOD","EMPGOV","EMPOFC",
				"EMPOTH","EMPRET","EMPSVC","EMPMED","EMPIND","EMPTOT_S","STUD_K12","STUD_UNI",
				"ENR_K12","ENR_UNI",
				"VT_TOT","VMT_TOT","CVMT_TOT","PT_TOT_RES","SOV_TOT_RES","HOV_TOT_RES",
				"TRN_TOT_RES","BK_TOT_RES","WK_TOT_RES","VT_TOT_cv","CV3_VT","VMT_TOT_cv",
				"CV3_VMT","CVMT_TOT_cv","CV3_CVMT"]


#intersections
varListIntersecn = ["INTXN_1WAY","INTXN_3WAY","INTXN_4WAY"]

# Job Center polygons

varListjobCenter = ['JOB_CTR']

#street centerline length
varListCLineDist = ['BUF_CTRLINE_MI']

# Bike Facilities
varListBikeNtwk = ['BIKC1_MIBUFF','BIKC2_MIBUFF','BIKC3_MIBUFF','BIKC4_MIBUFF']

# Google Transit
varListTransit = ['TRAN_LOCNS','TRAN_EVENTS']

# collisons
varListCollisionSums = ['PEDKILL','PEDINJ','BICKILL','BICINJ'] 
varListCollisionsCounts = ['FWY_COLLN',
							'NON_FWY_COLLN', 
							'FWY_FATAL_COLLN',
							'NONFWY_FATAL_COLLN'] #count of all collisions


# Model network (buffer)
varListModelBuffer = ['FwyVMT_buff','FwyCVMT_buff','FwyLnMi_buff','FwyRteMi_buff',
						'StVMT_buff','StCVMT_buff','StLnMi_buff','StRteMi_buff']

#TAZ-based accessibilityTxtDir
varListAccessibility = ['JOBS30D_PAVG','JOBS45T_PAVG','WKR30D_JBAVG','WKR45T_JBAVG']

#=================PREPARE OUTPUT TABLE================================
#header row elements are concatenated lists converted to strings with comma-separated words
Header_ProjInfo = 'projectID,PROJ_TYPE,commun_type,PROJ_LEN_MI'
Header_buffArea= 'buffarea_qm,buffarea_hm'
Header_allParcel = ','.join(varListAllParcel) #makes list into comma-sep'd string
Header_ILUT = ','.join(varListILUT)
Header_Intersecn = ','.join(varListIntersecn)
Header_jobCenter = ','.join(varListjobCenter)
Header_CLineDist = ','.join(varListCLineDist)
Header_bikeCLDist = ','.join(varListBikeNtwk)
Header_Transit = ','.join(varListTransit)
Header_TIMS = ','.join(varListCollisionsCounts) + ',' + ','.join(varListCollisionSums)
Header_modelBuff = ','.join(varListModelBuffer)
Header_access = ','.join(varListAccessibility)

#create output file
myfile = open(outputFile, 'w')

#write header row to output file
myfile.write(Header_ProjInfo + ','
			+ Header_buffArea + ','
			+ Header_allParcel + ','
			+ Header_ILUT + ','
			+ Header_Intersecn + ','
			+ Header_jobCenter + ','
			+ Header_CLineDist + ','
			+ Header_bikeCLDist + ','
			+ Header_Transit + ','
			+ Header_TIMS + ','
			+ Header_modelBuff + ','
			+ Header_access + ','
			+ '\n') #write out headers

#=======================make feature layers=========================
arcpy.MakeFeatureLayer_management(AllParcel,"inAllParcel_lyr")
arcpy.MakeFeatureLayer_management(ILUT,"inILUT_lyr")
arcpy.MakeFeatureLayer_management(commTypes,"incommTypes_lyr")
arcpy.MakeFeatureLayer_management(interSect,"inInterSect_lyr")
arcpy.MakeFeatureLayer_management(JobCenter,"inJobCenter_lyr")
arcpy.MakeFeatureLayer_management(BikewaysCurrent,"currBikeways_lyr")
arcpy.MakeFeatureLayer_management(BikewaysFuture,"futBikeways_lyr")
arcpy.MakeFeatureLayer_management(GTFSEvents,"inGTFS_lyr")
arcpy.MakeFeatureLayer_management(TIMS,"inTIMS_lyr")
arcpy.MakeFeatureLayer_management(modelNet,"inModelNetwork_lyr")
arcpy.MakeFeatureLayer_management(TAZ,"inTAZ_lyr")
arcpy.MakeFeatureLayer_management(centerLine,"inCenterline_lyr")


#make future bikeways layer combining present and proposed bikeways
future_bikeways = "in_memory\currAndFutBikewys"
arcpy.Merge_management(["currBikeways_lyr","futBikeways_lyr"],
						future_bikeways)
future_bikeways_fl = "future_bikeways_lyr"
arcpy.MakeFeatureLayer_management(future_bikeways,future_bikeways_fl)



#get unique list of community types
inList = ppaf.getItemList("incommTypes_lyr",commTypeIdCol,AllItems,commList) 

#if applicable, get regional totals
if run_regsum:
	from getMasterTable_region_bikwyfix import region_values
	print("running region-level summary...")
	regstring = region_values + '\n'
	myfile.write(regstring)

	
#================ITERATE THROUGH Community Types=========================

for cType in inList:
	projID = "Comm Type"
	print("summarizing data for " + str(cType) + " community type...")
	
	strSQL = commTypeIdCol + " = '" + str(cType) + "'" #note the single quote identifiers
	arcpy.SelectLayerByAttribute_management("incommTypes_lyr", 
											"NEW_SELECTION", 
											strSQL)

	commType = str(cType)
	pLength = str(0)
	pType = "All"
	
	stringProjInfo = projID + ',' + pType + ',' + commType + ',' \
					+ pLength
	del pType
	
	#================================ALL-PARCEL CALCULATIONS====================
	print("\tparcel data...")
	stringAllParcel = ppaf.pointSum("inAllParcel_lyr",varListAllParcel,0,
								"incommTypes_lyr")
	
	#================================ILUT CALCULATIONS====================
	print("\tILUT data...")
	stringILUT = ppaf.pointSum("inILUT_lyr",varListILUT,0,
								"incommTypes_lyr") 
	
	
	#=============================INTERSECTION CALCULATIONS=================

	# get the number of intersections within a buffer
	print("\tintersections data...")
	arcpy.SelectLayerByLocation_management("inInterSect_lyr", 
											"WITHIN_A_DISTANCE",
											"incommTypes_lyr", 
											0)
	aCursor = arcpy.SearchCursor("inInterSect_lyr")	
	cnt_type1=0
	cnt_type3=0
	cnt_type4=0
	for aCur in aCursor:
		linkType = aCur.getValue("LINKS")
		if linkType == 1:
			cnt_type1 += 1
		elif linkType == 3:
			cnt_type3 += 1
		elif linkType == 4:
			cnt_type4 += 1
	#print(str(cType)+"type:"+str(cnt_type3)+","+str(cnt_type4)	
	stringIntersecn = str(cnt_type1) + "," + str(cnt_type3) + "," + str(cnt_type4)
	
	del aCursor
	#=====================JOB CENTER CALCULATIONS=================		
	# Get the number of job centers within 4 mile
	print("\tjob center data...")
	arcpy.SelectLayerByLocation_management("inJobCenter_lyr", 
											"WITHIN_A_DISTANCE",
											"incommTypes_lyr", 
											bufferDistJC)
	result = arcpy.GetCount_management("inJobCenter_lyr")
	stringJobCtr = str(result.getOutput(0))
	
	#=================TRANSIT STATS============================
	print("\ttransit data...")
	stringGTFS = ppaf.transitEvents("incommTypes_lyr",0)
	
	
	#===================COLLISION STATS============================
	#set 50ft buffer so only collisions on/very close to segment are captured
	print("\tcollision data...")
	stringTIMS = ppaf.collisionSummary("incommTypes_lyr",0,varListCollisionSums)
	
	#=================TAZ-LEVEL ACCESSIBILITY STATS===============================
	#select TAZs that intersect with project centerline segments
	print("\taccessibility data...")
	arcpy.SelectLayerByLocation_management("inTAZ_lyr", "INTERSECT",
											"incommTypes_lyr")
	f = open(accessTxt,'r')
	inDict = csv.DictReader(f)
	tazDict = {}
	
	#create dict of all TAZs along with their accessibility metrics
	for i in inDict:
		tazDict[int(i['TAZ'])] = [float(i['JOBS30D']), #0
								float(i['JOBS45T']), #1
								float(i['POP']), #2
								float(i['WORKERS30D']), #3
								float(i['WORKERS45T']), #4
								float(i['JOBS'])] #5
		
	#create iterator for TAZs that intersect the project segments
	accCursor = arcpy.SearchCursor("inTAZ_lyr")	
	
	sumJobsD = 0 #simple sum of jobs within driving n mins driving
	sumJobsT = 0 ##simple sum of jobs within driving n mins via transit
	sumWorkersD = 0 #simple sum of workers within driving dist
	sumWorkersT = 0 #simple sum of workers within transit dist
	sumProductJobsD = 0 #for each taz, multiply jobacc*pop, then sum those products
	sumProductJobsT = 0 #same as sumProductJobsD, but for driving
	sumProductWkrsD = 0 #for each taz, multiple workers accessed * jobs
	sumProductWkrsT = 0
	sumTAZjobs = 0
	sumTAZPops = 0 #sum of pop in all TAZs intersecting project
	TAZcnt = 0 #count of TAZs the project intersects
	
	for row in accCursor: #get total pop of all tazs intersecting project, plus 
	#sumproducts for weighted avg.
		taz = row.getValue("TAZ07")
		sumJobsD += tazDict[taz][0]
		sumJobsT += tazDict[taz][1]
		sumWorkersD += tazDict[taz][3]
		sumWorkersT += tazDict[taz][4]
		sumProductJobsD += tazDict[taz][0]*tazDict[taz][2]
		sumProductJobsT += tazDict[taz][1]*tazDict[taz][2]
		sumProductWkrsD += tazDict[taz][3]*tazDict[taz][5] #driving workers weightd x jobs
		sumProductWkrsT += tazDict[taz][4]*tazDict[taz][5] #transit wkrs weighted x jobs
		sumTAZjobs += tazDict[taz][5]
		sumTAZPops += tazDict[taz][2]
		TAZcnt += 1
		
	#jobs weighted by resident (POP). If no resident, simple average (total jobs/count of TAZs)
	if sumTAZPops != 0: 
		avgPersnJobAccD = str(sumProductJobsD/sumTAZPops)
		avgPersnJobAccT = str(sumProductJobsT/sumTAZPops)
	elif sumTAZPops == 0 and TAZcnt > 0:
		avgPersnJobAccD = str(sumJobsD/TAZcnt)
		avgPersnJobAccT = str(sumJobsT/TAZcnt)
	#if the project is not in a TAZ, it is outside of SACOG jurisdiction.
	#for now am giving job access of zero, but need to know best way to handle these
	else:
		avgPersnJobAccD = str(0)
		avgPersnJobAccT = str(0)
	
	#accessibility to workers, weighted by jobs. if no jobs, simple average (tot wkrs/TAZ count)
	if sumTAZjobs != 0: 
		avgJobWkrAccD = str(sumProductWkrsD/sumTAZjobs) 
		avgJobWkrAccT = str(sumProductWkrsT/sumTAZjobs)
	elif sumTAZPops == 0 and TAZcnt > 0:
		avgJobWkrAccD = str(sumWorkersD/TAZcnt)
		avgJobWkrAccT = str(sumWorkersT/TAZcnt)
	else:
		avgJobWkrAccD = str(0)
		avgJobWkrAccT = str(0)
		
	stringAccMeasures = avgPersnJobAccD + ',' + avgPersnJobAccT + ',' \
						+ avgJobWkrAccD + ',' + avgJobWkrAccT
	
	f.close()
	
	#========CALCULATE COMMUNITY TYPE AREA======================================
	print("\tcommunity type area data...")
	community_type_area = 0
	with arcpy.da.SearchCursor("incommTypes_lyr","SHAPE@AREA") as commCursor:
		for ctype in commCursor:
			community_type_area += ctype[0]
	
	#make a 0.25-mile buffer around the selected centerline features (on-project)


	stringCommArea1 = str(community_type_area / 43559.92194048) #convert to acres 
	stringCommArea2 = stringCommArea1 #dummy value because these are not getting buffered,
							#but still need value to fill column
							
	strCommArea = stringCommArea1 + ',' + stringCommArea2
	
	#=========================TOTAL NON-FREEWAY CENTERLINE MILES========================
	print("\tcenterline data...")
	#get mileage for centerline segments whose centroid is in buffer
	arcpy.SelectLayerByLocation_management("inCenterline_lyr", 
											"HAVE_THEIR_CENTER_IN",
											"incommTypes_lyr")
	SQL = "CLASS NOT IN ( 'H' , 'RAMP' )"
	aCursor = arcpy.SearchCursor("inCenterline_lyr",SQL)
	totalLength = 0
	for cur in aCursor:
		shapeLength = cur.getValue("Shape_Length")
		totalLength += shapeLength
		
	stringCLineLength = str(totalLength/5280) #convert feet to miles then to string
	
	del aCursor
	#====================BIKEWAY CENTERLINE MILES================================
	#get mileage for bikeway segments whose centroid is in buffer
	print("\tbikeway data...")
	if int(Year) == 2036: #should change this so it's not hard-coded as 2036/2012!
		bike_lyr = future_bikeways_fl
	else:
		bike_lyr = "currBikeways_lyr"
	arcpy.SelectLayerByLocation_management(bike_lyr, 
											"HAVE_THEIR_CENTER_IN",
											"incommTypes_lyr")
	
	#bikeCursor = arcpy.SearchCursor(bike_lyr)
	class1 = 0
	class2 = 0
	class3 = 0
	class4 = 0
	
	with arcpy.da.SearchCursor(bike_lyr,["SHAPE@LENGTH","BIKE_CLASS"]) as bikeCursor:
		for aCur in bikeCursor:
			shapeLength = aCur[0]
			if aCur[1] == 1:
				class1 += shapeLength
			if aCur[1] == 2:
				class2 += shapeLength
			if aCur[1] == 3:
				class3 += shapeLength
			if aCur[1] == 4:
				class4 += shapeLength
	
	stringBikClsLen = ''
	cnt = 1
	for i in [class1,class2,class3,class4]:
		if cnt == 1:
			stringBikClsLen = str(i/5280) #convert feet to miles
		else:
			stringBikClsLen = stringBikClsLen + ',' + str(i/5280)
		cnt += 1
	
	#===================MODEL NETWORK CALCULATIONS===============================
	#capclasses: 1=freeway; 6,26,36=ramp; 56 = aux lane;  8=HOV; 9=HOV connector; 7 = bike path
	#62/63 = centroid connectors; 99=placeholder/proposed
	#to get surface street stats, select "not in" the above freeway/hov/ramp values
	print("\tmodel network data...")
	arcpy.SelectLayerByLocation_management("inModelNetwork_lyr", 
											"HAVE_THEIR_CENTER_IN",
											"incommTypes_lyr")
											
	network_metrx = ["DAYVMT","DAYCVMT","LANEMI","DISTANCE"]
	
	SQLFwy = 'CAPCLASS IN (1,6,26,36,56,8,9)'
	SQLNotFwy = 'CAPCLASS NOT IN (1,6,26,36,56,8,9,7,62,63,99)'
	
	stringFwyModBuff = ppaf.modelBuffCalc("inModelNetwork_lyr", network_metrx, SQLFwy)
	stringStreetModBuff = ppaf.modelBuffCalc("inModelNetwork_lyr", network_metrx, SQLNotFwy)
	
	stringCombModBuff = stringFwyModBuff + ',' + stringStreetModBuff
	
	
	#8/1/2017 - Route miles currently just sum of DISTANCE column. Final calc TBD
	
	
	
	#===================CONCATENATE OUTPUTS========================
	print("\twriting row to csv...")
	myfile.write(stringProjInfo + ','
				+ strCommArea + ','
				+ stringAllParcel + ',' 
				+ stringILUT + ',' 
				+ stringIntersecn + ',' 
				+ stringJobCtr + ','
				+ stringCLineLength + ','
				+ stringBikClsLen + ','
				+ stringGTFS + ','
				+ stringTIMS + ','
				+ stringCombModBuff + ','
				+ stringAccMeasures + ','
				+ '\n')
	i += 1


myfile.close()
print("Finished!")

end_time = time.time()
elapsed = str(round((end_time - start_time)/60,1))
print("Time elapsed: " + elapsed + " mins")

