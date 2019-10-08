/*
Name: PPA2_NPMRDS_metrics.sql
Purpose: Get data for each TMC for PPA 2.0 calcs:
	TMC code,
	Road name,
	Road number,
	F_System,
	off-peak 85th percentile speed (8pm-6am, all days),
	80th percentile TT:
		Weekdays 6am-10am
		Weekdays 10am-4pm
		Weekdays 4pm-8pm
		Weekends 6am-8pm,
	50th percentile TT:
		Weekdays 6am-10am
		Weekdays 10am-4pm
		Weekdays 4pm-8pm
		Weekends 6am-8pm,
	LOTTRs (80th/50th):
		Weekdays 6am-10am
		Weekdays 10am-4pm
		Weekdays 4pm-8pm
		Weekends 6am-8pm,
	Worst/highest LOTTR,
	Period of worst/highest LOTTR,
	Avg speed during worst 4 weekday hours,
	Worst hour of day,
	Avg hours per day with data,
	Count of epochs:
		All times
		Weekdays 6am-10am
		Weekdays 10am-4pm
		Weekdays 4pm-8pm
		Weekends 6am-8pm,
	1/0 NHS status

           
Author: Darren Conly
Last Updated: 9/2019
Updated by: <name>
Copyright:   (c) SACOG
SQL Flavor: SQL Server
*/

--==========PARAMETER VARIABLES=============================================================
USE NPMRDS
GO

--"bad" travel time percentile
DECLARE @PctlCongested FLOAT SET @PctlCongested = 0.8

--free-flow speed time period
DECLARE @FFprdStart INT SET @FFprdStart = 20 --free-flow period starts at or after this time at night
DECLARE @FFprdEnd INT SET @FFprdEnd = 6 --free-flow period ends before this time in the morning

--list of weekdays
DECLARE @weekdays TABLE (day_name VARCHAR(9))
	INSERT INTO @weekdays VALUES ('Monday')
	INSERT INTO @weekdays VALUES ('Tuesday')
	INSERT INTO @weekdays VALUES ('Wednesday')
	INSERT INTO @weekdays VALUES ('Thursday')
	INSERT INTO @weekdays VALUES ('Friday')

--hour period break points, use 24-hour time
DECLARE @AMpeakStart INT SET @AMpeakStart = 6 --greater than or equal to this time
DECLARE @AMpeakEnd INT SET @AMpeakEnd = 10 --less than this time
DECLARE @MiddayStart INT SET @MiddayStart = 10 --greater than or equal to this time
DECLARE @MiddayEnd INT SET @MiddayEnd = 16 --less than this time
DECLARE @PMpeakStart INT SET @PMpeakStart = 16 --greater than or equal to this time
DECLARE @PMpeakEnd INT SET @PMpeakEnd = 20 --less than this time
DECLARE @WkdPrdStart INT SET @WkdPrdStart = 6 --greater than or equal to this time
DECLARE @WkdPrdEnd INT SET @WkdPrdEnd = 20 --less than this time

--===========TRAVEL TIME PERCENTILES==============================
/*
--50th and 80th percentile TTs for AM peak
SELECT
	DISTINCT tmc_code,
	PERCENTILE_CONT(@PctlCongested)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p80_ampk,
	PERCENTILE_CONT(0.5)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p50_ampk
INTO #tt_pctl_ampk
FROM npmrds_2018_alltmc_paxtruck_comb
WHERE DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays) 
	AND DATEPART(hh, measurement_tstamp) >= @AMpeakStart 
	AND DATEPART(hh, measurement_tstamp) < @AMpeakEnd

--50th and 80th percentile TTs for weekday midday
SELECT
	DISTINCT tmc_code,
	PERCENTILE_CONT(@PctlCongested)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p80_midday,
	PERCENTILE_CONT(0.5)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p50_midday
INTO #tt_pctl_midday
FROM npmrds_2018_alltmc_paxtruck_comb
WHERE DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays) 
	AND DATEPART(hh, measurement_tstamp) >= @MiddayStart 
	AND DATEPART(hh, measurement_tstamp) < @MiddayEnd

--50th and 80th percentile TTs for pm peak
SELECT
	DISTINCT tmc_code,
	PERCENTILE_CONT(@PctlCongested)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p80_pmpk,
	PERCENTILE_CONT(0.5)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p50_pmpk
INTO #tt_pctl_pmpk
FROM npmrds_2018_alltmc_paxtruck_comb
WHERE DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays) 
	AND DATEPART(hh, measurement_tstamp) >= @PMpeakStart 
	AND DATEPART(hh, measurement_tstamp) < @PMpeakEnd

--50th and 80th percentile TTs for weekends
SELECT
	DISTINCT tmc_code,
	PERCENTILE_CONT(@PctlCongested)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p80_weekend,
	PERCENTILE_CONT(0.5)
		WITHIN GROUP (ORDER BY travel_time_seconds)
		OVER (PARTITION BY tmc_code) 
		AS tt_p50_weekend
INTO #tt_pctl_weekend
FROM npmrds_2018_alltmc_paxtruck_comb
WHERE DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays) 
	AND DATEPART(hh, measurement_tstamp) >= @WkdPrdStart 
	AND DATEPART(hh, measurement_tstamp) < @WkdPrdEnd

--count number of epochs in each LOTTR period
SELECT
	tmc.code,
	SUM(CASE WHEN DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays)
			AND DATEPART(hh, measurement_tstamp) >= @AMpeakStart
			AND DATEPART(hh, measurement_tstamp) < @AMpeakEnd
		THEN 1 ELSE 0 END AS epochs_ampk,
	SUM(CASE WHEN DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays)
			AND DATEPART(hh, measurement_tstamp) >= @MiddayStart
			AND DATEPART(hh, measurement_tstamp) < @MiddayEnd
		THEN 1 ELSE 0 END AS epochs_midday,
	SUM(CASE WHEN DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays)
			AND DATEPART(hh, measurement_tstamp) >= @PMpeakStart
			AND DATEPART(hh, measurement_tstamp) < @PMpeakEnd
		THEN 1 ELSE 0 END AS epochs_pmpk,
	SUM(CASE WHEN DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays)
			AND DATEPART(hh, measurement_tstamp) >= @WkdPrdStart
			AND DATEPART(hh, measurement_tstamp) < @WkdPrdEnd
		THEN 1 ELSE 0 END AS epochs_weekend
INTO #epochs_x_relprd
FROM npmrds_2018_alltmc_paxtruck_comb

*/
--===========CONGESTION METRICS==================================

