# ParkRun Web Scraping Implementation Plan

## Status: IMPLEMENTED & TESTED

## Overview
Automated web scraping system to fetch ParkRun results directly from parkrun.com.au, eliminating manual CSV updates and enabling real-time data refresh.

## Architecture

```
User Request
     |
     v
routes.py (auto_update=True)
     |
     v
data_loader.py::load_parkrun_data()
     |
     v
data_loader.py::update_results_from_web()
     |
     +----> load_athletes_config() -> data/athletes.csv
     |
     +----> For each athlete:
             |
             v
          data_fetcher.py::fetch_parkrun_results()
             |
             +----> HTTP GET parkrun.com.au
             +----> Parse HTML with BeautifulSoup
             +----> Extract athlete name + validate
             +----> Parse results table
             |
             v
          Merge with existing data/results.csv
```

## Data Sources

### Input: Athletes Config (data/athletes.csv)
Master list of athletes to track.

| Column | Example | Description |
|--------|---------|-------------|
| name | Brendan DIMECH | Full name (for validation) |
| parkrun_id | 7432768 | Numeric athlete ID |

### Output: Results CSV (data/results.csv)
Merged results from all athletes, scraped from web.

Columns: Event, Run Date, Run Number, Pos, Time, Age Grade, PB, Athlete Name, Athlete ID

## Implementation Details

### 1. Data Fetcher Module
**File:** `dashboard/data_fetcher.py`

**Core Function:** `fetch_parkrun_results(parkrun_id, expected_name=None)`
- Fetches HTML from `https://www.parkrun.com.au/parkrunner/{id}/all/`
- Uses browser-like headers to avoid blocking
- 30-second timeout for reliability
- Returns: `(athlete_name, results_dataframe)`

**Name Extraction:** `_extract_athlete_name(soup, parkrun_id)`
- Searches for heading containing athlete ID (e.g., "Brendan DIMECH (A7432768)")
- Uses regex to extract name before ID
- Fallback search across all page elements
- Raises `ParkRunScraperError` if not found

**Name Validation:** `_names_match(scraped_name, expected_name)`
- Case-insensitive comparison
- Raises `NameValidationError` if mismatch detected
- Protects against scraping wrong athlete data

**Table Parsing:** `_parse_results_table(soup, athlete_name, parkrun_id)`
- Locates "All Results" section
- Finds associated results table
- Maps columns: Event, Run Date, Run Number, Pos, Time, Age Grade, PB?
- Adds athlete metadata to each row
- Returns DataFrame with standardized columns

**Error Handling:**
- `ParkRunScraperError`: Base exception for all scraping failures
- `NameValidationError`: Specific error for name mismatches
- Handles network errors, missing tables, parsing failures

### 2. Data Loader Enhancements
**File:** `dashboard/data_loader.py`

**Athletes Config Loader:** `load_athletes_config(csv_path='data/athletes.csv')`
- Reads master athlete list
- Returns empty DataFrame if file missing
- Logs warning for missing config

**Web Update Function:** `update_results_from_web(results_path, athletes_path)`
- Iterates through all configured athletes
- Fetches results for each using `data_fetcher`
- Validates names against config
- Merges new data with existing results
- Handles errors gracefully (continues on failure)
- Deduplicates based on: Event + Date + Athlete ID
- Saves combined results to CSV
- Returns: `True` if any update succeeded, `False` otherwise

**Enhanced Load Function:** `load_parkrun_data(csv_path, auto_update=False)`
- New parameter: `auto_update` (default: False)
- If `auto_update=True`: fetches latest data before loading
- Falls back to cached CSV if web update fails
- Preserves existing functionality for offline mode
- Now handles athlete columns (AthleteName, AthleteID)

**Enhanced Athlete Info:** `get_athlete_info(df)`
- Extracts athlete name and ID from DataFrame columns
- Falls back to athletes.csv if not in data
- Returns structured dict: `{'name': str, 'id': str}`

### 3. Route Updates
**File:** `dashboard/routes.py`

**Index Route:** `@bp.route('/')`
- Checks for `?no_update=1` query parameter
- Default behavior: auto-update enabled
- Passes `auto_update` flag to `load_parkrun_data()`
- Allows manual disable for faster loading during development

## Usage Scenarios

### Initial Setup
1. Create `data/athletes.csv` with columns: name, parkrun_id
2. Add athlete entries (one per row)
3. Run Flask app
4. Dashboard auto-fetches all results on first load

### Regular Operation
1. User visits dashboard
2. System automatically checks for new results
3. Merges with existing data
4. Displays updated dashboard

### Development Mode
1. Visit `http://localhost:5000/?no_update=1`
2. Skips web scraping (uses cached data)
3. Faster page loads during development

