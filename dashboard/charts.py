"""
Module for creating Plotly charts
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def format_seconds_to_mmss(seconds):
    """Convert seconds to MM:SS format for axis labels"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def create_results_chart(df):
    """
    Create an interactive scatter plot of ParkRun results.

    Args:
        df: DataFrame with columns: Event, Date, TimeSeconds, TimeFormatted,
            Position, AgeGrade, IsPB

    Returns:
        str: HTML div containing the Plotly chart
    """
    fig = go.Figure()

    # Sort by date to identify PBs chronologically
    df_sorted = df.sort_values('Date').reset_index(drop=True)

    # Identify all PBs (times faster than all previous times)
    pb_indices = []
    min_time_so_far = float('inf')
    for idx, row in df_sorted.iterrows():
        if row['TimeSeconds'] < min_time_so_far:
            pb_indices.append(idx)
            min_time_so_far = row['TimeSeconds']

    # Mark PBs in the sorted dataframe
    df_sorted['IsPB'] = False
    df_sorted.loc[pb_indices, 'IsPB'] = True

    # Get events ordered by race count (highest first)
    event_counts = df_sorted['Event'].value_counts()
    events = event_counts.index.tolist()

    # Color palette for different events
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    # Create event to color mapping
    event_colors = {event: colors[i % len(colors)] for i, event in enumerate(events)}

    for i, event in enumerate(events):
        event_df = df_sorted[df_sorted['Event'] == event]
        color = event_colors[event]
        race_count = len(event_df)

        # Separate PB and non-PB races
        non_pb_df = event_df[~event_df['IsPB']]
        pb_df = event_df[event_df['IsPB']]

        # Add non-PB points
        fig.add_trace(go.Scatter(
            x=non_pb_df['Date'],
            y=non_pb_df['TimeSeconds'],
            mode='markers',
            name=f"{event} ({race_count})",
            marker=dict(
                size=8,
                color=color,
                symbol='circle',
                line=dict(width=1, color='white')
            ),
            customdata=non_pb_df[['TimeFormatted', 'Position', 'AgeGrade']],
            hovertemplate=(
                '<b>%{fullData.name}</b><br>' +
                'Date: %{x|%d/%m/%Y}<br>' +
                'Time: %{customdata[0]}<br>' +
                'Position: %{customdata[1]}<br>' +
                'Age Grade: %{customdata[2]}<br>' +
                '<extra></extra>'
            ),
            legendgroup=event,
            showlegend=True
        ))

        # Add PB points with star markers
        if not pb_df.empty:
            fig.add_trace(go.Scatter(
                x=pb_df['Date'],
                y=pb_df['TimeSeconds'],
                mode='markers',
                name=f"{event} ({race_count})",
                marker=dict(
                    size=14,
                    color=color,
                    symbol='star',
                    line=dict(width=2, color='gold')
                ),
                customdata=pb_df[['TimeFormatted', 'Position', 'AgeGrade']],
                hovertemplate=(
                    '<b>%{fullData.name}</b><br>' +
                    'Date: %{x|%d/%m/%Y}<br>' +
                    'Time: %{customdata[0]}<br>' +
                    'Position: %{customdata[1]}<br>' +
                    'Age Grade: %{customdata[2]}<br>' +
                    '<b>Personal Best!</b><br>' +
                    '<extra></extra>'
                ),
                legendgroup=event,
                showlegend=False
            ))

    # Create custom tick values and labels for y-axis
    y_min = df['TimeSeconds'].min()
    y_max = df['TimeSeconds'].max()
    tick_interval = 60  # 1 minute intervals
    y_ticks = list(range(int(y_min // tick_interval) * tick_interval,
                         int(y_max // tick_interval + 1) * tick_interval + tick_interval,
                         tick_interval))
    y_tick_labels = [format_seconds_to_mmss(t) for t in y_ticks]

    # Fixed axis ranges
    x_min = pd.Timestamp('2022-01-01')
    x_max = pd.Timestamp('2027-01-01')
    y_min_fixed = 22 * 60  # 22 minutes in seconds
    y_max_fixed = 30 * 60  # 30 minutes in seconds

    # Create tick values for fixed y-axis range
    tick_interval = 60  # 1 minute intervals
    y_ticks_fixed = list(range(y_min_fixed, y_max_fixed + tick_interval, tick_interval))
    y_tick_labels_fixed = [format_seconds_to_mmss(t) for t in y_ticks_fixed]

    # Add monthly dotted vertical lines
    shapes = []
    current_date = x_min
    while current_date <= x_max:
        shapes.append(dict(
            type='line',
            x0=current_date,
            x1=current_date,
            y0=0,
            y1=1,
            yref='paper',
            line=dict(color='lightgray', width=1, dash='dot')
        ))
        current_date += pd.DateOffset(months=1)

    # Update layout
    fig.update_layout(
        title=dict(
            text='ParkRun Results Over Time',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Date',
            showgrid=True,
            gridcolor='lightgray',
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            range=[x_min, x_max],
            fixedrange=True,
            tickangle=-45,
            tickfont=dict(size=10),
            title_standoff=25
        ),
        yaxis=dict(
            title='Time',
            showgrid=True,
            gridcolor='lightgray',
            tickmode='array',
            tickvals=y_ticks_fixed,
            ticktext=y_tick_labels_fixed,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            range=[y_min_fixed, y_max_fixed],
            fixedrange=True,
            tickfont=dict(size=10),
            title_standoff=15
        ),
        hovermode='closest',
        plot_bgcolor='white',
        height=600,
        margin=dict(l=80, b=100, r=250, t=60),
        legend=dict(
            title='Race Location (Count)',
            yanchor='top',
            y=0.98,
            xanchor='left',
            x=1.02,
            bordercolor='black',
            borderwidth=2,
            bgcolor='white',
            font=dict(size=11),
            itemsizing='constant',
            tracegroupgap=8
        ),
        shapes=shapes
    )

    # Convert to HTML
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
