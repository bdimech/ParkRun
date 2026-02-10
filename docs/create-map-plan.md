# Implementation Plan: Plotly Map for ParkRun Dashboard

## Overview
Add an interactive Plotly map below the existing chart showing ParkRun race locations with hover statistics (race count, best time, average time).

## Architecture Decision
**Map Type:** Plotly Scattermapbox with OpenStreetMap tiles (free, no API key)
**Layout:** Vertical stack - map positioned below existing chart
**Data Storage:** CSV file for location coordinates (matches existing pattern)

## Implementation Steps

### 1. Create Location Coordinates Data
**File:** `data/parkrun_locations.csv`

Create CSV with columns:
- Event (matches Event column in results.csv)
- Latitude
- Longitude
- State (optional, for disambiguation)

**Initial Setup:**
- Use geopy library with Nominatim geocoder (free)
- Create utility function: `geocode_new_locations()` in `dashboard/data_loader.py`
- Manually create initial file with common locations OR let auto-geocoding populate it

**Sample data:**
```csv
Event,Latitude,Longitude,State
Largs Bay,-34.8345,138.4916,SA
Kirkdale Reserve,-34.7381,138.6582,SA
```

**Auto-Update Behavior (NEW):**
When `--update` is run:
1. After scraping results, extract unique event names from new data
2. Load existing `parkrun_locations.csv`
3. Find events in results that are NOT in locations file
4. Geocode ONLY those new locations (incremental update)
5. Append new locations to `parkrun_locations.csv`
6. Log which locations were added

This ensures:
- No re-downloading of existing coordinates
- Automatic discovery of new race locations
- Minimal API calls to geocoding service

### 2. Add Map Creation Function
**File:** `dashboard/charts.py`

Add new function following existing `create_results_chart()` pattern:

```python
def create_location_map(df, locations_df):
    """
    Create interactive map of ParkRun race locations with statistics.

    Args:
        df: Results DataFrame (Event, Date, TimeSeconds, etc.)
        locations_df: Location coords (Event, Latitude, Longitude)

    Returns:
        str: HTML div with Plotly map
    """
```

**Implementation details:**
- Use `plotly.graph_objects.Scattermapbox`
- Aggregate stats per location:
  - Race count: `df.groupby('Event').size()`
  - Best time: `df.groupby('Event')['TimeSeconds'].min()`
  - Avg time: `df.groupby('Event')['TimeSeconds'].mean()`
- Marker styling:
  - Size: Proportional to race count (10-30px)
  - Color: Gradient by average time (blue=fast, red=slow)
  - Opacity: 0.7
- Hover template showing all three stats
- Map config:
  - Center: Auto-calculate from coordinates mean
  - Zoom: Level 5 (shows Australia)
  - Style: 'open-street-map'
  - Height: 600px

### 3. Add Location Data Functions
**File:** `dashboard/data_loader.py`

Add two functions:

**3a. Load existing locations:**
```python
def load_location_data(csv_path='data/parkrun_locations.csv'):
    """
    Load ParkRun location coordinates from CSV.

    Returns:
        DataFrame with Event, Latitude, Longitude columns
    """
    # Handle missing file gracefully
    # Log warning if file not found
    # Return empty DataFrame if missing
```

**3b. Geocode new locations (called during --update):**
```python
def geocode_new_locations(results_df, locations_csv='data/parkrun_locations.csv'):
    """
    Geocode any new event locations found in results that aren't in locations file.
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

    # 4. Geocode new events
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    import time

    geolocator = Nominatim(user_agent="parkrun_dashboard")
    new_rows = []

    for event in new_events:
        try:
            # Search for "parkrun [event name], Australia"
            query = f"parkrun {event}, Australia"
            location = geolocator.geocode(query, timeout=10)

            if location:
                new_rows.append({
                    'Event': event,
                    'Latitude': location.latitude,
                    'Longitude': location.longitude,
                    'State': ''  # Can be filled manually later
                })
                logger.info(f"Geocoded {event}: ({location.latitude}, {location.longitude})")
            else:
                logger.warning(f"Could not geocode: {event}")

            # Rate limit: wait 1 second between requests (Nominatim requirement)
            time.sleep(1)

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for {event}: {e}")
            continue

    # 5. Append new locations to CSV
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        updated_df = pd.concat([existing_locations, new_df], ignore_index=True)
        updated_df.to_csv(locations_csv, index=False)
        logger.info(f"Added {len(new_rows)} new locations to {locations_csv}")

    return len(new_rows)
```

**3c. Integrate into update_results_from_web:**
Modify the existing `update_results_from_web()` function to call geocoding after results are saved:

```python
def update_results_from_web(results_path='data/results.csv', athletes_path='data/athletes.csv'):
    # ... existing code to scrape and save results ...

    # NEW: After saving results, geocode any new locations
    if update_successful:
        try:
            # Load the updated results
            updated_df = pd.read_csv(results_path, encoding='latin-1')
            # Geocode new locations
            new_count = geocode_new_locations(updated_df)
            if new_count > 0:
                logger.info(f"Geocoded {new_count} new race locations")
        except Exception as e:
            logger.error(f"Failed to geocode new locations: {e}")
            # Don't fail the entire update if geocoding fails

    return update_successful
```

