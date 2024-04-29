# Garmin Data Extractor

This Python script allows you to extract health and activity data from Garmin Connect. It fetches data for a specified period and saves it to CSV files.

## Prerequisites

- Python version 3.x
- `garminconnect` package
- `pandas` package

## Installation

1. Clone the repository.
2. Install the required packages using pip:
3. Set up the environment variables:
   - `GARMINTOKENS`: Path to the directory where the Garmin Connect token will be stored.
   - `ACTIVITYTYPE`: Type of activity to fetch (e.g., cycling, running, swimming).

## Usage

1. Run the script:

    ```bash
    python extract_data.py <start_date> [--end_date <end_date>] [--days ] [--log_level <log_level>] [--username ] [--password ]
    ```

   - `<start_date>`: Start date of the period in 'YYYY-MM-DD' format.
   - `--end_date <end_date>`: (Optional) End date of the period in 'YYYY-MM-DD' format. Default is the current date.
   - `--days <days>`: (Optional) Number of days to fetch data for. Default is 31.
   - `--log_level <log_level>`: (Optional) Logger level (one of DEBUG, INFO, WARNING, ERROR). Default is INFO.
   - `--username <username>`: (Optional) Garmin Connect username. Default is None.
   - `--password <password>`: (Optional) Garmin Connect password. Default is None.
2. The health and activity data will be saved to the following CSV files:
   - `consolidated_garmin_health_stats.csv`
   - `garmin_activities.csv`

## Data Explain

Based on the Garmin devices you are using, the CSV file can contains a more complex dataset.
An exemple using a quite recent Garmin Watch (Fenix 7), the health dataset is having a lot of information:

```csv
calendar_date,total_steps,total_distance,step_goal,sleep_quality,intensity_minutes_goal,moderate_intensity_minutes,vigorous_intensity_minutes,intensity_minutes,weekly_avg,last_night_avg,last_night_5_min_high
2024-01-19,7256,5929,11600,89.0,150.0,0.0,0.0,0.0,59.0,69.0,107.0,"{'low_upper': 53, 'balanced_low': 58, 'balanced_upper': 77, 'marker_value': 0.27630615}",BALANCED,HRV_BALANCED_4,2024-01-19 06:21:44.673
```

The same extraction, got from my timelines years ago, is having a very few data:

```csv
calendar_date,total_steps,total_distance,step_goal,sleep_quality,intensity_minutes_goal,moderate_intensity_minutes,vigorous_intensity_minutes,intensity_minutes,weekly_avg,last_night_avg,last_night_5_min_high
2016-07-01,5423,4392,9205,,,,,,,,
```
