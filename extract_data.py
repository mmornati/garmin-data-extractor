import garth
from getpass import getpass
import pandas as pd
from datetime import datetime,timedelta
import logging
import os
import json
from getpass import getpass
import requests
from garth.exc import GarthHTTPError
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
)
import argparse  # Import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
activitytype = "" # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
HEALTH_FILE="consolidated_garmin_health_stats.csv"
ACTIVITIES_FILE="garmin_activities.csv"

def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password

def init_empty_dataframe(colums=[]) -> pd.DataFrame:
    logger.debug("Init empty DataFrame")
    df = pd.DataFrame(columns=colums)
    df.set_index("calendar_date", inplace=True)
    return df

def parse_args():
    """
    Parses command line arguments for fetching data from Garmin Connect.

    Returns:
        argparse.Namespace: Object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch data from Garmin Connect.')
    parser.add_argument('start_date', type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str, help='End date in YYYY-MM-DD format', default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument('--days', type=int, help='Number of days to load', default=31)
    parser.add_argument('--log_level', type=str, help='Logger Leve one of DEBUG,INFO,WARNING,ERROR', default='INFO')
    parser.add_argument('--username', type=str, help='GarminConnect username', default=None)
    parser.add_argument('--password', type=str, help='GarminConnect password', default=None)
    return parser.parse_args()

def init_api(email=None, password=None):
    """
    Initialize Garmin API with your credentials.

    Args:
        email (str): Email of your Garmin Connect account.
        password (str): Password of your Garmin Connect account.

    Returns:
        Garmin: Initialized Garmin API object.

    Raises:
        FileNotFoundError: If token files are not present in the directory.
        GarthHTTPError: If there is an issue with HTTP request.
        GarminConnectAuthenticationError: If there is an issue with authentication.
        requests.exceptions.HTTPError: If there is an issue with HTTP request.

    """

    try:
        # Try to login using token data from directory
        logger.info(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'..."
        )

        garmin = Garmin()
        garmin.login(tokenstore)
        garth.resume(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. Need to log in again
        logger.info(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            # Initialize Garmin API with provided credentials
            garmin = Garmin(email=email, password=password, is_cn=False, prompt_mfa=get_mfa)
            garmin.login()

            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)

            logger.info(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )

        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
            logger.error(err)
            return None

    return garmin

def get_mfa() -> str:
    """
    Prompt the user to input the MFA (Multi-Factor Authentication) one-time code.

    Returns:
        str: The MFA one-time code entered by the user.
    """

    # Prompt the user to input the MFA one-time code
    return input("Enter the MFA one-time code: ")

def fetch_steps(end, period):
    """
    Fetch the daily steps data for a given period.

    Args:
        end (str): The end date of the period in '%Y-%m-%d' format.
        period (int): The number of days in the period.

    Returns:
        pandas.DataFrame: The daily steps data.

    Raises:
        Exception: If there is an error fetching the data.
    """
    logger.debug("Extract Steps")

    try:
        # Fetch the daily steps data
        steps = pd.DataFrame(garth.DailySteps.list(end=end, period=period))
        # Convert the 'calendar_date' column to datetime and subtract one day
        steps["calendar_date"] = steps["calendar_date"].apply(lambda x: x - timedelta(days=1))
        # Set the 'calendar_date' column as the index
        steps.set_index("calendar_date", inplace=True)

        return steps

    # If there is an error, log the error message and return an empty dataframe
    except Exception as error:
        logger.debug(error)
        logger.info(f"Missing steps for the current period")
        return init_empty_dataframe(["calendar_date", "total_steps", "total_distance", "step_goal"])
    
def fetch_sleep(end, period):
    """
    Fetches the daily sleep data for a given period.

    Args:
        end (str): The end date of the period in '%Y-%m-%d' format.
        period (int): The number of days in the period.

    Returns:
        pandas.DataFrame: The daily sleep data.

    Raises:
        Exception: If there is an error fetching the data.
    """

    # Debug log the function call
    logger.debug("Extract Sleep")

    try:
        # Fetch the daily sleep data
        sleep = pd.DataFrame(garth.DailySleep.list(end=end, period=period))
        # Convert the 'calendar_date' column to datetime and subtract one day
        sleep["calendar_date"] = sleep["calendar_date"].apply(lambda x: x - timedelta(days=1))
        # Set the 'calendar_date' column as the index
        sleep.set_index("calendar_date", inplace=True)
        # Rename the 'value' column to 'sleep_quality'
        sleep.rename(columns={"value": "sleep_quality"}, inplace=True)

        return sleep

    # If there is an error, log the error message and return an empty dataframe
    except Exception as error:
        logger.debug(error)
        logger.info(f"Missing sleep for the current period")
        return init_empty_dataframe(["calendar_date", "sleep_quality"])

def fetch_intensity(end, period):
    """
    Fetches the daily intensity minutes data for a given period.

    Args:
        end (str): The end date of the period in '%Y-%m-%d' format.
        period (int): The number of days in the period.

    Returns:
        pandas.DataFrame: The daily intensity minutes data.

    Raises:
        Exception: If there is an error fetching the data.
    """

    # Debug log the function call
    logger.debug("Extract Daily Intensity Minutes")

    try:
        # Fetch the daily intensity minutes data
        intensity_minutes = pd.DataFrame(
            garth.DailyIntensityMinutes.list(end=end, period=period)
        )
        # Set the 'calendar_date' column as the index
        intensity_minutes.set_index("calendar_date", inplace=True)
        # Calculate the 'intensity_minutes' column by summing 'moderate_value' and twice 'vigorous_value'
        intensity_minutes["intensity_minutes"] = \
            intensity_minutes["moderate_value"] + 2 * intensity_minutes["vigorous_value"]
        # Rename the columns for better readability
        intensity_minutes.rename(
            columns={
                "weekly_goal": "intensity_minutes_goal",
                "moderate_value": "moderate_intensity_minutes",
                "vigorous_value": "vigorous_intensity_minutes",
            },
            inplace=True
        )

        return intensity_minutes

    # If there is an error, log the error message and return an empty dataframe
    except Exception as error:
        logger.debug(error)
        logger.info(f"Missing Daily Intensity for the current period")
        return init_empty_dataframe(["calendar_date", "weekly_goal",  "moderate_value", "vigorous_value"])

def fetch_hrv(end, period):
    """
    Fetches the daily HRV (Heart Rate Variability) data for a given period.

    Args:
        end (str): The end date of the period in '%Y-%m-%d' format.
        period (int): The number of days in the period.

    Returns:
        pandas.DataFrame: The daily HRV data.

    Raises:
        Exception: If there is an error fetching the data.
    """

    # Debug log the function call
    logger.debug(f"Extract Hearth Rate Variability")

    try:
        # Fetch the daily HRV data
        hrv = pd.DataFrame(garth.DailyHRV.list(end=end, period=period))
        ser = hrv['baseline'].apply(lambda s: pd.json_normalize(s))
        a = hrv.drop(columns=['baseline'])
        b = pd.concat(list(ser), ignore_index=True)
        hrv = a.join(b)

        # Set the 'calendar_date' column as the index
        hrv.set_index("calendar_date", inplace=True)

        return hrv

    # If there is an error, log the error message and return an empty dataframe
    except Exception as error:
        logger.debug(error)
        logger.info(f"Missing HRV for the current period")
        return init_empty_dataframe(["calendar_date", "weekly_avg", "last_night_avg", "last_night_5_min_high"])



def fetch_data(garmin, start_date, end_date, days_bulk):
    """
    Fetches health and activity data for a given period and saves it to CSV files.

    Args:
        garmin (GarminConnect): The GarminConnect object for connecting to the Garmin API.
        start_date (str): The start date of the period in '%Y-%m-%d' format.
        end_date (str): The end date of the period in '%Y-%m-%d' format.
        days_bulk (int): The number of days to fetch data for in each iteration.
    """

    # Convert start and end dates to datetime objects
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Iterate over each period
    while start <= end:
        # Calculate the end date for the current period
        loop_end = start + timedelta(days=days_bulk)
        logger.info(f"**** Getting Data for {start} - {loop_end}")

        # Fetch health data for the period
        stats = (
            fetch_steps(loop_end.strftime("%Y-%m-%d"), days_bulk)
            .join(fetch_sleep(loop_end.strftime("%Y-%m-%d"), days_bulk))
            .join(fetch_intensity(loop_end.strftime("%Y-%m-%d"), days_bulk))
            .join(fetch_hrv(loop_end.strftime("%Y-%m-%d"), days_bulk))
        )

        # Save health data to CSV file
        if os.path.isfile(HEALTH_FILE):
            stats.to_csv(HEALTH_FILE, mode='a', header=False)
        else:
            stats.to_csv(HEALTH_FILE, mode='w')

        # Fetch activity data for the period
        logger.debug("Extracting Activities")
        try:
            activities = pd.json_normalize(
                garmin.get_activities_by_date(start.isoformat(), loop_end.isoformat(), activitytype))
            activities.set_index("startTimeLocal", inplace=True)

            # Save activity data to CSV file
            if os.path.isfile(ACTIVITIES_FILE):
                activities.to_csv(ACTIVITIES_FILE, mode='a', header=False)
            else:
                activities.to_csv(ACTIVITIES_FILE, mode='w')
        except:
            logger.info(f"No Activities for the current period")

        # Move to the next period
        start += timedelta(days=days_bulk)

# Main function
def main():
    args = parse_args()
    logger.setLevel(logging.getLevelNamesMapping()[args.log_level])
    logger.debug("Init Garming Connect")
    garmin = init_api(args.username,args.password)
    if garmin:
        fetch_data(garmin, args.start_date, args.end_date, args.days)
        logger.info("Data successfully saved to garmin_health_data.csv")

if __name__ == "__main__":
    main()
    


