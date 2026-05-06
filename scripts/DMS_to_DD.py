#-----------------------------------------------------------------------------
# Name:     Create Survey Points from CSV
# Purpose:  This script tool imports CSV file containing DMS coordinates,
#           converts them into decimal degrees and generates a point feature
#           class. From this created featureclass the script identifies all
#           survey locations where species presence is recorded given by value 
#           1 in Presence field, and then calculates three most northern, southern, 
#           eastern, and western points based on their decimal latitude/longitude.
#
# Author:   Salman Haider
#
# Version:  1.05
# Created:  2025-11-17
#
# Inputs:   CSV file
#
# Outputs:  - A point featureclass 
#           - Text message output showing:
#               Total number of presence records
#               Three most northern presence points
#               Three most southern presence points
#               Three most eastern presence points
#               Three most western presence points
#
#-----------------------------------------------------------------------------

# Importing Libraries
import arcpy
import os
import sys

arcpy.env.overwriteOutput = True  # Allowing overwriting outputs (Set to true because I had to test tool multiple times and deleting already existing table again and again was tedious)

# Fuction for converting DMS to DD. Function inspired from my Lab 4. 
def dms_to_dd(degrees, minutes, seconds):
    degrees = float(degrees)
    minutes = float(minutes)
    seconds = float(seconds)

    if degrees >= 0:
        decimal_degrees = degrees + (minutes / 60.0) + (seconds / 3600.0)
    else:
        decimal_degrees = degrees - (minutes / 60.0) - (seconds / 3600.0)

    return decimal_degrees

# Function to read string DMS and extract degrees, minutes, seconds and send them to dms_to_dd function for conversion. 
def dms_string_to_dd(dms_string):
    parts = str(dms_string).split("-") # Splitting by hyphen to get hemisphere, degrees, minutes, seconds (DMS string is in format Direction-DD-MM-SS)
    if len(parts) != 4: # making sure if the string format is correct.
        raise ValueError("Unexpected DMS format: {0}".format(dms_string))

    hemisphere = parts[0].strip().upper()
    degrees = float(parts[1])
    minutes = float(parts[2])
    seconds = float(parts[3])

    if hemisphere in ("S", "W"):
        degrees = -degrees

    return dms_to_dd(degrees, minutes, seconds)

# Getting script tool parameters
input_csv = arcpy.GetParameterAsText(0)    # CSV file
output_fc = arcpy.GetParameterAsText(1)    # Output featureclass

temp_table_name = "survey_table"
temp_table = r"in_memory\{0}".format(temp_table_name) # Setting tbale path to in_memory workspace so that it is temprory and is deleted when tool finishes execution. reference: https://pro.arcgis.com/en/pro-app/3.4/help/analysis/geoprocessing/basics/the-in-memory-workspace.htm

try:
    arcpy.AddMessage("Importing CSV as a standalone table...")
    arcpy.conversion.TableToTable(input_csv, "in_memory", temp_table_name) # Importing CSV as table stored in memory temporarily

except Exception as import_err:
    arcpy.AddError("Failed to import CSV as table: {0}".format(import_err))
    sys.exit(0)

arcpy.AddMessage("Adding fields for decimal degree coordinates...")

latitude_dd_field = "LatDD"
longitude_dd_field = "LonDD"

existing_field_names = [field.name for field in arcpy.ListFields(temp_table)] # Getting list of all fields in temprory table

if latitude_dd_field not in existing_field_names: # checking if "LatDD" field already exists or not
    arcpy.management.AddField(temp_table, latitude_dd_field, "DOUBLE") # Adding new field "LatDD" for storing decimal degree latitude values

if longitude_dd_field not in existing_field_names: # checking if "LonDD" field already exists or not
    arcpy.management.AddField(temp_table, longitude_dd_field, "DOUBLE") # Adding new field "LonDD" for storing decimal degree latitude values

arcpy.AddMessage("Converting DMS strings to decimal degrees...")

fields_for_update = ["sLatitude", "sLongitude", latitude_dd_field, longitude_dd_field] # List of fields that would be used in update cursor

# Update cursor to edit the newly created fields and add converted DD values to them.
with arcpy.da.UpdateCursor(temp_table, fields_for_update) as update_cursor:
    for row in update_cursor:
        s_latitude = row[0] # sLatitude field
        s_longitude = row[1] # sLongitude field

        try:
            decimal_lat = dms_string_to_dd(s_latitude)
            decimal_lon = dms_string_to_dd(s_longitude)
        except Exception as coord_err:
            arcpy.AddWarning("Could not convert coordinates '{0}', '{1}': {2}".format(s_latitude, s_longitude, coord_err))
            continue

        row[2] = decimal_lat # LatDD field
        row[3] = decimal_lon # LonDD field
        update_cursor.updateRow(row) # psuhing the changes to the row

