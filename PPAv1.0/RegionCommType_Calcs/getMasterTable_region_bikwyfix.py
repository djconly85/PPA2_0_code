'''
Purpose - create tabular data table with PPA projects as rows and metrics as columns.
	Metrics are in excel sheet Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Spreadsheet\RawDataTableLayout.xlsx
    
	11/20/2017:
		Made this just a module. If user wants region-level data they can 
		bring in the output of this script in and write it to the community-types CSV.
	
	11/17/2017:
		for transit, use dissolved file with counts of vehicle stops (pre-made
		through dissolve in arcmap rather than in this script). Idea is that it
		is a smaller file (4500 rows instead of 126000) and takes fewer resources.
		
		import functions from stand-alone function script
	
	11/16/2017:
		adds tag to each project indicating community type
		
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
python Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\getMasterTable_wregiontotal_latest.py

to run in shell:
execfile(r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\getMasterTable_wregiontotal_latest.py')
'''
import arcpy
from arcpy import env
import datetime
import time
import sys
import os
import csv

arcpy.env.overwriteOutput = True

script_dir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Python\Master Table Scripts'
os.chdir(script_dir)
import ppa_functions1 as ppaf

dateSuffix = str(datetime.date.today().strftime('%m%d%Y'))

#===============USER-DEFINED PARAMETERS=========================
# Specify directories
workSpace = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\PPA_layers.gdb'
arcpy.env.workspace = workSpace
accessibilityTxtDir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Accessbility Metric'
outTextDir = r'Q:\ProjectLevelPerformanceAssessment\DataLayers_Proof_of_Concept\Spreadsheet\Region and CType Averages'


#project file inputs
projectsList = "mtpprojx_sampWCtyp11172017" # SHP/GDB file of all projects
projectIdCol = "F2016_Proje" #column with the unique project ids
#data layer inputs
centerLine = "Region_Centerline2017fwytag2"
AllParcel = "parcel_all"
JobCenter = "JobCenters"
BikewaysCurrent = "AllBikeways2015"
BikewaysFuture = "ProposedBikeways2015"
TransitData = "TrnStopLocnWTrpCnt11172017"
TIMS = "Collisions2011to2016fwytag"
TAZ = "TAZ07"
commTypes = "community_type"
commTypeIdCol = "type"

# input choices
Year = input("Enter year for regional data: ") #year to use for ILUT and model network data

# specify list of projects if you are testing and don't want to summarize all projects.
specProjList = ['PLA25548',
				'CAL20432',
				'SAC24704'] 

bufferDist1 = 1320 #distance in feet for transpo infrastructure buffers
bufferDist2 = 2640 #distance in feet for land-use buffers
bufferDistJC = 21120 # job center buffer distance in feet; 4 mile = 21120ft

start_time = time.time()

#==================DATA IMPORT AND PREPARATION========================

Year = str(Year)
ILUT = "parcel_" + Year
interSect = "intersections_" + Year
modelNet = "SM15_modelnet_" + Year
accessTxt = accessibilityTxtDir + "\\access_" + Year + ".csv"
outputFile = outTextDir+"\\RegionSum" + Year + "_" + dateSuffix + ".csv"
	
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
	#service density/vehicle stops (use pointSum function)
	#unique stop locations (look to UOP NPMRDS script for inspiration)

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

header_items = [Header_ProjInfo,Header_buffArea,Header_allParcel,
              Header_ILUT,Header_Intersecn,Header_jobCenter,
              Header_CLineDist,Header_bikeCLDist,Header_Transit,
              Header_TIMS,Header_modelBuff,Header_access]


header_line = ','.join(header_items) + '\n'

#=======================make feature layers=========================
arcpy.MakeFeatureLayer_management(AllParcel,"inAllParcel_lyr")
arcpy.MakeFeatureLayer_management(ILUT,"inILUT_lyr")
arcpy.MakeFeatureLayer_management(projectsList,"inprojectsList_lyr")
arcpy.MakeFeatureLayer_management(interSect,"inInterSect_lyr")
arcpy.MakeFeatureLayer_management(JobCenter,"inJobCenter_lyr")
arcpy.MakeFeatureLayer_management(BikewaysCurrent,"currBikeways_lyr")
arcpy.MakeFeatureLayer_management(BikewaysFuture,"futBikeways_lyr")
arcpy.MakeFeatureLayer_management(TransitData,"inGTFS_lyr")
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



#================CALCULATE REGION-LEVEL METRICS====================

