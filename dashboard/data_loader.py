"""
Module for loading and processing ParkRun data from CSV
"""
import pandas as pd
from datetime import datetime


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
    if seconds is None:
        return None

    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def load_parkrun_data(csv_path='data/results.csv'):
    """
    Load and process ParkRun results from CSV.

    Args:
        csv_path: Path to CSV file

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
    """
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
    df = df.rename(columns={
        'Run Number': 'RunNumber',
        'Pos': 'Position',
        'Age Grade': 'AgeGrade'
    })

    # Select and order columns
    df = df[['Event', 'Date', 'RunNumber', 'Position', 'TimeSeconds',
             'TimeFormatted', 'AgeGrade', 'IsPB']]

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
    # For now, return placeholder - can be enhanced later
    return {
        'name': 'Athlete',
        'id': 'TBD'
    }
