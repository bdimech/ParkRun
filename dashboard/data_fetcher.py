"""
Module for fetching ParkRun data from the web
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re


class ParkRunScraperError(Exception):
    """Custom exception for scraping errors"""
    pass


class NameValidationError(ParkRunScraperError):
    """Raised when scraped name doesn't match expected name"""
    pass


def fetch_parkrun_results(parkrun_id, expected_name=None):
    """
    Fetch ParkRun results for a given athlete ID from the website.

    Args:
        parkrun_id: The numeric ParkRun athlete ID (e.g., 7432768)
        expected_name: Optional name to validate against (e.g., "Brendan DIMECH")

    Returns:
        tuple: (athlete_name, DataFrame of results)

    Raises:
        ParkRunScraperError: If scraping fails
        NameValidationError: If name doesn't match expected
    """
    url = f"https://www.parkrun.com.au/parkrunner/{parkrun_id}/all/"

    # Use browser-like headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.parkrun.com.au/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ParkRunScraperError(f"Failed to fetch data for athlete {parkrun_id}: {e}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract athlete name from the page heading
    athlete_name = _extract_athlete_name(soup, parkrun_id)

    # Validate name if expected_name is provided
    if expected_name:
        if not _names_match(athlete_name, expected_name):
            raise NameValidationError(
                f"Name mismatch for ID {parkrun_id}: "
                f"expected '{expected_name}', got '{athlete_name}'"
            )

    # Parse the results table
    results_df = _parse_results_table(soup, athlete_name, parkrun_id)

    return athlete_name, results_df


def _extract_athlete_name(soup, parkrun_id):
    """
    Extract athlete name from the page.
    Looks for heading like "Brendan DIMECH (A7432768)"
    """
    # Try to find the main heading with the name
    # Look for h2 or similar containing the athlete ID
    id_pattern = f"A{parkrun_id}"

    for heading in soup.find_all(['h1', 'h2', 'h3']):
        text = heading.get_text(strip=True)
        if id_pattern in text:
            # Extract name (everything before the ID in parentheses)
            match = re.match(r'^(.+?)\s*\(' + id_pattern + r'\)', text)
            if match:
                return match.group(1).strip()

    # Fallback: search for any element containing the ID pattern
    for elem in soup.find_all(string=re.compile(id_pattern)):
        text = elem.strip()
        match = re.match(r'^(.+?)\s*\(' + id_pattern + r'\)', text)
        if match:
            return match.group(1).strip()

    raise ParkRunScraperError(f"Could not find athlete name for ID {parkrun_id}")


def _names_match(scraped_name, expected_name):
    """
    Check if scraped name matches expected name (case-insensitive).
    """
    return scraped_name.lower().strip() == expected_name.lower().strip()


def _parse_results_table(soup, athlete_name, parkrun_id):
    """
    Parse the results table from the page.

    Returns DataFrame with columns:
        Event, Run Date, Run Number, Pos, Time, Age Grade, PB, Athlete Name, Athlete ID
    """
    # Find the table with the expected columns
    table = None
    tables = soup.find_all('table')
    for t in tables:
        headers = [th.get_text(strip=True) for th in t.find_all('th')]
        # Look for the results table by its distinctive columns
        if 'Event' in headers and 'Run Date' in headers and 'Time' in headers:
            table = t
            break

    if not table:
        raise ParkRunScraperError("Could not find results table")

    # Parse table rows
    rows = []
    header_row = table.find('tr')
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

    # Map expected column names
    col_mapping = {
        'Event': 'Event',
        'Run Date': 'Run Date',
        'Run Number': 'Run Number',
        'Pos': 'Pos',
        'Time': 'Time',
        'Age Grade': 'Age Grade',
        'AgeGrade': 'Age Grade',  # Handle both formats
        'PB?': 'PB'
    }

    for tr in table.find_all('tr')[1:]:  # Skip header row
        cells = tr.find_all(['td', 'th'])
        if len(cells) >= len(headers):
            row = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i]
                    value = cell.get_text(strip=True)
                    # Map to standard column name
                    if header in col_mapping:
                        row[col_mapping[header]] = value
                    else:
                        row[header] = value

            # Add athlete info
            row['Athlete Name'] = athlete_name
            row['Athlete ID'] = str(parkrun_id)

            rows.append(row)

    if not rows:
        raise ParkRunScraperError("No results found in table")

    df = pd.DataFrame(rows)

    # Ensure required columns exist
    required_cols = ['Event', 'Run Date', 'Run Number', 'Pos', 'Time', 'Age Grade', 'PB', 'Athlete Name', 'Athlete ID']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''

    return df[required_cols]
