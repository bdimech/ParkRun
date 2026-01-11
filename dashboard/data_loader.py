"""
Module for loading and processing ParkRun data from CSV and web scraping
"""
import pandas as pd
from datetime import datetime
import os
import logging

from dashboard.data_fetcher import (
    fetch_parkrun_results,
    ParkRunScraperError,
    NameValidationError
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_time_to_seconds(time_str):
    """
    Convert time string to seconds.
    Handles MM:SS format. Strips trailing :00 from times like 24:02:00.

    Args:
        time_str: Time string (e.g., "22:58" or "24:02:00")

    Returns:
        int: Time in seconds
    """
    if pd.isna(time_str):
        return None

    time_str = str(time_str).strip()

    # Remove trailing :00 if present (e.g., "24:02:00" -> "24:02")
    if time_str.endswith(':00'):
        time_str = time_str[:-3]

    parts = time_str.split(':')

    if len(parts) == 2:
        # MM:SS format
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    else:
        return None


def format_seconds_to_time(seconds):
    """
    Convert seconds back to MM:SS format for display.

    Args:
        seconds: Time in seconds

    Returns:
        str: Formatted time string (MM:SS)
    """
    if seconds is None or pd.isna(seconds):
        return None

    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def load_athletes_config(csv_path='data/athletes.csv'):
    """
    Load master list of athletes to scrape.

    Args:
        csv_path: Path to athletes CSV file

    Returns:
        pandas.DataFrame: Athletes with columns 'name' and 'parkrun_id'
    """
    if not os.path.exists(csv_path):
        logger.warning(f"Athletes config file not found: {csv_path}")
        return pd.DataFrame(columns=['name', 'parkrun_id'])

    return pd.read_csv(csv_path)


def update_results_from_web(results_path='data/results.csv', athletes_path='data/athletes.csv'):
    """
    Fetch latest results for all configured athletes and merge with existing data.

    Args:
        results_path: Path to results CSV file
        athletes_path: Path to athletes config CSV file

    Returns:
        bool: True if update was successful, False otherwise
    """
    athletes_df = load_athletes_config(athletes_path)

    if athletes_df.empty:
        logger.warning("No athletes configured for scraping")
        return False

    # Load existing results if file exists
    if os.path.exists(results_path):
        existing_df = pd.read_csv(results_path, encoding='latin-1')
    else:
        existing_df = pd.DataFrame()

    all_new_results = []
    update_successful = False

    for _, athlete in athletes_df.iterrows():
        name = athlete['name']
        parkrun_id = athlete['parkrun_id']

        try:
            logger.info(f"Fetching results for {name} (ID: {parkrun_id})")
            scraped_name, results_df = fetch_parkrun_results(parkrun_id, expected_name=name)
            all_new_results.append(results_df)
            logger.info(f"Fetched {len(results_df)} results for {scraped_name}")
            update_successful = True

        except NameValidationError as e:
            logger.error(f"Name validation failed: {e}")
            continue

        except ParkRunScraperError as e:
            logger.error(f"Failed to scrape {name}: {e}")
            continue

        except Exception as e:
            logger.error(f"Unexpected error scraping {name}: {e}")
            continue

    if all_new_results:
        # Combine all new results
        new_df = pd.concat(all_new_results, ignore_index=True)

        if not existing_df.empty:
            # Merge with existing data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)

            # Remove duplicates based on Event and Run Date
            # (Athlete ID may be empty in old data)
            combined_df = combined_df.drop_duplicates(
                subset=['Event', 'Run Date'],
                keep='last'
            )
        else:
            combined_df = new_df

        # Save updated results
        combined_df.to_csv(results_path, index=False)
        logger.info(f"Saved {len(combined_df)} total results to {results_path}")

    return update_successful


def load_parkrun_data(csv_path='data/results.csv', auto_update=False):
    """
    Load and process ParkRun results from CSV.

    Args:
        csv_path: Path to CSV file
        auto_update: If True, fetch latest data from web before loading

    Returns:
        pandas.DataFrame: Processed results with columns:
            - Event: Race location
            - Date: datetime object
            - RunNumber: Event number
            - Position: Finishing position
            - TimeSeconds: Time in seconds
            - TimeFormatted: Time as MM:SS string
            - AgeGrade: Age grade percentage
            - IsPB: Boolean indicating personal best
            - AthleteName: Name of the athlete
            - AthleteID: ParkRun ID of the athlete
    """
    # Optionally update from web first
    if auto_update:
        try:
            update_results_from_web(csv_path)
        except Exception as e:
            logger.error(f"Failed to update from web: {e}")
            # Continue with cached data

    # Load CSV with latin-1 encoding to handle special characters
    df = pd.read_csv(csv_path, encoding='latin-1')

    # Parse dates (DD/MM/YYYY format)
    df['Date'] = pd.to_datetime(df['Run Date'], format='%d/%m/%Y')

    # Convert time to seconds
    df['TimeSeconds'] = df['Time'].apply(parse_time_to_seconds)
    df['TimeFormatted'] = df['TimeSeconds'].apply(format_seconds_to_time)

    # Clean PB column to boolean
    df['IsPB'] = df['PB'].notna() & (df['PB'].str.strip() != '')

    # Rename columns for clarity
    rename_map = {
        'Run Number': 'RunNumber',
        'Pos': 'Position',
        'Age Grade': 'AgeGrade'
    }

    # Add athlete columns if they exist
    if 'Athlete Name' in df.columns:
        rename_map['Athlete Name'] = 'AthleteName'
    if 'Athlete ID' in df.columns:
        rename_map['Athlete ID'] = 'AthleteID'

    df = df.rename(columns=rename_map)

    # Determine columns to select based on what's available
    base_cols = ['Event', 'Date', 'RunNumber', 'Position', 'TimeSeconds',
                 'TimeFormatted', 'AgeGrade', 'IsPB']

    if 'AthleteName' in df.columns:
        base_cols.append('AthleteName')
    if 'AthleteID' in df.columns:
        base_cols.append('AthleteID')

    df = df[base_cols]

    # Sort by date
    df = df.sort_values('Date')

    return df


def get_athlete_info(df):
    """
    Extract athlete information from the dataset.

    Args:
        df: DataFrame of results

    Returns:
        dict: Athlete info with keys 'name' and 'id'
    """
    if 'AthleteName' in df.columns and not df['AthleteName'].empty:
        # Get the first athlete's info (or could be extended for multiple)
        name = df['AthleteName'].iloc[0] if len(df) > 0 else 'Unknown'
        athlete_id = df['AthleteID'].iloc[0] if 'AthleteID' in df.columns and len(df) > 0 else 'Unknown'
        return {
            'name': name,
            'id': str(athlete_id)
        }

    # Fallback to loading from athletes config
    athletes_df = load_athletes_config()
    if not athletes_df.empty:
        return {
            'name': athletes_df.iloc[0]['name'],
            'id': str(athletes_df.iloc[0]['parkrun_id'])
        }

    return {
        'name': 'Athlete',
        'id': 'TBD'
    }
