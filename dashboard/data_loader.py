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
            # Normalize Athlete ID to string for consistent deduplication
            if 'Athlete ID' in existing_df.columns:
                existing_df['Athlete ID'] = existing_df['Athlete ID'].astype(str)
            if 'Athlete ID' in new_df.columns:
                new_df['Athlete ID'] = new_df['Athlete ID'].astype(str)

            # Merge with existing data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)

            # Remove duplicates based on Event, Run Date, and Athlete ID
            # Each athlete can have one result per event per date
            combined_df = combined_df.drop_duplicates(
                subset=['Event', 'Run Date', 'Athlete ID'],
                keep='last'
            )
        else:
            combined_df = new_df

        # Save updated results
        combined_df.to_csv(results_path, index=False)
        logger.info(f"Saved {len(combined_df)} total results to {results_path}")

        # Geocode any new locations
        if update_successful:
            try:
                new_count = geocode_new_locations(combined_df)
                if new_count > 0:
                    logger.info(f"Geocoded {new_count} new race locations")
            except Exception as e:
                logger.error(f"Failed to geocode new locations: {e}")
                # Don't fail the entire update if geocoding fails

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


def load_location_data(csv_path='data/parkrun_locations.csv'):
    """
    Load ParkRun location coordinates from CSV.

    Args:
        csv_path: Path to locations CSV file

    Returns:
        pandas.DataFrame: Location data with columns Event, Latitude, Longitude
    """
    if not os.path.exists(csv_path):
        logger.warning(f"Location data not found: {csv_path}")
        return pd.DataFrame(columns=['Event', 'Latitude', 'Longitude', 'State'])

    return pd.read_csv(csv_path)


def build_url_slug(event_name: str) -> str:
    """Convert an event name to a parkrun URL slug (lowercase, no spaces or commas)."""
    return event_name.lower().replace(' ', '').replace(',', '')


def extract_coordinates(html: str):
    """
    Parse a geo.position meta tag from HTML and return (latitude, longitude).
    Returns None if the tag is missing or malformed.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    geo_tag = soup.find('meta', attrs={'name': 'geo.position'})
    if not geo_tag or not geo_tag.get('content'):
        return None
    try:
        parts = geo_tag['content'].split(';')
        if len(parts) != 2:
            return None
        return (float(parts[0]), float(parts[1]))
    except (ValueError, IndexError):
        return None


def geocode_single_event(event: str, fetch_fn, prompt_fn, confirm_fn):
    """
    Attempt to geocode a single event, with fallback prompts.

    Args:
        event:      Event name (e.g. "Largs Bay")
        fetch_fn:   fn(url) -> (status_code, html)
        prompt_fn:  fn(message) -> str  (user input for manual URL, or "")
        confirm_fn: fn(message) -> bool (user confirms UK fallback)

    Returns:
        (latitude, longitude) tuple, or None if all attempts fail.
    """
    slug = build_url_slug(event)
    au_url = f"https://www.parkrun.com.au/{slug}/"

    status, html = fetch_fn(au_url)

    if status == 200:
        return extract_coordinates(html)

    # .com.au failed — ask for a manual URL
    manual_url = prompt_fn(
        f'Could not find "{event}" on parkrun.com.au. Enter URL (or press Enter to skip): '
    ).strip()

    if manual_url:
        status, html = fetch_fn(manual_url)
        if status == 200:
            return extract_coordinates(html)
        return None

    # User skipped — offer UK fallback as last resort
    if confirm_fn(f'Try UK parkrun (parkrun.org.uk) for "{event}"? [y/N]: '):
        uk_url = f"https://www.parkrun.org.uk/{slug}/"
        status, html = fetch_fn(uk_url)
        if status == 200:
            return extract_coordinates(html)

    return None


def geocode_new_locations(results_df, locations_csv='data/parkrun_locations.csv'):
    """
    Geocode any new event locations found in results that aren't in locations file.
    Scrapes coordinates from parkrun.com.au event pages (geo.position meta tag).
    Appends new coordinates to the CSV file.

    Args:
        results_df: DataFrame with Event column from scraped results
        locations_csv: Path to locations CSV file

    Returns:
        int: Number of new locations geocoded
    """
    # 1. Get unique events from results
    unique_events = results_df['Event'].unique()

    # 2. Load existing locations (or create empty if missing)
    if os.path.exists(locations_csv):
        existing_locations = pd.read_csv(locations_csv)
        existing_events = set(existing_locations['Event'].values)
    else:
        existing_locations = pd.DataFrame(columns=['Event', 'Latitude', 'Longitude', 'State'])
        existing_events = set()

    # 3. Find new events that need geocoding
    new_events = set(unique_events) - existing_events

    if not new_events:
        logger.info("No new locations to geocode")
        return 0

    logger.info(f"Geocoding {len(new_events)} new locations: {new_events}")

    import requests
    import time

    HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    def fetch_fn(url):
        try:
            response = requests.get(url, headers=HTTP_HEADERS, timeout=10)
            return response.status_code, response.text
        except requests.RequestException as e:
            logger.error(f"Network error fetching {url}: {e}")
            return 0, ""

    def prompt_fn(msg):
        return input(msg)

    def confirm_fn(msg):
        return input(msg).strip().lower() == 'y'

    new_rows = []

    for event in new_events:
        try:
            coords = geocode_single_event(event, fetch_fn, prompt_fn, confirm_fn)
            if coords:
                latitude, longitude = coords
                new_rows.append({
                    'Event': event,
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'State': ''
                })
                logger.info(f"Geocoded {event}: ({latitude}, {longitude})")
            else:
                logger.warning(f"Could not geocode {event} — skipping.")

            time.sleep(1)

        except Exception as e:
            logger.error(f"Unexpected error geocoding {event}: {e}")
            continue

    # 5. Append new locations to CSV
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        updated_df = pd.concat([existing_locations, new_df], ignore_index=True)
        updated_df.to_csv(locations_csv, index=False)
        logger.info(f"Added {len(new_rows)} new locations to {locations_csv}")

    return len(new_rows)
