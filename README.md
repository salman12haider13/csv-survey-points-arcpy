# CSV Survey Points to ArcGIS Feature Class

This project contains an ArcPy script tool that imports a CSV file containing survey locations with DMS coordinates, converts the coordinates into decimal degrees, and creates point feature class in ArcGIS Pro.

The script also identifies survey locations where species presence is recorded and reports the three most northern, southern, eastern, and western presence points.

## Project Purpose

The purpose of this script is to automate the process of converting survey coordinate data from CSV file into GIS point data. The original CSV stores latitude and longitude values in DMS format, so the script converts them into decimal degrees before creating the final point feature class.


## Main Tasks Performed

- Imports a CSV file into an in-memory ArcGIS table
- Converts DMS coordinate strings into decimal degrees
- Adds new latitude and longitude decimal degree fields
- Creates an XY event layer from the converted coordinates
- Exports the XY event layer as a point feature class
- Counts survey records where species presence is recorded
- Finds the top three northern, southern, eastern, and western presence points

## Required CSV Fields

The input CSV should contain the following fields:

| Field Name | Description |
|---|---|
| `SurveyID` | Unique ID for each survey location |
| `sLatitude` | Latitude in DMS string format |
| `sLongitude` | Longitude in DMS string format |
| `Presence` | Species presence value, where `1` means present |

## DMS Format

The coordinate format expected by the script is:

```text
Direction-Degrees-Minutes-Seconds
```

Example:

```text
N-51-02-30
W-114-04-15
```

South and west coordinates are converted into negative decimal degree values.

## Folder Structure

```text
csv-survey-points-arcpy/
│
├── README.md
├── .gitignore
│
├── scripts/
│   └── DMS_to_DD.py
│
├── toolbox/
│   └── CSV_to_points.atbx
│
├── sample_data/
│   └── Routes.csv
│
└── docs/
    └── Flowchart.pdf
```

## Tools and Technologies Used

- ArcGIS Pro
- ArcPy
- Python
- ArcGIS Script Tool
- CSV data processing
- Coordinate conversion
- Feature class creation

## How to Use

1. Open ArcGIS Pro.
2. Add the toolbox file from the `toolbox` folder.
3. Run the script tool.
4. Select the input CSV file.
5. Choose the output feature class location.
6. Run the tool.
7. Review the geoprocessing messages for:
   - Total presence records
   - Three most northern observations
   - Three most southern observations
   - Three most eastern observations
   - Three most western observations

## Output

The script creates a point feature class using WGS84 spatial reference.

It also prints messages in the ArcGIS Pro geoprocessing window showing summary results for presence records.

## Notes

This project is mainly intended to demonstrate ArcPy scripting, coordinate conversion, CSV-to-feature-class processing, and basic spatial data automation in ArcGIS Pro.