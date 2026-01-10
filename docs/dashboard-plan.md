# ParkRun Dashboard Implementation Plan

## Status: COMPLETED ✓

## Overview
Interactive dashboard displaying personal ParkRun results using Plotly (Python) for visualization with CSV data source.

## Data Structure (from CSV)
| Column | Example | Notes |
|--------|---------|-------|
| Event | Largs Bay | Race location name |
| Run Date | 10/05/2025 | DD/MM/YYYY format |
| Run Number | 333 | Event number at location |
| Pos | 30 | Finishing position |
| Time | 22:58 or 24:02:00 | MM:SS format (trailing :00 stripped) |
| Age Grade | 59.87% | Age-adjusted performance |
| PB | PB or empty | Personal best indicator |

## Dashboard Layout
```
+--------------------------------------------------------+
|            [Racer Name - Athlete ID]                   |  <- Title
+--------------------------------------------------------+
|                                           |  LEGEND    |
|              GRAPH                        |  --------  |
|  (Fixed axes: 22-30 mins, Jan 22-Jan 27) |  Largs (73)|
|    *     *      * (PB)                    |  Kirkdale  |
|      *      *                             |  Studley   |
|   *    *       *                          |  ...       |
|  ---------------------------------------- |            |
|        Date (X-axis, angled -45°)         |            |
+--------------------------------------------------------+
```

## Implementation Steps

### 1. Data Loading Module ✓
**File:** `dashboard/data_loader.py`

- Loads CSV from `data/results.csv` with latin-1 encoding
- Parses dates (DD/MM/YYYY -> datetime objects)
- Normalizes time format: strips trailing `:00` from times like `24:02:00`
- Converts times to seconds for plotting
- Formats times back to MM:SS for display
- Identifies PBs chronologically (times faster than all previous)
- Returns pandas DataFrame with processed data

### 2. Chart Module ✓
**File:** `dashboard/charts.py`

- Creates Plotly scatter chart with fixed axes
- **X-axis:** Date (Jan 2022 - Jan 2027, fixed range, -45° angle labels)
- **Y-axis:** Time in MM:SS format (22-30 minutes, fixed range)
- Each event = separate trace grouped by `legendgroup`
- **PB markers:** Gold-bordered stars (size 14) in race color
- **Regular markers:** Circles (size 8) in race color
- **Monthly gridlines:** Light gray dotted vertical lines
- **Border:** Black 2px border around plot area
- **Hover tooltips:** Event, date, time, position, age grade
- **Legend:** Right side with black border, shows race counts

### 3. Routes Update ✓
**File:** `dashboard/routes.py`

- Imports data_loader and charts modules
- Loads ParkRun data from CSV
- Extracts athlete information
- Generates interactive Plotly chart HTML
- Passes data to template for rendering

### 4. Template Update ✓
**File:** `templates/index.html`

- Header section with athlete name and ID
- Single-column layout with embedded chart
- Uses Jinja2 template variables for dynamic content
- Plotly chart rendered via CDN

### 5. Styling ✓
**File:** `static/style.css`

- Dashboard header with white background and shadow
- Chart container with full width
- Responsive max-width container (1400px)
- Clean, minimal design

## Files Created/Modified
| File | Status | Description |
|------|--------|-------------|
| `dashboard/data_loader.py` | ✓ Created | CSV parsing and time normalization |
| `dashboard/charts.py` | ✓ Created | Plotly chart generation with PB logic |
| `dashboard/__init__.py` | ✓ Modified | Fixed template/static folder paths |
| `dashboard/routes.py` | ✓ Modified | Integrated data loading and charting |
| `templates/index.html` | ✓ Modified | Dashboard layout with embedded chart |
| `static/style.css` | ✓ Modified | Dashboard styling |
| `requirements.txt` | ✓ Modified | Added plotly dependency |
| `data/results.csv` | ✓ Created | Sample ParkRun results data |

## Features Implemented
- ✓ Interactive Plotly scatter chart
- ✓ Fixed axis ranges (no auto-zoom when toggling races)
- ✓ PB markers with gold-bordered stars in race colors
- ✓ Legend with race counts, positioned on right side
- ✓ Monthly dotted gridlines
- ✓ Click legend to toggle races on/off
- ✓ Hover tooltips with detailed race information
- ✓ Time displayed in MM:SS format
- ✓ Date labels at -45° angle
- ✓ Black border around plot area
- ✓ Responsive layout

## Running the Dashboard
1. Install dependencies: `pip install -r requirements.txt`
2. Run Flask app: `python app.py`
3. Open http://localhost:5000
4. Toggle races via legend, hover for details