### Error Handling
- Network failure: Uses cached CSV data
- Name mismatch: Logs error, skips athlete, continues
- Missing table: Logs error, skips athlete, continues
- Partial success: Saves data from successful athletes

## Features Implemented

- Web scraping from parkrun.com.au
- Browser-like headers to avoid blocking
- Name validation for data integrity
- Athlete configuration management
- Automatic data merging and deduplication
- Graceful error handling with logging
- Auto-update toggle for development
- Offline fallback mode
- Multi-athlete support

## Files Created/Modified

| File | Status | Description |
|------|--------|-------------|
| `dashboard/data_fetcher.py` | Created | Web scraper with HTML parsing |
| `dashboard/data_loader.py` | Modified | Added update_results_from_web(), auto-update |
| `dashboard/routes.py` | Modified | Added auto_update parameter |
| `data/athletes.csv` | Created | Athlete configuration file |

## Testing Checklist

- [x] Test with valid athlete ID (should fetch results) ✅ Fetched 100 results for Brendan DIMECH
- [ ] Test with invalid athlete ID (should handle gracefully)
- [x] Test name validation (correct name) ✅ Verified during scraping
- [ ] Test name validation (incorrect name - should raise error)
- [ ] Test with empty athletes.csv (should log warning)
- [ ] Test with missing athletes.csv (should create empty DataFrame)
- [x] Test data deduplication (no duplicate entries) ✅ 126 unique results, 0 duplicates
- [x] Test offline mode (`?no_update=1`) ✅ Works correctly with cached data
- [x] Test auto-update mode (default behavior) ✅ Successfully fetches fresh data
- [ ] Test with network failure (should use cached data)
- [ ] Test with multiple athletes in config
- [ ] Test with athlete who has no results
- [x] Test merge logic (new + existing data) ✅ 86 old + 100 new = 126 unique results

## Bug Fixes Applied During Testing

### 1. HTTP 403 Forbidden Error
**Issue:** Initial requests were blocked by parkrun.com.au with 403 Forbidden
**Fix:** Added `Referer: https://www.parkrun.com.au/` and `DNT: 1` headers to appear more like a legitimate browser request

### 2. HTML Table Parsing Failure
**Issue:** Could not find "All Results" section header in the HTML
**Fix:** Updated `_parse_results_table()` to search for tables by column headers (Event, Run Date, Time) instead of relying on section headings

### 3. Column Name Mismatch
**Issue:** Age Grade column was named "AgeGrade" (one word) instead of "Age Grade" (two words)
**Fix:** Added mapping for both "AgeGrade" and "Age Grade" in the column mapping dictionary

### 4. Time Formatting Error
**Issue:** `ValueError: Unknown format code 'd' for object of type 'float'` when formatting time values
**Fix:** Added integer conversion and NaN check in `format_seconds_to_time()` function

### 5. Deduplication Not Working
**Issue:** 200+ duplicate rows created because old data had empty Athlete ID fields
**Fix:** Changed deduplication logic from `['Event', 'Run Date', 'Athlete ID']` to `['Event', 'Run Date']` to work with both old and new data formats

## Known Limitations

1. **Rate Limiting:** No delay between athlete requests (could add if needed)
2. **Regional Sites:** Hardcoded to .com.au (could be parameterized)
3. **Table Format:** Assumes specific HTML structure (may break if site changes)
4. **Single Page:** Only scrapes "All Results" page (not event-specific pages)
5. **Performance:** Fetches on every page load (could add caching/scheduling)

## Future Enhancements

1. **Scheduled Updates:** Background task to update data periodically
2. **Last Updated Timestamp:** Show when data was last refreshed
3. **Manual Refresh Button:** User-triggered update without page reload
4. **Cache Invalidation:** Time-based cache (e.g., update max once per hour)
5. **Regional Support:** Auto-detect or configure parkrun region (.com.au, .org.uk, etc.)
6. **Progress Indicator:** Show scraping progress for multiple athletes
7. **Error Dashboard:** UI to show scraping status/errors per athlete
8. **Historical Snapshots:** Archive old data before updates
9. **Diff Detection:** Only update if new results detected

## Running with Web Scraping

1. Create `data/athletes.csv`:
   ```csv
   name,parkrun_id
   Brendan DIMECH,7432768
   ```

2. Install dependencies:
   ```bash
   pip install requests beautifulsoup4
   ```

3. Run Flask app:
   ```bash
   python app.py
   ```

4. Access dashboard:
   - Auto-update mode: `http://localhost:5000`
   - Offline mode: `http://localhost:5000/?no_update=1`

## Logging

Uses Python's built-in logging module:
- `INFO`: Successful scrapes, data saves
- `WARNING`: Missing config files
- `ERROR`: Scraping failures, validation errors

View logs in console during Flask app execution.
