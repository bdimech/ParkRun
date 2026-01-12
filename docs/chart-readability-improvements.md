# Plan: Improve Chart Readability (Issue #12)

## Summary
Enhance the ParkRun results chart with better legend handling, view toggle, and axis improvements.

## Requirements
1. **Legend - All locations with fixed height**
   - Show ALL race locations (no grouping/Other)
   - Fixed border height to fit ~11 items (Brendan's max)
   - Scrollable if more locations than fit
   - Title moved outside box, centered above

2. **View Toggle (under legend)**
   - "All Results": Dynamic zoom to fit all data (current behavior)
   - "Golden Zone": Fixed range - Y: 20:00-30:00, X: Jan 2022 - June 2026

3. **Minor Axis Gridlines**
   - Vertical gridlines on odd months only (Jan, Mar, May, Jul, Sep, Nov)

## File to Modify
- `dashboard/charts.py`

## Implementation Steps

### Step 1: Update legend configuration
```python
legend=dict(
    title=dict(
        text='Race Location (Count)',
        side='top'  # Title above legend
    ),
    yanchor='top',
    y=0.98,
    xanchor='left',
    x=1.02,
    bordercolor='black',
    borderwidth=2,
    bgcolor='white',
    font=dict(size=11),
    itemsizing='constant',
    tracegroupgap=8,
    itemclick='toggle',
    itemdoubleclick='toggleothers'
)
```

Note: Plotly's legend doesn't natively support scrolling within the legend box itself.
For scrollable behavior, we'll wrap the chart in a container and use CSS to handle overflow,
OR accept that all items show (Brendan has 11 which fits reasonably).

### Step 2: Add view toggle buttons using Plotly updatemenus
```python
updatemenus=[
    dict(
        type='buttons',
        direction='right',
        x=1.02,
        y=-0.15,  # Below legend
        xanchor='left',
        buttons=[
            dict(
                label='All Results',
                method='relayout',
                args=[{'xaxis.range': [x_min_all, x_max_all],
                       'yaxis.range': [y_min_all, y_max_all]}]
            ),
            dict(
                label='Golden Zone',
                method='relayout',
                args=[{'xaxis.range': ['2022-01-01', '2026-06-30'],
                       'yaxis.range': [20*60, 30*60]}]  # 20:00-30:00 in seconds
            )
        ]
    )
]
```

### Step 3: Update gridlines to odd months only
```python
# Generate shapes for odd months only
odd_months = [1, 3, 5, 7, 9, 11]  # Jan, Mar, May, Jul, Sep, Nov
shapes = []
current_date = x_min
while current_date <= x_max:
    if current_date.month in odd_months:
        shapes.append(dict(
            type='line',
            x0=current_date,
            x1=current_date,
            y0=0, y1=1,
            yref='paper',
            line=dict(color='lightgray', width=1, dash='dot')
        ))
    current_date += pd.DateOffset(months=1)
```

### Step 4: Move legend title outside box
Use annotation instead of legend title for better positioning:
```python
annotations=[
    dict(
        text='<b>Race Location (Count)</b>',
        x=1.02,
        y=1.02,
        xref='paper',
        yref='paper',
        xanchor='left',
        showarrow=False,
        font=dict(size=12)
    )
]
```

## Verification
1. Run `python app.py` and open dashboard
2. Verify legend shows all race locations for the athlete
3. Verify legend title appears above the legend box (not inside)
4. Click "All Results" button - chart should zoom to fit all data
5. Click "Golden Zone" button - chart should show fixed range (20:00-30:00, Jan 2022-June 2026)
6. Verify gridlines only appear on odd months (Jan, Mar, May, Jul, Sep, Nov)
7. Test with different athletes to ensure behavior is consistent
