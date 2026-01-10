# ParkRun Dashboard Implementation Plan

## Overview
Build an interactive dashboard displaying personal ParkRun results using Plotly (Python) for visualization.

## Data Structure (from CSV)
| Column | Example | Notes |
|--------|---------|-------|
| Event | Largs Bay | Race location name |
| Run Date | 10/05/2025 | DD/MM/YYYY format |
| Run Number | 333 | Event number at location |
| Pos | 30 | Finishing position |
| Time | 22:58 or 24:02:00 | Inconsistent format (MM:SS or HH:MM:SS) |
| Age Grade | 59.87% | Age-adjusted performance |
| PB | PB or empty | Personal best indicator |

## Dashboard Layout
```
+------------------------------------------+
|        [Racer Name - Athlete ID]         |  <- Title
+------------------------------------------+
|              |                           |
|   LEGEND     |         GRAPH             |
|   --------   |                           |
|   [x] Largs  |    *     *                |
|   [x] Kirkd  |      *      * (PB)        |
|   [ ] Stud   |   *    *       *          |
|              |  ----------------------   |
|              |        Date (X-axis)      |
|              |                           |
+------------------------------------------+
```

## Implementation Steps

### 1. Data Loading Module
**File:** `dashboard/data_loader.py` (new)

- Load CSV from `data/results.csv`
- Parse dates (DD/MM/YYYY -> datetime)
- Normalize time format to seconds (handle both MM:SS and HH:MM:SS)
- Clean PB column to boolean
- Return pandas DataFrame

### 2. Chart Module
**File:** `dashboard/charts.py` (new)

- Create Plotly scatter chart
- X-axis: Run Date (chronological)
- Y-axis: Time in seconds (inverted - lower times at top)
- Each Event is a separate trace (enables built-in legend filtering)
- PB markers: larger size, different color/symbol
- Hover template: Event name, Date, Time, Position, Age Grade
- Click: Show detailed info panel

### 3. Routes Update
**File:** `dashboard/routes.py`

- Load data via data_loader
- Generate chart via charts module
- Pass chart HTML and metadata to template

### 4. Template Update
**File:** `templates/index.html`

- Title section with racer name/ID
- Two-column layout: legend (left), chart (center)
- Embed Plotly chart (uses plotly.js CDN)
- Custom legend styling with checkboxes

### 5. Styling
**File:** `static/style.css`

- Flexbox layout for legend + chart
- Legend panel styling
- Responsive design

## Files to Create/Modify
| File | Action |
|------|--------|
| `dashboard/data_loader.py` | Create |
| `dashboard/charts.py` | Create |
| `dashboard/routes.py` | Modify |
| `templates/index.html` | Modify |
| `static/style.css` | Modify |
| `requirements.txt` | Add plotly |

## Verification
1. Run Flask app: `python app.py`
2. Open http://localhost:5000
3. Verify:
   - Chart displays all races with correct dates/times
   - PB races are visually distinct
   - Clicking legend items toggles race visibility
   - Hover shows race details
   - Title shows racer info
