/*
Name: PPA2_NPMRDS_metrics.sql
Purpose: Get data for each TMC for PPA 2.0 calcs:
	TMC code,
	Road name,
	Road number,
	F_System,
	off-peak 85th percentile speed (8pm-6am, all days),
	LOTTRs (80th/50th):
		Weekdays 6am-10am
		Weekdays 10am-4pm
		Weekdays 4pm-8pm
		Weekends 6am-8pm,
	Worst/highest LOTTR,
	Period of worst/highest LOTTR,
	Avg hours per weekday in congested conditions,
	Avg hours per day with data,
	1/0 NHS status

           
Author: Darren Conly
Last Updated: 9/2019
Updated by: <name>
Copyright:   (c) SACOG
SQL Flavor: SQL Server
*/