#project ID and type are just "all" when referring to entire region----------
projstat_regn = "REGION,All,All"

#area of region within 0.25mi and 0.5mi of centerline, in acres--------------

regn_area_qmi = str(999) #temporary dummy
regn_area_hmi = str(999) #temporary dummy

print("calculating region-level centerline buffer areas (0.5mi and 0.25mi)...")
regn_area_qmi = str(ppaf.bufferArea("inCenterline_lyr", "tmpbuff_region", bufferDist1))
regn_area_hmi = str(ppaf.bufferArea("inCenterline_lyr", "tmpbuff_region", bufferDist2))


#regional centerline total length---------------------------
region_cline_tot = 0
print("summing lengths of centerline segments...")
with arcpy.da.SearchCursor("inCenterline_lyr","Shape_Length") as cline_cursor:
	for segment in cline_cursor:
		seg_length = segment[0]
		region_cline_tot += seg_length
	
region_cline_tot = str(region_cline_tot/5280) #convert from feet to miles

#-----------------------------------------------------------------

#calculate all-parcel stats for all parcels within 1/2 mile of regional centerline
print("getting general stats for parcels within half mile of centerline...")
region_pcl = ppaf.pointSum("inAllParcel_lyr",varListAllParcel,bufferDist2, 
			"inCenterline_lyr")

print("getting ILUT stats for parcels within half mile of centerline...")
region_ilut = ppaf.pointSum("inILUT_lyr",varListILUT,bufferDist2, 
			"inCenterline_lyr")


#get stats on intersections-------------------------------------------

print("summarizing intersection types, job centers...")
arcpy.SelectLayerByLocation_management("inInterSect_lyr", 
											"WITHIN_A_DISTANCE",
											"inCenterline_lyr", 
											bufferDist1)

cnt_type1=0
cnt_type3=0
cnt_type4=0

with arcpy.da.SearchCursor("inInterSect_lyr","LINKS") as aCursor:
	for aCur in aCursor:
		linkType = aCur[0]
		if linkType == 1:
			cnt_type1 += 1
		elif linkType == 3:
			cnt_type3 += 1
		elif linkType == 4:
			cnt_type4 += 1

region_intersxncnt = str(cnt_type1) + ',' + str(cnt_type3) + ',' \
					+ str(cnt_type4)
					
#total job centers in region. consider making an average of some sort---------
job_ctrs_region = str(arcpy.GetCount_management("inJobCenter_lyr"))

#non-freeway centerline miles in region-------------------------------
non_fwy_clinetot = 0
nofwy_sql = "fwy_yn = 0"

print("summing lengths of non-freeway centerline segments...")
with arcpy.da.SearchCursor("inCenterline_lyr","SHAPE@LENGTH",nofwy_sql) \
as cline_cursor_nonfwy:
	for segment in cline_cursor_nonfwy:
		seg_length = segment[0]
		if seg_length is None:
			seg_length = 0
		non_fwy_clinetot += seg_length
		
non_fwy_clinetot = str(non_fwy_clinetot/5280)

#bicycle facility miles in region----------------------------------------------

#activate this code if you want to only include bike segments whose centroid
#is within 0.25mi of the centerline file
tmpbuff_reg = "in_memory/tmpbuffproj"
arcpy.Buffer_analysis("inCenterline_lyr", 
							tmpbuff_reg, 
							bufferDist1, 
							"FULL", 
							"ROUND", 
							"ALL")

if int(Year) == 2036: #should change this so it's not hard-coded as 2036/2012!
	bike_lyr = future_bikeways_fl
else:
	bike_lyr = "currBikeways_lyr"
	
arcpy.SelectLayerByLocation_management(bike_lyr, 
											"HAVE_THEIR_CENTER_IN",tmpbuff_reg)

#arcpy.SelectLayerByLocation_management("currBikeways_lyr", 
#								"HAVE_THEIR_CENTER_IN",tmpbuff_reg)

class1r = 0
class2r = 0
class3r = 0
class4r = 0

where_clause = "BIKE_CLASS IN (1,2,3,4)"
with arcpy.da.SearchCursor(bike_lyr,["SHAPE@LENGTH","BIKE_CLASS"],
							where_clause) as bikeCursor:
	for aCur in bikeCursor:
		shapeLength = aCur[0]
		if shapeLength is None:
			shapeLength = 0
		if aCur[1] == 1:
			class1r += shapeLength
		if aCur[1] == 2:
			class2r += shapeLength
		if aCur[1] == 3:
			class3r += shapeLength
		if aCur[1] == 4:
			class4r += shapeLength