arcpy.AddMessage("Creating output point feature class...")

wgs84 = arcpy.SpatialReference(4326) # specifying WGS84 spatial reference for the output featureclass

event_layer_name = "survey_points_layer"
arcpy.management.MakeXYEventLayer(temp_table,longitude_dd_field,latitude_dd_field,event_layer_name,wgs84) # Creating new XY point layer using newly updated DD fields in the table.

arcpy.management.CopyFeatures(event_layer_name, output_fc) # Making new featureclass from XY point layer
arcpy.AddMessage("Output feature class created: {0}".format(output_fc))

arcpy.AddMessage("Calculating present and north/south/east/west points")

presence_field = "Presence"
survey_id_field = "SurveyID"

presence_points = [] # stores any points where species presence is recorded (i-e Presence field value is 1). Format: [ (SurveyID, LatDD, LonDD), (SurveyID, LatDD, LonDD), ...... ]
total_present = 0

# Search cursor to iterate through all the rows in featureclass and count total presence points and add values to presence_points list.
with arcpy.da.SearchCursor(output_fc,[survey_id_field, presence_field,latitude_dd_field, longitude_dd_field]) as search_cursor:
    for survey_id, presence, lat_dd, lon_dd in search_cursor:
        if presence == 1:
            total_present += 1 # Incrementing presence count
            presence_points.append((survey_id, lat_dd, lon_dd)) # Adding vaues to presence_points list

arcpy.AddMessage("Total survey locations where the species present: {0}".format(total_present))

# Checking if there are any presence records found or not
if total_present == 0:
    arcpy.AddWarning("No presence records found.")
    sys.exit(0)

#########################################################################
# Determine northernmost, southernmost, easternmost, and westernmost points
# -- BEGIN THIRD-PARTY CODE SNIPPET --

points_sorted_by_lat = sorted(presence_points, key=lambda row: row[1])

southern_three = points_sorted_by_lat[0:3]

northern_three = list(reversed(points_sorted_by_lat[-3:]))

points_sorted_by_lon = sorted(presence_points, key=lambda row: row[2])

western_three = points_sorted_by_lon[0:3]

eastern_three = list(reversed(points_sorted_by_lon[-3:]))

# -- END THIRD-PARTY CODE SNIPPET --
# The code was written with the help of ChatGPT. I was having trobles figuring out how to find points by direction from a list where i have latitudes and longitudes.
# Prompt 1: If I have a list named presence_points which stores a (ID, Lat,Lng). It looks like presence_points = [ (ID, Lat,Lng), (ID, Lat,Lng), (ID, Lat,Lng),......]. And i want to find out most northest point and most southest point and most eastest and most westest point. what can i do using python ?
# This prompt gave me suggestion to use min() and max(). i-e: max(presence_points, key=lambda p: p[1]) to find northernmost point.
# Prompt 2: How can i get top 3 points for each directions ?
# I used Prompt 2 because from prompt one i was only getting one point whereas i needed three points for each direction. This prompt suggested sorting the list by Lat and Lng first.
#########################################################################

# Outputing the results
arcpy.AddMessage("\nThree most northern observations:")
for survey_id, lat_dd, lon_dd in northern_three:
    arcpy.AddMessage("SurveyID {0}: Latitude = {1:.6f}, Longitude = {2:.6f}".format(survey_id, lat_dd, lon_dd))

arcpy.AddMessage("\nThree most southern observations:")
for survey_id, lat_dd, lon_dd in southern_three:
    arcpy.AddMessage("SurveyID {0}: Latitude = {1:.6f}, Longitude = {2:.6f}".format(survey_id, lat_dd, lon_dd))

arcpy.AddMessage("\nThree most eastern observations:")
for survey_id, lat_dd, lon_dd in eastern_three:
    arcpy.AddMessage("SurveyID {0}: Latitude = {1:.6f}, Longitude = {2:.6f}".format(survey_id, lat_dd, lon_dd))

arcpy.AddMessage("\nThree most western observations:")
for survey_id, lat_dd, lon_dd in western_three:
    arcpy.AddMessage("SurveyID {0}: Latitude = {1:.6f}, Longitude = {2:.6f}".format(survey_id, lat_dd, lon_dd))