### 4. Update Backend Route
**File:** `dashboard/routes.py`

Modify `index()` function:

**New imports:**
```python
from dashboard.charts import create_results_chart, create_location_map
from dashboard.data_loader import load_parkrun_data, ..., load_location_data
```

**Add map creation after chart:**
```python
# Create chart (existing)
chart_html = create_results_chart(df)

# NEW: Create map
locations_df = load_location_data()
if not locations_df.empty and not df.empty:
    map_html = create_location_map(df, locations_df)
else:
    map_html = '<div class="no-results">Location data not available.</div>'

# Pass both to template
return render_template('index.html',
                      ...,
                      chart_html=chart_html,
                      map_html=map_html)  # NEW
```

### 5. Update Frontend Template
**File:** `templates/index.html`

Add map container after existing chart container:

```html
<div class="chart-container">
    {{ chart_html|safe }}
</div>

<!-- NEW: Map container -->
<div class="map-container">
    {{ map_html|safe }}
</div>
```

### 6. Add CSS Styling
**File:** `static/style.css`

Add new styles:

```css
/* Map container */
.map-container {
    width: 100%;
    min-height: 600px;
    margin-top: 30px;
}

/* Optional visual separator */
.chart-container::after {
    content: '';
    display: block;
    height: 1px;
    background: linear-gradient(to right, transparent, #ddd, transparent);
    margin: 30px 0;
}
```

### 7. Dependencies
Add to `requirements.txt` (if not present):
```
geopy>=2.3.0
```

**Important Notes on Geocoding:**
- Uses OpenStreetMap Nominatim API (free, no API key required)
- Respects Nominatim usage policy: max 1 request per second (enforced with `time.sleep(1)`)
- Only geocodes NEW locations (incremental updates)
- If geocoding fails for a location, logs warning and continues (non-blocking)
- User-agent set to "parkrun_dashboard" as required by Nominatim

## Data Processing Details

**Joining locations with results:**
```python
# 1. Aggregate stats
stats_df = df.groupby('Event').agg({
    'TimeSeconds': ['count', 'min', 'mean'],
    'Date': 'max'
})

# 2. Join with coordinates
map_df = stats_df.merge(locations_df, on='Event', how='left')

# 3. Drop locations without coordinates (log warning)
map_df = map_df.dropna(subset=['Latitude', 'Longitude'])

# 4. Format times for display
map_df['BestTimeFormatted'] = map_df['BestTime'].apply(format_seconds_to_mmss)
map_df['AvgTimeFormatted'] = map_df['AvgTime'].apply(lambda x: format_seconds_to_mmss(int(x)))
```

## Critical Files to Modify

1. **dashboard/charts.py** - Add `create_location_map()` function
2. **dashboard/data_loader.py** - Add `load_location_data()` and `geocode_new_locations()` functions, modify `update_results_from_web()`
3. **dashboard/routes.py** - Modify `index()` to create and pass map
4. **templates/index.html** - Add map container div
5. **static/style.css** - Add map styling
6. **data/parkrun_locations.csv** - New file with coordinates (auto-populated during --update)

## Testing & Verification

### Unit Tests
1. Test `load_location_data()` loads CSV correctly
2. Test location coordinates are within Australia bounds
3. Test statistics aggregation (verify Largs Bay = 82 races)

### Integration Tests
1. Run dashboard and verify map displays below chart
2. Hover over markers - verify stats match data
3. Test with missing locations.csv - verify graceful degradation
4. Test responsive layout on mobile/tablet
5. **Test --update auto-geocoding:**
   - Delete one location from parkrun_locations.csv
   - Run `python app.py --update`
   - Verify the deleted location is re-geocoded and added back
   - Verify existing locations are NOT re-geocoded (check logs)
   - Verify only 1 new location was added (not all 77)

### Manual Verification
1. Check Largs Bay marker (most races) is largest
2. Verify hover shows: "Races: 82, Best Time: XX:XX, Avg Time: XX:XX"
3. Test zoom/pan controls work smoothly
4. Verify map centers on Australia automatically
5. Check all 77 locations appear (or log warnings for missing)

## Edge Cases to Handle

1. **Missing locations.csv** - Show friendly message, don't crash
2. **Location not in coordinates file** - Log warning, skip marker
3. **Empty results for athlete** - Don't display map
4. **Single location** - Map centers on that location
5. **Overlapping markers** - Opacity allows visibility

## Success Criteria

✅ Map displays below chart on dashboard
✅ All unique race locations show as markers
✅ Marker size reflects number of races at location
✅ Hover shows race count, best time, and average time
✅ Map is interactive (zoom, pan)
✅ Responsive on mobile/tablet
✅ Gracefully handles missing data
✅ Loads in <2 seconds with all data
✅ **--update auto-geocodes NEW locations only** (not all locations)
✅ **Existing location coordinates are never re-downloaded**
✅ **New locations logged and appended to CSV**