--Get free-flow speed, based on 85th percentile epoch speed during all epochs on all days of the year from 8pm-6am
--SELECT
--	DISTINCT tmc_code,
--	PERCENTILE_CONT(0.85)
--		WITHIN GROUP (ORDER BY speed)
--		OVER (PARTITION BY tmc_code) 
--		AS speed_85p_night
--INTO #offpk_85th_spd
--FROM npmrds_2018_alltmc_paxtruck_comb
--WHERE (DATEPART(hh,measurement_tstamp) >= @FFprdStart
--		OR DATEPART(hh,measurement_tstamp) < @FFprdEnd)

--get speeds by hour of day, long table
--SELECT
--	tt.tmc_code,
--	DATEPART(hh,tt.measurement_tstamp) AS hour_of_day,
--	COUNT(*) AS total_epochs_hr,
--	ff.speed_85p_night,
--	COUNT(*) / SUM(1.0/tt.speed) AS havg_spd_weekdy,
--	AVG(tt.travel_time_seconds) AS avg_tt_sec_weekdy,
--	(COUNT(*) / SUM(1.0/tt.speed)) / ff.speed_85p_night AS cong_ratio_hr_weekdy,
--	RANK() OVER (
--		PARTITION BY tt.tmc_code 
--		ORDER BY (COUNT(*) / SUM(1.0/tt.speed)) / ff.speed_85p_night ASC
--		) AS hour_cong_rank
--INTO #avspd_x_tmc_hour
--FROM npmrds_2018_alltmc_paxtruck_comb tt
--	JOIN #offpk_85th_spd ff
--		ON tt.tmc_code = ff.tmc_code
--WHERE DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays) 
--GROUP BY 
--	tt.tmc_code,
--	DATEPART(hh,measurement_tstamp),
--	ff.speed_85p_night

--get harmonic average speed from epochs that are in the worst 4 weekday hours
SELECT
	tt.tmc_code,
	COUNT(*) AS total_epochs_worst4hrs,
	ff.speed_85p_night,
	COUNT(*) / SUM(1.0/tt.speed) AS havg_spd_worst4hrs
INTO #most_congd_hrs
FROM npmrds_2018_alltmc_paxtruck_comb tt
	JOIN #offpk_85th_spd ff
		ON tt.tmc_code = ff.tmc_code
	JOIN #avspd_x_tmc_hour avs
		ON tt.tmc_code = avs.tmc_code
		AND DATEPART(hh, tt.measurement_tstamp) = avs.hour_of_day
WHERE DATENAME(dw, measurement_tstamp) IN (SELECT day_name FROM @weekdays) 
	AND avs.hour_cong_rank < 5
	--AND tt.tmc_code = '105+04687'
GROUP BY 
	tt.tmc_code,
	ff.speed_85p_night

--return most congested hour of the day
SELECT DISTINCT tt.tmc_code,
	COUNT(tt.measurement_tstamp) AS epochs_slowest_hr,
	avs.hour_of_day AS slowest_hr,
	avs.havg_spd_weekdy AS slowest_hr_speed
FROM npmrds_2018_alltmc_paxtruck_comb tt 
	JOIN #avspd_x_tmc_hour avs
		ON tt.tmc_code = avs.tmc_code
		AND DATEPART(hh, tt.measurement_tstamp) = avs.hour_of_day
		--AND tt.tmc_code = '105+04687'
WHERE avs.hour_cong_rank = 1
GROUP BY tt.tmc_code, avs.hour_of_day, avs.havg_spd_weekdy 
--=========COMBINE ALL TOGETHER FOR FINAL TABLE==================================

--rank each hour on each TMC based on congestion ration (1 = smallest congestion ratio, or worst congestion)
--SELECT
--	tmc.tmc,
--	avs.hour_of_day,
--	avs.cong_ratio_hr_weekdy,
--	RANK() OVER (PARTITION BY tmc.tmc) ORDER BY avs.cong_ratio_hr_weekdy ASC

--DROP TABLE #tt_pctl_ampk
--DROP TABLE #tt_pctl_midday
--DROP TABLE #tt_pctl_pmpk
--DROP TABLE #tt_pctl_weekend
--DROP TABLE #offpk_85th_spd
--DROP TABLE #avspd_x_tmc_hour