stringBikClsLenReg = ''
cnt = 1
for i in [class1r,class2r,class3r,class4r]:
	if cnt == 1:
		stringBikClsLenReg = str(i/5280) #convert feet to miles
	else:
		stringBikClsLenReg = stringBikClsLenReg + ',' + str(i/5280)
	cnt += 1

#regional transit stop data (unique stops and svc density-----------------------

#transit stops within 0.25mi of a centerline file feature
regl_transit_data = ppaf.transitEvents("inCenterline_lyr",bufferDist1)

#regional collision data-----------------------------------------------------
print("aggregating regional collision data...")
#different from normal collision selection; not spatial selection, so that it
#captures all collisions, including those that happened in SACOG region but are
#mapped outside of it due to bad geocoding.

fwy_colln = 0
nfwy_colln = 0
fwyfatal_colln = 0
nfwyfatal_colln = 0

with arcpy.da.SearchCursor("inTIMS_lyr",["KILLED","fwy_yn"]) as aCursor:
	for aCur in aCursor:
		fatal_ind = aCur[0] #"KILLED" column
		if aCur[1] == 1: #"fwy_yn" column
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

regionTIMSCounts = str(fwy_colln) + "," \
				+ str(nfwy_colln) + "," \
				 + str(fwyfatal_colln) + "," \
				 + str(nfwyfatal_colln)

 
regionTIMSSums = ppaf.pointSum("inTIMS_lyr",varListCollisionSums,50, 
						"inprojectsList_lyr", 
						trim_location = False, bufType="WITHIN_A_DISTANCE")
						
region_collisions = regionTIMSCounts + ',' + regionTIMSSums

del aCursor
#regional model network data (vmt, lane miles, route miles, etc.)---------------
SQLFwy = 'CAPCLASS IN (1,6,26,36,56,8,9)'
SQLNotFwy = 'CAPCLASS NOT IN (1,6,26,36,56,8,9,7,62,63,99)'

network_metrx = ["DAYVMT","DAYCVMT","LANEMI","DISTANCE"]

stringFwyModregn = ppaf.modelBuffCalc("inModelNetwork_lyr",network_metrx,SQLFwy)
stringStreetModregn = ppaf.modelBuffCalc("inModelNetwork_lyr",network_metrx,SQLNotFwy)

regnlevel_model = stringFwyModregn + ',' + stringStreetModregn


#regional accessibility---------------------------------------------------
print("getting regional accessibility stats...")

tazDict = {}
with open(accessTxt,'r') as f:
	inDict = csv.DictReader(f)

	#create dict of all TAZs along with their accessibility metrics
	for i in inDict:
		tazDict[int(i['TAZ'])] = [float(i['JOBS30D']), #0
								float(i['JOBS45T']), #1
								float(i['POP']), #2
								float(i['WORKERS30D']), #3
								float(i['WORKERS45T']), #4
								float(i['JOBS'])] #5
	
	
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

#create iterator for TAZs that intersect the project segments
with arcpy.da.SearchCursor("inTAZ_lyr","TAZ07") as accCursor:
	for row in accCursor: #get total pop of all tazs intersecting project, plus 
	#sumproducts for weighted avg.
		taz = row[0]
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
	
#jobs weighted by resident (POP)
regnJobAccD = str(sumProductJobsD/sumTAZPops)
regnJobAccT = str(sumProductJobsT/sumTAZPops)

#accessibility to workers, weighted by jobs.
regnJobWkrAccD = str(sumProductWkrsD/sumTAZjobs) 
regnJobWkrAccT = str(sumProductWkrsT/sumTAZjobs)

	
regnAccMeasures = regnJobAccD + ',' + regnJobAccT + ',' \
					+ regnJobWkrAccD + ',' + regnJobWkrAccT

#----------------consolidate to write to script-----------------------
print("writing regional values to CSV...")
region_variables = [projstat_regn, region_cline_tot, 
					regn_area_qmi, regn_area_hmi, region_pcl, region_ilut,
					region_intersxncnt, job_ctrs_region, 
					non_fwy_clinetot, stringBikClsLenReg, regl_transit_data, 
					region_collisions, regnlevel_model, regnAccMeasures]
					
region_values = ','.join(region_variables) + '\n'

with open(outputFile,'w') as f:
    f.write(header_line)
    f.write(region_values)


end_time = time.time()
elapsed = str(round((end_time - start_time)/60,1))
print("Time elapsed: " + elapsed + " mins")

